import { NextRequest, NextResponse } from 'next/server';
import { getLLMProvider, getSearchProvider, getStorageProvider } from '@/lib/container';
import { RequirementExtractionService } from '@/services/RequirementExtractionService';
import { ComplianceCheckService } from '@/services/ComplianceCheckService';
import type { AnalyzeRequest, AnalyzeResponse, ApiErrorResponse } from '@/types/api';

/**
 * POST /api/analyze
 * 特許侵害調査の分析を実行
 *
 * 依存性注入により、プロバイダーの実装を簡単に差し替え可能：
 * - 環境変数でOpenAI→Dify等に切り替え可能
 * - テスト時はモックプロバイダーを注入可能
 */
export async function POST(request: NextRequest) {
  try {
    // リクエストボディを解析
    const body: AnalyzeRequest = await request.json();
    const { patentNumber, claimText, companyName, productName } = body;

    // バリデーション
    if (!patentNumber || !claimText || !companyName || !productName) {
      return NextResponse.json<ApiErrorResponse>(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    // DIコンテナからプロバイダーを取得
    const llmProvider = getLLMProvider();
    const searchProvider = getSearchProvider();
    const storageProvider = getStorageProvider();

    // サービスを構築（依存性注入）
    const requirementService = new RequirementExtractionService(llmProvider);
    const complianceService = new ComplianceCheckService(llmProvider, searchProvider);

    console.log(`[API] Starting analysis for patent: ${patentNumber}`);

    // 1. 構成要件抽出
    console.log('[API] Step 1: Extracting requirements...');
    const requirements = await requirementService.extractRequirements(patentNumber, claimText);
    console.log(`[API] Extracted ${requirements.length} requirements`);

    // 2. 充足性判定
    console.log('[API] Step 2: Checking compliance...');
    const complianceResults = await Promise.all(
      requirements.map((req) =>
        complianceService.checkCompliance(req, productName, companyName)
      )
    );

    // 3. 総合判定
    const compliantCount = complianceResults.filter((r) => r.compliance === '○').length;
    const totalCount = requirements.length;

    const result: AnalyzeResponse = {
      patentNumber,
      companyName,
      productName,
      timestamp: new Date().toISOString(),
      requirements,
      complianceResults,
      summary: {
        totalRequirements: totalCount,
        compliantRequirements: compliantCount,
        complianceRate: (compliantCount / totalCount) * 100,
        infringementPossibility: compliantCount === totalCount ? '○' : '×',
      },
    };

    // 4. 結果を保存
    console.log('[API] Step 3: Saving results...');
    const savedPath = await storageProvider.saveAnalysis(result);
    console.log(`[API] Results saved to: ${savedPath}`);

    console.log('[API] Analysis completed successfully');

    return NextResponse.json<AnalyzeResponse>(result);
  } catch (error) {
    console.error('[API] Analysis error:', error);
    return NextResponse.json<ApiErrorResponse>(
      {
        error: 'Analysis failed',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
