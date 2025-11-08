import { NextRequest, NextResponse } from 'next/server';
import { Webhook } from 'standardwebhooks';
import { prisma } from '@/lib/prisma';

interface OpenAIWebhookEvent {
  type: string;
  data: {
    id: string;
    object: string;
    model: string;
    output: Array<{
      type: string;
      content: Array<{
        type: string;
        text?: string;
        annotations?: Array<{
          type: string;
          title?: string;
          url?: string;
        }>;
      }>;
    }>;
    usage?: {
      input_tokens: number;
      output_tokens: number;
      total_tokens: number;
    };
    metadata?: {
      job_id?: string;
    };
  };
}

/**
 * OpenAI Deep Research API Webhook受信エンドポイント
 *
 * OpenAIのDeep Research APIが調査完了時に送信するWebhookを受信し、
 * Supabaseに検索結果を永続化する。
 *
 * セキュリティ:
 * - Basic認証はバイパス（middleware.tsで設定）
 * - 代わりにOpenAIのWebhook署名検証を実施
 */
export async function POST(request: NextRequest) {
  try {
    console.log('[OpenAI Webhook] Received request');

    // 1. Webhook署名検証
    const signature = request.headers.get('webhook-signature');
    const webhookId = request.headers.get('webhook-id');
    const webhookTimestamp = request.headers.get('webhook-timestamp');
    const secret = process.env.OPENAI_WEBHOOK_SECRET;

    if (!signature || !webhookId || !webhookTimestamp) {
      console.error('[OpenAI Webhook] Missing webhook headers');
      return NextResponse.json(
        { error: 'Missing webhook headers' },
        { status: 400 }
      );
    }

    if (!secret) {
      console.error('[OpenAI Webhook] Missing OPENAI_WEBHOOK_SECRET');
      if (process.env.NODE_ENV === 'production') {
        throw new Error('OPENAI_WEBHOOK_SECRET must be set in production');
      }
      return NextResponse.json(
        { error: 'Server configuration error' },
        { status: 500 }
      );
    }

    const payload = await request.text();

    // Webhook署名検証
    const wh = new Webhook(secret);
    try {
      wh.verify(payload, {
        'webhook-id': webhookId,
        'webhook-timestamp': webhookTimestamp,
        'webhook-signature': signature,
      });
      console.log('[OpenAI Webhook] Signature verified successfully');
    } catch (err) {
      console.error('[OpenAI Webhook] Signature verification failed:', err);
      return NextResponse.json({ error: 'Invalid signature' }, { status: 401 });
    }

    // 2. ペイロード解析
    const event: OpenAIWebhookEvent = JSON.parse(payload);
    console.log('[OpenAI Webhook] Event type:', event.type);

    if (event.type === 'response.completed') {
      const { id: responseId, output, usage } = event.data;

      console.log(`[OpenAI Webhook] Processing response: ${responseId}`);

      // response.idでジョブを検索
      const job = await prisma.analysis_jobs.findFirst({
        where: { openaiResponseId: responseId },
      });

      if (!job) {
        console.error(
          `[OpenAI Webhook] No job found for response ID: ${responseId}`
        );
        return NextResponse.json(
          { error: 'Job not found' },
          { status: 404 }
        );
      }

      console.log(`[OpenAI Webhook] Found job: ${job.id}`);

      // 重複処理チェック
      if (job.status === 'completed') {
        console.warn(`[OpenAI Webhook] Job ${job.id} already completed, skipping`);
        return NextResponse.json({ status: 'already_completed' });
      }

      // 3. 検索結果を解析
      const lastOutput = output[output.length - 1];
      const textContent = lastOutput?.content?.find((c) => c.type === 'text');
      const finalReport = textContent?.text || '';
      const citations = textContent?.annotations || [];

      const researchResults = {
        reportText: finalReport,
        citations: citations.map((c) => ({
          type: c.type,
          title: c.title || '',
          url: c.url || '',
        })),
        rawResponse: event.data,
        usage: usage || null,
      };

      console.log(
        `[OpenAI Webhook] Research completed for job ${job.id}:`,
        {
          reportLength: finalReport.length,
          citationsCount: citations.length,
          usage,
        }
      );

      // 4. Supabaseに保存
      await prisma.analysis_jobs.update({
        where: { id: job.id },
        data: {
          status: 'completed',
          progress: 100,
          researchResults,
        },
      });

      console.log(`[OpenAI Webhook] Job ${job.id} saved to database`);

      return NextResponse.json({ status: 'success', job_id: job.id });
    } else {
      console.log(`[OpenAI Webhook] Ignoring event type: ${event.type}`);
      return NextResponse.json({ status: 'ignored' });
    }
  } catch (error) {
    console.error('[OpenAI Webhook] Error:', error);
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
