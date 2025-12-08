import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function GET(
  _request: NextRequest,
  { params }: { params: { job_id: string } }
) {
  try {
    const jobId = params.job_id;

    console.log(`[API] Fetching result for job: ${jobId}`);

    const job = await prisma.analysis_jobs.findUnique({
      where: { id: jobId },
    });

    if (!job) {
      return NextResponse.json({ error: 'Job not found' }, { status: 404 });
    }

    if (job.status !== 'completed') {
      return NextResponse.json(
        {
          error: 'Job not completed yet',
          status: job.status,
          progress: job.progress,
        },
        { status: 400 }
      );
    }

    // research_resultsをフロントエンド用の形式に変換
    let formattedResearchResults = null;
    if (job.researchResults) {
      // OpenAI Deep Researchの結果が配列形式の場合、適切に変換
      if (Array.isArray(job.researchResults)) {
        // 最後のメッセージ（通常は結果）を探す
        const messageResult = (job.researchResults as any[])
          .reverse()
          .find((item: any) => item.type === 'message' && item.content);

        let reportText = '結果が取得できませんでした';
        let citations: any[] = [];

        if (messageResult && messageResult.content) {
          // contentが配列の場合、textタイプのものを結合
          if (Array.isArray(messageResult.content)) {
            reportText = messageResult.content
              .filter((c: any) => c.type === 'output_text' || c.text)
              .map((c: any) => c.text || '')
              .join('\n\n');

            // annotationsからcitationsを抽出
            const annotations = messageResult.content
              .flatMap((c: any) => c.annotations || [])
              .filter((a: any) => a.type === 'url_citation');

            citations = annotations.map((a: any) => ({
              type: a.type,
              title: a.title || a.url,
              url: a.url
            }));
          } else {
            reportText = messageResult.content;
          }
        }

        formattedResearchResults = {
          reportText: reportText,
          citations: citations,
          rawResponse: {
            output: job.researchResults,
            model: process.env.OPENAI_DEEP_RESEARCH_MODEL || 'o4-mini-deep-research-2025-06-26'
          },
          usage: null // Deep Researchではusage情報が別途必要
        };
      } else if (typeof job.researchResults === 'object') {
        // すでにオブジェクト形式の場合はそのまま使用
        formattedResearchResults = job.researchResults;
      }
    }

    return NextResponse.json({
      job_id: job.id,
      status: job.status,
      created_at: job.createdAt.toISOString(),
      updated_at: job.updatedAt.toISOString(),
      patent_number: job.patentNumber,
      company_name: job.companyName,
      product_name: job.productName,
      claim_text: job.claimText,
      input_prompt: job.inputPrompt,
      research_results: formattedResearchResults,
      requirements: job.requirements,
      compliance_results: job.complianceResults,
      summary: job.summary,
    });
  } catch (error) {
    console.error('[API] Error in /api/analyze/result:', error);
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
