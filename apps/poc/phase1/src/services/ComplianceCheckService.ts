import type { ILLMProvider } from '@/interfaces/ILLMProvider';
import type { ISearchProvider, SearchResult } from '@/interfaces/ISearchProvider';
import type { Requirement } from '@/types/patent';
import type { ComplianceResult } from '@/types/analysis';
import { PROMPTS } from '@/lib/prompts';

/**
 * 充足性判定サービス
 * LLMプロバイダーと検索プロバイダーに依存（DI）
 */
export class ComplianceCheckService {
  constructor(
    private llmProvider: ILLMProvider,
    private searchProvider: ISearchProvider
  ) {}

  /**
   * 構成要件の充足性を判定
   */
  async checkCompliance(
    requirement: Requirement,
    productName: string,
    companyName: string
  ): Promise<ComplianceResult> {
    // 製品情報を検索
    const searchQuery = `${companyName} ${productName} specifications features`;
    const searchResults = await this.searchProvider.search(searchQuery, 3);

    // 検索結果を製品仕様として整理
    const productSpec = this.formatSearchResults(searchResults);

    // LLMで充足性を判定
    const systemPrompt = PROMPTS.checkCompliance.system;
    const userPrompt = PROMPTS.checkCompliance.user(
      requirement.description,
      productName,
      companyName,
      productSpec
    );

    const response = await this.llmProvider.generate(systemPrompt, userPrompt);

    // レスポンスをパース
    const judgment = this.parseJudgment(response);

    return {
      requirementId: requirement.id,
      requirement: requirement.description,
      compliance: judgment.compliance,
      reason: judgment.reason,
      evidence: judgment.evidence,
      urls: searchResults.map((r) => r.url),
    };
  }

  /**
   * 検索結果を整形
   */
  private formatSearchResults(results: SearchResult[]): string {
    return results
      .map((result, i) => `${i + 1}. ${result.title}\n${result.snippet}`)
      .join('\n\n');
  }

  /**
   * 判定結果をパース
   */
  private parseJudgment(response: string): {
    compliance: '○' | '×';
    reason: string;
    evidence: string;
  } {
    const lines = response.trim().split('\n');
    const judgment = {
      compliance: '×' as '○' | '×',
      reason: '',
      evidence: '',
    };

    for (const line of lines) {
      const trimmedLine = line.trim();
      if (trimmedLine.includes('充足判断') || trimmedLine.toLowerCase().includes('compliance')) {
        if (trimmedLine.includes('○')) {
          judgment.compliance = '○';
        } else if (trimmedLine.includes('×')) {
          judgment.compliance = '×';
        }
      } else if (trimmedLine.includes('理由') || trimmedLine.toLowerCase().includes('reason')) {
        judgment.reason = trimmedLine.includes(':') ? trimmedLine.split(':', 2)[1].trim() : trimmedLine;
      } else if (trimmedLine.includes('根拠') || trimmedLine.toLowerCase().includes('evidence')) {
        judgment.evidence = trimmedLine.includes(':') ? trimmedLine.split(':', 2)[1].trim() : trimmedLine;
      }
    }

    return judgment;
  }
}
