# PlantUML Diagrams

このディレクトリには、特許侵害調査ワークフローのPlantUML図が含まれています。

## ファイル一覧

- **current-workflow.puml** - 現行の手動ワークフロー（スイムレーン図）
- **automated-workflow.puml** - 自動化後のワークフロー（スイムレーン図）
- **data-flow.puml** - データフロー図

## SVGファイルの生成方法

### 方法1: npm scriptを使用（推奨）

```bash
# すべての図をSVGに変換
npm run diagrams:generate

# 個別に変換
npm run diagrams:current      # 現行ワークフロー
npm run diagrams:automated    # 自動化ワークフロー
npm run diagrams:dataflow     # データフロー
```

### 方法2: node-plantumlコマンドを直接使用

```bash
# 個別ファイルを変換
npx puml generate docs/diagrams/current-workflow.puml -o docs/diagrams/current-workflow.svg

# すべてのファイルを一括変換
npx puml generate docs/diagrams/*.puml -o docs/diagrams/
```

### 方法3: PlantUMLの公式ツールを使用

PlantUMLがインストールされている場合：

```bash
# Java版PlantUMLを使用
java -jar plantuml.jar docs/diagrams/current-workflow.puml -tsvg

# または、PlantUML CLIを使用
plantuml docs/diagrams/current-workflow.puml -tsvg
```

### 方法4: オンラインエディタを使用

1. [PlantUML Online Editor](http://www.plantuml.com/plantuml/uml/)にアクセス
2. `.puml`ファイルの内容をコピー＆ペースト
3. SVGファイルとしてダウンロード

## Markdown での使用方法

### Docusaurusでの自動レンダリング

Docusaurusは`remark-local-plantuml`プラグインを使用してPlantUMLコードを自動的にレンダリングします：

```markdown
\`\`\`plantuml
@startuml
... PlantUML code ...
@enduml
\`\`\`
```

### SVG画像として埋め込み

事前に生成したSVGファイルを使用する場合：

```markdown
![ワークフロー図](./diagrams/current-workflow.svg)
```

## 編集のワークフロー

1. `.puml`ファイルを編集
2. SVGファイルを再生成（必要に応じて）
3. Docusaurusで確認: `npm start`
4. 変更をコミット（`.puml`ファイルと生成された`.svg`ファイルの両方）

## 注意事項

- `.puml`ファイルがソースファイルです。これを編集してください。
- 生成された`.svg`ファイルは、Git管理に含めるかどうかプロジェクトポリシーに従ってください。
- Docusaurusはビルド時に自動的にPlantUMLをレンダリングするため、`.svg`ファイルは必須ではありません。
- `.svg`ファイルは、外部ドキュメントやプレゼンテーションで使用する際に便利です。

## PlantUMLの参考資料

- [PlantUML 公式ドキュメント](https://plantuml.com/)
- [PlantUML スイムレーン図](https://plantuml.com/activity-diagram-beta)
- [PlantUML クラス図](https://plantuml.com/class-diagram)
