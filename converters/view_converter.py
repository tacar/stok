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

        # SwiftUIのbodyブロックを抽出
        body_content = extract_body_content(swift_content)

        # Jetpack Compose のビューを生成
        kotlin_content = generate_compose_view(view_info, package_name, body_content)

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

def extract_body_content(swift_content: str) -> str:
    """
    SwiftUIのビューからbodyブロックの内容を抽出します。

    Args:
        swift_content: SwiftUIのコード

    Returns:
        bodyブロックの内容、見つからない場合は空文字列
    """
    # var body: some View { ... } または var body: View { ... } パターンを検索
    body_pattern = r'var\s+body\s*:\s*(?:some\s+)?View\s*\{([\s\S]*?)(?:\n\s*\}|\}$)'
    body_match = re.search(body_pattern, swift_content)

    if body_match:
        # bodyブロックの内容を取得
        body_content = body_match.group(1).strip()
        return body_content

    return ""

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

def generate_compose_view(view_info: Dict[str, Any], package_name: str, body_content: str = "") -> str:
    """
    SwiftUI のビュー情報から Jetpack Compose のビューを生成します。

    Args:
        view_info: SwiftUI ビューの情報
        package_name: Android アプリのパッケージ名
        body_content: SwiftUIのbodyブロックの内容

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
        "import androidx.compose.ui.tooling.preview.Preview",
        "import androidx.compose.foundation.Image",
        "import androidx.compose.ui.res.painterResource",
        "import androidx.compose.ui.text.style.TextAlign",
        "import androidx.compose.ui.graphics.Color",
        "import coil.compose.rememberAsyncImagePainter",
        "import androidx.compose.material.icons.Icons",
        "import androidx.compose.material.icons.filled.*",
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
        "        // SwiftUIのビュー構造をJetpack Composeに変換",
        "        MainContent()",
        "    }",
        "}",
        "",
        "@Composable",
        "private fun MainContent() {"
    ])

    # bodyの内容があれば変換して追加
    if body_content:
        # SwiftUIのコードをJetpack Composeに変換
        compose_content = convert_swiftui_to_compose(body_content)

        # インデントを追加
        compose_lines = compose_content.split('\n')
        indented_compose_lines = ['    ' + line for line in compose_lines]

        lines.extend(indented_compose_lines)
    else:
        # デフォルトのコンテンツ
        lines.extend([
            "    Column(",
            "        modifier = Modifier",
            "            .fillMaxSize()",
            "            .padding(16.dp),",
            "        horizontalAlignment = Alignment.CenterHorizontally,",
            "        verticalArrangement = Arrangement.Center",
            "    ) {",
            "        // TODO: SwiftUIのコードから変換されたコンテンツ",
            "        // 以下は一般的なSwiftUIコンポーネントのJetpack Compose対応例",
            "        ",
            "        // Text(\"Hello, World!\") → Text(text = \"Hello, World!\")",
            "        Text(",
            "            text = \"Hello, Compose!\",",
            "            style = MaterialTheme.typography.headlineMedium",
            "        )",
            "        ",
            "        Spacer(modifier = Modifier.height(16.dp))",
            "        ",
            "        // Button(action: { ... }) { Text(\"Click me\") } →",
            "        // Button(onClick = { ... }) { Text(text = \"Click me\") }",
            "        Button(",
            "            onClick = { /* TODO: アクション */ }",
            "        ) {",
            "            Text(text = \"Click me\")",
            "        }",
            "        ",
            "        Spacer(modifier = Modifier.height(16.dp))",
            "        ",
            "        // Image(\"image_name\") → Image(painter = painterResource(id = R.drawable.image_name), ...)",
            "        // 注意: 画像リソースは手動で追加する必要があります",
            "        // Image(",
            "        //     painter = painterResource(id = R.drawable.placeholder),",
            "        //     contentDescription = \"サンプル画像\",",
            "        //     modifier = Modifier.size(100.dp)",
            "        // )",
            "    }"
        ])

    lines.append("}")

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

def convert_swiftui_to_compose(swift_code: str) -> str:
    """
    SwiftUIのコードをJetpack Composeのコードに変換します。

    Args:
        swift_code: SwiftUIのコード

    Returns:
        変換されたJetpack Composeのコード
    """
    compose_code = []

    # SwiftUIの主要コンポーネントの変換マッピング
    component_mappings = {
        # テキスト
        r'Text\("([^"]+)"\)': lambda m: f'Text(text = "{m.group(1)}")',
        r'Text\("([^"]+)"\)\.font\(\.(\w+)\)': lambda m: f'Text(text = "{m.group(1)}", style = MaterialTheme.typography.{map_font_style(m.group(2))})',
        r'Text\("([^"]+)"\)\.foregroundColor\(\.(\w+)\)': lambda m: f'Text(text = "{m.group(1)}", color = {map_color(m.group(2))})',

        # ボタン
        r'Button\("([^"]+)"\)\s*{\s*([^}]+)\s*}': lambda m: f'Button(onClick = {{ {convert_action(m.group(2))} }}) {{ Text(text = "{m.group(1)}") }}',
        r'Button\(action:\s*{\s*([^}]+)\s*}\)\s*{\s*Text\("([^"]+)"\)\s*}': lambda m: f'Button(onClick = {{ {convert_action(m.group(1))} }}) {{ Text(text = "{m.group(2)}") }}',

        # 画像
        r'Image\("([^"]+)"\)': lambda m: f'Image(painter = painterResource(id = R.drawable.{m.group(1)}), contentDescription = null)',
        r'Image\(systemName:\s*"([^"]+)"\)': lambda m: f'Icon(imageVector = Icons.Default.{map_system_icon(m.group(1))}, contentDescription = null)',

        # レイアウト
        r'VStack(\([^)]*\))?\s*{': 'Column(modifier = Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {',
        r'HStack(\([^)]*\))?\s*{': 'Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {',
        r'ZStack(\([^)]*\))?\s*{': 'Box(modifier = Modifier.fillMaxWidth()) {',

        # スペーサー
        r'Spacer\(\)': 'Spacer(modifier = Modifier.weight(1f))',
        r'Spacer\(\).frame\(height:\s*(\d+)\)': lambda m: f'Spacer(modifier = Modifier.height({m.group(1)}.dp))',
        r'Spacer\(\).frame\(width:\s*(\d+)\)': lambda m: f'Spacer(modifier = Modifier.width({m.group(1)}.dp))',

        # パディング
        r'\.padding\((\d+)\)': lambda m: f'.padding({m.group(1)}.dp)',
        r'\.padding\(\[\.(\w+), \.(\w+)\], (\d+)\)': lambda m: f'.padding({map_edge_insets(m.group(1), m.group(2), m.group(3))})',

        # フレーム
        r'\.frame\(width:\s*(\d+),\s*height:\s*(\d+)\)': lambda m: f'.size({m.group(1)}.dp, {m.group(2)}.dp)',
        r'\.frame\(width:\s*(\d+)\)': lambda m: f'.width({m.group(1)}.dp)',
        r'\.frame\(height:\s*(\d+)\)': lambda m: f'.height({m.group(1)}.dp)',

        # 背景色
        r'\.background\(Color\.(\w+)\)': lambda m: f'.background({map_color(m.group(1))})',
    }

    # 行ごとに処理
    lines = swift_code.split('\n')
    for line in lines:
        # インデントを保持
        indent = len(line) - len(line.lstrip())
        indent_str = ' ' * indent
        line = line.strip()

        # 各マッピングを適用
        for pattern, replacement in component_mappings.items():
            if callable(replacement):
                line = re.sub(pattern, replacement, line)
            else:
                line = re.sub(pattern, replacement, line)

        compose_code.append(indent_str + line)

    return '\n'.join(compose_code)

def map_font_style(swift_font: str) -> str:
    """SwiftUIのフォントスタイルをMaterial3のタイポグラフィスタイルにマッピングします"""
    mapping = {
        'largeTitle': 'displayLarge',
        'title': 'headlineLarge',
        'title2': 'headlineMedium',
        'title3': 'headlineSmall',
        'headline': 'titleLarge',
        'subheadline': 'titleMedium',
        'body': 'bodyLarge',
        'callout': 'bodyMedium',
        'footnote': 'bodySmall',
        'caption': 'labelSmall',
    }
    return mapping.get(swift_font, 'bodyMedium')

def map_color(swift_color: str) -> str:
    """SwiftUIの色をJetpack Composeの色にマッピングします"""
    mapping = {
        'red': 'Color.Red',
        'blue': 'Color.Blue',
        'green': 'Color.Green',
        'yellow': 'Color.Yellow',
        'orange': 'Color.hsl(25f, 1f, 0.5f)',
        'purple': 'Color(0xFF9C27B0)',
        'pink': 'Color(0xFFE91E63)',
        'primary': 'MaterialTheme.colorScheme.primary',
        'secondary': 'MaterialTheme.colorScheme.secondary',
        'black': 'Color.Black',
        'white': 'Color.White',
        'gray': 'Color.Gray',
    }
    return mapping.get(swift_color, 'Color.Black')

def map_system_icon(system_name: str) -> str:
    """SwiftUIのシステムアイコン名をMaterial Iconsにマッピングします"""
    mapping = {
        'person': 'Person',
        'house': 'Home',
        'gear': 'Settings',
        'bell': 'Notifications',
        'star': 'Star',
        'heart': 'Favorite',
        'magnifyingglass': 'Search',
        'plus': 'Add',
        'minus': 'Remove',
        'trash': 'Delete',
        'folder': 'Folder',
        'doc': 'Description',
        'envelope': 'Email',
        'phone': 'Phone',
        'lock': 'Lock',
        'key': 'Key',
    }
    return mapping.get(system_name, 'Info')

def map_edge_insets(edge1: str, edge2: str, value: str) -> str:
    """SwiftUIのエッジインセットをJetpack Composeのパディングにマッピングします"""
    edges = {edge1, edge2}

    if edges == {'top', 'bottom'}:
        return f'vertical = {value}.dp'
    elif edges == {'leading', 'trailing'} or edges == {'left', 'right'}:
        return f'horizontal = {value}.dp'
    else:
        # 個別のエッジを処理
        padding_parts = []
        if 'top' in edges:
            padding_parts.append(f'top = {value}.dp')
        if 'bottom' in edges:
            padding_parts.append(f'bottom = {value}.dp')
        if 'leading' in edges or 'left' in edges:
            padding_parts.append(f'start = {value}.dp')
        if 'trailing' in edges or 'right' in edges:
            padding_parts.append(f'end = {value}.dp')

        return ', '.join(padding_parts)

def convert_action(swift_action: str) -> str:
    """SwiftUIのアクションをJetpack Composeのラムダにマッピングします"""
    # 基本的な変換
    kotlin_action = swift_action.strip()

    # self.method() → viewModel.method()
    kotlin_action = re.sub(r'self\.(\w+)\(\)', r'viewModel.\1()', kotlin_action)

    # isActive.toggle() → isActive = !isActive
    kotlin_action = re.sub(r'(\w+)\.toggle\(\)', r'\1 = !\1', kotlin_action)

    return kotlin_action