/**
 * LLMプロンプトテンプレート
 * プロバイダーに依存しない汎用的なプロンプト定義
 */

export const PROMPTS = {
  /**
   * 構成要件抽出プロンプト
   */
  extractRequirements: {
    system: `あなたは特許の専門家です。
特許請求項を分析し、構成要件を明確に分解してください。
各構成要件には、ID（構成要件A、構成要件B等）と説明を含めてください。`,

    user: (patentNumber: string, claimText: string) =>
      `以下の特許の請求項1を分析し、構成要件を抽出してください。

【特許番号】
${patentNumber}

【請求項1】
${claimText}

各構成要件を以下の形式で出力してください:
1. 構成要件A: [構成要件の説明]
2. 構成要件B: [構成要件の説明]
...`,
  },

  /**
   * 充足性判定プロンプト
   */
  checkCompliance: {
    system: `あなたは特許侵害の充足性を判定する専門家です。
構成要件と製品の仕様を比較し、充足性を判定してください。`,

    user: (
      requirement: string,
      productName: string,
      companyName: string,
      productSpec: string
    ) =>
      `以下の構成要件について、製品が充足しているか判定してください。

【構成要件】
${requirement}

【製品情報】
製品名: ${productName}
企業名: ${companyName}
仕様情報: ${productSpec}

判定結果を以下の形式で出力してください:
- 充足判断: ○/×
- 理由: [判定理由を簡潔に記載]
- 根拠: [参照URLまたは具体的な製品機能]`,
  },
} as const;
