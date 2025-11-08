import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

/**
 * GET /api/test-prisma
 * Prisma接続テスト用エンドポイント
 */
export async function GET() {
  try {
    // 全ジョブ数を取得
    const totalJobs = await prisma.analysis_jobs.count();

    // 最新の5件を取得
    const recentJobs = await prisma.analysis_jobs.findMany({
      take: 5,
      orderBy: { createdAt: 'desc' },
      select: {
        id: true,
        status: true,
        patentNumber: true,
        companyName: true,
        productName: true,
        progress: true,
        createdAt: true,
      },
    });

    // ステータス別集計
    const statusCounts = await prisma.analysis_jobs.groupBy({
      by: ['status'],
      _count: true,
    });

    return NextResponse.json({
      success: true,
      data: {
        totalJobs,
        recentJobs,
        statusCounts,
      },
    });
  } catch (error) {
    console.error('[Prisma Test] Error:', error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}

/**
 * POST /api/test-prisma
 * テストジョブ作成
 */
export async function POST() {
  try {
    const testJob = await prisma.analysis_jobs.create({
      data: {
        status: 'pending',
        progress: 0,
        patentNumber: 'JP-TEST-' + Date.now(),
        claimText: 'テスト請求項の内容',
        companyName: 'テスト企業株式会社',
        productName: 'テスト製品',
      },
    });

    return NextResponse.json({
      success: true,
      data: testJob,
    });
  } catch (error) {
    console.error('[Prisma Test] Error:', error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
