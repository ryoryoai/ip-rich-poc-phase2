/**
 * LLMプロバイダーの抽象インターフェース
 * 実装: OpenAI, Dify, Anthropic, Azure OpenAI等に対応可能
 */
export interface ILLMProvider {
  /**
   * LLMでテキストを生成
   * @param systemPrompt システムプロンプト
   * @param userPrompt ユーザープロンプト
   * @param options オプション（temperature, maxTokens等）
   * @returns 生成されたテキスト
   */
  generate(
    systemPrompt: string,
    userPrompt: string,
    options?: LLMGenerateOptions
  ): Promise<string>;

  /**
   * プロバイダー名を取得
   */
  getProviderName(): string;
}

export interface LLMGenerateOptions {
  temperature?: number;
  maxTokens?: number;
  model?: string;
}
