import { Router, Request, Response } from 'express';
import axios from 'axios';

const router = Router();

interface ResearchRequest {
  job_id: string;
  webhook_url: string;
  query: string;
  max_results?: number;
  patent_mode?: boolean; // 特許情報取得モード
  next_js_api_url?: string; // Next.js APIのURL
}

// モードを環境変数で切り替え
const USE_MOCK = process.env.USE_MOCK === 'true';

router.post('/start', async (req: Request, res: Response) => {
  const {
    job_id,
    webhook_url,
    query,
    max_results = 5,
    patent_mode = false,
    next_js_api_url,
  }: ResearchRequest = req.body;

  // バリデーション
  if (!job_id || !webhook_url || !query) {
    return res.status(400).json({
      error: 'Missing required fields: job_id, webhook_url, query',
    });
  }

  console.log(
    `[Research] Starting job ${job_id} for query: "${query}" (patent_mode: ${patent_mode})`
  );

  // すぐにレスポンス（非同期処理開始）
  res.status(202).json({
    status: 'accepted',
    job_id,
    message: 'Research started in background',
  });

  // バックグラウンドで処理
  if (patent_mode && next_js_api_url) {
    performPatentResearch(job_id, webhook_url, query, next_js_api_url);
  } else {
    performResearch(job_id, webhook_url, query, max_results);
  }
});

async function performResearch(
  job_id: string,
  webhook_url: string,
  query: string,
  max_results: number
) {
  try {
    console.log(`[Research] Job ${job_id}: Starting research (${USE_MOCK ? 'MOCK' : 'REAL'})...`);

    let results;

    if (USE_MOCK) {
      // モックデータ（即座に返す）
      await new Promise((resolve) => setTimeout(resolve, 2000)); // 2秒待機

      results = [
        {
          title: 'Mock Product Specification',
          url: 'https://example.com/product',
          content: 'This product has features A, B, and C.',
          score: 0.95,
        },
        {
          title: 'Mock Technical Documentation',
          url: 'https://example.com/docs',
          content: 'Technical details about the implementation.',
          score: 0.87,
        },
      ];
    } else {
      // 実際のTavily API呼び出し
      const tavilyResponse = await axios.post(
        'https://api.tavily.com/search',
        {
          api_key: process.env.TAVILY_API_KEY,
          query,
          search_depth: 'advanced',
          max_results,
          include_answer: true,
          include_raw_content: false,
        },
        { timeout: 900000 } // 15分
      );

      results = tavilyResponse.data.results;
    }

    console.log(`[Research] Job ${job_id}: Research completed, sending webhook...`);

    // Webhook送信
    await axios.post(
      webhook_url,
      {
        job_id,
        status: 'completed',
        results,
      },
      {
        timeout: 30000, // 30秒
      }
    );

    console.log(`[Research] Job ${job_id}: Webhook sent successfully`);
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error(`[Research] Job ${job_id}: Error - ${errorMessage}`);

    // エラー時もWebhookで通知
    try {
      await axios.post(
        webhook_url,
        {
          job_id,
          status: 'failed',
          error: errorMessage,
        },
        { timeout: 30000 }
      );
    } catch (webhookError) {
      console.error(`[Research] Job ${job_id}: Failed to send error webhook`);
    }
  }
}

// 特許情報取得専用の関数
async function performPatentResearch(
  job_id: string,
  webhook_url: string,
  patentNumber: string,
  next_js_api_url: string
) {
  try {
    console.log(`[Patent Research] Job ${job_id}: Fetching patent info for "${patentNumber}"...`);

    let patentInfo;

    if (USE_MOCK) {
      // モックデータ（即座に返す）
      await new Promise((resolve) => setTimeout(resolve, 3000)); // 3秒待機

      patentInfo = {
        patentNumber,
        patentTitle: 'モック特許発明',
        claim1: 'これはモックの請求項1の内容です。',
        assignee: 'モック株式会社',
        potentialInfringers: [
          {
            company: 'サンプル企業A',
            product: 'サンプル製品X',
            probability: '高',
          },
          {
            company: 'サンプル企業B',
            product: 'サンプル製品Y',
            probability: '中',
          },
        ],
      };
    } else {
      // 実際のDeep Research API呼び出し
      const deepResearchResponse = await axios.post(
        `${next_js_api_url}/api/analyze-deep`,
        {
          patentNumber,
          mode: 'full',
        },
        {
          timeout: 900000, // 15分
        }
      );

      patentInfo = deepResearchResponse.data;
    }

    console.log(`[Patent Research] Job ${job_id}: Patent research completed, sending webhook...`);

    // Webhook送信
    await axios.post(
      webhook_url,
      {
        job_id,
        status: 'completed',
        patent_info: patentInfo,
      },
      {
        timeout: 30000, // 30秒
      }
    );

    console.log(`[Patent Research] Job ${job_id}: Webhook sent successfully`);
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error(`[Patent Research] Job ${job_id}: Error - ${errorMessage}`);

    // エラー時もWebhookで通知
    try {
      await axios.post(
        webhook_url,
        {
          job_id,
          status: 'failed',
          error: errorMessage,
        },
        { timeout: 30000 }
      );
    } catch (webhookError) {
      console.error(`[Patent Research] Job ${job_id}: Failed to send error webhook`);
    }
  }
}

export { router as researchRouter };
