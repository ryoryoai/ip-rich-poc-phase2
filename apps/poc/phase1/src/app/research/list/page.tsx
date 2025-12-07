'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { useEffect, useState } from 'react';

interface Job {
  job_id: string;
  status: string;
  progress: number;
  patent_number: string;
  claim_text: string;
  company_name: string;
  product_name: string;
  priority: number;
  created_at: string;
  updated_at: string;
  started_at?: string;
  finished_at?: string;
  error_message?: string;
}

interface ListResponse {
  jobs: Job[];
  total: number;
  limit: number;
  offset: number;
}

const statusLabels: Record<string, string> = {
  pending: '待機中',
  researching: '処理中',
  analyzing: '分析中',
  completed: '完了',
  failed: '失敗',
};

const statusColors: Record<string, string> = {
  pending: 'bg-gray-200 text-gray-800',
  researching: 'bg-blue-200 text-blue-800',
  analyzing: 'bg-yellow-200 text-yellow-800',
  completed: 'bg-green-200 text-green-800',
  failed: 'bg-red-200 text-red-800',
};

export default function ListPage() {
  const [selectedStatus, setSelectedStatus] = useState<string>('');

  const { data, refetch } = useQuery<ListResponse>({
    queryKey: ['jobs', selectedStatus],
    queryFn: async () => {
      const url = selectedStatus
        ? `/api/analyze/list?status=${selectedStatus}&limit=50`
        : '/api/analyze/list?limit=50';
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch jobs');
      return res.json();
    },
    refetchInterval: 60000, // 1分ごとにポーリング
  });

  // cron APIの更新を検出するためのポーリング
  useEffect(() => {
    const interval = setInterval(() => {
      refetch();
    }, 60000);

    return () => clearInterval(interval);
  }, [refetch]);

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

  const truncateText = (text: string, maxLength: number = 200) => {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-3xl font-bold text-gray-900">侵害調査一覧</h2>
          <div className="flex items-center gap-4">
            <div>
              <label htmlFor="status" className="mr-2 text-sm text-gray-700">
                ステータス:
              </label>
              <select
                id="status"
                className="px-3 py-2 border border-gray-300 rounded-md"
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
              >
                <option value="">すべて</option>
                <option value="pending">待機中</option>
                <option value="researching">処理中</option>
                <option value="analyzing">分析中</option>
                <option value="completed">完了</option>
                <option value="failed">失敗</option>
              </select>
            </div>
            <a
              href="/research"
              className="px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700"
            >
              新しい調査を開始
            </a>
          </div>
        </div>

        <p className="mb-6 text-sm text-gray-500">
          全 {data?.total || 0} 件の調査
        </p>

        {!data ? (
          <div className="text-center py-8 text-gray-500">読み込み中...</div>
        ) : data.jobs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            調査がありません
            <a
              href="/research"
              className="mt-4 block text-blue-600 hover:text-blue-800"
            >
              最初の調査を開始する →
            </a>
          </div>
        ) : (
          <div className="space-y-4">
            {data.jobs.map((job) => (
              <Link
                key={job.job_id}
                href={
                  job.status === 'completed'
                    ? `/research/result/${job.job_id}`
                    : `/research/status/${job.job_id}`
                }
                className="block bg-white p-4 rounded-lg shadow hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          statusColors[job.status] || statusColors.pending
                        }`}
                      >
                        {statusLabels[job.status] || job.status}
                      </span>
                      <span className="text-xs text-gray-500">
                        優先度: {job.priority || 5}
                      </span>
                      <span className="text-xs text-gray-700 font-medium">
                        特許番号: {job.patent_number}
                      </span>
                    </div>

                    {/* 請求項1の表示 */}
                    <p className="text-gray-900 text-sm mb-2 line-clamp-2">
                      {truncateText(job.claim_text)}
                    </p>

                    {/* 企業・製品情報 */}
                    {(job.company_name || job.product_name) && (
                      <p className="text-sm text-gray-600 mb-2">
                        {job.company_name && <span>{job.company_name}</span>}
                        {job.company_name && job.product_name && ' - '}
                        {job.product_name && <span>{job.product_name}</span>}
                      </p>
                    )}

                    <div className="mt-2 text-xs text-gray-500">
                      作成: {formatDate(job.created_at)}
                      {job.started_at && (
                        <>
                          {' '}
                          | 開始: {formatDate(job.started_at)}
                        </>
                      )}
                      {job.finished_at && (
                        <>
                          {' '}
                          | 完了: {formatDate(job.finished_at)}
                        </>
                      )}
                    </div>

                    {/* エラーメッセージ */}
                    {job.error_message && (
                      <div className="mt-2 text-xs text-red-600">
                        エラー: {job.error_message}
                      </div>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}