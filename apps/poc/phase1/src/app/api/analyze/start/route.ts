import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';
import { prisma } from '@/lib/prisma';

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

interface AnalyzeStartRequest {
  patentNumber: string;
  claimText: string;
  companyName: string;
  productName: string;
}

interface AnalyzeStartResponse {
  job_id: string;
  status: 'pending';
  created_at: string;
}

export async function POST(request: NextRequest) {
  try {
    const body: AnalyzeStartRequest = await request.json();
    const { patentNumber, claimText, companyName, productName } = body;

    // バリデーション
    if (!patentNumber || !claimText || !companyName || !productName) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    console.log(`[API] Creating job for patent: ${patentNumber}`);

    // 同じ特許番号の完了済みジョブをチェック
    const existingJob = await prisma.analysis_jobs.findFirst({
      where: {
        patentNumber,
        status: 'completed',
      },
      orderBy: {
        createdAt: 'desc',
      },
    });

    if (existingJob) {
      console.log(
        `[API] Found existing completed job for patent ${patentNumber}: ${existingJob.id}`
      );
      return NextResponse.json({
        job_id: existingJob.id,
        status: 'completed',
        created_at: existingJob.createdAt.toISOString(),
        existing: true,
      });
    }

    // ジョブ作成
    const job = await prisma.analysis_jobs.create({
      data: {
        status: 'pending',
        patentNumber,
        claimText,
        companyName,
        productName,
        progress: 0,
      },
    });

    console.log(`[API] Job created: ${job.id}`);

    // OpenAI Deep Research API呼び出し（非同期モード）
    const webhookUrl =
      process.env.OPENAI_WEBHOOK_URL ||
      `${process.env.NEXT_PUBLIC_APP_URL}/api/webhook/openai`;

    // サンプル/侵害調査プロンプト.txt のフォーマットに従う
    const query = `下記の特許${patentNumber}の請求項１の要件を満たす侵害製品を念入りに調査せよ。対象は日本国内でサービス展開している外国企業とする。

▼要求事項：
・請求項１に記載された**すべての構成要件を満たす製品のみ**を調査対象とする（１つでも欠ける場合は除外）
・特許番号と請求項１の全文を**完全に照合**の上で処理すること（他の特許と絶対に混同しないこと）
・請求項１の構成要件をそのまま引用して記載する（勝手に要約・再構成しない）
・各構成要件ごとに、製品の仕様と比較し、充足性（○/×）を判断
・参考として請求項２以降や発明の詳細な説明を参照してもよいが、主判断基準は請求項１のみとする
・**web検索を使用して**、製品の公開仕様・企業ページ・販売情報などを確認のうえ根拠を示すこと
・**複数の製品を調査**し、それぞれについて充足性を判定すること
・出力フォーマットは以下に従うこと：

▼出力フォーマット（マークダウンテーブル形式で複数製品を記載）：
| 製品名 | 製品の対応構成 | 充足判断 | 根拠（URL・公開情報） |
|--------|--------------|---------|-------------------|
| 製品A | 構成要件の実装内容 | ○/× | 根拠となるURL等 |
| 製品B | 構成要件の実装内容 | ○/× | 根拠となるURL等 |

※各構成要件ごとに上記テーブルを作成すること
・日本語で回答すること

＜以下、特許${patentNumber}（請求項１を全文で記載）＞
${claimText}`;

    console.log(`[API] Starting OpenAI Deep Research...`);
    console.log(`[API] Patent Number: ${patentNumber}`);
    console.log(`[API] Webhook URL: ${webhookUrl}`);

    try {
      const response = await openai.responses.create({
        model: 'o4-mini-deep-research-2025-06-26',
        input: [
          {
            type: 'message',
            role: 'user',
            content: query,
          },
        ],
        reasoning: { summary: 'auto' },
        tools: [{ type: 'web_search_preview' }],
        background: true, // 非同期モード
        metadata: { job_id: job.id }, // Webhook時に識別するため
        // NOTE: WebhookはOpenAI Dashboard (https://platform.openai.com/webhooks) で設定
      });

      console.log(`[API] Deep Research started:`, response.id);

      // ステータス更新（response.idとプロンプトを保存）
      await prisma.analysis_jobs.update({
        where: { id: job.id },
        data: {
          status: 'researching',
          progress: 10,
          openaiResponseId: response.id, // Webhook時に照合するため
          inputPrompt: query, // プロンプトを保存
        },
      });

      console.log(`[API] Job status updated to 'researching' with response ID: ${response.id}`);
    } catch (error) {
      console.error('[API] Failed to start OpenAI Deep Research:', error);

      // エラー時はジョブを失敗状態に更新
      await prisma.analysis_jobs.update({
        where: { id: job.id },
        data: {
          status: 'failed',
          errorMessage:
            error instanceof Error
              ? error.message
              : 'Failed to start OpenAI Deep Research',
        },
      });

      return NextResponse.json(
        {
          error: 'Failed to start OpenAI Deep Research',
          details: error instanceof Error ? error.message : 'Unknown error',
        },
        { status: 500 }
      );
    }

    const response: AnalyzeStartResponse = {
      job_id: job.id,
      status: 'pending',
      created_at: job.createdAt.toISOString(),
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error('[API] Error in /api/analyze/start:', error);
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
