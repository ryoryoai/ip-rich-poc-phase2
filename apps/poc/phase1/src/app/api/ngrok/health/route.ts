import { NextResponse } from 'next/server';

/**
 * ngrok疎通確認用のヘルスチェックエンドポイント
 *
 * スマホなどの外部デバイスからngrok経由でアクセス可能か確認するためのエンドポイント。
 *
 * レスポンス例:
 * {
 *   "status": "ok",
 *   "service": "Next.js (Phase1 Patent Analysis)",
 *   "timestamp": "2025-11-08T12:34:56.789Z",
 *   "ngrok": {
 *     "ready": true,
 *     "message": "ngrok tunnel is working correctly"
 *   }
 * }
 */
export async function GET() {
  return NextResponse.json({
    status: 'ok',
    service: 'Next.js (Phase1 Patent Analysis)',
    timestamp: new Date().toISOString(),
    ngrok: {
      ready: true,
      message: 'ngrok tunnel is working correctly',
    },
    endpoints: {
      webhook: '/api/webhook/research',
      analyze_start: '/api/analyze/start',
      health: '/api/ngrok/health',
    },
  });
}
