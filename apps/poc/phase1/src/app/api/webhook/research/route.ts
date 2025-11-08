import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';


interface WebhookResearchRequest {
  job_id: string;
  status: 'completed' | 'failed';
  results?: Array<{
    title: string;
    url: string;
    content: string;
    score: number;
  }>;
  patent_info?: {
    patentNumber: string;
    patentTitle?: string;
    claim1?: string;
    assignee?: string;
    potentialInfringers?: Array<{
      company: string;
      product: string;
      probability?: string;
    }>;
  };
  error?: string;
}

export async function POST(request: NextRequest) {
  try {
    const body: WebhookResearchRequest = await request.json();
    const { job_id, status, results, patent_info, error } = body;

    console.log(`[Webhook] Received research result for job: ${job_id}`);
    console.log(`[Webhook] Status: ${status}`);

    // ジョブが存在するか確認
    const job = await prisma.analysis_jobs.findUnique({
      where: { id: job_id },
    });

    if (!job) {
      console.error(`[Webhook] Job not found: ${job_id}`);
      return NextResponse.json({ error: 'Job not found' }, { status: 404 });
    }

    if (status === 'failed') {
      console.error(`[Webhook] Research failed for job ${job_id}:`, error);

      await prisma.analysis_jobs.update({
        where: { id: job_id },
        data: {
          status: 'failed',
          errorMessage: error || 'Deep Research failed',
        },
      });

      return NextResponse.json({ status: 'error_recorded' });
    }

    // 特許情報が含まれている場合
    if (patent_info) {
      console.log(`[Webhook] Saving patent info for job ${job_id}`);

      await prisma.analysis_jobs.update({
        where: { id: job_id },
        data: {
          claimText: patent_info.claim1 || job.claimText,
          companyName:
            patent_info.potentialInfringers?.[0]?.company || job.companyName,
          productName:
            patent_info.potentialInfringers?.[0]?.product || job.productName,
          researchResults: patent_info as any,
          status: 'completed',
          progress: 100,
        },
      });

      console.log(`[Webhook] Patent info saved for job ${job_id}`);
    } else if (results) {
      // 通常の検索結果の場合
      console.log(
        `[Webhook] Saving ${results.length} research results for job ${job_id}`
      );

      await prisma.analysis_jobs.update({
        where: { id: job_id },
        data: {
          researchResults: results || [],
          status: 'completed',
          progress: 100,
        },
      });

      console.log(`[Webhook] Job ${job_id} completed successfully`);
    }

    return NextResponse.json({ status: 'success' });
  } catch (error) {
    console.error('[Webhook] Error in /api/webhook/research:', error);
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
