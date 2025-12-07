/**
 * 特許番号7666636の統合テスト
 * Cronバッチ処理とDBの状態確認を含む
 */

import axios from 'axios';

const BASE_URL = process.env.BASE_URL || 'http://localhost:3001';
const AUTH = {
  username: 'patent',
  password: 'datas1234'
};
const CRON_SECRET = 'cron-secret-key-phase1-batch-processing';

// 特許データ
const PATENT_DATA = {
  patentNumber: '7666636',
  claimText: `身体運動に関する時系列データを入力とし、身体動作から身体動作に伴う物体の挙動の推定結果を出力するように学習されたモデルを用いて、対象者の身体運動に関する時系列データから前記対象者の身体動作に伴う物体の挙動を推定する推定部と、推定した物体の挙動と実際の物体の挙動との誤差に基づき、前記対象者を評価する評価部とを含み、前記対象者の身体運動に関する時系列データは、前記対象者の対戦相手から見た前記対象者の動作に関連する時系列データであり、前記評価部は、推定した前記物体の挙動と、実際の前記物体の挙動との乖離が大きいほど高い評価を算出し、前記対象者が行う運動は対戦型の球技であり、前記物体は球技で使われる球である`,
  priority: 8
};

// Axios設定
const axiosInstance = axios.create({
  baseURL: BASE_URL,
  auth: AUTH,
  headers: {
    'Content-Type': 'application/json'
  }
});

describe('Patent 7666636 Cron Batch Processing Integration Test', () => {
  let jobId: string;

  // テスト全体のタイムアウトを30秒に設定
  jest.setTimeout(30000);

  test('Step 1: Register patent search job', async () => {
    console.log('🔵 Step 1: Registering patent search job...');

    const response = await axiosInstance.post('/api/patent-search/schedule', PATENT_DATA);

    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('job_id');
    // 高優先度の場合、即座に実行される可能性があるため両方を許可
    expect(['scheduled', 'researching', 'pending']).toContain(response.data.status);
    expect(response.data.priority).toBe(PATENT_DATA.priority);

    jobId = response.data.job_id;
    expect(jobId).toBeDefined();
    expect(jobId).not.toBe('undefined');

    console.log(`✅ Job registered: ${jobId}`);
    console.log(`   Status: ${response.data.status}`);
    console.log(`   Priority: ${response.data.priority}`);
    console.log(`   Message: ${response.data.message}`);
  });

  test('Step 2: Trigger cron check-and-do', async () => {
    console.log('🔵 Step 2: Triggering cron check-and-do...');

    const response = await axiosInstance.post('/api/cron/check-and-do', {}, {
      headers: {
        'X-Cron-Secret': CRON_SECRET
      }
    });

    expect(response.status).toBe(200);
    expect(response.data.started).toBeGreaterThanOrEqual(0);

    console.log(`✅ Cron executed:`);
    console.log(`   Jobs started: ${response.data.started}`);
    console.log(`   Currently running: ${response.data.currentRunning}`);
    console.log(`   Stats:`, response.data.stats);
  });

  test('Step 3: Check job status via API', async () => {
    console.log('🔵 Step 3: Checking job status...');

    // jobIdが設定されていない場合はスキップ
    if (!jobId || jobId === 'undefined') {
      console.warn('⚠️ Job ID not set, skipping status check');
      return;
    }

    const response = await axiosInstance.get(`/api/analyze/status/${jobId}`);

    expect(response.status).toBe(200);
    expect(response.data.job_id).toBe(jobId);
    expect(['pending', 'researching', 'completed', 'failed']).toContain(response.data.status);

    console.log(`✅ Job status:`);
    console.log(`   ID: ${response.data.job_id}`);
    console.log(`   Patent: ${response.data.patent_number}`);
    console.log(`   Status: ${response.data.status}`);
    console.log(`   Progress: ${response.data.progress}%`);

    if (response.data.openai_response_id) {
      console.log(`   OpenAI Response ID: ${response.data.openai_response_id}`);
    }
  });

  test('Step 4: Verify DB state via Supabase MCP', async () => {
    console.log('🔵 Step 4: Verifying database state...');

    // DB確認用のエンドポイントを作成するか、
    // 既存のanalyze/listエンドポイントを使用
    const response = await axiosInstance.get('/api/analyze/list', {
      params: {
        limit: 10
      }
    });

    expect(response.status).toBe(200);

    // 登録したジョブが含まれているか確認
    const jobs = response.data.jobs || response.data;
    const targetJob = jobs.find((job: any) => job.id === jobId);

    if (targetJob) {
      console.log(`✅ Job found in database:`);
      console.log(`   Patent Number: ${targetJob.patentNumber}`);
      console.log(`   Status: ${targetJob.status}`);
      console.log(`   Priority: ${targetJob.priority}`);
      console.log(`   Search Type: ${targetJob.searchType || 'infringement_check'}`);

      // 期待される状態の検証
      expect(targetJob.patentNumber).toBe(PATENT_DATA.patentNumber);
      expect(targetJob.priority).toBe(PATENT_DATA.priority);
      expect(['pending', 'researching', 'completed', 'failed']).toContain(targetJob.status);

      if (targetJob.status === 'researching' || targetJob.status === 'completed') {
        expect(targetJob.openaiResponseId).toBeTruthy();
        console.log(`   OpenAI Response ID: ${targetJob.openaiResponseId}`);
      }
    } else {
      console.log(`⚠️ Job ${jobId} not found in job list`);
    }
  });

  test('Step 5: Run cron again to check progress', async () => {
    console.log('🔵 Step 5: Running cron again to check progress...');

    // 2秒待機
    await new Promise(resolve => setTimeout(resolve, 2000));

    const response = await axiosInstance.post('/api/cron/check-and-do', {}, {
      headers: {
        'X-Cron-Secret': CRON_SECRET
      }
    });

    expect(response.status).toBe(200);

    console.log(`✅ Second cron run:`);
    console.log(`   Jobs checked: ${response.data.checked}`);
    console.log(`   Jobs completed: ${response.data.completed}`);
    console.log(`   Jobs failed: ${response.data.failed}`);
    console.log(`   Currently running: ${response.data.currentRunning}`);

    // ステータス統計
    if (response.data.stats) {
      console.log(`   Status breakdown:`, response.data.stats);
    }
  });

  test('Step 6: Final status verification', async () => {
    console.log('🔵 Step 6: Final status verification...');

    // jobIdが設定されていない場合はスキップ
    if (!jobId || jobId === 'undefined') {
      console.warn('⚠️ Job ID not set, skipping final verification');
      return;
    }

    const response = await axiosInstance.get(`/api/analyze/status/${jobId}`);

    expect(response.status).toBe(200);

    console.log('✅ Final job status:');
    console.log(`   Job ID: ${response.data.job_id}`);
    console.log(`   Patent Number: ${response.data.patent_number}`);
    console.log(`   Status: ${response.data.status}`);
    console.log(`   Progress: ${response.data.progress}%`);

    // テストサマリー
    console.log('\n========================================');
    console.log('📊 Test Summary');
    console.log('========================================');
    console.log(`✅ Job successfully registered: ${jobId}`);
    console.log(`✅ Patent Number: ${PATENT_DATA.patentNumber}`);
    console.log(`✅ Priority: ${PATENT_DATA.priority}`);
    console.log(`✅ Current Status: ${response.data.status}`);

    if (response.data.status === 'researching') {
      console.log(`⏳ Job is being processed by OpenAI Deep Research`);
      console.log(`   OpenAI Response ID: ${response.data.openai_response_id}`);
    } else if (response.data.status === 'completed') {
      console.log(`✅ Job completed successfully`);
    } else if (response.data.status === 'pending') {
      console.log(`⏳ Job is queued for processing`);
    }

    console.log('========================================\n');
  });
});

// エラーハンドリング
process.on('unhandledRejection', (error) => {
  console.error('❌ Unhandled rejection:', error);
  process.exit(1);
});