import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';


export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '50');
    const offset = parseInt(searchParams.get('offset') || '0');
    const status = searchParams.get('status');

    console.log(`[API] Fetching job list (limit: ${limit}, offset: ${offset}, status: ${status})`);

    const where = status ? { status } : {};

    const jobs = await prisma.analysis_jobs.findMany({
      where,
      orderBy: [
        { priority: 'desc' },
        { createdAt: 'desc' }
      ],
      take: limit,
      skip: offset,
      select: {
        id: true,
        status: true,
        progress: true,
        patentNumber: true,
        claimText: true,
        companyName: true,
        productName: true,
        priority: true,
        createdAt: true,
        updatedAt: true,
        startedAt: true,
        finishedAt: true,
        errorMessage: true,
      },
    });

    const total = await prisma.analysis_jobs.count({ where });

    return NextResponse.json({
      jobs: jobs.map((job) => ({
        job_id: job.id,
        status: job.status,
        progress: job.progress,
        patent_number: job.patentNumber,
        claim_text: job.claimText,
        company_name: job.companyName,
        product_name: job.productName,
        priority: job.priority || 5,
        created_at: job.createdAt.toISOString(),
        updated_at: job.updatedAt.toISOString(),
        started_at: job.startedAt?.toISOString(),
        finished_at: job.finishedAt?.toISOString(),
        error_message: job.errorMessage,
      })),
      total,
      limit,
      offset,
    });
  } catch (error) {
    console.error('[API] Error in /api/analyze/list:', error);
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
