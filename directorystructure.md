日本語で返答

Swiftプロジェクト→Kotlinプロジェクトの変換ツールを考えています。

フォルダ校正
from 変換元のiosプロジェクト
tmpios iOSのテンプレート
tmpkotlin Androidのテンプレート
to jetpack compose 生成プロジェクト出力 jetpack composeで
tool 変換ツール　これを作る


iOS側
MVVM（Model-View-ViewModel）: ビジネスロジックとUIを分離
リポジトリパターン: データアクセスを抽象化
依存性注入: コンポーネント間の結合度を低減
SwiftData: ローカルデータ永続化
技術スタック
SwiftUI: UIフレームワーク
SwiftData: データ永続化
Firebase: 認証
Combine: 非同期処理

Android側
言語: Kotlin
UI: Jetpack Compose
アーキテクチャ: MVVM（Model-View-ViewModel）
依存性注入: Koin
データベース: SQLDelight
ネットワーク: Ktor
認証: Firebase Authentication
その他: Firebase Crashlytics, Firebase Analytics

