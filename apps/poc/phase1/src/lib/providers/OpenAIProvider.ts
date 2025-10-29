import OpenAI from 'openai';
import type { ILLMProvider, LLMGenerateOptions } from '@/interfaces/ILLMProvider';

/**
 * OpenAI APIを使用したLLMプロバイダー実装
 * 環境変数: OPENAI_API_KEY, MODEL_NAME, MAX_TOKENS, TEMPERATURE
 */
export class OpenAIProvider implements ILLMProvider {
  private client: OpenAI;
  private defaultModel: string;
  private defaultMaxTokens: number;
  private defaultTemperature: number;

  constructor() {
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
      throw new Error('OPENAI_API_KEY environment variable is required');
    }

    this.client = new OpenAI({ apiKey });
    this.defaultModel = process.env.MODEL_NAME || 'gpt-3.5-turbo';
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
      const response = await this.client.chat.completions.create({
        model,
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt },
        ],
        max_tokens: maxTokens,
        temperature,
      });

      return response.choices[0]?.message?.content || '';
    } catch (error) {
      console.error('OpenAI API error:', error);
      throw new Error(`OpenAI API error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  getProviderName(): string {
    return 'OpenAI';
  }
}
