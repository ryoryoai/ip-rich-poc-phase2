import axios from 'axios';
import type { ISearchProvider, SearchResult } from '@/interfaces/ISearchProvider';

/**
 * Tavily APIを使用した検索プロバイダー実装
 * 無料枠: 1000検索/月
 * 環境変数: TAVILY_API_KEY
 */
export class TavilySearchProvider implements ISearchProvider {
  private apiKey: string | undefined;

  constructor() {
    this.apiKey = process.env.TAVILY_API_KEY;
    if (!this.apiKey) {
      console.warn('TAVILY_API_KEY not set, search functionality will be limited');
    }
  }

  async search(query: string, numResults: number = 5): Promise<SearchResult[]> {
    if (!this.apiKey) {
      console.warn('Tavily API key not configured, returning empty results');
      return [];
    }

    try {
      const response = await axios.post('https://api.tavily.com/search', {
        api_key: this.apiKey,
        query,
        max_results: numResults,
        search_depth: 'advanced',
        include_raw_content: false,
      });

      if (response.data && response.data.results) {
        return response.data.results.map((item: any) => ({
          title: item.title || '',
          url: item.url || '',
          snippet: item.content || item.snippet || '',
        }));
      }

      return [];
    } catch (error) {
      console.error('Tavily search error:', error);
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        throw new Error('Invalid Tavily API key');
      }
      throw new Error(`Tavily search failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  getProviderName(): string {
    return 'Tavily Search';
  }

  isConfigured(): boolean {
    return !!this.apiKey;
  }
}