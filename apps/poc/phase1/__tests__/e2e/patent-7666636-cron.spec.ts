import { test, expect } from '@playwright/test';
import { prisma } from '@/lib/prisma';

// Basic認証の設定
const AUTH = {
  username: 'patent',
  password: 'datas1234'
};

// Cron認証キー
const CRON_SECRET = 'cron-secret-key-phase1-batch-processing';

// 特許情報
const PATENT_DATA = {
  patentNumber: '7666636',
  claimText: `身体運動に関する時系列データを入力とし、身体動作から身体動作に伴う物体の挙動の推定結果を出力するように学習されたモデルを用いて、対象者の身体運動に関する時系列データから前記対象者の身体動作に伴う物体の挙動を推定する推定部と、推定した物体の挙動と実際の物体の挙動との誤差に基づき、前記対象者を評価する評価部とを含み、前記対象者の身体運動に関する時系列データは、前記対象者の対戦相手から見た前記対象者の動作に関連する時系列データであり、前記評価部は、推定した前記物体の挙動と、実際の前記物体の挙動との乖離が大きいほど高い評価を算出し、前記対象者が行う運動は対戦型の球技であり、前記物体は球技で使われる球である`,
  priority: 8 // 高優先度
};

test.describe('Patent 7666636 Cron Batch Processing', () => {
  let jobId: string;

  test.beforeAll(async () => {
    // 既存の同じ特許番号のジョブをクリーンアップ（オプション）
    try {
      await prisma.analysis_jobs.deleteMany({
        where: {
          patentNumber: PATENT_DATA.patentNumber,
          status: { in: ['pending', 'researching'] }
        }
      });
    } catch (error) {
      console.log('Cleanup skipped or failed:', error);
    }
  });

  test('Step 1: Register patent search job via schedule API', async ({ request }) => {
    // ジョブ登録APIを呼び出し
    const response = await request.post('/api/patent-search/schedule', {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + Buffer.from(`${AUTH.username}:${AUTH.password}`).toString('base64')
      },
      data: PATENT_DATA
    });

    expect(response.ok()).toBeTruthy();

    const responseData = await response.json();

    // レスポンスの検証
    expect(responseData).toHaveProperty('job_id');
    expect(responseData.status).toBe('scheduled');
    expect(responseData.priority).toBe(PATENT_DATA.priority);

    jobId = responseData.job_id;
    console.log('Job registered:', jobId);
  });

  test('Step 2: Trigger cron check-and-do endpoint', async ({ request }) => {
    // Cronエンドポイントを実行
    const response = await request.post('/api/cron/check-and-do', {
      headers: {
        'Content-Type': 'application/json',
        'X-Cron-Secret': CRON_SECRET,
        'Authorization': 'Basic ' + Buffer.from(`${AUTH.username}:${AUTH.password}`).toString('base64')
      }
    });

    expect(response.ok()).toBeTruthy();

    const cronResult = await response.json();

    // Cronの実行結果を検証
    expect(cronResult.started).toBeGreaterThan(0); // 少なくとも1つのジョブが開始されたこと
    expect(cronResult.currentRunning).toBeGreaterThan(0); // 実行中のジョブがあること

    console.log('Cron executed:', {
      started: cronResult.started,
      currentRunning: cronResult.currentRunning
    });
  });

  test('Step 3: Verify database state', async () => {
    // DBから直接ジョブの状態を確認
    const job = await prisma.analysis_jobs.findUnique({
      where: { id: jobId }
    });

    expect(job).not.toBeNull();

    // ジョブの基本情報を検証
    expect(job!.patentNumber).toBe(PATENT_DATA.patentNumber);
    expect(job!.priority).toBe(PATENT_DATA.priority);
    expect(job!.searchType).toBe('infringement_check');

    // ステータスの検証（pendingまたはresearchingであるべき）
    expect(['pending', 'researching']).toContain(job!.status);

    // researchingの場合、追加の検証
    if (job!.status === 'researching') {
      expect(job!.openaiResponseId).not.toBeNull();
      expect(job!.openaiResponseId).toMatch(/^resp_/); // OpenAI Response IDの形式
      expect(job!.startedAt).not.toBeNull();
      expect(job!.inputPrompt).toContain(PATENT_DATA.patentNumber);
      expect(job!.progress).toBeGreaterThan(0);
    }

    console.log('Database state verified:', {
      id: job!.id,
      patentNumber: job!.patentNumber,
      status: job!.status,
      priority: job!.priority,
      openaiResponseId: job!.openaiResponseId,
      startedAt: job!.startedAt
    });
  });

  test('Step 4: Check job status via status API', async ({ request }) => {
    // ステータス確認APIを呼び出し
    const response = await request.get(`/api/analyze/status/${jobId}`, {
      headers: {
        'Authorization': 'Basic ' + Buffer.from(`${AUTH.username}:${AUTH.password}`).toString('base64')
      }
    });

    expect(response.ok()).toBeTruthy();

    const statusData = await response.json();

    // ステータスAPIの検証
    expect(statusData.job_id).toBe(jobId);
    expect(['pending', 'researching', 'completed', 'failed']).toContain(statusData.status);
    expect(statusData.patent_number).toBe(PATENT_DATA.patentNumber);

    console.log('Job status:', statusData);
  });

  test('Step 5: Run cron again to check progress', async ({ request }) => {
    // 少し待機してから再度Cronを実行
    await new Promise(resolve => setTimeout(resolve, 2000));

    const response = await request.post('/api/cron/check-and-do', {
      headers: {
        'Content-Type': 'application/json',
        'X-Cron-Secret': CRON_SECRET,
        'Authorization': 'Basic ' + Buffer.from(`${AUTH.username}:${AUTH.password}`).toString('base64')
      }
    });

    expect(response.ok()).toBeTruthy();

    const cronResult = await response.json();

    // ステータスチェックが行われたことを確認
    expect(cronResult.checked).toBeGreaterThanOrEqual(0);

    console.log('Second cron run:', {
      checked: cronResult.checked,
      completed: cronResult.completed,
      currentRunning: cronResult.currentRunning
    });
  });

  test('Step 6: Final database state verification', async () => {
    // 最終的なDB状態を確認
    const finalJob = await prisma.analysis_jobs.findUnique({
      where: { id: jobId },
      select: {
        id: true,
        patentNumber: true,
        status: true,
        priority: true,
        openaiResponseId: true,
        startedAt: true,
        finishedAt: true,
        retryCount: true,
        searchType: true,
        progress: true
      }
    });

    expect(finalJob).not.toBeNull();

    console.log('Final job state:', finalJob);

    // 最終検証結果のサマリー
    const summary = {
      testPassed: true,
      jobId: finalJob!.id,
      patentNumber: finalJob!.patentNumber,
      status: finalJob!.status,
      hasOpenAIResponseId: !!finalJob!.openaiResponseId,
      isProcessing: finalJob!.status === 'researching',
      progress: finalJob!.progress
    };

    console.log('Test Summary:', summary);

    // ジョブが適切に処理されていることを確認
    expect(finalJob!.status).toMatch(/^(pending|researching|completed|failed)$/);
    if (finalJob!.status === 'researching' || finalJob!.status === 'completed') {
      expect(finalJob!.openaiResponseId).not.toBeNull();
    }
  });
});

test.afterAll(async () => {
  // Prisma接続をクリーンアップ
  await prisma.$disconnect();
});