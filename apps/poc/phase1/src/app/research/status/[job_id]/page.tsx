'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface StatusData {
  job_id: string;
  status: 'pending' | 'researching' | 'analyzing' | 'completed' | 'failed';
  progress: number;
  error_message?: string;
}

export default function StatusPage({ params }: { params: { job_id: string } }) {
  const router = useRouter();
  const [status, setStatus] = useState<StatusData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [pollCount, setPollCount] = useState(0);

  const MAX_POLL_ATTEMPTS = 90; // 15分 (90回 × 10秒)

  useEffect(() => {
    const pollStatus = async () => {
      try {
        const res = await fetch(`/api/analyze/status/${params.job_id}`);
        const data = await res.json();

        if (!res.ok) {
          throw new Error(data.error || 'Failed to fetch status');
        }

        setStatus(data);
        setLastChecked(new Date());
        setPollCount(prev => prev + 1);

        // タイムアウトチェック
        if (pollCount >= MAX_POLL_ATTEMPTS && data.status === 'researching') {
          setError('分析がタイムアウトしました（15分経過）。しばらく時間をおいて、分析履歴から確認してください。');
          return;
        }

        // 完了したら結果ページへ遷移
        if (data.status === 'completed') {
          setTimeout(() => {
            router.push(`/research/result/${params.job_id}`);
          }, 1000);
        }

        // 失敗したらエラー表示
        if (data.status === 'failed') {
          setError(data.error_message || 'Analysis failed');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      }
    };

    // 初回実行
    pollStatus();

    // タイムアウトしている場合はポーリングを停止
    if (pollCount >= MAX_POLL_ATTEMPTS) {
      return;
    }

    // 10秒ごとにポーリング
    const interval = setInterval(pollStatus, 10000);

    return () => clearInterval(interval);
  }, [params.job_id, router, pollCount]);

  const getStatusText = () => {
    if (!status) return '読み込み中...';
    switch (status.status) {
      case 'pending':
        return '分析を開始しています...';
      case 'researching':
        return '特許情報を検索中...';
      case 'analyzing':
        return 'AI分析を実行中...';
      case 'completed':
        return '分析完了！結果ページに移動します...';
      case 'failed':
        return '分析に失敗しました';
      default:
        return '処理中...';
    }
  };

  const getStatusColor = () => {
    if (!status) return 'bg-gray-600';
    switch (status.status) {
      case 'completed':
        return 'bg-green-600';
      case 'failed':
        return 'bg-red-600';
      default:
        return 'bg-blue-600';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white shadow rounded-lg p-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">
            分析ステータス
          </h1>

          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              <p className="font-medium">エラー</p>
              <p className="text-sm mt-1">{error}</p>
            </div>
          )}

          <div className="space-y-6">
            <div>
              <p className="text-sm text-gray-500 mb-1">ジョブ ID</p>
              <p className="font-mono text-sm text-gray-700">{params.job_id}</p>
            </div>

            <div>
              <p className="text-lg font-medium text-gray-900 mb-2">
                {getStatusText()}
              </p>

              {lastChecked && status?.status === 'researching' && (
                <p className="text-sm text-gray-600">
                  最終確認日時: {lastChecked.toLocaleString('ja-JP', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                  })}
                </p>
              )}

              {status?.status === 'researching' && (
                <div className="mt-4 flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                  <span className="text-sm text-gray-600">10秒ごとに自動確認中...</span>
                </div>
              )}
            </div>

            {status?.status === 'completed' && (
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
                <p className="font-medium">✓ 分析が完了しました</p>
                <p className="text-sm mt-1">結果ページに移動します...</p>
              </div>
            )}

            <div className="flex justify-between pt-4">
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
      </div>
    </div>
  );
}
