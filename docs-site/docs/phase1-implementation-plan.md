---
sidebar_position: 5
---

# Phase 1: 侵害調査自動化 - 実装計画

Phase 1（侵害調査の自動化）の詳細な実装計画です。

## 概要

**期間**: 2〜3週間（13営業日）
**目標**: 特許1件あたりの侵害可能性を自動判定するシステムを構築
**コスト**: $0.02〜1/月

## プロジェクト構造（Next.js版）

```
ip-rich-tools/
├── infra/                           # Terraform インフラ
├── docs-site/                       # Docusaurus ドキュメント
└── apps/
    └── poc/
        └── phase1/                  # Phase 1: 侵害調査自動化（Next.js）
            ├── README.md
            ├── package.json
            ├── tsconfig.json
            ├── next.config.js
            ├── tailwind.config.ts
            ├── .env.local.example
            ├── .gitignore
            ├── src/
            │   ├── app/             # Next.js App Router
            │   │   ├── layout.tsx
            │   │   ├── page.tsx
            │   │   ├── analyze/
            │   │   │   └── page.tsx
            │   │   └── api/
            │   │       ├── analyze/
            │   │       │   └── route.ts
            │   │       ├── requirements/
            │   │       │   └── route.ts
            │   │       └── compliance/
            │   │           └── route.ts
            │   ├── components/
            │   │   ├── ui/          # shadcn/ui
            │   │   │   ├── button.tsx
            │   │   │   ├── card.tsx
            │   │   │   ├── input.tsx
            │   │   │   └── textarea.tsx
            │   │   ├── PatentInputForm.tsx
            │   │   ├── RequirementsList.tsx
            │   │   ├── ComplianceResults.tsx
            │   │   └── AnalysisReport.tsx
            │   ├── lib/
            │   │   ├── openai.ts
            │   │   ├── search.ts
            │   │   ├── storage.ts
            │   │   ├── prompts.ts
            │   │   └── utils.ts
            │   └── types/
            │       ├── patent.ts
            │       ├── analysis.ts
            │       └── api.ts
            ├── public/
            │   └── sample-data/
            │       └── patents.json
            └── data/
                ├── results/
                └── cache/
```

---

## Week 1: 基盤構築とプロンプト開発（5日間）

### Day 1-2: プロジェクト初期化とプロンプト設計

**作業内容**:
1. プロジェクト構造の作成
2. 依存関係の定義（requirements.txt）
3. 環境変数の設定（.env.example）
4. プロンプトテンプレートの設計

**成果物**:
- プロジェクト骨格
- requirements.txt
- プロンプト設計ドキュメント

**package.json**:
```json
{
  "name": "phase1-infringement-analyzer",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev -p 3000",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "jest"
  },
  "dependencies": {
    "next": "14.1.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "openai": "^4.26.0",
    "axios": "^1.6.5",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-slot": "^1.0.2",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "lucide-react": "^0.321.0",
    "tailwind-merge": "^2.2.1",
    "zod": "^3.22.4"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "autoprefixer": "^10.0.1",
    "postcss": "^8",
    "tailwindcss": "^3.3.0",
    "typescript": "^5"
  }
}
```

**.env.local.example**:
```bash
# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

# Perplexity API (Optional)
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# SerpAPI (Optional)
SERPAPI_KEY=your_serpapi_key_here

# Settings
MODEL_NAME=gpt-3.5-turbo
MAX_TOKENS=2000
TEMPERATURE=0.3

# Next.js
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

**プロンプトテンプレート（src/lib/prompts.ts）**:
```typescript
export const PROMPTS = {
  extractRequirements: {
    system: `あなたは特許の構成要件を抽出する専門家です。
請求項1を分析し、構成要件を個別に抽出してください。`,

    user: (patentNumber: string, claimText: string) => `以下の特許請求項1から、構成要件を抽出してください。
各構成要件を番号付きリストで出力してください。

【特許番号】${patentNumber}
【請求項1】
${claimText}

出力フォーマット:
1. 構成要件A: [要件の説明]
2. 構成要件B: [要件の説明]
...`,
  },

  checkCompliance: {
    system: `あなたは特許侵害の充足性を判定する専門家です。
構成要件と製品の仕様を比較し、充足性を判定してください。`,

    user: (requirement: string, productName: string, companyName: string, productSpec: string) =>
      `以下の構成要件について、製品が充足しているか判定してください。

【構成要件】
${requirement}

【製品情報】
製品名: ${productName}
企業名: ${companyName}
仕様情報: ${productSpec}

判定結果を以下の形式で出力してください:
- 充足判断: ○/×
- 理由: [判定理由を簡潔に記載]
- 根拠: [参照URLまたは具体的な製品機能]`,
  },
} as const;
```

### Day 3-4: コアモジュールの実装

**作業内容**:
1. OpenAI APIクライアントの実装
2. 構成要件抽出モジュールの実装
3. データストレージモジュールの実装

**成果物**:
- `utils/openai_client.py`
- `modules/requirement_extractor.py`
- `utils/data_storage.py`

**サンプルコード（utils/openai_client.py）**:
```python
import os
from openai import OpenAI
from typing import Optional

class OpenAIClient:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "2000"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.3"))

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None
    ) -> str:
        """OpenAI APIを呼び出してテキストを生成"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=temperature or self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API Error: {str(e)}")
```

**サンプルコード（modules/requirement_extractor.py）**:
```python
import yaml
from typing import List, Dict
from utils.openai_client import OpenAIClient

class RequirementExtractor:
    def __init__(self, prompt_config_path: str = "config/prompts.yaml"):
        self.client = OpenAIClient()
        with open(prompt_config_path, 'r', encoding='utf-8') as f:
            self.prompts = yaml.safe_load(f)

    def extract_requirements(
        self,
        patent_number: str,
        claim_text: str
    ) -> List[Dict[str, str]]:
        """請求項1から構成要件を抽出"""
        system_prompt = self.prompts['extract_requirements']['system']
        user_prompt = self.prompts['extract_requirements']['user'].format(
            patent_number=patent_number,
            claim_text=claim_text
        )

        response = self.client.generate(system_prompt, user_prompt)

        # レスポンスをパースして構成要件リストに変換
        requirements = self._parse_requirements(response)
        return requirements

    def _parse_requirements(self, response: str) -> List[Dict[str, str]]:
        """構成要件のパース処理"""
        requirements = []
        lines = response.strip().split('\n')

        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # "1. 構成要件A: 説明" のような形式をパース
                parts = line.split(':', 1)
                if len(parts) == 2:
                    requirement_id = parts[0].strip()
                    description = parts[1].strip()
                    requirements.append({
                        'id': requirement_id,
                        'description': description
                    })

        return requirements
```

### Day 5: Web検索モジュールとテスト

**作業内容**:
1. Web検索モジュールの実装（Perplexity/SerpAPI + フォールバック）
2. 単体テストの作成
3. 初期テスト実行

**成果物**:
- `modules/web_search.py`
- `tests/test_requirement_extractor.py`

**サンプルコード（modules/web_search.py）**:
```python
import os
import requests
from typing import List, Dict, Optional

class WebSearchClient:
    def __init__(self):
        self.perplexity_key = os.getenv("PERPLEXITY_API_KEY")
        self.serpapi_key = os.getenv("SERPAPI_KEY")

    def search(
        self,
        query: str,
        num_results: int = 5
    ) -> List[Dict[str, str]]:
        """Web検索を実行（Perplexity → SerpAPI → フォールバック）"""

        # Perplexity APIを試す
        if self.perplexity_key:
            try:
                return self._search_perplexity(query, num_results)
            except Exception as e:
                print(f"Perplexity API failed: {e}")

        # SerpAPIを試す
        if self.serpapi_key:
            try:
                return self._search_serpapi(query, num_results)
            except Exception as e:
                print(f"SerpAPI failed: {e}")

        # フォールバック: 基本的なスクレイピング
        return self._search_fallback(query, num_results)

    def _search_perplexity(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """Perplexity API検索"""
        # TODO: Perplexity API実装
        pass

    def _search_serpapi(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """SerpAPI検索"""
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": self.serpapi_key,
            "num": num_results
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        results = []

        for item in data.get("organic_results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", "")
            })

        return results

    def _search_fallback(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """フォールバック検索（基本的なスクレイピング）"""
        # 簡易実装: 実際にはより高度なスクレイピングが必要
        print(f"Warning: Using fallback search for query: {query}")
        return []
```

---

## Week 2: 充足性判定とUI開発（5日間）

### Day 6-7: 充足性判定モジュールの実装

**作業内容**:
1. 充足性判定モジュールの実装
2. レポート生成モジュールの実装
3. データ保存機能の実装

**成果物**:
- `modules/compliance_checker.py`
- `modules/report_generator.py`

**サンプルコード（modules/compliance_checker.py）**:
```python
import yaml
from typing import Dict, List
from utils.openai_client import OpenAIClient
from modules.web_search import WebSearchClient

class ComplianceChecker:
    def __init__(self, prompt_config_path: str = "config/prompts.yaml"):
        self.client = OpenAIClient()
        self.search_client = WebSearchClient()
        with open(prompt_config_path, 'r', encoding='utf-8') as f:
            self.prompts = yaml.safe_load(f)

    def check_compliance(
        self,
        requirement: Dict[str, str],
        product_name: str,
        company_name: str
    ) -> Dict[str, any]:
        """構成要件の充足性を判定"""

        # 製品情報を検索
        search_query = f"{company_name} {product_name} specifications features"
        search_results = self.search_client.search(search_query, num_results=3)

        # 検索結果を製品仕様として整理
        product_spec = self._format_search_results(search_results)

        # GPTで充足性を判定
        system_prompt = self.prompts['check_compliance']['system']
        user_prompt = self.prompts['check_compliance']['user'].format(
            requirement=requirement['description'],
            product_name=product_name,
            company_name=company_name,
            product_spec=product_spec
        )

        response = self.client.generate(system_prompt, user_prompt)

        # レスポンスをパース
        judgment = self._parse_judgment(response, search_results)

        return {
            'requirement_id': requirement['id'],
            'requirement': requirement['description'],
            'compliance': judgment['compliance'],
            'reason': judgment['reason'],
            'evidence': judgment['evidence'],
            'urls': [r['url'] for r in search_results]
        }

    def _format_search_results(self, results: List[Dict[str, str]]) -> str:
        """検索結果を整形"""
        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(f"{i}. {result['title']}\n{result['snippet']}")
        return "\n\n".join(formatted)

    def _parse_judgment(
        self,
        response: str,
        search_results: List[Dict[str, str]]
    ) -> Dict[str, str]:
        """判定結果をパース"""
        lines = response.strip().split('\n')
        judgment = {
            'compliance': '×',
            'reason': '',
            'evidence': ''
        }

        for line in lines:
            line = line.strip()
            if '充足判断' in line or 'compliance' in line.lower():
                if '○' in line:
                    judgment['compliance'] = '○'
                elif '×' in line:
                    judgment['compliance'] = '×'
            elif '理由' in line or 'reason' in line.lower():
                judgment['reason'] = line.split(':', 1)[1].strip() if ':' in line else line
            elif '根拠' in line or 'evidence' in line.lower():
                judgment['evidence'] = line.split(':', 1)[1].strip() if ':' in line else line

        return judgment
```

### Day 8-9: Streamlit UIの開発

**作業内容**:
1. Streamlitメインアプリの実装
2. UI/UXの調整
3. 入力フォームとレポート表示の実装

**成果物**:
- `src/main.py`

**サンプルコード（src/main.py）**:
```python
import streamlit as st
import json
from datetime import datetime
from modules.requirement_extractor import RequirementExtractor
from modules.compliance_checker import ComplianceChecker
from utils.data_storage import DataStorage

# ページ設定
st.set_page_config(
    page_title="特許侵害調査システム - Phase 1 PoC",
    page_icon="🔍",
    layout="wide"
)

# タイトル
st.title("🔍 特許侵害調査システム - Phase 1 PoC")
st.markdown("特許の構成要件抽出と侵害可能性の自動判定")

# サイドバー: 入力フォーム
with st.sidebar:
    st.header("📝 特許情報入力")

    patent_number = st.text_input("特許番号", placeholder="例: 06195960")
    claim_text = st.text_area(
        "請求項1",
        height=200,
        placeholder="請求項1の全文を入力してください"
    )

    st.header("🏢 対象企業・製品")
    company_name = st.text_input("企業名", placeholder="例: TeamViewer")
    product_name = st.text_input("製品名", placeholder="例: TeamViewer Assist AR")

    analyze_button = st.button("🚀 分析開始", type="primary", use_container_width=True)

# メインエリア
if analyze_button:
    if not patent_number or not claim_text:
        st.error("特許番号と請求項1を入力してください")
    elif not company_name or not product_name:
        st.error("企業名と製品名を入力してください")
    else:
        with st.spinner("分析中..."):
            # 構成要件抽出
            st.subheader("📋 構成要件抽出")
            extractor = RequirementExtractor()
            requirements = extractor.extract_requirements(patent_number, claim_text)

            # 構成要件を表示
            for req in requirements:
                st.markdown(f"**{req['id']}**: {req['description']}")

            st.divider()

            # 充足性判定
            st.subheader("✅ 充足性判定")
            checker = ComplianceChecker()

            results = []
            for req in requirements:
                with st.expander(f"{req['id']} の判定結果", expanded=True):
                    result = checker.check_compliance(req, product_name, company_name)
                    results.append(result)

                    # 判定結果を表示
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if result['compliance'] == '○':
                            st.success(result['compliance'])
                        else:
                            st.error(result['compliance'])
                    with col2:
                        st.markdown(f"**理由**: {result['reason']}")
                        st.markdown(f"**根拠**: {result['evidence']}")
                        if result['urls']:
                            st.markdown("**参考URL**:")
                            for url in result['urls'][:3]:
                                st.markdown(f"- {url}")

            # 総合判定
            st.divider()
            st.subheader("📊 総合判定")

            compliant_count = sum(1 for r in results if r['compliance'] == '○')
            total_count = len(results)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("総構成要件数", total_count)
            with col2:
                st.metric("充足要件数", compliant_count)
            with col3:
                compliance_rate = (compliant_count / total_count * 100) if total_count > 0 else 0
                st.metric("充足率", f"{compliance_rate:.1f}%")

            # 侵害可能性判定
            if compliant_count == total_count:
                st.success("✅ 侵害可能性: ○（すべての構成要件を充足）")
            else:
                st.warning(f"❌ 侵害可能性: ×（{total_count - compliant_count}件の構成要件が不充足）")

            # 結果を保存
            storage = DataStorage()
            analysis_data = {
                'patent_number': patent_number,
                'company_name': company_name,
                'product_name': product_name,
                'timestamp': datetime.now().isoformat(),
                'requirements': requirements,
                'compliance_results': results,
                'summary': {
                    'total_requirements': total_count,
                    'compliant_requirements': compliant_count,
                    'compliance_rate': compliance_rate,
                    'infringement_possibility': '○' if compliant_count == total_count else '×'
                }
            }

            file_path = storage.save_analysis(analysis_data)

            # ダウンロードボタン
            st.download_button(
                label="📥 結果をJSONでダウンロード",
                data=json.dumps(analysis_data, ensure_ascii=False, indent=2),
                file_name=f"analysis_{patent_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

            st.success(f"✅ 分析完了！結果を保存しました: {file_path}")
else:
    # 初期画面
    st.info("👈 サイドバーから特許情報を入力して、分析を開始してください")

    st.markdown("""
    ### 使い方

    1. **特許情報入力**: サイドバーに特許番号と請求項1を入力
    2. **企業・製品情報**: 分析対象の企業名と製品名を入力
    3. **分析開始**: ボタンをクリックして自動分析を実行
    4. **結果確認**: 構成要件の充足性と総合判定を確認
    5. **保存**: 結果をJSONファイルでダウンロード

    ### 機能

    - ✅ 請求項1から構成要件を自動抽出
    - ✅ Web検索で製品仕様を自動収集
    - ✅ GPT-3.5-turboで充足性を自動判定
    - ✅ 結果をJSON形式で保存
    """)
```

### Day 10: テストと修正

**作業内容**:
1. 実際の特許データでテスト
2. バグ修正と調整
3. ドキュメント作成

**成果物**:
- テスト結果レポート
- README.md
- setup.md

---

## Week 3: 検証と最適化（3日間）

### Day 11-12: 精度検証

**作業内容**:
1. サンプル特許データで検証（オプティムの特許5件程度）
2. 人間の判断との比較
3. プロンプトの調整と改善

**検証データ**:
- 特許06195960（遠隔指示システム）
- 特許05148670（固有アドレスによる電化製品設定）
- 特許06077068（拡張現実システム）
- 特許04895405（レピュテーションベースセキュリティ）

**検証指標**:
| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| 構成要件抽出精度 | 90%以上 | 人間が抽出した構成要件と比較 |
| 充足性判定精度 | 80%以上 | 人間の判断と一致率 |
| 処理時間 | 5分/件以下 | 実測 |

### Day 13: ドキュメント整備とデモ準備

**作業内容**:
1. READMEの完成
2. セットアップガイドの作成
3. デモ用スクリプトの準備
4. Phase 1完成レポートの作成

**成果物**:
- 完成したPhase 1システム
- ドキュメント一式
- デモ用資料
- 精度検証レポート

---

## 技術仕様

### API利用

**OpenAI API**:
- モデル: gpt-3.5-turbo
- トークン制限: 2000 tokens/request
- Temperature: 0.3（一貫性重視）
- 推定コスト: $0.02〜1/月（10件分析時）

**Web検索**:
- 優先順位1: Perplexity API（無料枠: 100req/日）
- 優先順位2: SerpAPI（無料枠: 100検索/月）
- フォールバック: requests + BeautifulSoup

### データ形式

**入力データ**:
```json
{
  "patent_number": "06195960",
  "claim_text": "請求項1の全文...",
  "company_name": "TeamViewer",
  "product_name": "TeamViewer Assist AR"
}
```

**出力データ**:
```json
{
  "patent_number": "06195960",
  "company_name": "TeamViewer",
  "product_name": "TeamViewer Assist AR",
  "timestamp": "2025-10-13T12:00:00",
  "requirements": [
    {
      "id": "1",
      "description": "構成要件A: ..."
    }
  ],
  "compliance_results": [
    {
      "requirement_id": "1",
      "requirement": "構成要件A: ...",
      "compliance": "○",
      "reason": "製品は該当機能を実装している",
      "evidence": "公式ドキュメントに記載あり",
      "urls": ["https://example.com"]
    }
  ],
  "summary": {
    "total_requirements": 5,
    "compliant_requirements": 5,
    "compliance_rate": 100.0,
    "infringement_possibility": "○"
  }
}
```

---

## マイルストーン

| マイルストーン | 期限 | 成果物 |
|---------------|------|--------|
| **M1: プロジェクト初期化完了** | Day 2 | プロジェクト構造、プロンプト設計 |
| **M2: コアモジュール完成** | Day 5 | 構成要件抽出、Web検索機能 |
| **M3: 充足性判定機能完成** | Day 7 | 充足性判定モジュール |
| **M4: UI完成** | Day 9 | Streamlitアプリ |
| **M5: 検証完了** | Day 12 | 精度検証レポート |
| **M6: Phase 1完成** | Day 13 | 完成システム + ドキュメント |

---

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| OpenAI API制限・コスト超過 | 中 | キャッシング実装、トークン数削減 |
| Web検索API無料枠超過 | 中 | フォールバック実装、キャッシング |
| 構成要件抽出精度不足 | 高 | プロンプト改善、few-shot例追加 |
| 充足性判定精度不足 | 高 | プロンプト改善、検索結果の質向上 |
| 処理時間超過（5分/件） | 低 | 並列処理、キャッシング |

---

## 次のステップ

Phase 1完成後:
1. Phase 2（売上推定の自動化）の開発開始
2. Phase 1の改善点をフィードバック
3. Phase 2へのデータ連携設計

---

## 関連資料

- [PoC開発計画](./poc-development-plan.md) - PoC全体の計画
- [特許侵害調査ワークフロー](./patent-workflow.md) - 自動化対象のワークフロー
