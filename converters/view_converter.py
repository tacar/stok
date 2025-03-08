#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SwiftUI のビューを Jetpack Compose のビューに変換するモジュール
"""

import os
import re
from typing import Dict, List, Any

from utils.file_utils import read_file, write_file, get_filename
from utils.parser import parse_swift_file

def convert_views(from_dir: str, package_dir: str, project_info: Dict[str, Any], package_name: str) -> None:
    """
    SwiftUI のビューを Jetpack Compose のビューに変換します。

    Args:
        from_dir: 変換元の iOS プロジェクトディレクトリ
        package_dir: 変換先の Android パッケージディレクトリ
        project_info: プロジェクト情報
        package_name: Android アプリのパッケージ名
    """
    print("ビューを変換しています...")

    screens_dir = os.path.join(package_dir, 'ui/screens')
    components_dir = os.path.join(package_dir, 'ui/components')

    os.makedirs(screens_dir, exist_ok=True)
    os.makedirs(components_dir, exist_ok=True)

    for view_path in project_info['views']:
        full_path = os.path.join(from_dir, view_path)
        if not os.path.exists(full_path):
            print(f"警告: ビューファイルが見つかりません: {full_path}")
            continue

        print(f"ビューを変換しています: {view_path}")

        # Swift ファイルを解析
        swift_content = read_file(full_path)
        view_info = parse_swift_file(swift_content)

        # Jetpack Compose のビューを生成
        kotlin_content = generate_compose_view(view_info, package_name)

        # ファイル名を決定
        filename = get_filename(view_path)
        kotlin_filename = f"{filename}.kt"

        # 画面かコンポーネントかを判断
        if is_screen_view(filename, swift_content):
            output_dir = screens_dir
        else:
            output_dir = components_dir

        # Kotlin ファイルを書き込み
        kotlin_path = os.path.join(output_dir, kotlin_filename)
        write_file(kotlin_path, kotlin_content)

        print(f"ビューを変換しました: {kotlin_path}")

def is_screen_view(filename: str, content: str) -> bool:
    """
    ビューが画面かコンポーネントかを判断します。

    Args:
        filename: ファイル名
        content: ファイルの内容

    Returns:
        画面の場合は True、コンポーネントの場合は False
    """
    # 画面を示す特徴
    screen_indicators = [
        'Screen', 'Page', 'View', 'Activity', 'Fragment',
        'NavigationView', 'TabView', 'NavigationLink',
        '@main', 'App', 'Scene', 'WindowGroup'
    ]

    # コンポーネントを示す特徴
    component_indicators = [
        'Button', 'Text', 'Image', 'List', 'Form', 'Section',
        'TextField', 'Toggle', 'Picker', 'Slider', 'Stepper',
        'ProgressView', 'Label', 'Link', 'Menu', 'Divider'
    ]

    # ファイル名に基づく判断
    for indicator in screen_indicators:
        if indicator in filename:
            return True

    for indicator in component_indicators:
        if indicator in filename and not any(screen in filename for screen in screen_indicators):
            return False

    # 内容に基づく判断
    if 'NavigationView' in content or 'TabView' in content or '@main' in content:
        return True

    # デフォルトでは画面として扱う
    return True

def generate_compose_view(view_info: Dict[str, Any], package_name: str) -> str:
    """
    SwiftUI のビュー情報から Jetpack Compose のビューを生成します。

    Args:
        view_info: SwiftUI ビューの情報
        package_name: Android アプリのパッケージ名

    Returns:
        生成された Jetpack Compose のコード
    """
    class_name = view_info['class_name']

    # 画面かコンポーネントかを判断
    is_screen = is_screen_view(class_name, "")

    # パッケージとインポート
    if is_screen:
        package = f"{package_name}.ui.screens"
    else:
        package = f"{package_name}.ui.components"

    lines = [
        f"package {package}",
        "",
        "import androidx.compose.foundation.layout.*",
        "import androidx.compose.material3.*",
        "import androidx.compose.runtime.*",
        "import androidx.compose.ui.Alignment",
        "import androidx.compose.ui.Modifier",
        "import androidx.compose.ui.unit.dp",
        "import androidx.lifecycle.viewmodel.compose.viewModel",
        f"import {package_name}.viewmodels.*",
        f"import {package_name}.models.*",
        f"import {package_name}.ui.theme.*"
    ]

    # 画面の場合は追加のインポート
    if is_screen:
        lines.extend([
            "import androidx.navigation.NavController",
            "import androidx.navigation.compose.rememberNavController"
        ])

    lines.append("")

    # Composable 関数
    if is_screen:
        lines.append("@Composable")
        lines.append(f"fun {class_name}Screen(")
        lines.append("    navController: NavController = rememberNavController(),")

        # ViewModel があれば追加
        viewmodel_name = f"{class_name}ViewModel"
        lines.append(f"    viewModel: {viewmodel_name} = viewModel()")

        lines.append(") {")
    else:
        lines.append("@Composable")
        lines.append(f"fun {class_name}(")
        lines.append("    modifier: Modifier = Modifier")
        lines.append(") {")

    # 基本的なレイアウト
    lines.extend([
        "    Surface(",
        "        modifier = modifier.fillMaxSize(),",
        "        color = MaterialTheme.colorScheme.background",
        "    ) {",
        "        Column(",
        "            modifier = Modifier",
        "                .fillMaxSize()",
        "                .padding(16.dp),",
        "            horizontalAlignment = Alignment.CenterHorizontally,",
        "            verticalArrangement = Arrangement.Center",
        "        ) {",
        "            // TODO: ここにコンテンツを追加",
        "            Text(text = \"Hello, Compose!\")",
        "        }",
        "    }",
        "}"
    ])

    # プレビュー関数
    lines.extend([
        "",
        "@Preview(showBackground = true)",
        "@Composable",
        f"fun {class_name}Preview() {{",
        f"    AppTheme {{",
        f"        {class_name}()" if not is_screen else f"        {class_name}Screen()",
        f"    }}",
        f"}}"
    ])

    return "\n".join(lines)