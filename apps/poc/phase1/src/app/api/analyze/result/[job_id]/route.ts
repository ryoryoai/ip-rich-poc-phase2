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
      research_results: job.researchResults,
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
