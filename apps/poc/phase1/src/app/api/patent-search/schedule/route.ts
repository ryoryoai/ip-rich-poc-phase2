import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

interface PatentSearchScheduleRequest {
  patentNumber: string;
  claimText: string;
  priority?: number;
  scheduledFor?: string;
  searchType?: 'infringement_check' | 'revenue_estimation' | 'comprehensive';
}

export async function POST(request: NextRequest) {
  try {
    const body: PatentSearchScheduleRequest = await request.json();
    const {
      patentNumber,
      claimText,
      priority = 5,
      scheduledFor,
      searchType = 'infringement_check'
    } = body;

    // バリデーション
    if (!patentNumber || !claimText) {
      return NextResponse.json(
        { error: 'Patent number and claim text are required' },
        { status: 400 }
      );
    }

    console.log(`[Schedule] Creating job for patent: ${patentNumber} with priority: ${priority}`);

    // 同じ特許番号でpending/researchingのジョブがあるかチェック
    const existingJob = await prisma.analysis_jobs.findFirst({
      where: {
        patentNumber,
        status: { in: ['pending', 'researching'] }
      }
    });

    if (existingJob) {
      console.log(`[Schedule] Found existing job for patent ${patentNumber}: ${existingJob.id}`);
      return NextResponse.json({
        job_id: existingJob.id,
        status: existingJob.status,
        message: 'Job already exists and is being processed',
        existing: true
      });
    }

    // ジョブを作成（Dream Researchのようにすぐには実行しない）
    const job = await prisma.analysis_jobs.create({
      data: {
        status: 'pending',
        patentNumber,
        claimText,
        companyName: 'To be detected', // Cronジョブで自動検出
        productName: 'To be detected',  // Cronジョブで自動検出
        priority,
        scheduledFor: scheduledFor ? new Date(scheduledFor) : null,
        searchType,
        progress: 0,
        retryCount: 0,
        maxRetries: 3
      }
    });

    console.log(`[Schedule] Job created: ${job.id} for patent ${patentNumber}`);

    // 高優先度（9以上）かつ即時実行の場合
    if (priority >= 9 && !scheduledFor) {
      console.log(`[Schedule] High priority job, triggering immediate processing`);

      // Cronエンドポイントを内部的に呼び出して即座に処理開始
      try {
        const cronResponse = await fetch(
          `${process.env.NEXT_PUBLIC_APP_URL}/api/cron/check-and-do`,
          {
            method: 'POST',
            headers: {
              'X-Cron-Secret': process.env.CRON_SECRET_KEY!,
              'Content-Type': 'application/json'
            }
          }
        );

        if (cronResponse.ok) {
          console.log(`[Schedule] Immediate processing triggered successfully`);
        }
      } catch (error) {
        console.error('[Schedule] Failed to trigger immediate processing:', error);
        // エラーは無視（次回のCronで処理される）
      }
    }

    // 推定完了時刻を計算
    const estimatedCompletion = calculateEstimatedCompletion(priority, scheduledFor);

    return NextResponse.json({
      job_id: job.id,
      status: 'scheduled',
      priority,
      scheduled_for: job.scheduledFor?.toISOString(),
      estimated_completion: estimatedCompletion,
      message: getScheduleMessage(priority, scheduledFor)
    });

  } catch (error) {
    console.error('[Schedule] Error:', error);
    return NextResponse.json(
      {
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  } finally {
    await prisma.$disconnect();
  }
}

// 推定完了時刻を計算
function calculateEstimatedCompletion(priority: number, scheduledFor?: string): string {
  const now = new Date();
  let executionTime: Date;

  if (scheduledFor) {
    executionTime = new Date(scheduledFor);
  } else {
    // 優先度に基づいて実行時刻を推定
    const jstOffset = 9 * 60 * 60 * 1000; // JST offset
    const currentHour = (now.getTime() + jstOffset) / (60 * 60 * 1000) % 24;

    if (priority >= 9) {
      // 即座に実行
      executionTime = new Date(now.getTime() + 15 * 60 * 1000); // 15分後
    } else if (priority >= 8) {
      // 高優先度: 22:00 JST
      executionTime = getNextExecutionTime(22, jstOffset);
    } else if (priority >= 4) {
      // 中優先度: 23:00 JST
      executionTime = getNextExecutionTime(23, jstOffset);
    } else {
      // 低優先度: 00:00 JST
      executionTime = getNextExecutionTime(0, jstOffset);
    }
  }

  // 処理時間（約15-30分）を追加
  const completionTime = new Date(executionTime.getTime() + 30 * 60 * 1000);
  return completionTime.toISOString();
}

// 次の実行時刻を取得
function getNextExecutionTime(targetHourJST: number, jstOffset: number): Date {
  const now = new Date();
  const nowJST = new Date(now.getTime() + jstOffset);
  const currentHour = nowJST.getUTCHours();

  let executionTime = new Date(nowJST);
  executionTime.setUTCHours(targetHourJST, 0, 0, 0);

  // 既に過ぎている場合は翌日
  if (currentHour >= targetHourJST) {
    executionTime.setUTCDate(executionTime.getUTCDate() + 1);
  }

  // UTCに戻す
  return new Date(executionTime.getTime() - jstOffset);
}

// スケジュールメッセージを生成
function getScheduleMessage(priority: number, scheduledFor?: string): string {
  if (scheduledFor) {
    return `ジョブは指定された時刻に実行されます`;
  }

  if (priority >= 9) {
    return '高優先度ジョブとして即座に処理を開始します';
  } else if (priority >= 8) {
    return '本日22:00（JST）に処理を開始します';
  } else if (priority >= 4) {
    return '本日23:00（JST）に処理を開始します';
  } else {
    return '本日深夜0:00（JST）に処理を開始します';
  }
}

// GET: ジョブ一覧を取得
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const status = searchParams.get('status');
    const limit = parseInt(searchParams.get('limit') || '50');

    const where: any = {};
    if (status) {
      where.status = status;
    }

    const jobs = await prisma.analysis_jobs.findMany({
      where,
      orderBy: [
        { priority: 'desc' },
        { createdAt: 'desc' }
      ],
      take: limit,
      select: {
        id: true,
        patentNumber: true,
        status: true,
        priority: true,
        scheduledFor: true,
        searchType: true,
        infringementScore: true,
        createdAt: true,
        startedAt: true,
        finishedAt: true,
        progress: true
      }
    });

    // 優先度でグループ化
    const grouped = {
      high: jobs.filter(j => j.priority >= 8),
      medium: jobs.filter(j => j.priority >= 4 && j.priority < 8),
      low: jobs.filter(j => j.priority < 4),
      stats: {
        total: jobs.length,
        pending: jobs.filter(j => j.status === 'pending').length,
        researching: jobs.filter(j => j.status === 'researching').length,
        completed: jobs.filter(j => j.status === 'completed').length,
        failed: jobs.filter(j => j.status === 'failed').length
      }
    };

    return NextResponse.json(grouped);

  } catch (error) {
    console.error('[Schedule] Error fetching jobs:', error);
    return NextResponse.json(
      { error: 'Failed to fetch jobs' },
      { status: 500 }
    );
  } finally {
    await prisma.$disconnect();
  }
}