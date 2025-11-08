import { NextRequest, NextResponse } from 'next/server';
import { Prisma } from '@prisma/client';
import OpenAI from 'openai';
import { prisma } from '@/lib/prisma';

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

interface AnalyzeStatusResponse {
  job_id: string;
  status: 'pending' | 'researching' | 'analyzing' | 'completed' | 'failed';
  progress: number;
  error_message?: string;
}

// OpenAI Response型定義
interface OpenAIMessageContent {
  type: 'text' | 'image_url';
  text?: string;
  annotations?: Array<{
    type: string;
    title?: string;
    url?: string;
  }>;
}

interface OpenAIOutput {
  type: string;
  content?: OpenAIMessageContent[];
}

export async function GET(
  _request: NextRequest,
  { params }: { params: { job_id: string } }
) {
  try {
    const jobId = params.job_id;

    console.log(`[API] Checking status for job: ${jobId}`);

    const job = await prisma.analysis_jobs.findUnique({
      where: { id: jobId },
      select: {
        id: true,
        status: true,
        progress: true,
        errorMessage: true,
        openaiResponseId: true,
      },
    });

    if (!job) {
      return NextResponse.json({ error: 'Job not found' }, { status: 404 });
    }

    // researching状態でopenaiResponseIdがある場合、OpenAI APIに問い合わせ
    if (job.status === 'researching' && job.openaiResponseId) {
      console.log(
        `[API] Checking OpenAI status for response: ${job.openaiResponseId}`
      );

      try {
        const openaiResponse = await openai.responses.retrieve(
          job.openaiResponseId
        );

        console.log(
          `[API] OpenAI response status: ${openaiResponse.status}`
        );

        // 完了していたら結果を取得して保存
        if (openaiResponse.status === 'completed') {
          console.log(
            `[API] OpenAI research completed, saving results for job: ${jobId}`
          );

          // 結果を解析（最後のmessageタイプのoutputを探す）
          const output = (openaiResponse.output || []) as OpenAIOutput[];
          const messageOutput = [...output]
            .reverse()
            .find((o) => o.type === 'message');
          const textContent = messageOutput?.content?.find(
            (c) => c.type === 'text'
          );
          const finalReport = textContent?.text || '';
          const citations = textContent?.annotations || [];

          // Prisma JsonValue互換の形式に変換
          const researchResults: Prisma.JsonObject = {
            reportText: finalReport,
            citations: citations.map((c) => ({
              type: c.type,
              title: c.title || '',
              url: c.url || '',
            })),
            rawResponse: JSON.parse(JSON.stringify(openaiResponse)),
            usage: openaiResponse.usage ? JSON.parse(JSON.stringify(openaiResponse.usage)) : null,
          };

          // DBに保存
          await prisma.analysis_jobs.update({
            where: { id: jobId },
            data: {
              status: 'completed',
              progress: 100,
              researchResults,
            },
          });

          console.log(`[API] Job ${jobId} updated to completed`);

          // 更新後のステータスを返す
          return NextResponse.json({
            job_id: jobId,
            status: 'completed',
            progress: 100,
          });
        } else if (openaiResponse.status === 'failed') {
          // 失敗していた場合
          console.log(`[API] OpenAI research failed for job: ${jobId}`);

          await prisma.analysis_jobs.update({
            where: { id: jobId },
            data: {
              status: 'failed',
              errorMessage: 'OpenAI Deep Research failed',
            },
          });

          return NextResponse.json({
            job_id: jobId,
            status: 'failed',
            progress: job.progress,
            error_message: 'OpenAI Deep Research failed',
          });
        }
        // in_progress の場合はそのまま継続
      } catch (openaiError) {
        console.error('[API] Failed to check OpenAI status:', openaiError);
        // OpenAI APIエラーは無視してDBの状態を返す
      }
    }

    const response: AnalyzeStatusResponse = {
      job_id: job.id,
      status: job.status as any,
      progress: job.progress,
      error_message: job.errorMessage || undefined,
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error('[API] Error in /api/analyze/status:', error);
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
