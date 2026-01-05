import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function POST(
  request: NextRequest,
  { params }: { params: { job_id: string } }
) {
  try {
    const jobId = params.job_id;

    // 現在のジョブを取得
    const job = await prisma.analysis_jobs.findUnique({
      where: { id: jobId },
    });

    if (!job) {
      return NextResponse.json(
        { error: 'Job not found' },
        { status: 404 }
      );
    }

    // failedステータスのジョブのみリトライ可能
    if (job.status !== 'failed') {
      return NextResponse.json(
        { error: `Cannot retry job with status: ${job.status}` },
        { status: 400 }
      );
    }

    console.log(`[API] Retrying failed job: ${jobId}`);

    // ジョブをpendingに戻す
    const updatedJob = await prisma.analysis_jobs.update({
      where: { id: jobId },
      data: {
        status: 'pending',
        progress: 0,
        errorMessage: null,
        retryCount: job.retryCount + 1,
        openaiResponseId: null, // 前回のレスポンスIDをクリア
        researchResults: null,   // 前回の結果をクリア
        updatedAt: new Date(),
      },
    });

    console.log(`[API] Job ${jobId} reset to pending status for retry`);

    // ステータスレスポンスを返す
    return NextResponse.json({
      job_id: updatedJob.id,
      status: updatedJob.status,
      progress: updatedJob.progress,
      error_message: null,
    });
  } catch (error) {
    console.error('[API] Error in /api/analyze/retry:', error);
    return NextResponse.json(
      {
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  } finally {
    await prisma.$disconnect();
  }
}