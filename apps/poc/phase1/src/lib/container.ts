import type { ILLMProvider } from '@/interfaces/ILLMProvider';
import type { ISearchProvider } from '@/interfaces/ISearchProvider';
import type { IStorageProvider } from '@/interfaces/IStorageProvider';
import type { IPatentProvider } from '@/interfaces/IPatentProvider';
import { OpenAIProvider } from './providers/OpenAIProvider';
import { ClaudeProvider } from './providers/ClaudeProvider';
import { DummySearchProvider } from './providers/DummySearchProvider';
import { TavilySearchProvider } from './providers/TavilySearchProvider';
import { LocalStorageProvider } from './providers/LocalStorageProvider';
import { OpenAIDeepResearchProvider } from './providers/OpenAIDeepResearchProvider';

/**
 * 依存性注入コンテナ
 * 環境変数に基づいて適切なプロバイダーを選択・インスタンス化
 *
 * 将来的な拡張:
 * - LLM_PROVIDER=dify → DifyProviderを使用
 * - SEARCH_PROVIDER=perplexity → PerplexityProviderを使用
 * - STORAGE_PROVIDER=dynamodb → DynamoDBProviderを使用
 */

let llmProviderInstance: ILLMProvider | null = null;
let searchProviderInstance: ISearchProvider | null = null;
let storageProviderInstance: IStorageProvider | null = null;
let patentProviderInstance: IPatentProvider | null = null;

/**
 * LLMプロバイダーを取得（シングルトン）
 */
export function getLLMProvider(): ILLMProvider {
  if (!llmProviderInstance) {
    const provider = process.env.LLM_PROVIDER || 'openai';

    switch (provider.toLowerCase()) {
      case 'openai':
        llmProviderInstance = new OpenAIProvider();
        break;
      case 'claude':
      case 'anthropic':
        llmProviderInstance = new ClaudeProvider();
        break;
      // 将来的な拡張:
      // case 'dify':
      //   llmProviderInstance = new DifyProvider();
      //   break;
      default:
        throw new Error(`Unknown LLM provider: ${provider}`);
    }

    console.log(`[Container] Using LLM Provider: ${llmProviderInstance.getProviderName()}`);
  }

  return llmProviderInstance;
}

/**
 * 検索プロバイダーを取得（シングルトン）
 */
export function getSearchProvider(): ISearchProvider {
  if (!searchProviderInstance) {
    const provider = process.env.SEARCH_PROVIDER || 'dummy';

    switch (provider.toLowerCase()) {
      case 'dummy':
        searchProviderInstance = new DummySearchProvider();
        break;
      case 'tavily':
        searchProviderInstance = new TavilySearchProvider();
        break;
      // 将来的な拡張:
      // case 'perplexity':
      //   searchProviderInstance = new PerplexityProvider();
      //   break;
      // case 'serpapi':
      //   searchProviderInstance = new SerpAPIProvider();
      //   break;
      default:
        throw new Error(`Unknown search provider: ${provider}`);
    }

    console.log(`[Container] Using Search Provider: ${searchProviderInstance.getProviderName()}`);
  }

  return searchProviderInstance;
}

/**
 * ストレージプロバイダーを取得（シングルトン）
 */
export function getStorageProvider(): IStorageProvider {
  if (!storageProviderInstance) {
    const provider = process.env.STORAGE_PROVIDER || 'local';

    switch (provider.toLowerCase()) {
      case 'local':
        storageProviderInstance = new LocalStorageProvider();
        break;
      // 将来的な拡張:
      // case 'dynamodb':
      //   storageProviderInstance = new DynamoDBProvider();
      //   break;
      // case 's3':
      //   storageProviderInstance = new S3Provider();
      //   break;
      default:
        throw new Error(`Unknown storage provider: ${provider}`);
    }

    console.log(`[Container] Using Storage Provider: ${storageProviderInstance.getProviderName()}`);
  }

  return storageProviderInstance;
}

/**
 * 特許プロバイダーを取得（シングルトン）
 */
export function getPatentProvider(): IPatentProvider {
  if (!patentProviderInstance) {
    // 現在はOpenAI Deep Researchプロバイダーのみサポート
    patentProviderInstance = new OpenAIDeepResearchProvider();
    console.log(`[Container] Using Patent Provider: ${patentProviderInstance.getProviderName()}`);
  }

  return patentProviderInstance;
}

/**
 * テスト用: プロバイダーインスタンスをリセット
 */
export function resetProviders() {
  llmProviderInstance = null;
  searchProviderInstance = null;
  storageProviderInstance = null;
  patentProviderInstance = null;
}
