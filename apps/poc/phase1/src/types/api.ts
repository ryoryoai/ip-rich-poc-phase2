import type { AnalysisResult } from './analysis';

/**
 * /api/analyze へのリクエスト型
 */
export interface AnalyzeRequest {
  patentNumber: string;
  claimText: string;
  companyName: string;
  productName: string;
}

/**
 * /api/analyze からのレスポンス型
 */
export interface AnalyzeResponse extends AnalysisResult {}

/**
 * APIエラーレスポンス型
 */
export interface ApiErrorResponse {
  error: string;
  details?: string;
}
