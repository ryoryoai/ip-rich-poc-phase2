import { NextRequest, NextResponse } from 'next/server';
import { getLLMProvider } from '@/lib/container';

/**
 * 特許IDのみで侵害調査を実行するシンプルなAPIエンドポイント
 * 処理フロー：
 * 1. J-PlatPatから請求項1を取得
 * 2. sample/侵害調査プロンプト.txt を使用して侵害調査
 */
export async function POST(request: NextRequest) {
  try {
    const { patentId } = await request.json();

    if (!patentId) {
      return NextResponse.json(
        { error: '特許IDが指定されていません' },
        { status: 400 }
      );
    }

    console.log(`[API] Starting infringement analysis for patent: ${patentId}`);

    const llmProvider = getLLMProvider();

    // ========================================
    // 処理1: J-PlatPatから請求項1を取得
    // ========================================
    const fetchClaimPrompt = `
あなたは特許調査の専門家です。
J-PlatPat（日本特許情報プラットフォーム）から特許情報を取得してください。

▼タスク：
特許番号「${patentId}」について以下の情報を取得してください：
1. 特許権者（出願人/権利者）
2. 発明の名称と内容の要約
3. 請求項1の全文

▼検索方法：
1. J-PlatPat (https://www.j-platpat.inpit.go.jp/) にアクセス
2. 「特許・実用新案番号照会」で「${patentId}」を検索
3. 書誌情報から特許権者を確認
4. 請求項1の全文を取得
5. 発明の内容を要約

▼重要：
- 請求項1は一字一句省略せずに取得すること
- 特許権者名は正確に記載（例：株式会社〇〇、〇〇 Inc.など）
- 発明の内容は技術分野と主要な特徴を含めて簡潔に要約
- 日本語の場合は日本語のまま取得

【TPM制限対応】
- 150,000トークンに近づいたら処理を中断
- 最低限「請求項1」と「特許権者」だけは必ず取得して返す
- 部分的な情報でもJSON形式で返す

▼出力形式：
以下のJSON形式で返してください：
{
  "patentNumber": "${patentId}",
  "title": "発明の名称",
  "patentHolder": "特許権者（出願人）の正式名称",
  "inventionSummary": "発明の内容の要約（技術分野、主要な特徴など）",
  "claim1": "請求項1の完全な全文",
  "technicalField": "技術分野"
}
`;

    console.log(`[API] Step 1: Fetching claim 1 from J-PlatPat...`);

    const patentInfoResponse = await llmProvider.generate(fetchClaimPrompt);

    // JSONをパース
    let patentInfo;
    try {
      patentInfo = JSON.parse(patentInfoResponse);
    } catch (e) {
      console.error('[API] Failed to parse patent info:', e);
      // フォールバック：テキストから抽出を試みる
      patentInfo = {
        patentNumber: patentId,
        claim1: patentInfoResponse,
        title: '',
        assignee: ''
      };
    }

    if (!patentInfo.claim1) {
      return NextResponse.json(
        { error: '請求項1を取得できませんでした' },
        { status: 404 }
      );
    }

    console.log(`[API] Successfully fetched claim 1`);

    // ========================================
    // 処理2: 侵害調査プロンプトを使用して分析
    // ========================================
    const infringementPrompt = `下記の特許${patentId}の請求項１の要件を満たす侵害製品を調査せよ。対象は日本国内でサービス展開している外国企業とする。

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

＜以下、特許${patentId}（請求項１を全文で記載）＞
${patentInfo.claim1}
`;

    console.log(`[API] Step 2: Executing infringement analysis with Deep Search...`);

    const analysisResult = await llmProvider.generate(infringementPrompt);

    // 結果を構造化して返す
    const result = {
      patentId,
      patentTitle: patentInfo.title || '',
      patentHolder: patentInfo.patentHolder || patentInfo.assignee || '',
      inventionSummary: patentInfo.inventionSummary || '',
      technicalField: patentInfo.technicalField || '',
      claim1: patentInfo.claim1,
      analysisDate: new Date().toISOString(),
      infringementAnalysis: analysisResult,
      // 構造化された結果を抽出
      detectedProducts: extractProductsFromAnalysis(analysisResult),
      summary: generateSummary(analysisResult)
    };

    return NextResponse.json(result);
  } catch (error) {
    console.error('[API] Analysis error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : '分析中にエラーが発生しました' },
      { status: 500 }
    );
  }
}

/**
 * 分析結果から製品情報を抽出
 */
function extractProductsFromAnalysis(analysisText: string): Array<{
  company: string;
  product: string;
  compliance: string;
  evidence: string;
}> {
  const products = [];
  const lines = analysisText.split('\n');

  for (const line of lines) {
    // "構成要件｜製品の対応構成｜充足判断（○/×）｜根拠" の形式をパース
    if (line.includes('｜')) {
      const parts = line.split('｜').map(p => p.trim());
      if (parts.length >= 4 && (parts[2] === '○' || parts[2] === '×')) {
        // 製品名を抽出（製品の対応構成から）
        const productMatch = parts[1].match(/([^（）]+)/);
        if (productMatch) {
          products.push({
            company: '', // 後で企業名を抽出
            product: productMatch[1],
            compliance: parts[2],
            evidence: parts[3]
          });
        }
      }
    }
  }

  // 重複を除去
  const uniqueProducts = Array.from(
    new Map(products.map(p => [p.product, p])).values()
  );

  return uniqueProducts;
}

/**
 * 分析結果のサマリーを生成
 */
function generateSummary(analysisText: string): string {
  const hasInfringement = analysisText.includes('○');
  const productCount = (analysisText.match(/製品/g) || []).length;

  if (hasInfringement) {
    return `侵害可能性のある製品が検出されました。${productCount}件の製品について詳細分析を実施しました。`;
  } else {
    return `現時点で明確な侵害製品は検出されませんでした。${productCount}件の製品について分析を実施しました。`;
  }
}