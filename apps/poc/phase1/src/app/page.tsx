import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold mb-8 text-center">
          特許侵害調査システム - Phase 1 PoC
        </h1>
        <p className="text-center mb-8">
          特許の構成要件抽出と侵害可能性を自動判定するシステムです
        </p>
        

        {/* タイムライン（ガントチャート） */}
        <div className="mt-8 mb-12">
          <h2 className="text-xl font-bold mb-6 text-center">📅 開発タイムライン</h2>
          <div className="bg-white border rounded-lg p-6 overflow-x-auto">
            {/* 月ヘッダー */}
            <div className="flex mb-1">
              <div className="w-28 shrink-0"></div>
              <div className="flex-1 grid grid-cols-12 text-xs text-center text-gray-500 border-b pb-1">
                <div className="col-span-2 border-r border-gray-200">10月</div>
                <div className="col-span-2 border-r border-gray-200">11月</div>
                <div className="col-span-2 border-r border-gray-200">12月</div>
                <div className="col-span-2 border-r border-gray-200">1月</div>
                <div className="col-span-2 border-r border-gray-200">2月</div>
                <div className="col-span-2">3月〜</div>
              </div>
            </div>
            <div className="flex mb-3">
              <div className="w-28 shrink-0"></div>
              <div className="flex-1 grid grid-cols-12 text-[10px] text-center text-gray-400">
                <div>前</div>
                <div>後</div>
                <div>前</div>
                <div>後</div>
                <div>前</div>
                <div>後</div>
                <div>前</div>
                <div>後</div>
                <div>前</div>
                <div>後</div>
                <div>前</div>
                <div>後</div>
              </div>
            </div>

            {/* Phase 1: 10月後半〜11月末 */}
            <div className="flex items-center mb-3">
              <div className="w-28 shrink-0 text-sm font-medium text-green-700">Phase 1</div>
              <div className="flex-1 grid grid-cols-12 h-8">
                <div></div>
                <div className="col-span-3 bg-green-500 rounded-l-full rounded-r-full flex items-center justify-center text-white text-xs font-medium">
                  完了
                </div>
              </div>
            </div>

            {/* Phase 2: 12月 */}
            <div className="flex items-center mb-3">
              <div className="w-28 shrink-0 text-sm font-medium text-blue-700">Phase 2</div>
              <div className="flex-1 grid grid-cols-12 h-8">
                <div className="col-span-4"></div>
                <div className="col-span-2 bg-blue-500 rounded-l-full rounded-r-full flex items-center justify-center text-white text-xs font-medium animate-pulse">
                  進行中
                </div>
              </div>
            </div>

            {/* Phase 3: 1月〜3月中旬（2.5ヶ月） */}
            <div className="flex items-center mb-3">
              <div className="w-28 shrink-0 text-sm font-medium text-purple-700">Phase 3</div>
              <div className="flex-1 grid grid-cols-12 h-8">
                <div className="col-span-6"></div>
                <div className="col-span-5 bg-purple-200 border-2 border-dashed border-purple-400 rounded-l-full rounded-r-full flex items-center justify-center text-purple-600 text-xs">
                  予定
                </div>
              </div>
            </div>

            {/* Phase 4: 3月後半〜 */}
            <div className="flex items-center">
              <div className="w-28 shrink-0 text-sm font-medium text-gray-500">Phase 4</div>
              <div className="flex-1 grid grid-cols-12 h-8">
                <div className="col-span-11"></div>
                <div className="bg-gray-200 border-2 border-dashed border-gray-400 rounded-l-full rounded-r-full flex items-center justify-center text-gray-500 text-xs">

                </div>
              </div>
            </div>

            {/* 現在位置マーカー */}
            <div className="flex mt-4 pt-2 border-t">
              <div className="w-28 shrink-0"></div>
              <div className="flex-1 grid grid-cols-12">
                <div className="col-span-4"></div>
                <div className="flex justify-center">
                  <div className="text-red-500 text-xs font-bold">▼今</div>
                </div>
              </div>
            </div>

            {/* 体制情報 */}
            <div className="flex mt-4 pt-3 border-t">
              <div className="w-28 shrink-0 text-xs font-medium text-gray-600">体制</div>
              <div className="flex-1 grid grid-cols-12 text-[10px] text-gray-600">
                <div className="col-span-4 flex items-center justify-center bg-green-50 rounded py-1">
                  <span>エンジニア 0.1</span>
                </div>
                <div className="col-span-2 flex items-center justify-center bg-blue-50 rounded py-1 text-center leading-tight">
                  <span>Eng 0.1<br/>+ 特許 0.2</span>
                </div>
                <div className="col-span-6 flex items-center justify-center bg-orange-50 rounded py-1 text-orange-700">
                  <span>⚠️ 体制構築が必要</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 業務フロー図 */}
        <div className="mb-12">
          <h2 className="text-xl font-bold mb-4 text-center">🔄 業務フローと自動化対象</h2>
          <div className="bg-white border rounded-lg p-4 overflow-x-auto">
            <img
              src="/current-workflow.svg"
              alt="業務フロー図"
              className="max-w-full h-auto mx-auto"
              style={{ maxHeight: '500px' }}
            />
          </div>

          {/* 自動化対象の説明 */}
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <h3 className="font-bold text-green-800 text-sm mb-2">自動化対象① 特許一覧作成</h3>
              <p className="text-xs text-gray-600">J-PlatPat連携による特許情報の自動取得</p>
              <p className="text-xs text-purple-600 font-medium mt-1">→ Phase 3 で対応予定</p>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <h3 className="font-bold text-blue-800 text-sm mb-2">自動化対象② 侵害調査</h3>
              <p className="text-xs text-gray-600">OpenAI Deep Researchによる侵害可能性分析</p>
              <p className="text-xs text-blue-600 font-medium mt-1">→ 現在対応中（Phase 1-2）</p>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
              <h3 className="font-bold text-purple-800 text-sm mb-2">自動化対象③ 売上推定</h3>
              <p className="text-xs text-gray-600">被疑侵害製品の売上・収益性分析</p>
              <p className="text-xs text-purple-600 font-medium mt-1">→ Phase 3 で対応予定</p>
            </div>
          </div>

          {/* 人で対応する業務 */}
          <div className="mt-4 bg-gray-50 border border-gray-200 rounded-lg p-3">
            <h3 className="font-bold text-gray-700 text-sm mb-2">👤 人で対応する業務</h3>
            <div className="flex flex-wrap gap-4 text-xs text-gray-600">
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full"></span>
                <span>無効調査（特許の有効性確認）</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full"></span>
                <span>訴訟手続き（法的対応）</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full"></span>
                <span>総合判断（訴訟可否の最終決定）</span>
              </div>
            </div>
          </div>
        </div>

        {/* 機能要件表 */}
        <div className="mb-12">
          <h2 className="text-xl font-bold mb-4 text-center">📋 Phase別 機能要件</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border px-3 py-2 text-left w-40">機能</th>
                  <th className="border px-3 py-2 text-center bg-green-50 text-green-800">Phase 1<br/><span className="text-xs font-normal">PoC完成</span></th>
                  <th className="border px-3 py-2 text-center bg-blue-50 text-blue-800">Phase 2<br/><span className="text-xs font-normal">妥当性検証</span></th>
                  <th className="border px-3 py-2 text-center bg-purple-50 text-purple-800">Phase 3<br/><span className="text-xs font-normal">業務効率化</span></th>
                  <th className="border px-3 py-2 text-center bg-gray-100 text-gray-700">Phase 4<br/><span className="text-xs font-normal">外部公開</span></th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="border px-3 py-2 font-medium">侵害調査（Deep Research）</td>
                  <td className="border px-3 py-2 text-center text-green-600">✅</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                </tr>
                <tr className="bg-gray-50">
                  <td className="border px-3 py-2 font-medium">夜間バッチ実行</td>
                  <td className="border px-3 py-2 text-center text-green-600">✅</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                </tr>
                <tr>
                  <td className="border px-3 py-2 font-medium">侵害調査履歴の閲覧</td>
                  <td className="border px-3 py-2 text-center text-green-600">✅</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                </tr>
                <tr className="bg-gray-50">
                  <td className="border px-3 py-2 font-medium">J-PlatPat連携</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-purple-600">✅</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                </tr>
                <tr>
                  <td className="border px-3 py-2 font-medium">侵害調査結果の管理・検索</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-purple-600">✅</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                </tr>
                <tr className="bg-gray-50">
                  <td className="border px-3 py-2 font-medium">侵害額推定</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-purple-600">✅</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                </tr>
                <tr>
                  <td className="border px-3 py-2 font-medium">CSV出力</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-purple-600">✅</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                </tr>
                <tr className="bg-gray-50">
                  <td className="border px-3 py-2 font-medium">ログイン機能</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-gray-600">✅</td>
                </tr>
                <tr>
                  <td className="border px-3 py-2 font-medium">ユーザー・グループ管理</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-gray-600">✅</td>
                </tr>
                <tr className="bg-gray-50">
                  <td className="border px-3 py-2 font-medium">利用料管理・課金</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-gray-400">−</td>
                  <td className="border px-3 py-2 text-center text-gray-600">✅</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            ※ Phase 3では侵害結果を検索し、気になるもののみ侵害額推定を実行するフローを想定
          </p>
        </div>

        {/* Phase詳細 */}
        <div className="space-y-8">
          <div className="bg-green-50 border-2 border-green-300 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4 text-green-900">✅ Phase 1 完了: PoC完成</h2>
            <div className="space-y-4">
              <div className="bg-green-100 p-3 rounded-lg mb-4">
                <p className="text-sm font-semibold text-green-900">
                  🎯 達成: 特許侵害調査の自動化基盤を構築し、動作確認完了
                </p>
              </div>

              <div>
                <h3 className="font-semibold mb-2">💼 ビジネス的にできること</h3>
                <div className="bg-white p-3 rounded-lg border border-green-200">
                  <ul className="list-disc list-inside space-y-2 text-sm">
                    <li><strong>特許番号と請求項1を入力するだけで侵害製品調査を開始できる</strong></li>
                    <li><strong>バッチ処理により夜間や休日も自動で調査を実行可能</strong></li>
                    <li><strong>調査結果をデータベースに保存し、いつでも参照可能</strong></li>
                    <li><strong>過去の調査履歴を一覧で確認・再利用できる</strong></li>
                  </ul>
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-2 text-gray-600">🔧 技術的な実装内容</h3>
                <ul className="list-disc list-inside space-y-1 text-xs text-gray-600">
                  <li>OpenAI O4 Mini Deep Research APIによる特許情報の自動取得</li>
                  <li>非同期処理による長時間分析のサポート（最大15分）</li>
                  <li>Supabase + Prismaによるジョブ管理とデータ永続化</li>
                  <li>Webhook + Cronポーリングによる確実な結果取得</li>
                  <li>Vercelへのデプロイ完了</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 border-2 border-blue-300 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4 text-blue-900">🚧 Phase 2 進行中: 業務利用可能性検証</h2>
            <div className="space-y-4">
              <div className="bg-blue-100 p-3 rounded-lg mb-4">
                <p className="text-sm font-semibold text-blue-900">
                  🎯 目標: iprich内で業務利用可能性を検証できる状態にする
                </p>
              </div>

              <div>
                <h3 className="font-semibold mb-2">💼 達成するとできること</h3>
                <div className="bg-white p-3 rounded-lg border border-blue-200">
                  <ul className="list-disc list-inside space-y-2 text-sm">
                    <li><strong>複数の特許を一括登録し、自動的に順次調査を実行</strong></li>
                    <li><strong>発見した侵害製品の売上規模を自動推定</strong></li>
                    <li><strong>損害賠償額の概算を自動計算</strong></li>
                </ul>
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-2">📊 実装状況</h3>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-center gap-2">
                    <span className="text-green-600">✅</span>
                    <span>バッチ処理基盤（Cron + 優先度キュー）</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-600">✅</span>
                    <span>DBスキーマに売上推定・バッチID等のフィールド追加済み</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-yellow-600">🔄</span>
                    <span>売上推定プロンプトの実装・検証</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-gray-400">⬚</span>
                    <span>一括登録UI</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-gray-400">⬚</span>
                    <span>エラー通知・自動リトライの強化</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div className="bg-purple-50 border-2 border-purple-300 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4 text-purple-900">📋 Phase 3: 業務運用の効率化</h2>
            <div className="space-y-4">
              <div className="bg-purple-100 p-3 rounded-lg mb-4">
                <p className="text-sm font-semibold text-purple-900">
                  🎯 目標: iprich社内で日常業務として利用可能な状態にする
                </p>
              </div>

              <div>
                <h3 className="font-semibold mb-2">💼 達成するとできること</h3>
                <div className="bg-white p-3 rounded-lg border border-purple-200">
                  <ul className="list-disc list-inside space-y-2 text-sm">
                    <li><strong>J-PlatPatから特許情報を自動取得（手入力不要）</strong></li>
                    <li><strong>侵害調査結果を管理し、条件検索で絞り込み</strong></li>
                    <li><strong>気になる結果のみ侵害額推定を実行</strong></li>
                    <li><strong>調査結果をCSVでエクスポート</strong></li>
                  </ul>
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-2 text-gray-600">🔧 主な実装項目</h3>
                <ul className="list-disc list-inside space-y-1 text-xs text-gray-600">
                  <li>J-PlatPat API連携（特許情報の自動取得）</li>
                  <li>侵害調査結果の構造化・保存</li>
                  <li>検索・フィルタリングUI</li>
                  <li>侵害額推定機能</li>
                  <li>CSV出力機能</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold mb-2 text-orange-600">⚠️ 体制構築が必要</h3>
                <p className="text-xs text-gray-600">
                  Phase 3以降は機能開発のボリュームが増加するため、エンジニアリソースの増強を検討
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4 text-gray-700">🌐 Phase 4: 外部公開（商用利用）</h2>
            <div className="space-y-4">
              <div className="bg-gray-100 p-3 rounded-lg mb-4">
                <p className="text-sm font-semibold text-gray-700">
                  🎯 目標: 外部顧客へのサービス提供と収益化
                </p>
              </div>

              <div>
                <h3 className="font-semibold mb-2">💼 達成するとできること</h3>
                <div className="bg-white p-3 rounded-lg border border-gray-200">
                  <ul className="list-disc list-inside space-y-2 text-sm">
                    <li><strong>外部の企業・特許事務所にサービスとして提供</strong></li>
                    <li><strong>ユーザーごとにログインし、自社データのみ閲覧</strong></li>
                    <li><strong>ユーザーグループ（企業）単位で利用料を管理・請求</strong></li>
                  </ul>
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-2 text-gray-600">🔧 主な実装項目</h3>
                <ul className="list-disc list-inside space-y-1 text-xs text-gray-600">
                  <li>ログイン・認証機能（OAuth/メール認証等）</li>
                  <li>ユーザー・ユーザーグループ管理</li>
                  <li>利用料管理・課金システム（Stripe等）</li>
                  <li>マルチテナント対応（データ分離）</li>
                  <li>API公開とドキュメント整備</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold mb-2 text-orange-600">⚠️ 体制構築が必要</h3>
                <p className="text-xs text-gray-600">
                  商用サービスとして運用するため、開発・運用体制の本格的な構築が必要
                </p>
              </div>
            </div>
          </div>

        </div>
      </div>
      
        <div className="mt-16">
          <h2 className="text-xl font-bold mb-4 text-center">システムの使い方</h2>
          <div className="max-w-2xl mx-auto space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-bold mb-2">📝 Step 1: 特許情報の入力</h3>
              <ul className="list-disc list-inside space-y-1 text-sm">
                <li><strong>特許番号</strong>を入力（例: 07666636, US7666636）</li>
                <li><strong>請求項1の全文</strong>を入力</li>
                <li>この2つだけで分析開始！</li>
              </ul>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <h3 className="font-bold mb-2">🔍 Step 2: AI による自動調査（バックグラウンド実行）</h3>
              <ul className="list-disc list-inside space-y-1 text-sm">
                <li>OpenAI Deep ResearchがWeb検索で情報収集</li>
                <li>日本国内でサービス展開している外国企業の製品を調査</li>
                <li>請求項1の構成要件を満たす製品を検出</li>
                <li>最大15分の長時間分析をサポート</li>
              </ul>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <h3 className="font-bold mb-2">📊 Step 3: 結果の確認</h3>
              <ul className="list-disc list-inside space-y-1 text-sm">
                <li>各製品の構成要件充足性をマークダウンテーブルで表示</li>
                <li>充足判断（○/×）と根拠となるURL・公開情報を提示</li>
                <li>複数製品の分析結果を一覧で確認可能</li>
                <li>分析履歴はデータベースに保存され、いつでも参照可能</li>
              </ul>
            </div>
          </div>
      </div>
      <div className="flex justify-center gap-4">
          <Link
            href="/research"
            className="px-8 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-lg font-medium"
          >
            🚀 侵害調査を開始
          </Link>
        </div>
    </main>
  );
}
