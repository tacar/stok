# Swift から Kotlin への変換ツール

このツールは、Swift/SwiftUI プロジェクトを Kotlin/Jetpack Compose プロジェクトに変換するためのものです。

## 機能

- Swift のモデルを Kotlin のデータクラスに変換
- SwiftUI のビューを Jetpack Compose のコンポーザブルに変換
- Swift の ViewModel を Kotlin の ViewModel に変換
- リポジトリパターンの実装を変換
- 依存性注入（Koin）の設定
- Firebase 認証の設定
- SQLDelight によるローカルデータベースの設定
- Ktor によるネットワーク通信の設定
- リソースファイルの変換
- Gradle の設定

## 前提条件

- Python 3.7 以上
- 変換元の iOS プロジェクト
- iOS テンプレート（参照用）
- Android テンプレート（参照用）

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/swift-to-kotlin-converter.git

# ディレクトリに移動
cd swift-to-kotlin-converter
```

## 使い方

```bash
# 基本的な使い方
python swift_to_kotlin_converter.py --from-dir /path/to/ios/project --output-dir /path/to/output

# すべてのオプションを指定
python swift_to_kotlin_converter.py \
  --from-dir /path/to/ios/project \
  --template-ios /path/to/ios/template \
  --template-kotlin /path/to/kotlin/template \
  --output-dir /path/to/output \
  --package-name com.example.app \
  --app-name MyApp \
  --clean
```

### オプション

- `--from-dir`: 変換元の iOS プロジェクトディレクトリ（デフォルト: ../from）
- `--template-ios`: iOS テンプレートディレクトリ（デフォルト: ../tmpios）
- `--template-kotlin`: Kotlin テンプレートディレクトリ（デフォルト: ../tmpkotlin）
- `--output-dir`: 出力先ディレクトリ（デフォルト: ../to）
- `--package-name`: Android アプリのパッケージ名（デフォルト: com.example.app）
- `--app-name`: アプリケーション名（デフォルト: MyApp）
- `--clean`: 出力先ディレクトリを事前にクリアする

## 変換の対応関係

### アーキテクチャ

| iOS (Swift)        | Android (Kotlin)   |
| ------------------ | ------------------ |
| MVVM               | MVVM               |
| リポジトリパターン | リポジトリパターン |
| 依存性注入         | Koin               |
| SwiftData          | SQLDelight         |
| SwiftUI            | Jetpack Compose    |
| Combine            | Flow               |
| Firebase           | Firebase           |

### ファイル構造

| iOS (Swift)   | Android (Kotlin)            |
| ------------- | --------------------------- |
| Models/       | models/                     |
| Views/        | ui/screens/, ui/components/ |
| ViewModels/   | viewmodels/                 |
| Repositories/ | repositories/               |
| Services/     | services/                   |
| Resources/    | res/                        |

## 制限事項

- 複雑な SwiftUI のレイアウトは完全に変換できない場合があります
- カスタムアニメーションは手動での調整が必要な場合があります
- プラットフォーム固有の機能は適切に変換されない場合があります
- 変換後のコードは手動でのレビューと調整が必要です

## ライセンス

MIT

## 貢献

プルリクエストは歓迎します。大きな変更を加える場合は、まずイシューを開いて議論してください。
