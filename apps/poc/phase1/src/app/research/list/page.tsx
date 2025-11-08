'use client';

import { useEffect, useState } from 'react';

interface Job {
  job_id: string;
  status: string;
  progress: number;
  patent_number: string;
  company_name: string;
  product_name: string;
  created_at: string;
  updated_at: string;
  error_message?: string;
}

interface ListResponse {
  jobs: Job[];
  total: number;
  limit: number;
  offset: number;
}

export default function ListPage() {
  const [data, setData] = useState<ListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const res = await fetch('/api/analyze/list?limit=50');
        const jsonData = await res.json();

        if (!res.ok) {
          throw new Error(jsonData.error || 'Failed to fetch jobs');
        }

        setData(jsonData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchJobs();
  }, []);

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<
      string,
      { label: string; className: string }
    > = {
      pending: { label: '待機中', className: 'bg-gray-100 text-gray-800' },
      researching: { label: '検索中', className: 'bg-blue-100 text-blue-800' },
      analyzing: { label: '分析中', className: 'bg-yellow-100 text-yellow-800' },
      completed: { label: '完了', className: 'bg-green-100 text-green-800' },
      failed: { label: '失敗', className: 'bg-red-100 text-red-800' },
    };

    const config = statusConfig[status] || statusConfig.pending;

    return (
      <span
        className={`px-2 py-1 text-xs font-medium rounded-full ${config.className}`}
      >
        {config.label}
      </span>
    );
  };

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

  const handleRowClick = (job: Job) => {
    if (job.status === 'completed') {
      window.location.href = `/research/result/${job.job_id}`;
    } else if (job.status === 'failed') {
      // 失敗したジョブはクリックしても何もしない
    } else {
      // 処理中のジョブはステータスページへ
      window.location.href = `/research/status/${job.job_id}`;
    }
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
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-5 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  分析履歴一覧
                </h1>
                <p className="mt-1 text-sm text-gray-500">
                  全 {data?.total || 0} 件の分析履歴
                </p>
              </div>
              <a
                href="/research"
                className="px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700"
              >
                新しい分析を開始
              </a>
            </div>
          </div>

          {data && data.jobs.length === 0 ? (
            <div className="px-6 py-12 text-center text-gray-500">
              <p>まだ分析履歴がありません</p>
              <a
                href="/research"
                className="mt-4 inline-block text-blue-600 hover:text-blue-800"
              >
                最初の分析を開始する →
              </a>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      特許番号
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      企業 / 製品
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      ステータス
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      作成日時
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      最終更新日時
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data?.jobs.map((job) => (
                    <tr
                      key={job.job_id}
                      onClick={() => handleRowClick(job)}
                      className="hover:bg-gray-50 cursor-pointer"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {job.patent_number}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">
                          {job.company_name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {job.product_name}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(job.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(job.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(job.updated_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
