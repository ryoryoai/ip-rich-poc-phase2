import type { ILLMProvider } from '@/interfaces/ILLMProvider';
import type { Requirement } from '@/types/patent';
import { PROMPTS } from '@/lib/prompts';

/**
 * 構成要件抽出サービス
 * LLMプロバイダーに依存（DI）
 */
export class RequirementExtractionService {
  constructor(private llmProvider: ILLMProvider) {}

  /**
   * 請求項から構成要件を抽出
   */
  async extractRequirements(
    patentNumber: string,
    claimText: string
  ): Promise<Requirement[]> {
    const systemPrompt = PROMPTS.extractRequirements.system;
    const userPrompt = PROMPTS.extractRequirements.user(patentNumber, claimText);

    const response = await this.llmProvider.generate(systemPrompt, userPrompt);

    return this.parseRequirements(response);
  }

  /**
   * LLM応答から構成要件をパース
   */
  private parseRequirements(response: string): Requirement[] {
    const requirements: Requirement[] = [];
    const lines = response.trim().split('\n');

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      // "1. 構成要件A: 説明" 形式をパース
      const match = trimmed.match(/^(\d+\.?\s*|[-•]\s*)(.+?):\s*(.+)$/);
      if (match) {
        const [, , id, description] = match;
        requirements.push({
          id: id.trim(),
          description: description.trim(),
        });
      }
    }

    return requirements;
  }
}
