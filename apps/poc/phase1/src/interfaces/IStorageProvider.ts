import type { AnalysisResult } from '@/types/analysis';

/**
 * データストレージプロバイダーの抽象インターフェース
 * 実装: LocalStorage, DynamoDB, S3, Dify等に対応可能
 */
export interface IStorageProvider {
  /**
   * 分析結果を保存
   * @param data 分析結果データ
   * @returns 保存されたファイルパスまたはID
   */
  saveAnalysis(data: AnalysisResult): Promise<string>;

  /**
   * 分析結果を取得
   * @param id ファイルパスまたはID
   * @returns 分析結果データ
   */
  getAnalysis(id: string): Promise<AnalysisResult | null>;

  /**
   * すべての分析結果を取得
   * @param limit 取得する最大件数
   * @returns 分析結果のリスト
   */
  listAnalyses(limit?: number): Promise<AnalysisResult[]>;

  /**
   * プロバイダー名を取得
   */
  getProviderName(): string;
}
