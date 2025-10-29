import { NextRequest, NextResponse } from 'next/server';
import { getPatentProvider } from '@/lib/container';

/**
 * 特許情報取得APIエンドポイント
 */
export async function POST(request: NextRequest) {
  try {
    const { patentNumber } = await request.json();

    if (!patentNumber) {
      return NextResponse.json(
        { error: '特許番号が指定されていません' },
        { status: 400 }
      );
    }

    console.log(`[API] Fetching patent information for: ${patentNumber}`);

    // 特許プロバイダーを取得
    const patentProvider = getPatentProvider();

    // 特許情報を取得
    const patentInfo = await patentProvider.fetchPatent(patentNumber);

    console.log(`[API] Successfully fetched patent: ${patentInfo.title}`);

    return NextResponse.json(patentInfo);
  } catch (error) {
    console.error('[API] Patent fetch error:', error);

    const errorMessage = error instanceof Error
      ? error.message
      : '特許情報の取得中にエラーが発生しました';

    return NextResponse.json(
      { error: errorMessage },
      { status: 500 }
    );
  }
}