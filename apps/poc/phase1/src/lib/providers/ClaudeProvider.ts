import Anthropic from '@anthropic-ai/sdk';
import type { ILLMProvider, LLMGenerateOptions } from '@/interfaces/ILLMProvider';

/**
 * Claude APIを使用したLLMプロバイダー実装
 * 環境変数: ANTHROPIC_API_KEY, MODEL_NAME, MAX_TOKENS, TEMPERATURE
 */
export class ClaudeProvider implements ILLMProvider {
  private client: Anthropic;
  private defaultModel: string;
  private defaultMaxTokens: number;
  private defaultTemperature: number;

  constructor() {
    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      throw new Error('ANTHROPIC_API_KEY environment variable is required');
    }

    this.client = new Anthropic({ apiKey });
    this.defaultModel = process.env.MODEL_NAME || 'claude-3-5-sonnet-20241022';
    this.defaultMaxTokens = parseInt(process.env.MAX_TOKENS || '2000', 10);
    this.defaultTemperature = parseFloat(process.env.TEMPERATURE || '0.3');
  }

  async generate(
    systemPrompt: string,
    userPrompt: string,
    options?: LLMGenerateOptions
  ): Promise<string> {
    const model = options?.model || this.defaultModel;
    const maxTokens = options?.maxTokens || this.defaultMaxTokens;
    const temperature = options?.temperature ?? this.defaultTemperature;

    try {
      const response = await this.client.messages.create({
        model,
        max_tokens: maxTokens,
        temperature,
        system: systemPrompt,
        messages: [
          { role: 'user', content: userPrompt },
        ],
      });

      // Claude APIのレスポンス処理
      const content = response.content[0];
      if (content.type === 'text') {
        return content.text;
      }
      return '';
    } catch (error) {
      console.error('Claude API error:', error);
      throw new Error(`Claude API error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  getProviderName(): string {
    return 'Claude (Anthropic)';
  }
}