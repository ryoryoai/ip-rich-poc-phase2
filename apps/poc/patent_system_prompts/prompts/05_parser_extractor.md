# 05 実装プロンプト: 公報XMLパーサ（請求項抽出）を作る

`app/parse/jp_gazette_parser.py` を実装し、JPO公報XMLから請求項を抽出してください。

## 重点要件
- claim num="1" の全文を返せること
- XMLの名前空間有無に耐えること（XPathで local-name() を使う）
- claim-text 内のインラインタグや改行をテキストとして統合
- 文字コードは XML宣言を尊重（バイト列で読み、lxml等で安全にパース）

## 抽出対象（MVP）
- country: "JP"
- doc_number: <doc-number> 相当（XMLから取得）
- kind: kind-of-st16 が取れればそれ、無ければ kind-of-jp でもよい
- claims: claim_no と claim_text

## 正規化
- claim_text は、行頭行末の空白を除去し、連続空行は1つにまとめる
- 改行は \n

## CLI連携
- `python -m app.cli parse --raw-file-id <id>` で1件を解析できる
- `python -m app.cli parse --all` で未解析のraw_filesを順次処理できる

## エラー
- claim1が無い場合は documents は登録してよいが、claims は空でもよい
- ただしログに warn を残す

## テスト
- tests/fixtures に最小のXMLを置き、claim1抽出と正規化を検証
