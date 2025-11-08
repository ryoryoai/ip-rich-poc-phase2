import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const url = request.nextUrl;

  // Webhook受信エンドポイントは認証をバイパス
  if (
    url.pathname === '/api/webhook/research' ||
    url.pathname === '/api/webhook/openai'
  ) {
    return NextResponse.next();
  }

  // Basic認証をスキップする環境（開発環境など）
  if (process.env.SKIP_AUTH === 'true') {
    return NextResponse.next();
  }

  // Basic認証の設定
  const basicAuth = request.headers.get('authorization');

  // 環境変数から認証情報を取得
  const username = process.env.BASIC_AUTH_USERNAME || 'admin';
  const password = process.env.BASIC_AUTH_PASSWORD || 'password';

  if (basicAuth) {
    const authValue = basicAuth.split(' ')[1];
    const [user, pwd] = atob(authValue).split(':');

    if (user === username && pwd === password) {
      return NextResponse.next();
    }
  }

  url.pathname = '/api/auth';

  return NextResponse.rewrite(url);
}

// ミドルウェアを適用するパスの設定
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api/auth (認証エンドポイント自体)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api/auth|_next/static|_next/image|favicon.ico).*)',
  ],
};