/**
 * 環境変数の検証
 * 本番環境で必須の環境変数が欠けている場合にエラーを投げる
 */

const requiredEnvVars = {
  production: [
    'DATABASE_URL',
    'DIRECT_URL',
    'OPENAI_API_KEY',
    'OPENAI_WEBHOOK_SECRET',
  ],
  development: [
    'DATABASE_URL',
  ],
} as const;

export function validateEnv() {
  const env = process.env.NODE_ENV || 'development';
  const required = requiredEnvVars[env as keyof typeof requiredEnvVars] || [];

  const missing = required.filter((key) => !process.env[key]);

  if (missing.length > 0) {
    throw new Error(
      `Missing required environment variables in ${env}: ${missing.join(', ')}`
    );
  }
}

// 起動時に検証
if (typeof window === 'undefined') {
  // サーバーサイドのみで実行
  validateEnv();
}
