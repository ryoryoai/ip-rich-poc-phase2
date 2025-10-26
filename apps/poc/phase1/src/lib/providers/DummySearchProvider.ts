import type { ISearchProvider, SearchResult } from '@/interfaces/ISearchProvider';

/**
 * ダミー検索プロバイダー（PoC検証用）
 * 実際のAPI呼び出しを行わず、モックデータを返す
 */
export class DummySearchProvider implements ISearchProvider {
  async search(query: string, numResults: number = 3): Promise<SearchResult[]> {
    console.log(`[DummySearchProvider] Searching for: "${query}" (${numResults} results)`);

    // ダミーデータを返す
    return [
      {
        title: `${query} - 公式ドキュメント`,
        url: 'https://example.com/doc',
        snippet: `${query}に関する公式ドキュメントです。製品の詳細な仕様が記載されています。`,
      },
      {
        title: `${query} - 技術レビュー`,
        url: 'https://example.com/review',
        snippet: `${query}の技術的なレビュー記事です。主要な機能と特徴について解説しています。`,
      },
      {
        title: `${query} - ユーザーガイド`,
        url: 'https://example.com/guide',
        snippet: `${query}のユーザーガイドです。使用方法や設定について詳しく説明されています。`,
      },
    ].slice(0, numResults);
  }

  getProviderName(): string {
    return 'Dummy Search';
  }
}
