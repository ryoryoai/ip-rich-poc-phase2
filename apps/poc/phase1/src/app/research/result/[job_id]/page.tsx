'use client';

import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ResultData {
  job_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  patent_number: string;
  company_name: string;
  product_name: string;
  claim_text: string;
  input_prompt?: string;
  research_results?: {
    reportText: string;
    citations: Array<{
      type: string;
      title: string;
      url: string;
    }>;
    rawResponse: any;
    usage: {
      input_tokens: number;
      output_tokens: number;
      total_tokens: number;
    } | null;
  };
  requirements?: any;
  compliance_results?: any;
  summary?: any;
}

export default function ResultPage({ params }: { params: { job_id: string } }) {
  const [result, setResult] = useState<ResultData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showRawJson, setShowRawJson] = useState(false);
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async () => {
    if (!result?.research_results?.rawResponse) return;

    try {
      await navigator.clipboard.writeText(
        JSON.stringify(result.research_results.rawResponse, null, 2)
      );
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  // コスト計算 (OpenAI o4-mini-deep-research の料金)
  // https://openai.com/api/pricing/
  // Input: $1.50 / 1M tokens, Output: $6.00 / 1M tokens
  const calculateCost = (usage: { input_tokens: number; output_tokens: number }) => {
    const inputCost = (usage.input_tokens / 1_000_000) * 1.50;
    const outputCost = (usage.output_tokens / 1_000_000) * 6.00;
    const totalCost = inputCost + outputCost;
    return {
      inputCost,
      outputCost,
      totalCost,
      totalCostJPY: totalCost * 150, // 1USD = 150円と仮定
    };
  };

  useEffect(() => {
    const fetchResult = async () => {
      try {
        const res = await fetch(`/api/analyze/result/${params.job_id}`);
        const data = await res.json();

        if (!res.ok) {
          throw new Error(data.error || 'Failed to fetch result');
        }

        setResult(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchResult();
  }, [params.job_id]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center">読み込み中...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
          <a
            href="/research/list"
            className="text-blue-600 hover:text-blue-800"
          >
            ← 分析履歴一覧に戻る
          </a>
        </div>
      </div>
    );
  }

  if (!result) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <a
            href="/research/list"
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            ← 分析履歴一覧
          </a>
        </div>

        <div className="bg-white shadow rounded-lg p-8 mb-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                分析結果
              </h1>
              <p className="text-sm text-gray-500">
                作成日時: {formatDate(result.created_at)}
              </p>
            </div>
            <span className="px-3 py-1 bg-green-100 text-green-800 text-sm font-medium rounded-full">
              完了
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-1">
                特許番号
              </h3>
              <p className="text-lg font-semibold text-gray-900">
                {result.patent_number}
              </p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-1">
                調査対象
              </h3>
              <p className="text-lg font-semibold text-gray-900">
                {result.company_name} / {result.product_name}
              </p>
            </div>
          </div>

          <div className="border-t border-gray-200 pt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              請求項1
            </h3>
            <p className="text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 p-4 rounded">
              {result.claim_text}
            </p>
          </div>
        </div>

        {result.research_results && (
          <>
            {/* 入力プロンプト */}
            {result.input_prompt && (
              <div className="bg-white shadow rounded-lg p-8 mb-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">
                  入力プロンプト
                </h2>
                <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-gray-50 p-4 rounded border border-gray-200">
                  {result.input_prompt}
                </pre>
              </div>
            )}

            {/* Deep Research レポート */}
            {(() => {
              // 最後のmessageタイプのoutputを取得
              const outputs = result.research_results.rawResponse?.output || [];
              const lastMessage = [...outputs]
                .reverse()
                .find((o: any) => o.type === 'message');
              const finalText = lastMessage?.content?.find((c: any) => c.type === 'output_text')?.text;

              if (!finalText) return null;

              // 全角パイプを半角パイプに変換
              const normalizedText = finalText.replace(/｜/g, '|');

              return (
                <div className="bg-white shadow rounded-lg p-8 mb-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">
                    Deep Research レポート
                  </h2>
                  <div className="bg-gray-50 p-6 rounded border border-gray-200 overflow-x-auto">
                    <div className="markdown-content">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {normalizedText}
                      </ReactMarkdown>
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* 引用文献 */}
            {result.research_results.citations && result.research_results.citations.length > 0 && (
              <div className="bg-white shadow rounded-lg p-8 mb-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">
                  引用文献 ({result.research_results.citations.length})
                </h2>
                <div className="space-y-3">
                  {result.research_results.citations.map((citation, index) => (
                    <div
                      key={index}
                      className="border-l-4 border-blue-500 pl-4 py-2"
                    >
                      <div className="flex items-start space-x-2">
                        <span className="text-sm font-medium text-gray-500">
                          [{index + 1}]
                        </span>
                        <div className="flex-1">
                          {citation.title && (
                            <p className="text-sm font-medium text-gray-900">
                              {citation.title}
                            </p>
                          )}
                          {citation.url && (
                            <a
                              href={citation.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-blue-600 hover:text-blue-800 break-all"
                            >
                              {citation.url}
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* API使用状況とコスト */}
            {result.research_results.usage && (
              <div className="bg-white shadow rounded-lg p-8 mb-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">
                  API使用状況・コスト推定
                </h2>

                {/* モデルと所要時間 */}
                <div className="grid grid-cols-2 gap-4 mb-6 pb-6 border-b">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">使用モデル</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {result.research_results.rawResponse?.model || 'o4-mini-deep-research-2025-06-26'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 mb-1">所要時間</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {(() => {
                        const start = new Date(result.created_at);
                        const end = new Date(result.updated_at);
                        const diffMs = end.getTime() - start.getTime();
                        const diffMins = Math.floor(diffMs / 60000);
                        const diffSecs = Math.floor((diffMs % 60000) / 1000);
                        return `${diffMins}分 ${diffSecs}秒`;
                      })()}
                    </p>
                  </div>
                </div>

                {/* トークン数 */}
                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="bg-gray-50 p-4 rounded">
                    <p className="text-sm text-gray-500">入力トークン</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {result.research_results.usage.input_tokens.toLocaleString()}
                    </p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded">
                    <p className="text-sm text-gray-500">出力トークン</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {result.research_results.usage.output_tokens.toLocaleString()}
                    </p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded">
                    <p className="text-sm text-gray-500">合計トークン</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {result.research_results.usage.total_tokens.toLocaleString()}
                    </p>
                  </div>
                </div>

                {/* コスト推定 */}
                {(() => {
                  const cost = calculateCost(result.research_results.usage);
                  return (
                    <div className="border-t pt-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">
                        コスト推定
                      </h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-blue-50 p-4 rounded">
                          <p className="text-sm text-gray-600 mb-1">入力コスト</p>
                          <p className="text-xl font-bold text-blue-900">
                            ${cost.inputCost.toFixed(4)}
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
                            約 ¥{cost.inputCost * 150}
                          </p>
                        </div>
                        <div className="bg-blue-50 p-4 rounded">
                          <p className="text-sm text-gray-600 mb-1">出力コスト</p>
                          <p className="text-xl font-bold text-blue-900">
                            ${cost.outputCost.toFixed(4)}
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
                            約 ¥{cost.outputCost * 150}
                          </p>
                        </div>
                      </div>
                      <div className="bg-green-50 p-4 rounded mt-4">
                        <div className="flex justify-between items-center">
                          <p className="text-sm text-gray-600">合計コスト</p>
                          <div className="text-right">
                            <p className="text-2xl font-bold text-green-900">
                              ${cost.totalCost.toFixed(4)}
                            </p>
                            <p className="text-lg text-green-700">
                              約 ¥{Math.round(cost.totalCostJPY)}
                            </p>
                          </div>
                        </div>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        ※ o4-mini-deep-research: 入力 $1.50/1M, 出力 $6.00/1M (1USD = ¥150で計算)
                      </p>
                    </div>
                  );
                })()}
              </div>
            )}

            {/* OpenAI Raw JSON (トグル) */}
            <div className="bg-white shadow rounded-lg p-8 mb-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold text-gray-900">
                  OpenAI レスポンス詳細 (JSON)
                </h2>
                <div className="flex gap-2">
                  <button
                    onClick={copyToClipboard}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    {copied ? '✓ コピー済み' : 'JSONをコピー'}
                  </button>
                  <button
                    onClick={() => setShowRawJson(!showRawJson)}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                  >
                    {showRawJson ? '閉じる' : '表示する'}
                  </button>
                </div>
              </div>
              {showRawJson && (
                <div className="mt-4">
                  <pre className="bg-gray-900 text-gray-100 p-4 rounded overflow-x-auto text-xs">
                    {JSON.stringify(result.research_results.rawResponse, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </>
        )}

        {!result.research_results && (
          <div className="bg-white shadow rounded-lg p-8">
            <p className="text-gray-500 text-center">
              検索結果がありません
            </p>
          </div>
        )}

        <div className="flex justify-between mt-6">
          <a
            href="/research/list"
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            ← 分析履歴一覧
          </a>
          <a
            href="/research"
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            新しい分析を開始 →
          </a>
        </div>
      </div>
    </div>
  );
}
