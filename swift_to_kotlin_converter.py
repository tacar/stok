#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Swift から Kotlin への変換ツール

このスクリプトは、Swift/SwiftUI プロジェクトを Kotlin/Jetpack Compose プロジェクトに変換します。
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
    ensure_directory(args.output_dir)

    # Kotlin テンプレートを出力先にコピー
    print(f"Kotlin テンプレートをコピーしています: {args.template_kotlin} -> {args.output_dir}")
    copy_directory(args.template_kotlin, args.output_dir, exclude=['.git', '.idea', 'build', '.gradle'])

    # パッケージディレクトリ構造を作成
    package_path = args.package_name.replace('.', '/')
    java_dir = os.path.join(args.output_dir, 'app/src/main/java')
    package_dir = os.path.join(java_dir, package_path)

    # 必要なディレクトリを作成
    for directory in [
        'models',
        'ui/screens',
        'ui/components',
        'ui/theme',
        'viewmodels',
        'repositories',
        'services',
        'di',
        'data/local',
        'data/remote',
        'utils'
    ]:
        ensure_directory(os.path.join(package_dir, directory))

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
    }

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
                elif file.endswith('ViewModel.swift'):
                    project_info['viewmodels'].append(relative_path)
                elif 'Repository' in file or '/Repositories/' in file_path:
                    project_info['repositories'].append(relative_path)
                elif 'Service' in file or '/Services/' in file_path:
                    project_info['services'].append(relative_path)

                # 特定の機能の使用を検出
                content = read_file(file_path)
                if 'Firebase' in content:
                    project_info['uses_firebase'] = True
                if 'SwiftData' in content or '@Model' in content:
                    project_info['uses_swiftdata'] = True
                if 'Combine' in content or 'Publisher' in content or 'Subject' in content:
                    project_info['uses_combine'] = True

    # リソースファイルを収集
    for root, dirs, files in os.walk(os.path.join(from_dir, 'Resources')):
        for file in files:
            if file.endswith(('.png', '.jpg', '.jpeg', '.svg', '.json')):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, from_dir)
                project_info['resources'].append(relative_path)

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
            project_info = analyze_swift_project(args.from_dir)
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
            }

        # 各コンポーネントを変換
        try:
            convert_models(args.from_dir, package_dir, project_info, args.package_name)
        except Exception as e:
            print(f"警告: モデルの変換中にエラーが発生しました: {e}")

        try:
            convert_views(args.from_dir, package_dir, project_info, args.package_name)
        except Exception as e:
            print(f"警告: ビューの変換中にエラーが発生しました: {e}")

        try:
            convert_viewmodels(args.from_dir, package_dir, project_info, args.package_name)
        except Exception as e:
            print(f"警告: ViewModelの変換中にエラーが発生しました: {e}")

        try:
            convert_repositories(args.from_dir, package_dir, project_info, args.package_name)
        except Exception as e:
            print(f"警告: リポジトリの変換中にエラーが発生しました: {e}")

        try:
            convert_services(args.from_dir, package_dir, project_info, args.package_name)
        except Exception as e:
            print(f"警告: サービスの変換中にエラーが発生しました: {e}")

        # 依存性注入をセットアップ
        try:
            setup_dependency_injection(package_dir, project_info, args.package_name)
        except Exception as e:
            print(f"警告: 依存性注入のセットアップ中にエラーが発生しました: {e}")

        # Firebase をセットアップ（必要な場合）
        if project_info.get('uses_firebase', False):
            try:
                setup_firebase(args.output_dir, args.package_name)
            except Exception as e:
                print(f"警告: Firebaseのセットアップ中にエラーが発生しました: {e}")

        # データベースをセットアップ（SwiftData を使用している場合）
        if project_info.get('uses_swiftdata', False):
            try:
                setup_database(args.output_dir, package_dir, project_info, args.package_name)
            except Exception as e:
                print(f"警告: データベースのセットアップ中にエラーが発生しました: {e}")

        # ネットワークをセットアップ
        try:
            setup_network(package_dir, project_info, args.package_name)
        except Exception as e:
            print(f"警告: ネットワークのセットアップ中にエラーが発生しました: {e}")

        # リソースを変換
        try:
            convert_resources(args.from_dir, args.output_dir, project_info)
        except Exception as e:
            print(f"警告: リソースの変換中にエラーが発生しました: {e}")

        # AndroidManifest.xml を生成
        try:
            generate_manifest(args.output_dir, args.package_name, args.app_name)
        except Exception as e:
            print(f"警告: AndroidManifest.xmlの生成中にエラーが発生しました: {e}")

        # Gradle ファイルをセットアップ
        try:
            # Gradleファイルをセットアップ
            setup_gradle(args.output_dir, project_info, args.package_name, args.app_name)
        except Exception as e:
            print(f"警告: Gradleファイルのセットアップ中にエラーが発生しました: {e}")

        print("変換が完了しました！")
        print(f"生成されたプロジェクトは {args.output_dir} にあります。")
    except Exception as e:
        print(f"エラー: 変換処理中に予期しないエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()