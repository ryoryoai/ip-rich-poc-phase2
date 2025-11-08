import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';


export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '50');
    const offset = parseInt(searchParams.get('offset') || '0');

    console.log(`[API] Fetching job list (limit: ${limit}, offset: ${offset})`);

    const jobs = await prisma.analysis_jobs.findMany({
      orderBy: { createdAt: 'desc' },
      take: limit,
      skip: offset,
      select: {
        id: true,
        status: true,
        progress: true,
        patentNumber: true,
        companyName: true,
        productName: true,
        createdAt: true,
        updatedAt: true,
        errorMessage: true,
      },
    });

    const total = await prisma.analysis_jobs.count();

    return NextResponse.json({
      jobs: jobs.map((job) => ({
        job_id: job.id,
        status: job.status,
        progress: job.progress,
        patent_number: job.patentNumber,
        company_name: job.companyName,
        product_name: job.productName,
        created_at: job.createdAt.toISOString(),
        updated_at: job.updatedAt.toISOString(),
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
