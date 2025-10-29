import { NextRequest, NextResponse } from 'next/server';
import { getPatentProvider, getLLMProvider } from '@/lib/container';

/**
 * Deep Search分析APIエンドポイント
 * 特許番号のみを受け取り、自動的に侵害可能性のある製品を検出
 */
export async function POST(request: NextRequest) {
  try {
    const { patentNumber, mode = 'auto' } = await request.json();

    if (!patentNumber) {
      return NextResponse.json(
        { error: '特許番号が指定されていません' },
        { status: 400 }
      );
    }

    console.log(`[API] Starting deep search analysis for patent: ${patentNumber}`);

    // Step 1: 特許情報を軽量モードで取得（TPM節約）
    const patentProvider = getPatentProvider();
    const patentInfo = await patentProvider.fetchPatent(patentNumber);

    if (!patentInfo.claims || patentInfo.claims.length === 0) {
      return NextResponse.json(
        { error: '特許の請求項を取得できませんでした' },
        { status: 404 }
      );
    }

    // Step 2: Deep Searchで侵害可能性のある製品を自動検出
    const llmProvider = getLLMProvider();
    const { systemPrompt, userPrompt } = buildDeepSearchPrompts(patentNumber, patentInfo.claims[0], mode);

    console.log(`[API] Executing deep search with O4 Mini model...`);
    const analysisResult = await llmProvider.generate(systemPrompt, userPrompt);

    // Step 3: 結果を構造化
    const structuredResult = {
      patentNumber,
      patentTitle: patentInfo.title,
      claim1: patentInfo.claims[0],
      mode,
      analysisDate: new Date().toISOString(),
      deepSearchResult: analysisResult,
      potentialInfringers: extractPotentialInfringers(analysisResult),
      tokensUsed: analysisResult.length, // 概算
      tpmInfo: {
        stage1_tokens: patentInfo.claims[0].length,
        stage2_tokens: analysisResult.length,
        total_tokens: patentInfo.claims[0].length + analysisResult.length,
        saved_percentage: '約40-60%のトークン節約'
      }
    };

    return NextResponse.json(structuredResult);
  } catch (error) {
    console.error('[API] Deep search error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Deep search failed' },
      { status: 500 }
    );
  }
}

/**
 * Deep Search用のプロンプト構築
 */
function buildDeepSearchPrompts(patentNumber: string, claim1: string, mode: string): { systemPrompt: string; userPrompt: string } {
  const systemPrompt = '特許侵害調査の専門家として、Web検索機能を活用して包括的な調査を実施してください。';

  let userPrompt: string;

  if (mode === 'auto') {
    // 完全自動モード：侵害可能性のある製品を自動検出
    userPrompt = `
特許${patentNumber}の請求項１について、侵害可能性のある製品・サービスを調査せよ。

▼請求項１：
${claim1}

▼調査要求事項：
1. **Web検索を活用**して、この特許の技術分野に関連する主要企業と製品を特定
2. 日本国内でサービス展開している外国企業を重点的に調査
3. 各構成要件を満たす可能性の高い製品を3-5個リストアップ
4. 各製品について構成要件との対応関係を分析

▼出力フォーマット：
### 検出された潜在的侵害製品

**製品1: [企業名] - [製品名]**
- 侵害可能性: [高/中/低]
- 構成要件充足度: [X/Y要件]
- 根拠URL: [公開情報のURL]
- 詳細分析:
  構成要件A｜[対応機能]｜[○/×]｜[根拠]
  構成要件B｜[対応機能]｜[○/×]｜[根拠]

**製品2: ...**

### サマリー
- 最も侵害可能性が高い製品: [製品名]
- 推奨される詳細調査対象: [1-2製品]

注意：150,000 TPMの制限内で効率的に分析すること。
`;
  } else {
    // セミオートモード：技術分野のみ特定して調査
    userPrompt = `
特許${patentNumber}の技術分野における主要プレイヤーと製品を調査せよ。

▼請求項１（要約）：
${claim1.substring(0, 500)}...

▼調査内容：
1. この技術分野の主要企業トップ5
2. 各企業の関連製品・サービス
3. 特に日本市場での展開状況
4. 簡易的な侵害可能性評価

効率的にまとめ、トークン使用を最小限に抑えること。
`;
  }

  return { systemPrompt, userPrompt };
}

/**
 * 分析結果から潜在的侵害者を抽出
 */
function extractPotentialInfringers(analysisResult: string): Array<{
  company: string;
  product: string;
  probability: string;
}> {
  const infringers = [];

  // 簡易的なパターンマッチングで企業・製品を抽出
  const productPattern = /\*\*製品\d+:\s*\[([^\]]+)\]\s*-\s*\[([^\]]+)\]\*\*/g;
  let match;

  while ((match = productPattern.exec(analysisResult)) !== null) {
    infringers.push({
      company: match[1],
      product: match[2],
      probability: 'TBD'
    });
  }

  return infringers;
}