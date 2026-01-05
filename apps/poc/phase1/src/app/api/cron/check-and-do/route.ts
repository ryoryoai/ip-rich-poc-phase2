import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import OpenAI from 'openai';

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

// NULL文字を除去する関数
function sanitizeText(text: any): any {
  if (typeof text === 'string') {
    // NULL文字（\u0000）を除去
    return text.replace(/\u0000/g, '');
  } else if (Array.isArray(text)) {
    return text.map(sanitizeText);
  } else if (text !== null && typeof text === 'object') {
    const sanitized: any = {};
    for (const key in text) {
      sanitized[key] = sanitizeText(text[key]);
    }
    return sanitized;
  }
  return text;
}

// GETハンドラー（互換性のため）
export async function GET(request: NextRequest) {
  return POST(request);
}

export async function POST(request: NextRequest) {
  // Cron認証
  const cronSecret = request.headers.get('X-Cron-Secret');
  if (cronSecret !== process.env.CRON_SECRET_KEY) {
    console.log('[Cron] Unauthorized access attempt');
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    console.log('[Cron] Starting check-and-do process');

    // 1. 実行中ジョブのステータス確認
    const inProgressJobs = await prisma.analysis_jobs.findMany({
      where: { status: 'researching' },
      select: {
        id: true,
        openaiResponseId: true,
        patentNumber: true,
        retryCount: true,
        maxRetries: true
      }
    });

    console.log(`[Cron] Checking ${inProgressJobs.length} in-progress jobs`);

    let completedCount = 0;
    let failedCount = 0;

    for (const job of inProgressJobs) {
      if (job.openaiResponseId) {
        try {
          // OpenAI APIでステータス確認
          console.log(`[Cron] Checking status for job ${job.id} (response: ${job.openaiResponseId})`);
          const response = await openai.responses.retrieve(job.openaiResponseId);

          if (response.status === 'completed') {
            console.log(`[Cron] Job ${job.id} completed`);

            // 結果を保存（NULL文字を除去）
            const sanitizedOutput = sanitizeText(response.output);
            await prisma.analysis_jobs.update({
              where: { id: job.id },
              data: {
                status: 'completed',
                researchResults: sanitizedOutput as any,
                finishedAt: new Date(),
                progress: 100
              }
            });
            completedCount++;
          } else if (response.status === 'failed' || response.status === 'cancelled') {
            console.log(`[Cron] Job ${job.id} failed/cancelled`);

            await prisma.analysis_jobs.update({
              where: { id: job.id },
              data: {
                status: 'failed',
                errorMessage: sanitizeText(`Research ${response.status}`),
                finishedAt: new Date()
              }
            });
            failedCount++;
          }
          // in_progress の場合は何もしない（次回チェック）
        } catch (error) {
          console.error(`[Cron] Error checking job ${job.id}:`, error);

          // リトライ回数を増やす
          const newRetryCount = (job.retryCount || 0) + 1;
          const maxRetries = job.maxRetries || 3;

          if (newRetryCount >= maxRetries) {
            await prisma.analysis_jobs.update({
              where: { id: job.id },
              data: {
                status: 'failed',
                errorMessage: sanitizeText(error instanceof Error ? error.message : 'Failed to check status'),
                retryCount: newRetryCount,
                finishedAt: new Date()
              }
            });
            failedCount++;
          } else {
            await prisma.analysis_jobs.update({
              where: { id: job.id },
              data: {
                retryCount: newRetryCount
              }
            });
          }
        }
      }
    }

    // 2. 新規ジョブの開始
    const maxConcurrent = parseInt(process.env.MAX_CONCURRENT_JOBS || '3');
    const currentRunning = await prisma.analysis_jobs.count({
      where: { status: 'researching' }
    });

    const slotsAvailable = maxConcurrent - currentRunning;
    console.log(`[Cron] Slots available: ${slotsAvailable} (max: ${maxConcurrent}, running: ${currentRunning})`);

    let startedCount = 0;

    if (slotsAvailable > 0) {
      // 優先度順でpendingジョブを取得
      const pendingJobs = await prisma.analysis_jobs.findMany({
        where: {
          status: 'pending',
          OR: [
            { scheduledFor: null },
            { scheduledFor: { lte: new Date() } }
          ]
        },
        orderBy: [
          { priority: 'desc' },
          { createdAt: 'asc' }
        ],
        take: slotsAvailable
      });

      console.log(`[Cron] Found ${pendingJobs.length} pending jobs to start`);

      for (const job of pendingJobs) {
        try {
          console.log(`[Cron] Starting job ${job.id} for patent ${job.patentNumber}`);

          // プロンプトを構築
          const query = buildInfringementQuery(job.patentNumber, job.claimText);

          // OpenAI Deep Research APIを呼び出し
          const response = await openai.responses.create({
            model: process.env.OPENAI_DEEP_RESEARCH_MODEL || 'o4-mini-deep-research-2025-06-26',
            input: [
              {
                type: 'message',
                role: 'user',
                content: query,
              },
            ],
            reasoning: { summary: 'auto' },
            tools: [{ type: 'web_search_preview' }],
            background: true,
            metadata: { job_id: job.id },
          });

          console.log(`[Cron] Deep Research started for job ${job.id}: ${response.id}`);

          // ジョブステータスを更新
          await prisma.analysis_jobs.update({
            where: { id: job.id },
            data: {
              status: 'researching',
              openaiResponseId: response.id,
              inputPrompt: query,
              startedAt: new Date(),
              queuedAt: job.queuedAt || new Date(),
              progress: 10
            }
          });

          startedCount++;
        } catch (error) {
          console.error(`[Cron] Failed to start job ${job.id}:`, error);

          // リトライカウントを増やす
          const newRetryCount = (job.retryCount || 0) + 1;
          const maxRetries = job.maxRetries || 3;

          if (newRetryCount >= maxRetries) {
            await prisma.analysis_jobs.update({
              where: { id: job.id },
              data: {
                status: 'failed',
                retryCount: newRetryCount,
                errorMessage: sanitizeText(error instanceof Error ? error.message : 'Failed to start'),
                finishedAt: new Date()
              }
            });
          } else {
            await prisma.analysis_jobs.update({
              where: { id: job.id },
              data: {
                retryCount: newRetryCount
              }
            });
          }
        }
      }
    }

    // 3. 統計情報を収集
    const stats = await prisma.analysis_jobs.groupBy({
      by: ['status'],
      _count: true
    });

    const summary = {
      checked: inProgressJobs.length,
      completed: completedCount,
      failed: failedCount,
      started: startedCount,
      currentRunning: currentRunning - completedCount - failedCount + startedCount,
      stats: stats.reduce((acc, curr) => {
        acc[curr.status] = curr._count;
        return acc;
      }, {} as Record<string, number>)
    };

    console.log('[Cron] Check-and-do completed:', summary);

    return NextResponse.json(summary);

  } catch (error) {
    console.error('[Cron] Error in check-and-do:', error);
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

// 既存のプロンプト生成関数を流用
function buildInfringementQuery(patentNumber: string, claimText: string): string {
  // NULL文字を除去
  const sanitizedPatentNumber = sanitizeText(patentNumber);
  const sanitizedClaimText = sanitizeText(claimText);

  return `下記の特許${sanitizedPatentNumber}の請求項１の要件を満たす侵害製品を念入りに調査せよ。対象は日本国内でサービス展開している外国企業（日本企業以外）とする。

▼重要指示：
・**実際に侵害可能性が高い製品を優先的に探すこと**（GAFAMなど大手企業にこだわる必要はない）
・以下の分野の企業を重点的に調査すること：
  1. スポーツテック企業（モーションキャプチャ、動作解析システム）
  2. スポーツトレーニング・分析システム企業
  3. VR/ARスポーツトレーニング企業
  4. AIを使ったスポーツコーチング企業
  5. 球技のパフォーマンス解析システム企業

▼要求事項：
・特許番号と請求項１の全文を**完全に照合**の上で処理すること（他の特許と絶対に混同しないこと）
・請求項１の構成要件をそのまま引用して記載する（勝手に要約・再構成しない）
・各構成要件ごとに、製品の仕様と比較し、充足性（○/×）を判断
・参考として請求項２以降や発明の詳細な説明を参照してもよいが、主判断基準は請求項１のみとする
・**web検索を使用して**、製品の公開仕様・企業ページ・販売情報などを確認のうえ根拠を示すこと
・**侵害可能性がある製品を最低1つは見つけるよう努力**し、3社以上について充足性を判定すること
・請求項１に記載された**すべての構成要件を満たす製品のみ**を調査対象とする（１つでも×の場合は除外）

▼出力フォーマット（企業ごとにテーブルを作成）：

## 企業名1（例：Catapult Sports - 製品名：Vector等）
| 構成要件 | 製品の対応構成 | 充足判断 | 根拠 |
|----------|--------------|---------|------|
| 構成要件A（請求項1から引用） | 製品での具体的な実装内容 | ○/× | URL・公開情報等 |
| 構成要件B（請求項1から引用） | 製品での具体的な実装内容 | ○/× | URL・公開情報等 |
| 構成要件C（請求項1から引用） | 製品での具体的な実装内容 | ○/× | URL・公開情報等 |

**総合判定**: ○/× （全構成要件を満たす場合のみ○）

## 企業名2（例：STATSports - 製品名：APEX等）
| 構成要件 | 製品の対応構成 | 充足判断 | 根拠 |
|----------|--------------|---------|------|
| 構成要件A（請求項1から引用） | 製品での具体的な実装内容 | ○/× | URL・公開情報等 |
| 構成要件B（請求項1から引用） | 製品での具体的な実装内容 | ○/× | URL・公開情報等 |
| 構成要件C（請求項1から引用） | 製品での具体的な実装内容 | ○/× | URL・公開情報等 |

**総合判定**: ○/× （全構成要件を満たす場合のみ○）

※侵害可能性が高い製品から順に3社以上調査すること
・日本語で回答すること

＜以下、特許${sanitizedPatentNumber}（請求項１を全文で記載）＞
${sanitizedClaimText}`;
}