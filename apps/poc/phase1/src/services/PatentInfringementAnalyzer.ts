import { IPatentProvider, PatentInfo } from '@/interfaces/IPatentProvider';
import { ILLMProvider } from '@/interfaces/ILLMProvider';
import { ISearchProvider } from '@/interfaces/ISearchProvider';

/**
 * 特許侵害調査分析サービス
 * sample/侵害調査プロンプト.txt のロジックを実装
 */
export class PatentInfringementAnalyzer {
  constructor(
    private patentProvider: IPatentProvider,
    private llmProvider: ILLMProvider,
    private searchProvider: ISearchProvider
  ) {}

  /**
   * 特許番号のみから侵害可能性を分析
   */
  async analyzeByPatentNumber(
    patentNumber: string,
    targetCompany?: string,
    targetProduct?: string
  ): Promise<InfringementAnalysisResult> {
    console.log(`[Analyzer] Starting analysis for patent: ${patentNumber}`);

    // Step 1: 特許情報を取得
    const patentInfo = await this.patentProvider.fetchPatent(patentNumber);

    if (!patentInfo.claims || patentInfo.claims.length === 0) {
      throw new Error('特許の請求項を取得できませんでした');
    }

    const claim1 = patentInfo.claims[0];
    console.log(`[Analyzer] Retrieved Claim 1: ${claim1.substring(0, 100)}...`);

    // Step 2: 侵害調査プロンプトの構築
    const analysisPrompt = this.buildInfringementAnalysisPrompt(
      patentNumber,
      claim1,
      patentInfo,
      targetCompany,
      targetProduct
    );

    // Step 3: LLMによる侵害分析
    const analysisResult = await this.llmProvider.generate(analysisPrompt);

    // Step 4: 結果の構造化
    return this.parseAnalysisResult(analysisResult, patentInfo);
  }

  /**
   * 侵害調査プロンプトを構築（sample/侵害調査プロンプト.txt に基づく）
   */
  private buildInfringementAnalysisPrompt(
    patentNumber: string,
    claim1: string,
    patentInfo: PatentInfo,
    targetCompany?: string,
    targetProduct?: string
  ): string {
    let prompt = `下記の特許${patentNumber}の請求項１の要件を満たす侵害製品を調査せよ。`;

    if (targetCompany && targetProduct) {
      prompt += `対象は${targetCompany}社の${targetProduct}とする。`;
    } else if (targetCompany) {
      prompt += `対象は${targetCompany}社の製品とする。`;
    } else {
      prompt += `対象は日本国内でサービス展開している外国企業とする。`;
    }

    prompt += `

▼要求事項：
・請求項１に記載された**すべての構成要件を満たす製品のみ**を調査対象とする（１つでも欠ける場合は除外）
・特許番号と請求項１の全文を**完全に照合**の上で処理すること（他の特許と絶対に混同しないこと）
・請求項１の構成要件をそのまま引用して記載する（勝手に要約・再構成しない）
・各構成要件ごとに、製品の仕様と比較し、充足性（○/×）を判断
・参考として請求項２以降や発明の詳細な説明を参照してもよいが、主判断基準は請求項１のみとする
・**web検索を使用して**、製品の公開仕様・企業ページ・販売情報などを確認のうえ根拠を示すこと
・出力フォーマットは以下に従うこと：

▼出力フォーマット：
構成要件｜製品の対応構成｜充足判断（○/×）｜根拠（可能な限りURLや公開情報を記載）

・日本語で回答すること

＜以下、特許${patentNumber}（請求項１を全文で記載）＞
${claim1}

`;

    // 追加情報があれば含める
    if (patentInfo.title) {
      prompt += `
＜参考：発明の名称＞
${patentInfo.title}
`;
    }

    if (patentInfo.abstract) {
      prompt += `
＜参考：要約＞
${patentInfo.abstract}
`;
    }

    return prompt;
  }

  /**
   * 構成要件を抽出
   */
  async extractRequirements(claim1: string): Promise<string[]> {
    const prompt = `以下の特許請求項１から、個別の構成要件を抽出してください。
各構成要件は独立した技術的特徴として分離し、番号付きリストで出力してください。

請求項１：
${claim1}

出力形式：
1. [構成要件1]
2. [構成要件2]
...`;

    const result = await this.llmProvider.generate(prompt);

    // 番号付きリストをパース
    const requirements = result
      .split('\n')
      .filter(line => /^\d+\./.test(line))
      .map(line => line.replace(/^\d+\.\s*/, '').trim());

    return requirements;
  }

  /**
   * 分析結果をパース
   */
  private parseAnalysisResult(
    analysisText: string,
    patentInfo: PatentInfo
  ): InfringementAnalysisResult {
    const lines = analysisText.split('\n');
    const requirements: RequirementAnalysis[] = [];

    for (const line of lines) {
      if (line.includes('｜')) {
        const parts = line.split('｜').map(p => p.trim());
        if (parts.length >= 4) {
          requirements.push({
            requirement: parts[0],
            productFeature: parts[1],
            isSatisfied: parts[2] === '○',
            evidence: parts[3]
          });
        }
      }
    }

    // 全体の侵害判定
    const overallInfringement = requirements.length > 0 &&
      requirements.every(r => r.isSatisfied);

    return {
      patentNumber: patentInfo.patentNumber,
      patentTitle: patentInfo.title || '',
      claim1: patentInfo.claims?.[0] || '',
      requirements,
      overallInfringement,
      analysisDate: new Date().toISOString(),
      confidence: this.calculateConfidence(requirements)
    };
  }

  /**
   * 信頼度スコアを計算
   */
  private calculateConfidence(requirements: RequirementAnalysis[]): number {
    if (requirements.length === 0) return 0;

    const withEvidence = requirements.filter(r => r.evidence && r.evidence.length > 10);
    return Math.round((withEvidence.length / requirements.length) * 100);
  }
}

/**
 * 構成要件の分析結果
 */
export interface RequirementAnalysis {
  requirement: string;      // 構成要件
  productFeature: string;   // 製品の対応構成
  isSatisfied: boolean;     // 充足判断
  evidence: string;         // 根拠（URL等）
}

/**
 * 侵害分析の全体結果
 */
export interface InfringementAnalysisResult {
  patentNumber: string;
  patentTitle: string;
  claim1: string;
  requirements: RequirementAnalysis[];
  overallInfringement: boolean;
  analysisDate: string;
  confidence: number;  // 0-100
  targetCompany?: string;
  targetProduct?: string;
}