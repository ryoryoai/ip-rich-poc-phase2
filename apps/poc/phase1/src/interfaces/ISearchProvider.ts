/**
 * Web検索プロバイダーの抽象インターフェース
 * 実装: Perplexity, SerpAPI, Google Search API, Dify等に対応可能
 */
export interface ISearchProvider {
  /**
   * Web検索を実行
   * @param query 検索クエリ
   * @param numResults 取得する結果数
   * @returns 検索結果のリスト
   */
  search(query: string, numResults?: number): Promise<SearchResult[]>;

  /**
   * プロバイダー名を取得
   */
  getProviderName(): string;
}

export interface SearchResult {
  title: string;
  url: string;
  snippet: string;
}
