#!/usr/bin/env node

/**
 * Supabase接続テストスクリプト
 *
 * 使い方:
 *   node scripts/test-supabase-connection.mjs
 */

import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// .env.local を読み込み
dotenv.config({ path: resolve(__dirname, '../.env.local') });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

console.log('🔍 Supabase接続テスト開始...\n');

if (!supabaseUrl || !supabaseAnonKey || !supabaseServiceKey) {
  console.error('❌ 環境変数が設定されていません:');
  console.error(`NEXT_PUBLIC_SUPABASE_URL: ${supabaseUrl ? '✅' : '❌'}`);
  console.error(`NEXT_PUBLIC_SUPABASE_ANON_KEY: ${supabaseAnonKey ? '✅' : '❌'}`);
  console.error(`SUPABASE_SERVICE_ROLE_KEY: ${supabaseServiceKey ? '✅' : '❌'}`);
  console.error('\n.env.localファイルを確認してください。');
  process.exit(1);
}

console.log(`📍 Supabase URL: ${supabaseUrl}`);
console.log(`🔑 Anon Key: ${supabaseAnonKey.substring(0, 20)}...`);
console.log(`🔐 Service Role Key: ${supabaseServiceKey.substring(0, 20)}...\n`);

// Service roleでクライアント作成（全権限）
const supabase = createClient(supabaseUrl, supabaseServiceKey);

async function testConnection() {
  try {
    // 1. analysis_jobs_localテーブルの存在確認
    console.log('1️⃣ テーブル存在確認...');
    const { data: tables, error: tablesError } = await supabase
      .from('analysis_jobs_local')
      .select('*')
      .limit(0);

    if (tablesError) {
      console.error('❌ テーブルが見つかりません:', tablesError.message);
      console.error('\nSupabase DashboardのSQL Editorで以下のSQLを実行してください:');
      console.error('supabase/migrations/00001_create_analysis_jobs_cloud.sql');
      return false;
    }

    console.log('✅ analysis_jobs_localテーブルが存在します\n');

    // 2. テストデータ挿入
    console.log('2️⃣ テストデータ挿入...');
    const testJob = {
      status: 'pending',
      patent_number: 'JP-TEST-001',
      claim_text: 'テスト請求項の内容',
      company_name: 'テスト企業株式会社',
      product_name: 'テスト製品',
      progress: 0,
    };

    const { data: inserted, error: insertError } = await supabase
      .from('analysis_jobs_local')
      .insert(testJob)
      .select()
      .single();

    if (insertError) {
      console.error('❌ データ挿入エラー:', insertError.message);
      return false;
    }

    console.log('✅ テストデータを挿入しました');
    console.log(`   Job ID: ${inserted.id}`);
    console.log(`   特許番号: ${inserted.patent_number}\n`);

    // 3. データ取得
    console.log('3️⃣ データ取得テスト...');
    const { data: fetched, error: fetchError } = await supabase
      .from('analysis_jobs_local')
      .select('*')
      .eq('id', inserted.id)
      .single();

    if (fetchError) {
      console.error('❌ データ取得エラー:', fetchError.message);
      return false;
    }

    console.log('✅ データを正常に取得しました');
    console.log(`   特許番号: ${fetched.patent_number}`);
    console.log(`   企業名: ${fetched.company_name}\n`);

    // 4. データ更新
    console.log('4️⃣ データ更新テスト...');
    const { error: updateError } = await supabase
      .from('analysis_jobs_local')
      .update({ status: 'completed', progress: 100 })
      .eq('id', inserted.id);

    if (updateError) {
      console.error('❌ データ更新エラー:', updateError.message);
      return false;
    }

    console.log('✅ データを正常に更新しました\n');

    // 5. 更新確認
    console.log('5️⃣ 更新確認...');
    const { data: updated } = await supabase
      .from('analysis_jobs_local')
      .select('status, progress, updated_at')
      .eq('id', inserted.id)
      .single();

    console.log(`✅ ステータス: ${updated.status}`);
    console.log(`   進捗: ${updated.progress}%`);
    console.log(`   更新日時: ${updated.updated_at}\n`);

    // 6. テストデータ削除
    console.log('6️⃣ テストデータ削除...');
    const { error: deleteError } = await supabase
      .from('analysis_jobs_local')
      .delete()
      .eq('id', inserted.id);

    if (deleteError) {
      console.error('❌ データ削除エラー:', deleteError.message);
      return false;
    }

    console.log('✅ テストデータを削除しました\n');

    // 7. 全件数確認
    console.log('7️⃣ 現在のレコード数確認...');
    const { count, error: countError } = await supabase
      .from('analysis_jobs_local')
      .select('*', { count: 'exact', head: true });

    if (countError) {
      console.error('❌ カウントエラー:', countError.message);
      return false;
    }

    console.log(`✅ 現在のレコード数: ${count}件\n`);

    return true;
  } catch (error) {
    console.error('❌ 予期しないエラー:', error);
    return false;
  }
}

// テスト実行
testConnection()
  .then((success) => {
    if (success) {
      console.log('🎉 全てのテストが成功しました！');
      console.log('\nSupabase接続が正常に動作しています。');
      console.log('Next.jsアプリから同じ環境変数でSupabaseを使用できます。\n');
      process.exit(0);
    } else {
      console.log('\n❌ 一部のテストが失敗しました。');
      console.log('上記のエラーメッセージを確認してください。\n');
      process.exit(1);
    }
  })
  .catch((error) => {
    console.error('\n💥 テスト実行中にエラーが発生しました:', error);
    process.exit(1);
  });
