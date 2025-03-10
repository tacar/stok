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

SWIFT_TO_KOTLIN_TYPE_MAPPINGS = {
    'String': 'String',
    'Int': 'Int',
    'Double': 'Double',
    'Float': 'Float',
    'Bool': 'Boolean',
    '[String]': 'List<String>',
    '[Int]': 'List<Int>',
    'Date': 'LocalDateTime',
    'UUID': 'String',
    'Data': 'ByteArray',
    'Optional<String>': 'String?',
    'Optional<Int>': 'Int?',
    'Optional<Bool>': 'Boolean?',
    'Any': 'Any',
    'AnyObject': 'Any',
    'Void': 'Unit'
}

DEFAULT_IMPORTS = """
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.tooling.preview.Preview
import androidx.navigation.NavController
import androidx.navigation.compose.rememberNavController
import java.time.LocalDateTime
""".strip()

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
    parser.add_argument('--package-name', type=str, default="com.company.amap",
                        help='Android アプリのパッケージ名 (デフォルト: com.company.amap)')
    parser.add_argument('--app-name', type=str, default="MyApp",
                        help='アプリケーション名 (デフォルト: MyApp)')
    parser.add_argument('--clean', action='store_true',
                        help='出力先ディレクトリを事前にクリアする')

    args = parser.parse_args()
    # パッケージ名を固定値から引数で受け取った値に変更
    return args

def setup_project_structure(args):
    """プロジェクト構造をセットアップします"""
    print(f"プロジェクト構造をセットアップしています...")

    # build.gradle の namespace を設定
    build_gradle_path = os.path.join(args.output_dir, 'app/build.gradle')
    if os.path.exists(build_gradle_path):
        with open(build_gradle_path, 'r') as f:
            content = f.read()

        # namespace を設定
        content = re.sub(
            r'namespace ["\'].*["\']',
            f'namespace "{args.package_name}"',
            content
        )

        with open(build_gradle_path, 'w') as f:
            f.write(content)

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

def convert_views(from_dir: str, package_dir: str, project_info: Dict[str, Any], package_name: str):
    """SwiftUIビューをJetpack Composeに変換します"""
    print("ビューを変換しています...")

    # R クラスのインポートを追加
    r_import = f"import {package_name}.R\n"

    for view_file in project_info.get('views', []):
        try:
            swift_path = os.path.join(from_dir, view_file)
            if not os.path.exists(swift_path):
                print(f"警告: ファイルが見つかりません: {swift_path}")
                continue

            # SwiftUIファイルを読み込む
            with open(swift_path, 'r', encoding='utf-8') as f:
                swift_content = f.read()

            # ファイル名からKotlinファイル名を生成
            kotlin_file_name = os.path.basename(view_file).replace('.swift', '.kt')
            if '/Views/' in view_file:
                relative_path = 'ui/components'
            elif '/Screens/' in view_file or '/Features/' in view_file:
                relative_path = 'ui/screens'
            else:
                relative_path = 'ui/components'

            kotlin_dir = os.path.join(package_dir, relative_path)
            os.makedirs(kotlin_dir, exist_ok=True)
            kotlin_path = os.path.join(kotlin_dir, kotlin_file_name)

            # パッケージ名を生成 - 固定値ではなく引数から取得
            package_path = f"{package_name}.{relative_path.replace('/', '.')}"

            # R クラスのインポートを追加
            kotlin_content = r_import + convert_swiftui_to_compose(swift_content, package_path)

            # 変換されたコードを保存
            with open(kotlin_path, 'w', encoding='utf-8') as f:
                f.write(kotlin_content)

            print(f"変換完了: {view_file} -> {kotlin_path}")
        except Exception as e:
            print(f"警告: {view_file}の変換中にエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()

def convert_swiftui_to_compose(swift_content: str, package_name: str) -> str:
    """SwiftUIコードをJetpack Composeコードに変換します"""
    try:
        # コメントを削除
        swift_content = remove_comments(swift_content)

        # パッケージ宣言とインポート文を生成 - 常に com.example.app を使用
        kotlin_content = f"""package {package_name}

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.tooling.preview.Preview
import androidx.navigation.NavController
import androidx.navigation.compose.rememberNavController
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.app.R

"""
        # struct定義を検出
        struct_matches = re.finditer(r'struct\s+(\w+)(?::\s*View)?\s*{([^}]+)}', swift_content)

        for struct_match in struct_matches:
            struct_name = struct_match.group(1)
            struct_body = struct_match.group(2)

            # プロパティを抽出
            properties = extract_properties(struct_body)

            # State宣言を生成
            state_declarations = convert_properties_to_state(properties)

            # body部分を抽出して変換
            body_content = extract_and_convert_body(struct_body)

            # Composable関数を生成
            kotlin_content += f"""
@Composable
fun {struct_name}(
    modifier: Modifier = Modifier,
    navController: NavController = rememberNavController()
) {{
    {state_declarations}

    Surface(
        modifier = modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background
    ) {{
        {body_content}
    }}
}}

@Preview(showBackground = true)
@Composable
private fun {struct_name}Preview() {{
    {struct_name}()
}}
"""

        return kotlin_content.strip()
    except Exception as e:
        print(f"警告: SwiftUIコードの変換中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return ""

def extract_properties(content: str) -> List[Dict[str, str]]:
    """プロパティを抽出します"""
    properties = []

    # @State, @Binding, @Published などのプロパティを検出
    property_patterns = [
        (r'@State\s+(?:private\s+)?var\s+(\w+)\s*:\s*([^=\n]+)(?:\s*=\s*([^\n]+))?', 'State'),
        (r'@Binding\s+var\s+(\w+)\s*:\s*([^=\n]+)(?:\s*=\s*([^\n]+))?', 'Binding'),
        (r'@Published\s+var\s+(\w+)\s*:\s*([^=\n]+)(?:\s*=\s*([^\n]+))?', 'Published'),
    ]

    for pattern, prop_type in property_patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            default_value = None
            if match.group(3):
                default_value = match.group(3)

            properties.append({
                'name': match.group(1),
                'type': match.group(2),
                'default': default_value,
                'property_type': prop_type
            })

    return properties

def convert_properties_to_state(properties: List[Dict[str, str]]) -> str:
    """プロパティをComposeのStateに変換します"""
    state_declarations = []

    for prop in properties:
        kotlin_type = convert_type(prop['type'])
        if prop['default']:
            default_value = prop['default']
        else:
            default_value = get_default_value(kotlin_type)

        if prop['property_type'] == 'State':
            state_declarations.append(
                f"var {prop['name']} by remember {{ mutableStateOf<{kotlin_type}>({default_value}) }}"
            )
        elif prop['property_type'] == 'Binding':
            state_declarations.append(
                f"var {prop['name']}: MutableState<{kotlin_type}> = remember {{ mutableStateOf({default_value}) }}"
            )

    return "\n    ".join(state_declarations)

def get_default_value(kotlin_type: str) -> str:
    """型のデフォルト値を返します"""
    defaults = {
        'String': '""',
        'Int': '0',
        'Long': '0L',
        'Float': '0f',
        'Double': '0.0',
        'Boolean': 'false',
        'List<*>': 'emptyList()',
        'Set<*>': 'emptySet()',
        'Map<*,*>': 'emptyMap()',
    }

    for type_pattern, default in defaults.items():
        if '*' in type_pattern:
            pattern = type_pattern.replace('*', r'[^>]+')
            if re.match(pattern, kotlin_type):
                return default
        elif kotlin_type == type_pattern:
            return default

    return "null"

def extract_and_convert_body(body_content: str) -> str:
    """body部分を抽出して変換します"""
    # var body: some View { ... } を検出
    body_match = re.search(r'var\s+body\s*:\s*some\s+View\s*{([^}]+)}', body_content)
    if body_match:
        body_content = body_match.group(1)

    # レイアウト構造を変換
    body_content = convert_layout_structure(body_content)

    # モディファイアを変換
    body_content = convert_modifiers(body_content)

    # 条件付きビューを変換
    body_content = convert_conditional_views(body_content)

    return body_content.strip()

def convert_layout_structure(content: str) -> str:
    """レイアウト構造を変換します"""
    try:
        # 基本的なレイアウトの変換
        layout_patterns = {
            r'VStack\s*(?:\([^)]*\))?\s*{([^}]+)}': 'Column',
            r'HStack\s*(?:\([^)]*\))?\s*{([^}]+)}': 'Row',
            r'ZStack\s*(?:\([^)]*\))?\s*{([^}]+)}': 'Box',
            r'ScrollView\s*(?:\([^)]*\))?\s*{([^}]+)}': 'LazyColumn',
            r'List\s*{([^}]+)}': 'LazyColumn',
        }

        for pattern, compose_widget in layout_patterns.items():
            content = re.sub(
                pattern,
                lambda m: f'{compose_widget}(modifier = Modifier.fillMaxWidth()) {{\n{convert_layout_content(m.group(1))}\n}}',
                content
            )

        # ForEachの変換
        content = re.sub(
            r'ForEach\s*\(([^)]+)\)\s*{([^}]+)}',
            lambda m: convert_foreach(m.group(1), m.group(2)),
            content
        )

        return content
    except Exception as e:
        print(f"警告: レイアウト構造の変換中にエラーが発生しました: {e}")
        return content

def convert_layout_content(content: str) -> str:
    """レイアウトの内容を変換します"""
    try:
        # 各行を処理
        lines = []
        for line in content.split('\n'):
            line = line.strip()
            if line:
                # コンポーネントを変換
                line = convert_components(line)
                lines.append(line)

        return '\n'.join(lines)
    except Exception as e:
        print(f"警告: レイアウトコンテンツの変換中にエラーが発生しました: {e}")
        return content

def convert_foreach(items: str, content: str) -> str:
    """ForEachを変換します"""
    try:
        # パラメータを解析
        params_match = re.search(r'([^,]+)(?:,\s*id:\s*\\\.(\w+))?', items)
        if not params_match:
            return f'// TODO: Convert ForEach: {items}'

        collection = params_match.group(1).strip()
        id_param = params_match.group(2)

        # items関数に変換
        if id_param:
            return f'''items({collection}, key = {{ it.{id_param} }}) {{ item ->
    {convert_layout_content(content)}
}}'''
        else:
            return f'''items({collection}) {{ item ->
    {convert_layout_content(content)}
}}'''
    except Exception as e:
        print(f"警告: ForEachの変換中にエラーが発生しました: {e}")
        return f'// TODO: Convert ForEach: {items}'

def generate_compose_imports(package_name: str) -> str:
    """必要なインポート文を生成します"""
    return f"""package com.example.app.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.foundation.Image
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.graphics.Color
import coil.compose.rememberAsyncImagePainter
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import androidx.navigation.compose.rememberNavController
"""

def remove_comments(content: str) -> str:
    """コメントを削除します"""
    import re
    # 単一行コメントを削除
    content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
    # 複数行コメントを削除
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    return content

def convert_components(content: str) -> str:
    """SwiftUIコンポーネントをJetpack Composeコンポーネントに変換します"""
    try:
        # パッケージ宣言とインポートを追加
        if not content.startswith("package"):
            content = add_package_declaration(content)

        # 基本的なコンポーネントの変換
        content = convert_basic_components(content)

        # 特殊なコンポーネントの変換
        content = convert_special_components(content)

        # イベントハンドラの変換
        content = convert_event_handlers(content)

        # トップレベル関数の変換
        content = convert_top_level_functions(content)

        return content.strip()
    except Exception as e:
        print(f"警告: コンポーネントの変換中にエラーが発生しました: {e}")
        return content

def add_package_declaration(content: str) -> str:
    """パッケージ宣言とインポートを追加します"""
    package_decl = """package com.example.app.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import androidx.navigation.compose.rememberNavController
"""
    return package_decl + "\n" + content

def convert_top_level_functions(content: str) -> str:
    """トップレベル関数を変換します"""
    try:
        # struct定義をComposable関数に変換
        content = re.sub(
            r'struct\s+(\w+)(?::\s*View)?\s*{([^}]+)}',
            lambda m: convert_struct_to_composable(m.group(1), m.group(2)),
            content
        )

        # プロパティをStateに変換
        content = re.sub(
            r'@State\s+(?:private\s+)?var\s+(\w+)\s*:\s*([^=\n]+)(?:\s*=\s*([^\n]+))?',
            lambda m: convert_state_property(m.group(1), m.group(2), m.group(3)),
            content
        )

        return content
    except Exception as e:
        print(f"警告: トップレベル関数の変換中にエラーが発生しました: {e}")
        return content

def convert_struct_to_composable(name: str, body: str) -> str:
    """struct定義をComposable関数に変換します"""
    try:
        # body部分を解析して必要な変数を抽出
        state_vars = extract_state_variables(body)
        view_content = extract_view_content(body)

        return f"""
@Composable
fun {name}(
    modifier: Modifier = Modifier,
    navController: NavController = rememberNavController()
) {{
    {state_vars}

    Surface(
        modifier = modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background
    ) {{
        {view_content}
    }}
}}

@Preview(showBackground = true)
@Composable
private fun {name}Preview() {{
    {name}()
}}
"""
    except Exception as e:
        print(f"警告: struct定義の変換中にエラーが発生しました: {e}")
        return f"// TODO: Convert struct {name}"

def extract_state_variables(body: str) -> str:
    """State変数を抽出します"""
    state_vars = []
    state_pattern = r'@State\s+(?:private\s+)?var\s+(\w+)\s*:\s*([^=\n]+)(?:\s*=\s*([^\n]+))?'

    for match in re.finditer(state_pattern, body):
        name = match.group(1)
        type_name = convert_type(match.group(2))
        if match.group(3):
            default_value = match.group(3)
        else:
            default_value = get_default_value(type_name)

        state_vars.append(
            f"var {name} by remember {{ mutableStateOf<{type_name}>({default_value}) }}"
        )

    return "\n    ".join(state_vars)

def extract_view_content(body: str) -> str:
    """View部分を抽出して変換します"""
    try:
        # var body: some View { ... } を検出
        body_match = re.search(r'var\s+body\s*:\s*some\s+View\s*{([^}]+)}', body)
        if body_match:
            content = body_match.group(1)

            # レイアウト構造を変換
            content = convert_layout_structure(content)

            # モディファイアを変換
            content = convert_modifiers(content)

            return content.strip()
        return ""
    except Exception as e:
        print(f"警告: View部分の抽出中にエラーが発生しました: {e}")
        return ""

def convert_state_property(name: str, type_name: str, default_value: str = None) -> str:
    """State プロパティを変換します"""
    kotlin_type = convert_type(type_name)
    if default_value:
        default = default_value
    else:
        default = get_default_value(kotlin_type)
    return f"var {name} by remember {{ mutableStateOf<{kotlin_type}>({default}) }}"

def convert_basic_components(content: str) -> str:
    """基本的なコンポーネントを変換します"""
    try:
        # Text
        content = re.sub(
            r'Text\s*\("([^"]+)"\)',
            lambda m: f'Text(text = "{m.group(1)}")',
            content
        )

        # Button
        content = re.sub(
            r'Button\s*\(action:\s*{\s*([^}]+)\s*}\)\s*{\s*([^}]+)\s*}',
            lambda m: f'''Button(
                onClick = {{ {m.group(1).strip()} }},
                modifier = Modifier.fillMaxWidth()
            ) {{
                {convert_components(m.group(2))}
            }}''',
            content
        )

        # TextField
        content = re.sub(
            r'TextField\s*\("([^"]+)",\s*text:\s*\$(\w+)\)',
            lambda m: f'''OutlinedTextField(
                value = {m.group(2)},
                onValueChange = {{ {m.group(2)} = it }},
                label = {{ Text(text = "{m.group(1)}") }},
                modifier = Modifier.fillMaxWidth()
            )''',
            content
        )

        # Image - 文字列のlower()メソッドを使用
        content = re.sub(
            r'Image\s*\("([^"]+)"\)',
            lambda m: f'Image(painter = painterResource(id = R.drawable.{m.group(1).lower()}), contentDescription = null)',
            content
        )

        return content
    except Exception as e:
        print(f"警告: 基本コンポーネントの変換中にエラーが発生しました: {e}")
        return content

def convert_special_components(content: str) -> str:
    """特殊なコンポーネントを変換します"""
    try:
        # NavigationLink
        content = re.sub(
            r'NavigationLink\s*\(destination:\s*([^)]+)\)\s*{\s*([^}]+)\s*}',
            lambda m: convert_navigation_link(m.group(1), m.group(2)),
            content
        )

        # Alert
        content = re.sub(
            r'\.alert\s*\(isPresented:\s*\$([^)]+)\)\s*{\s*([^}]+)\s*}',
            lambda m: convert_alert(m.group(1), m.group(2)),
            content
        )

        # Sheet
        content = re.sub(
            r'\.sheet\s*\(isPresented:\s*\$([^)]+)\)\s*{\s*([^}]+)\s*}',
            lambda m: convert_sheet(m.group(1), m.group(2)),
            content
        )

        return content
    except Exception as e:
        print(f"警告: 特殊コンポーネントの変換中にエラーが発生しました: {e}")
        return content

def convert_navigation_link(destination: str) -> str:
    """NavigationLinkを変換します"""
    try:
        # 単純な変換として、destinationをそのまま使用
        route = destination.strip()
        # クォートを削除
        if route.startswith('"') and route.endswith('"'):
            route = route[1:-1]
        # 括弧を削除
        if route.endswith("()"):
            route = route[:-2]
        # 小文字に変換して最初の文字を小文字に
        route = route.lower()

        return f'''TextButton(
            onClick = {{ navController.navigate("{route}") }},
            modifier = Modifier.fillMaxWidth()
        ) {{
            {convert_layout_content(destination)}
        }}'''
    except Exception as e:
        print(f"警告: NavigationLinkの変換中にエラーが発生しました: {e}")
        return f'// TODO: Convert NavigationLink: {destination}'

def convert_alert(binding: str, content: str) -> str:
    """アラートを変換します"""
    try:
        title = re.search(r'Text\s*\("([^"]+)"\)', content)
        message = re.search(r'message:\s*"([^"]+)"', content)

        title_text = "Alert"
        if title:
            title_text = title.group(1)

        message_text = ""
        if message:
            message_text = message.group(1)

        return f'''if ({binding}) {{
            AlertDialog(
                onDismissRequest = {{ {binding} = false }},
                title = {{ Text(text = "{title_text}") }},
                text = {{ Text(text = "{message_text}") }},
                confirmButton = {{
                    TextButton(onClick = {{ {binding} = false }}) {{
                        Text(text = "OK")
                    }}
                }}
            )
        }}'''
    except Exception as e:
        print(f"警告: Alertの変換中にエラーが発生しました: {e}")
        return f'// TODO: Convert Alert: {binding}'

def convert_sheet(binding: str, content: str) -> str:
    """シートを変換します"""
    try:
        return f'''if ({binding}) {{
            ModalBottomSheet(
                onDismissRequest = {{ {binding} = false }},
                sheetState = rememberModalBottomSheetState()
            ) {{
                {convert_layout_content(content)}
            }}
        }}'''
    except Exception as e:
        print(f"警告: Sheetの変換中にエラーが発生しました: {e}")
        return f'// TODO: Convert Sheet: {binding}'

def convert_event_handlers(content: str) -> str:
    """イベントハンドラを変換します"""
    try:
        # onTapGesture
        content = re.sub(
            r'\.onTapGesture\s*{\s*([^}]+)\s*}',
            lambda m: f'.clickable {{ {m.group(1).strip()} }}',
            content
        )

        # onAppear
        content = re.sub(
            r'\.onAppear\s*{\s*([^}]+)\s*}',
            lambda m: f'''LaunchedEffect(Unit) {{
                {m.group(1).strip()}
            }}''',
            content
        )

        # onChange
        content = re.sub(
            r'\.onChange\s*\(of:\s*([^)]+)\)\s*{\s*([^}]+)\s*}',
            lambda m: f'''LaunchedEffect({m.group(1)}) {{
                {m.group(2).strip()}
            }}''',
            content
        )

        return content
    except Exception as e:
        print(f"警告: イベントハンドラの変換中にエラーが発生しました: {e}")
        return content

def convert_system_icon(icon_name: str) -> str:
    """システムアイコンを変換します"""
    icon_mapping = {
        'house': 'Home',
        'gear': 'Settings',
        'person': 'Person',
        'bell': 'Notifications',
        'star': 'Star',
        'heart': 'Favorite',
        'magnifyingglass': 'Search',
        'plus': 'Add',
        'minus': 'Remove',
        'checkmark': 'Check',
        'xmark': 'Close',
        'trash': 'Delete',
        'folder': 'Folder',
        'doc': 'Description',
        'pencil': 'Edit',
        'arrow.left': 'ArrowBack',
        'arrow.right': 'ArrowForward',
        'arrow.up': 'ArrowUpward',
        'arrow.down': 'ArrowDownward',
        'calendar': 'DateRange',
        'clock': 'Schedule',
        'location': 'LocationOn',
        'camera': 'Camera',
        'photo': 'Photo',
        'mic': 'Mic',
        'video': 'Videocam',
        'speaker': 'VolumeUp',
        'message': 'Message',
        'mail': 'Email',
        'phone': 'Phone',
        'wifi': 'Wifi',
        'bluetooth': 'Bluetooth',
        'battery': 'BatteryFull',
        'airplane': 'AirplanemodeActive',
        'cart': 'ShoppingCart',
        'tag': 'LocalOffer',
        'flag': 'Flag',
        'bookmark': 'Bookmark',
        'link': 'Link',
        'cloud': 'Cloud',
        'download': 'Download',
        'upload': 'Upload',
        'refresh': 'Refresh',
        'share': 'Share',
        'info': 'Info',
        'warning': 'Warning',
        'error': 'Error',
        'question': 'Help',
        'lock': 'Lock',
        'unlock': 'LockOpen',
        'key': 'VpnKey',
        'shield': 'Security',
    }

    return icon_mapping.get(icon_name, 'Default')

def convert_type(swift_type: str) -> str:
    """Swiftの型をKotlinの型に変換します"""
    return SWIFT_TO_KOTLIN_TYPE_MAPPINGS.get(swift_type.strip(), 'Any')

def setup_database(output_dir: str, package_dir: str, project_info: Dict[str, Any], package_name: str):
    """データベースをセットアップします"""
    try:
        # SQLDelightのディレクトリを作成
        sqldelight_dir = os.path.join(output_dir, 'app/src/main/sqldelight')
        database_dir = os.path.join(sqldelight_dir, package_name.split('.')[-1] + 'Database')
        ensure_directory(database_dir)

        # 重複を避けるため、既存のデータベースファイルを削除
        if os.path.exists(database_dir):
            shutil.rmtree(database_dir)

        # データベースのセットアップ
        tables = {
            'EditView': ('id TEXT PRIMARY KEY NOT NULL', 'data TEXT NOT NULL'),
            'SubscriptionView': ('id TEXT PRIMARY KEY NOT NULL', 'data TEXT NOT NULL'),
            'CalendarView': ('id TEXT PRIMARY KEY NOT NULL', 'data TEXT NOT NULL'),
            'HomeView': ('id TEXT PRIMARY KEY NOT NULL', 'data TEXT NOT NULL'),
            'WorkoutItem': ('id TEXT PRIMARY KEY NOT NULL', 'data TEXT NOT NULL'),
            'StatsView': ('id TEXT PRIMARY KEY NOT NULL', 'data TEXT NOT NULL'),
            'Encouragement': ('id TEXT PRIMARY KEY NOT NULL', 'data TEXT NOT NULL'),
            'Calendar': ('id TEXT PRIMARY KEY NOT NULL', 'data TEXT NOT NULL'),
            'AppTabView': ('id TEXT PRIMARY KEY NOT NULL', 'data TEXT NOT NULL'),
            'SwiftUICode': ('id TEXT PRIMARY KEY NOT NULL', 'data TEXT NOT NULL'),
            'Translation': ('id TEXT PRIMARY KEY NOT NULL', 'data TEXT NOT NULL'),
            'AppUpdateView': ('id TEXT PRIMARY KEY NOT NULL', 'data TEXT NOT NULL'),
            'EncouragementView': ('id TEXT PRIMARY KEY NOT NULL', 'data TEXT NOT NULL'),
            'Settings': ('id TEXT PRIMARY KEY NOT NULL', 'data TEXT NOT NULL'),
            'WorkoutType': ('id TEXT PRIMARY KEY NOT NULL', 'data TEXT NOT NULL'),
            'SwiftUICodeView': ('id TEXT PRIMARY KEY NOT NULL', 'data TEXT NOT NULL'),
            'SettingsView': ('id TEXT PRIMARY KEY NOT NULL', 'data TEXT NOT NULL')
        }

        # 各テーブルのSQLファイルを生成
        for table_name, columns in tables.items():
            sql_file = os.path.join(database_dir, f'{table_name}.sq')
            column_definitions = ',\n    '.join(columns)
            sql_content = (
                f"-- {table_name}.sq\n"
                f"CREATE TABLE {table_name} (\n"
                f"    {column_definitions},\n"
                f"    created_at INTEGER NOT NULL,\n"
                f"    updated_at INTEGER NOT NULL\n"
                f");\n\n"
                f"selectAll:\n"
                f"SELECT *\n"
                f"FROM {table_name};\n\n"
                f"insertItem:\n"
                f"INSERT INTO {table_name}(id, data, created_at, updated_at)\n"
                f"VALUES (?, ?, ?, ?);\n\n"
                f"updateItem:\n"
                f"UPDATE {table_name}\n"
                f"SET data = ?, updated_at = ?\n"
                f"WHERE id = ?;\n\n"
                f"deleteItem:\n"
                f"DELETE FROM {table_name}\n"
                f"WHERE id = ?;\n"
            )
            with open(sql_file, 'w') as f:
                f.write(sql_content)

        # build.gradleにSQLDelightの設定を追加
        build_gradle_path = os.path.join(output_dir, 'app/build.gradle')
        with open(build_gradle_path, 'r') as f:
            content = f.read()

        if 'sqldelight' not in content:
            # SQLDelightプラグインの設定を追加
            content = content.replace(
                'plugins {',
                'plugins {\n    id "com.squareup.sqldelight"'
            )

            # SQLDelightの設定を追加
            content += (
                f"\n\nsqldelight {{\n"
                f"    MyAppDatabase {{\n"
                f'        packageName = "{package_name}.data.local"\n'
                f'        sourceFolders = ["sqldelight"]\n'
                f'        schemaOutputDirectory = file("src/main/sqldelight/databases")\n'
                f"    }}\n"
                f"}}\n"
            )
            with open(build_gradle_path, 'w') as f:
                f.write(content)

        print(f"データベースのセットアップが完了しました: {database_dir}")
    except Exception as e:
        print(f"警告: データベースのセットアップ中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

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