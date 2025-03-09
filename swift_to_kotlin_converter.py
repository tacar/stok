#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Swift から Kotlin への変換ツール

【重要な参照先】
- from/Features: 変換元のSwiftコードの主要機能が格納されているディレクトリです。UIコンポーネントやビジネスロジックの実装を含みます。
- from/Features/Navigation/AppTabView.swift: アプリのメイン画面構成とナビゲーション構造を定義しているファイルです。UI階層を理解する上で最も重要なファイルの一つです。
- tmpios: iOSのテンプレートコードが含まれるディレクトリです。変換の参考として使用されますが、実際の変換対象ではありません。

【ツールの機能】
このスクリプトは、Swift/SwiftUI プロジェクトを Kotlin/Jetpack Compose プロジェクトに変換します。
主な機能:
- Swiftのモデル、ビュー、ビューモデルをKotlinに変換
- リポジトリとサービスの実装を移植
- 依存性注入の設定
- データベースとネットワーク層の構築
- リソースファイルの変換
- Gradleファイルとマニフェストの生成

変換は以下の対応に基づいて行われます：

iOS側:
- MVVM（Model-View-ViewModel）
- リポジトリパターン
- 依存性注入
- SwiftData（ローカルデータ永続化）
- SwiftUI（UIフレームワーク）
- Firebase（認証）
- Combine（非同期処理）

Android側:
- Kotlin
- Jetpack Compose（UI）
- MVVM（Model-View-ViewModel）
- Koin（依存性注入）
- SQLDelight（データベース）
- Ktor（ネットワーク）
- Firebase Authentication（認証）
- Firebase Crashlytics, Firebase Analytics
"""

import os
import sys
import shutil
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# モジュールのインポート
from converters.model_converter import convert_models
from converters.view_converter import convert_views
from converters.viewmodel_converter import convert_viewmodels
from converters.repository_converter import convert_repositories
from converters.service_converter import convert_services
from converters.di_converter import setup_dependency_injection
from converters.firebase_converter import setup_firebase
from converters.database_converter import setup_database
from converters.network_converter import setup_network
from converters.resource_converter import convert_resources
from converters.manifest_converter import generate_manifest
from converters.gradle_converter import setup_gradle
from utils.file_utils import copy_directory, ensure_directory, read_file, write_file
from utils.parser import parse_swift_file, parse_kotlin_template

# 定数
DEFAULT_FROM_DIR = "../from"
DEFAULT_TEMPLATE_IOS_DIR = "../tmpios"
DEFAULT_TEMPLATE_KOTLIN_DIR = "../tmpkotlin"
DEFAULT_OUTPUT_DIR = "../to"

def parse_arguments():
    """コマンドライン引数をパースします"""
    parser = argparse.ArgumentParser(description='Swift から Kotlin への変換ツール')
    parser.add_argument('--from-dir', type=str, default=DEFAULT_FROM_DIR,
                        help=f'変換元の iOS プロジェクトディレクトリ (デフォルト: {DEFAULT_FROM_DIR})')
    parser.add_argument('--template-ios', type=str, default=DEFAULT_TEMPLATE_IOS_DIR,
                        help=f'iOS テンプレートディレクトリ (デフォルト: {DEFAULT_TEMPLATE_IOS_DIR})')
    parser.add_argument('--template-kotlin', type=str, default=DEFAULT_TEMPLATE_KOTLIN_DIR,
                        help=f'Kotlin テンプレートディレクトリ (デフォルト: {DEFAULT_TEMPLATE_KOTLIN_DIR})')
    parser.add_argument('--output-dir', type=str, default=DEFAULT_OUTPUT_DIR,
                        help=f'出力先ディレクトリ (デフォルト: {DEFAULT_OUTPUT_DIR})')
    parser.add_argument('--package-name', type=str, default="com.example.app",
                        help='Android アプリのパッケージ名 (デフォルト: com.example.app)')
    parser.add_argument('--app-name', type=str, default="MyApp",
                        help='アプリケーション名 (デフォルト: MyApp)')
    parser.add_argument('--clean', action='store_true',
                        help='出力先ディレクトリを事前にクリアする')

    return parser.parse_args()

def setup_project_structure(args):
    """プロジェクト構造をセットアップします"""
    print(f"プロジェクト構造をセットアップしています...")

    # 絶対パスに変換
    output_dir_abs = os.path.abspath(args.output_dir)
    from_dir_abs = os.path.abspath(args.from_dir)
    template_kotlin_abs = os.path.abspath(args.template_kotlin)

    # 入力ディレクトリの存在確認
    if not os.path.exists(from_dir_abs):
        print(f"エラー: 変換元ディレクトリが存在しません: {from_dir_abs}")
        return None

    if not os.path.exists(template_kotlin_abs):
        print(f"エラー: Kotlinテンプレートディレクトリが存在しません: {template_kotlin_abs}")
        return None

    # 出力先ディレクトリをクリアする（必要な場合）
    if args.clean and os.path.exists(output_dir_abs):
        print(f"出力先ディレクトリをクリアしています: {output_dir_abs}")
        try:
            # 現在のディレクトリを保存
            current_dir = os.getcwd()

            # 現在のディレクトリが出力先ディレクトリ内にある場合は、親ディレクトリに移動
            if current_dir.startswith(output_dir_abs):
                parent_dir = os.path.dirname(os.path.dirname(output_dir_abs))
                os.chdir(parent_dir)
                print(f"安全のため、ディレクトリを変更しました: {parent_dir}")

            # ディレクトリを削除
            shutil.rmtree(output_dir_abs)

            # 元のディレクトリに戻る（可能な場合）
            if os.path.exists(current_dir) and not current_dir.startswith(output_dir_abs):
                os.chdir(current_dir)
        except Exception as e:
            print(f"警告: 出力先ディレクトリのクリア中にエラーが発生しました: {e}")
            # エラーが発生した場合でも続行

    # 出力先ディレクトリを作成
    try:
        ensure_directory(args.output_dir)
        print(f"出力先ディレクトリを作成しました: {output_dir_abs}")
    except Exception as e:
        print(f"エラー: 出力先ディレクトリの作成に失敗しました: {e}")
        return None

    # Kotlin テンプレートを出力先にコピー
    print(f"Kotlin テンプレートをコピーしています: {args.template_kotlin} -> {args.output_dir}")
    try:
        copy_directory(args.template_kotlin, args.output_dir, exclude=['.git', '.idea', 'build', '.gradle', 'local.properties'])
        print(f"Kotlinテンプレートのコピーが完了しました")
    except Exception as e:
        print(f"警告: Kotlinテンプレートのコピー中にエラーが発生しました: {e}")
        # エラーが発生した場合でも続行

    # パッケージディレクトリ構造を作成
    package_path = args.package_name.replace('.', '/')
    java_dir = os.path.join(args.output_dir, 'app/src/main/java')
    package_dir = os.path.join(java_dir, package_path)

    # 必要なディレクトリを作成
    print(f"アプリケーション構造を作成しています...")
    app_directories = [
        'models',
        'ui/screens',
        'ui/components',
        'ui/theme',
        'ui/navigation',
        'viewmodels',
        'repositories',
        'services',
        'di',
        'data/local',
        'data/remote',
        'utils',
        'utils/extensions'
    ]

    for directory in app_directories:
        dir_path = os.path.join(package_dir, directory)
        try:
            ensure_directory(dir_path)
        except Exception as e:
            print(f"警告: ディレクトリの作成中にエラーが発生しました ({directory}): {e}")

    # リソースディレクトリを作成
    resource_dirs = [
        'app/src/main/res/drawable',
        'app/src/main/res/drawable-hdpi',
        'app/src/main/res/drawable-mdpi',
        'app/src/main/res/drawable-xhdpi',
        'app/src/main/res/drawable-xxhdpi',
        'app/src/main/res/layout',
        'app/src/main/res/values',
        'app/src/main/res/values-night',
        'app/src/main/res/raw'
    ]

    for directory in resource_dirs:
        dir_path = os.path.join(args.output_dir, directory)
        try:
            ensure_directory(dir_path)
        except Exception as e:
            print(f"警告: リソースディレクトリの作成中にエラーが発生しました ({directory}): {e}")

    print(f"プロジェクト構造のセットアップが完了しました")
    return package_dir

def analyze_swift_project(from_dir: str) -> Dict[str, Any]:
    """Swift プロジェクトを解析し、変換に必要な情報を収集します"""
    print(f"Swift プロジェクトを解析しています: {from_dir}")

    project_info = {
        'models': [],
        'views': [],
        'viewmodels': [],
        'repositories': [],
        'services': [],
        'resources': [],
        'uses_firebase': False,
        'uses_swiftdata': False,
        'uses_combine': False,
        'uses_networking': False,
        'app_structure': {
            'main_navigation': None,
            'screens': [],
            'components': []
        },
        'dependencies': set()
    }

    # 特に重要なファイルを確認
    app_tab_view_path = os.path.join(from_dir, 'Features/Navigation/AppTabView.swift')
    if os.path.exists(app_tab_view_path):
        project_info['app_structure']['main_navigation'] = 'Features/Navigation/AppTabView.swift'
        print(f"メインナビゲーションファイルを検出: {app_tab_view_path}")
        # AppTabViewの内容を解析して画面構造を把握
        try:
            content = read_file(app_tab_view_path)
            # 画面名を抽出する簡易的な方法（実際にはより高度な解析が必要）
            view_matches = re.findall(r'(\w+View)\(\)', content)
            if view_matches:
                project_info['app_structure']['screens'].extend(view_matches)
                print(f"検出された画面: {', '.join(view_matches)}")
        except Exception as e:
            print(f"警告: AppTabViewの解析中にエラーが発生しました: {e}")

    # ディレクトリを再帰的に走査
    for root, dirs, files in os.walk(from_dir):
        for file in files:
            if file.endswith('.swift'):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, from_dir)

                # ファイルの種類を判断
                if file.endswith('Model.swift') or '/Models/' in file_path:
                    project_info['models'].append(relative_path)
                elif file.endswith('View.swift') or '/Views/' in file_path or '/Features/' in file_path:
                    project_info['views'].append(relative_path)
                    # UIコンポーネントかスクリーンかを判断
                    if '/Components/' in file_path:
                        project_info['app_structure']['components'].append(relative_path)
                    elif '/Screens/' in file_path or '/Features/' in file_path:
                        project_info['app_structure']['screens'].append(relative_path)
                elif file.endswith('ViewModel.swift'):
                    project_info['viewmodels'].append(relative_path)
                elif 'Repository' in file or '/Repositories/' in file_path:
                    project_info['repositories'].append(relative_path)
                elif 'Service' in file or '/Services/' in file_path:
                    project_info['services'].append(relative_path)

                # 特定の機能の使用を検出
                try:
                    content = read_file(file_path)
                    if 'Firebase' in content or 'import Firebase' in content:
                        project_info['uses_firebase'] = True
                        project_info['dependencies'].add('firebase')
                    if 'SwiftData' in content or '@Model' in content:
                        project_info['uses_swiftdata'] = True
                        project_info['dependencies'].add('database')
                    if 'Combine' in content or 'Publisher' in content or 'Subject' in content:
                        project_info['uses_combine'] = True
                        project_info['dependencies'].add('coroutines')
                    if 'URLSession' in content or 'Alamofire' in content or 'API' in content:
                        project_info['uses_networking'] = True
                        project_info['dependencies'].add('networking')
                except Exception as e:
                    print(f"警告: ファイル {file_path} の解析中にエラーが発生しました: {e}")

    # リソースファイルを収集
    resources_dir = os.path.join(from_dir, 'Resources')
    if os.path.exists(resources_dir):
        for root, dirs, files in os.walk(resources_dir):
            for file in files:
                if file.endswith(('.png', '.jpg', '.jpeg', '.svg', '.json', '.xml')):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, from_dir)
                    project_info['resources'].append(relative_path)

    # 依存関係をリストに変換
    project_info['dependencies'] = list(project_info['dependencies'])

    # 解析結果のサマリーを表示
    print(f"\n解析結果サマリー:")
    print(f"- モデル: {len(project_info['models'])}個")
    print(f"- ビュー: {len(project_info['views'])}個")
    print(f"- ビューモデル: {len(project_info['viewmodels'])}個")
    print(f"- リポジトリ: {len(project_info['repositories'])}個")
    print(f"- サービス: {len(project_info['services'])}個")
    print(f"- リソース: {len(project_info['resources'])}個")
    print(f"- 検出された依存関係: {', '.join(project_info['dependencies'])}")

    return project_info

def main():
    """メイン関数"""
    try:
        args = parse_arguments()

        print("Swift から Kotlin への変換を開始します...")
        print(f"変換元: {args.from_dir}")
        print(f"出力先: {args.output_dir}")
        print(f"パッケージ名: {args.package_name}")
        print(f"アプリ名: {args.app_name}")

        # プロジェクト構造をセットアップ
        package_dir = setup_project_structure(args)
        if not package_dir or not os.path.exists(package_dir):
            print(f"エラー: パッケージディレクトリの作成に失敗しました: {package_dir}")
            return

        # Swift プロジェクトを解析
        try:
            print("Swift プロジェクトを解析しています...")
            project_info = analyze_swift_project(args.from_dir)
            print(f"解析完了: {len(project_info['models'])} モデル, {len(project_info['views'])} ビュー, {len(project_info['viewmodels'])} ビューモデルを検出しました")
        except Exception as e:
            print(f"警告: Swift プロジェクトの解析中にエラーが発生しました: {e}")
            project_info = {
                'models': [],
                'views': [],
                'viewmodels': [],
                'repositories': [],
                'services': [],
                'resources': [],
                'uses_firebase': False,
                'uses_swiftdata': False,
                'uses_combine': False,
                'uses_networking': False,
                'app_structure': {
                    'main_navigation': None,
                    'screens': [],
                    'components': []
                },
                'dependencies': set()
            }

        # 各コンポーネントを変換
        conversion_steps = [
            ("モデル", convert_models, args.from_dir, package_dir, project_info, args.package_name),
            ("ビュー", convert_views, args.from_dir, package_dir, project_info, args.package_name),
            ("ビューモデル", convert_viewmodels, args.from_dir, package_dir, project_info, args.package_name),
            ("リポジトリ", convert_repositories, args.from_dir, package_dir, project_info, args.package_name),
            ("サービス", convert_services, args.from_dir, package_dir, project_info, args.package_name),
        ]

        for step_name, converter_func, *converter_args in conversion_steps:
            try:
                print(f"{step_name}を変換しています...")
                converter_func(*converter_args)
                print(f"{step_name}の変換が完了しました")
            except Exception as e:
                print(f"警告: {step_name}の変換中にエラーが発生しました: {e}")
                import traceback
                traceback.print_exc()

        # 依存性注入をセットアップ
        try:
            print("依存性注入をセットアップしています...")
            setup_dependency_injection(package_dir, project_info, args.package_name)
            print("依存性注入のセットアップが完了しました")
        except Exception as e:
            print(f"警告: 依存性注入のセットアップ中にエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()

        # Firebase をセットアップ（必要な場合）
        if project_info.get('uses_firebase', False):
            try:
                print("Firebaseをセットアップしています...")
                setup_firebase(args.output_dir, args.package_name)
                print("Firebaseのセットアップが完了しました")
            except Exception as e:
                print(f"警告: Firebaseのセットアップ中にエラーが発生しました: {e}")
                import traceback
                traceback.print_exc()

        # データベースをセットアップ（SwiftData を使用している場合）
        if project_info.get('uses_swiftdata', False):
            try:
                print("データベースをセットアップしています...")
                setup_database(args.output_dir, package_dir, project_info, args.package_name)
                print("データベースのセットアップが完了しました")
            except Exception as e:
                print(f"警告: データベースのセットアップ中にエラーが発生しました: {e}")
                import traceback
                traceback.print_exc()

        # ネットワークをセットアップ
        try:
            print("ネットワーク層をセットアップしています...")
            setup_network(package_dir, project_info, args.package_name)
            print("ネットワーク層のセットアップが完了しました")
        except Exception as e:
            print(f"警告: ネットワークのセットアップ中にエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()

        # リソースを変換
        try:
            print("リソースファイルを変換しています...")
            convert_resources(args.from_dir, args.output_dir, project_info)
            print("リソースファイルの変換が完了しました")
        except Exception as e:
            print(f"警告: リソースの変換中にエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()

        # AndroidManifest.xml を生成
        try:
            print("AndroidManifest.xmlを生成しています...")
            generate_manifest(args.output_dir, args.package_name, args.app_name)
            print("AndroidManifest.xmlの生成が完了しました")
        except Exception as e:
            print(f"警告: AndroidManifest.xmlの生成中にエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()

        # Gradle ファイルをセットアップ
        try:
            print("Gradleファイルをセットアップしています...")
            setup_gradle(args.output_dir, project_info, args.package_name, args.app_name)
            print("Gradleファイルのセットアップが完了しました")
        except Exception as e:
            print(f"警告: Gradleファイルのセットアップ中にエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()

        print("\n変換が完了しました！")
        print(f"生成されたプロジェクトは {os.path.abspath(args.output_dir)} にあります。")
        print("\n次のステップ:")
        print("1. Android Studioでプロジェクトを開く")
        print("2. Gradleの同期を実行する")
        print("3. 必要に応じてコードを調整する")
        print("\n注意: 自動変換されたコードは手動での確認と調整が必要な場合があります。")
    except Exception as e:
        print(f"エラー: 変換処理中に予期しないエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        print("\n変換プロセスは完了しませんでした。上記のエラーを修正して再試行してください。")
        sys.exit(1)

if __name__ == "__main__":
    main()