import { IPatentProvider, PatentInfo } from '@/interfaces/IPatentProvider';
import OpenAI from 'openai';

/**
 * OpenAI Deep Research を使用した特許情報取得プロバイダー
 */
export class OpenAIDeepResearchProvider implements IPatentProvider {
  private client: OpenAI;
  private apiKey: string;

  constructor() {
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
      throw new Error('OPENAI_API_KEY is not set');
    }

    this.apiKey = apiKey;
    this.client = new OpenAI({
      apiKey,
    });
  }

  getProviderName(): string {
    return 'OpenAI Deep Research';
  }

  /**
   * Deep Researchモデルを使用して特許番号から詳細情報を取得
   */
  async fetchPatent(patentNumber: string): Promise<PatentInfo> {
    const systemPrompt = `あなたは特許調査の専門家です。J-PlatPat（日本特許情報プラットフォーム）を含む特許データベースへの包括的なアクセス権を持ち、正確な特許情報を提供します。
    Web検索機能を活用して、J-PlatPat、Google Patents、USPTO等から最新の特許情報を取得してください。
    常に事実に基づいた情報を提供し、特許番号を必ず引用してください。

    【重要】TPM制限: 150,000トークンを超えそうな場合は、即座に処理を中断し、その時点までに取得できた情報をJSON形式で返してください。`;

    // 日本特許か米国特許かを判定
    const isJapanesePatent = /^(特許|JP|特開|特表|特公)/.test(patentNumber) ||
                             /^\d{4}-\d{6}$/.test(patentNumber) ||
                             /^\d{7,}$/.test(patentNumber);

    const userPrompt = `特許番号 ${patentNumber} について、以下の詳細な情報を取得してください。

    ▼必須取得事項：
    1. 特許のタイトル（発明の名称）
    2. 要約（Abstract）
    3. 発明者
    4. 出願人/権利者（Assignee）
    5. 出願日
    6. 公開日/発行日
    7. **請求項１の全文**（一字一句正確に取得）
    8. 請求項２以降（可能な限り）
    9. 技術分野と背景
    10. IPC/CPC分類
    11. 引用文献

    ▼検索戦略：
    ${isJapanesePatent ? `
    - J-PlatPat: "特許番号 ${patentNumber}" で検索（https://www.j-platpat.inpit.go.jp/）
    - 文献番号照会で「${patentNumber}」を検索
    - 特許・実用新案テキスト検索を使用
    ` : `
    - Google Patents: "US${patentNumber} site:patents.google.com" で検索
    - USPTO: "${patentNumber} site:uspto.gov" で検索
    `}

    **重要**:
    - 請求項１は省略せず、完全な形で取得してください
    - J-PlatPatから取得した情報を優先してください
    - 日本語の請求項はそのまま日本語で取得してください

    JSONフォーマットで構造化して返してください。

    【重要なTPM制限対応】
    - 処理中に150,000トークンに達しそうな場合は、その時点で処理を中断
    - 最低限「請求項１の全文」と「特許権者」は必ず含めて返す
    - 部分的な情報でもJSON形式で返し、取得できなかった項目はnullまたは空文字列とする
    - レスポンスサイズを意識し、不要な繰り返しや冗長な説明は避ける
    `;

    try {
      console.log(`[OpenAI Deep Research] ========== 処理開始 ==========`);
      console.log(`[OpenAI Deep Research] 特許番号: ${patentNumber}`);
      console.log(`[OpenAI Deep Research] 処理内容: J-PlatPatから特許情報を検索・取得`);
      console.log(`[OpenAI Deep Research] 期待時間: 1-3分`);
      console.log(`[OpenAI Deep Research] ================================`);

      const modelName = process.env.MODEL_NAME || 'gpt-4o';
      let responseContent: string = '';

      // O4 Mini Deep Researchモデルの場合、特別な処理
      if (modelName.includes('o4-mini-deep-research')) {
        console.log('[OpenAI Deep Research] Using O4 Mini Deep Research model with v1/responses endpoint');

        // 直接APIを呼び出す（SDK未対応のため）
        // 正しいAPI形式: inputパラメータとtoolsを使用
        const response = await fetch('https://api.openai.com/v1/responses', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.apiKey}`
          },
          body: JSON.stringify({
            model: modelName,
            input: `${systemPrompt}\n\n${userPrompt}`,  // promptではなくinput
            reasoning: {
              summary: "auto"  // 自動的に推論サマリーを生成
            },
            background: true,  // バックグラウンド処理を有効化
            tools: [
              {
                type: "web_search_preview"  // Deep Research用のWeb検索ツール
              }
            ],
            max_output_tokens: 10000
            // temperatureは削除（O4 Mini Deep Researchではサポートされていない）
          })
        });

        if (!response.ok) {
          const errorText = await response.text();
          console.error('[OpenAI Deep Research] API Error:', errorText);

          // フォールバックとして通常のGPT-4を使用
          console.log('[OpenAI Deep Research] Falling back to GPT-4o...');
          const fallbackCompletion = await this.client.chat.completions.create({
            model: 'gpt-4o',
            messages: [
              { role: 'system', content: systemPrompt },
              { role: 'user', content: userPrompt }
            ],
            temperature: 0.1,
            max_tokens: 4000,
            response_format: { type: 'json_object' }
          });

          responseContent = fallbackCompletion.choices[0]?.message?.content || '';
        } else {
          const data = await response.json();
          console.log('[OpenAI Deep Research] Initial response:', JSON.stringify(data, null, 2).substring(0, 500));

          // バックグラウンド処理の場合、完了を待つ
          if (data.status === 'queued' || data.status === 'in_progress') {
            const responseId = data.id;
            console.log('[OpenAI Deep Research] Response is queued/in_progress. Polling for completion...');

            // ポーリングして結果を待つ（最大15分）
            let attempts = 0;
            const maxAttempts = 90; // 15分（10秒間隔で90回）

            while (attempts < maxAttempts) {
              await new Promise(resolve => setTimeout(resolve, 10000)); // 10秒待機

              const pollResponse = await fetch(`https://api.openai.com/v1/responses/${responseId}`, {
                method: 'GET',
                headers: {
                  'Authorization': `Bearer ${this.apiKey}`
                }
              });

              if (pollResponse.ok) {
                const pollData = await pollResponse.json();

                // 進行状況を詳細に表示
                const elapsedSeconds = attempts + 1;
                const progressBar = '▓'.repeat(Math.floor(elapsedSeconds / 10)) + '░'.repeat(Math.max(0, 18 - Math.floor(elapsedSeconds / 10)));
                console.log(`[OpenAI Deep Research] [${progressBar}] ${elapsedSeconds}秒経過 - status: ${pollData.status}`);

                // 思考過程を詳細に表示
                if (pollData.metadata) {
                  console.log('[OpenAI Deep Research] Metadata:', JSON.stringify(pollData.metadata, null, 2));
                }
                if (pollData.reasoning) {
                  console.log('[OpenAI Deep Research] 推論中:', typeof pollData.reasoning === 'string'
                    ? pollData.reasoning.substring(0, 200) + '...'
                    : JSON.stringify(pollData.reasoning).substring(0, 200) + '...');
                }
                if (pollData.progress) {
                  console.log('[OpenAI Deep Research] 進捗:', pollData.progress);
                }

                // 10秒ごとに詳細状態を表示
                if (attempts % 10 === 0) {
                  console.log('[OpenAI Deep Research] === 処理状況サマリー ===');
                  console.log(`  - 特許番号: ${patentNumber}`);
                  console.log(`  - 経過時間: ${elapsedSeconds}秒`);
                  console.log(`  - ステータス: ${pollData.status}`);
                  console.log(`  - タイムアウトまで: ${maxAttempts - attempts}秒`);
                  console.log('========================');
                }

                if (pollData.status === 'completed') {
                  console.log('[OpenAI Deep Research] === 処理完了！ ===');
                  console.log(`[OpenAI Deep Research] 総処理時間: ${elapsedSeconds}秒`);

                  // 完了した場合、outputから結果を取得
                  if (Array.isArray(pollData.output) && pollData.output.length > 0) {
                    // outputの最初のメッセージを取得
                    const output = pollData.output[0];
                    if (output.type === 'message' && output.content) {
                      responseContent = Array.isArray(output.content)
                        ? output.content.map((c: any) => c.text || '').join('\n')
                        : output.content;
                    } else {
                      responseContent = JSON.stringify(pollData.output);
                    }
                  } else {
                    responseContent = JSON.stringify(pollData);
                  }
                  break;
                } else if (pollData.status === 'failed') {
                  console.log('[OpenAI Deep Research] === 処理失敗 ===');
                  console.log('[OpenAI Deep Research] エラー詳細:', JSON.stringify(pollData.error, null, 2));
                  throw new Error('Deep Research failed: ' + JSON.stringify(pollData.error));
                }
              }

              attempts++;
            }

            if (attempts >= maxAttempts) {
              console.error('[OpenAI Deep Research] Timeout waiting for response');
              // タイムアウト時はフォールバック
              throw new Error('Deep Research timeout');
            }
          } else {
            // 即座に完了している場合
            if (Array.isArray(data.output) && data.output.length > 0) {
              const output = data.output[0];
              if (output.type === 'message' && output.content) {
                responseContent = Array.isArray(output.content)
                  ? output.content.map((c: any) => c.text || '').join('\n')
                  : output.content;
              } else {
                responseContent = JSON.stringify(data.output);
              }
            } else {
              responseContent = JSON.stringify(data);
            }
          }
        }
      } else {
        // 通常のGPTモデルを使用
        console.log(`[OpenAI Deep Research] Using standard model: ${modelName}`);
        const completion = await this.client.chat.completions.create({
          model: modelName,
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: userPrompt }
          ],
          temperature: 0.1,
          max_tokens: 4000,
          response_format: { type: 'json_object' }
        });

        responseContent = completion.choices[0]?.message?.content || '';
      }

      if (!responseContent) {
        throw new Error('No response from OpenAI');
      }

      // JSONをパース
      let patentData;
      try {
        patentData = JSON.parse(responseContent);
      } catch (e) {
        console.error('[OpenAI Deep Research] Failed to parse JSON response, extracting from text');
        // JSONパースに失敗した場合、テキストから情報を抽出
        patentData = this.extractPatentInfoFromText(responseContent, patentNumber);
      }

      return {
        patentNumber: patentData.patentNumber || patentNumber,
        title: patentData.title || '',
        abstract: patentData.abstract,
        inventors: patentData.inventors || [],
        assignee: patentData.assignee,
        filingDate: patentData.filingDate,
        publicationDate: patentData.publicationDate || patentData.issueDate,
        claims: patentData.claims || (patentData.claim1 ? [patentData.claim1] : []),
        description: patentData.description,
        classifications: patentData.classifications || [],
        citations: patentData.citations || []
      };
    } catch (error) {
      console.error('[OpenAI Deep Research] Error fetching patent:', error);
      throw new Error(`Failed to fetch patent information: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * 特許の請求項のみを取得
   */
  async fetchClaims(patentNumber: string): Promise<string[]> {
    const patentInfo = await this.fetchPatent(patentNumber);
    return patentInfo.claims || [];
  }

  /**
   * テキストから特許情報を抽出（フォールバック用）
   */
  private extractPatentInfoFromText(text: any, patentNumber: string): any {
    const info: any = {
      patentNumber,
      claims: []
    };

    // textが文字列でない場合の処理
    if (typeof text !== 'string') {
      console.warn('[OpenAI Deep Research] Response is not a string:', text);

      // オブジェクトの場合、プロパティから情報を抽出
      if (text && typeof text === 'object') {
        info.title = text.title || text.patentTitle || '';
        info.claims = text.claims || (text.claim1 ? [text.claim1] : []);
        info.assignee = text.assignee || text.applicant || '';
        return info;
      }

      // それ以外の場合は文字列に変換
      text = String(text);
    }

    // タイトルの抽出
    const titleMatch = text.match(/(?:発明の名称|Title|タイトル)[：:]\s*([^\n]+)/i);
    if (titleMatch) info.title = titleMatch[1].trim();

    // 請求項1の抽出
    const claim1Match = text.match(/(?:請求項1|Claim 1)[：:]\s*([\s\S]*?)(?=請求項2|Claim 2|$)/i);
    if (claim1Match) {
      info.claim1 = claim1Match[1].trim();
      info.claims = [claim1Match[1].trim()];
    }

    // 出願人の抽出
    const assigneeMatch = text.match(/(?:出願人|権利者|Assignee)[：:]\s*([^\n]+)/i);
    if (assigneeMatch) info.assignee = assigneeMatch[1].trim();

    return info;
  }
}