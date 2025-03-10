#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SwiftUI のビューを Jetpack Compose のビューに変換するモジュール
"""

import os
import re
from typing import Dict, List, Any, Optional

from utils.file_utils import read_file, write_file, get_filename
from utils.parser import parse_swift_file

class ViewConverter:
    def __init__(self, package_name: str):
        self.package_name = package_name

    def convert_views(self, swift_content: str, view_name: str) -> str:
        """SwiftUIビューをJetpack Composeに変換します"""
        return f"""
package {self.package_name}

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel

@Composable
fun {view_name}(
    modifier: Modifier = Modifier,
    viewModel: {view_name}ViewModel = viewModel()
) {{
    {self._extract_state_variables(swift_content)}

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {{
        {self._convert_view_body(swift_content)}
    }}
}}

@Preview(showBackground = true)
@Composable
private fun {view_name}Preview() {{
    {view_name}()
}}
""".strip()

    def _extract_state_variables(self, content: str) -> str:
        """@Stateプロパティを抽出してKotlinのState変数に変換します"""
        state_vars = []
        for match in re.finditer(r'@State\s+(?:private\s+)?var\s+(\w+)\s*:\s*([^=\n]+)(?:\s*=\s*([^\n]+))?', content):
            name = match.group(1)
            type_name = match.group(2).strip()
            default_value = match.group(3).strip() if match.group(3) else None

            kotlin_type = self._convert_type(type_name)
            kotlin_default = self._convert_default_value(default_value, kotlin_type)

            state_vars.append(f"var {name} by remember {{ mutableStateOf{kotlin_default} }}")

        return "\n    ".join(state_vars)

    def _convert_view_body(self, content: str) -> str:
        """ビューの本体部分を変換します"""
        # Text の変換
        content = re.sub(
            r'Text\("([^"]+)"\)',
            r'Text(text = "\1")',
            content
        )

        # Button の変換
        content = re.sub(
            r'Button\(action:\s*{\s*([^}]+)\s*}\)\s*{\s*Text\("([^"]+)"\)\s*}',
            r'Button(onClick = { \1 }) { Text(text = "\2") }',
            content
        )

        # TextField の変換
        content = re.sub(
            r'TextField\("([^"]+)",\s*text:\s*\$(\w+)\)',
            r'OutlinedTextField(value = \2, onValueChange = { \2 = it }, label = { Text("\1") })',
            content
        )

        return content

    def _convert_type(self, swift_type: str) -> str:
        """Swiftの型をKotlinの型に変換します"""
        type_mapping = {
            'String': 'String',
            'Int': 'Int',
            'Double': 'Double',
            'Bool': 'Boolean',
            '[String]': 'List<String>',
            '[Int]': 'List<Int>'
        }
        return type_mapping.get(swift_type.strip(), 'String')

    def _convert_default_value(self, swift_value: Optional[str], kotlin_type: str) -> str:
        """デフォルト値を変換します"""
        if swift_value is None:
            defaults = {
                'String': '("")',
                'Int': '(0)',
                'Boolean': '(false)',
                'Double': '(0.0)',
                'List<String>': '(listOf())',
                'List<Int>': '(listOf())'
            }
            return defaults.get(kotlin_type, '(null)')

        # Swift値をKotlin値に変換
        value = swift_value.strip()
        value = value.replace('true', 'true').replace('false', 'false').replace('nil', 'null')
        return f'({value})'

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

    # インポート文
    imports = [
        "androidx.compose.foundation.layout.*",
        "androidx.compose.material3.*",
        "androidx.compose.runtime.*",
        "androidx.compose.ui.Alignment",
        "androidx.compose.ui.Modifier",
        "androidx.compose.ui.unit.dp",
        "androidx.compose.ui.tooling.preview.Preview",
        "androidx.compose.foundation.Image",
        "androidx.compose.ui.res.painterResource",
        "androidx.compose.ui.text.style.TextAlign",
        "androidx.compose.ui.graphics.Color",
        "coil.compose.rememberAsyncImagePainter",
        "androidx.compose.material.icons.Icons",
        "androidx.compose.material.icons.filled.*",
        "androidx.compose.foundation.lazy.LazyColumn",
        "androidx.compose.foundation.lazy.items",
        "androidx.compose.ui.text.font.FontWeight",
        "androidx.compose.ui.text.font.FontStyle",
        "androidx.compose.foundation.shape.RoundedCornerShape",
        "androidx.lifecycle.viewmodel.compose.viewModel",
        "androidx.compose.foundation.layout.PaddingValues",
        f"{package_name}.viewmodels.*",
        f"{package_name}.models.*",
        f"{package_name}.ui.theme.*",
        f"{package_name}.R",
        "androidx.navigation.NavController",
        "androidx.navigation.compose.rememberNavController"
    ]

    # ViewModel名を生成
    view_model_name = f"{class_name}ViewModel"

    # SwiftUIのコードをJetpack Composeに変換
    compose_body = convert_swiftui_to_compose(body_content)

    # Jetpack Composeのコードを生成
    lines = []

    # パッケージ宣言
    lines.append(f"package {package}")
    lines.append("")

    # インポート文
    for import_stmt in imports:
        lines.append(f"import {import_stmt}")
    lines.append("")

    # メイン関数
    if is_screen:
        screen_name = f"{class_name}Screen"
        lines.extend([
            f"@Composable",
            f"fun {screen_name}(",
            f"    navController: NavController = rememberNavController(),",
            f"    viewModel: {view_model_name} = viewModel()",
            f") {{"
        ])
    else:
        lines.extend([
            f"@Composable",
            f"fun {class_name}(",
            f"    modifier: Modifier = Modifier,",
            f"    viewModel: {view_model_name} = viewModel()",
            f") {{"
        ])

    # Surface
    if is_screen:
        lines.extend([
            "    Surface(",
            "        modifier = Modifier.fillMaxSize(),",
            "        color = MaterialTheme.colorScheme.background",
            "    ) {",
            "        // SwiftUIのビュー構造をJetpack Composeに変換",
            "        MainContent(viewModel)",
            "    }",
            "}",
            ""
        ])
    else:
        lines.extend([
            "    // SwiftUIのビュー構造をJetpack Composeに変換",
            "    Box(modifier = modifier) {",
            "        // TODO: ここにコンポーネントの内容を実装",
            "    }",
            "}",
            ""
        ])

    # MainContent関数（画面の場合のみ）
    if is_screen:
        lines.extend([
            "@Composable",
            f"private fun MainContent(viewModel: {view_model_name}) {{",
            f"{compose_body}",
            "}",
            ""
        ])

    # プレビュー関数
    if is_screen:
        lines.extend([
            "@Preview(showBackground = true)",
            "@Composable",
            f"fun {class_name}Preview() {{",
            "    AppTheme {",
            f"        {screen_name}()",
            "    }",
            "}"
        ])
    else:
        lines.extend([
            "@Preview(showBackground = true)",
            "@Composable",
            f"fun {class_name}Preview() {{",
            "    AppTheme {",
            f"        {class_name}()",
            "    }",
            "}"
        ])

    return '\n'.join(lines)

def convert_swiftui_to_compose(swift_code: str) -> str:
    """
    SwiftUIのコードをJetpack Composeのコードに変換します。

    Args:
        swift_code: SwiftUIのコード

    Returns:
        変換されたJetpack Composeのコード
    """
    # 変換前に不要なSwift構文を削除または置換
    # 1. 型指定を削除（Unexpected type specification）
    swift_code = re.sub(r':\s*\w+\s*=', ' =', swift_code)
    swift_code = re.sub(r':\s*\w+\s*\{', ' {', swift_code)

    # 2. 環境変数を削除
    swift_code = re.sub(r'\.environment\([^)]*\)', '', swift_code)

    # 3. SwiftUIの特殊構文を置換
    swift_code = re.sub(r'TabView\s*\{', '// TabView START\n', swift_code)
    swift_code = re.sub(r'\.tabItem\s*\{', '// Tab Item\n', swift_code)

    # 4. systemImageをIconに変換
    swift_code = re.sub(r'systemImage:\s*"([^"]+)"', r'imageVector = Icons.Default.\1', swift_code)

    # 5. セミコロンを削除
    swift_code = re.sub(r';', '', swift_code)

    # 6. Swift特有の構文を削除
    swift_code = re.sub(r'@State\s+var\s+', 'var ', swift_code)
    swift_code = re.sub(r'@Binding\s+var\s+', 'var ', swift_code)
    swift_code = re.sub(r'@Published\s+var\s+', 'var ', swift_code)
    swift_code = re.sub(r'@ObservedObject\s+var\s+', 'var ', swift_code)
    swift_code = re.sub(r'@EnvironmentObject\s+var\s+', 'var ', swift_code)

    # 7. 型指定を削除
    swift_code = re.sub(r':\s*\w+(\.\w+)*', '', swift_code)

    # 8. 引数ラベルを削除
    swift_code = re.sub(r'(\w+):\s*', '', swift_code)

    # 9. 余分なカンマを削除
    swift_code = re.sub(r',\s*,', ',', swift_code)
    swift_code = re.sub(r',\s*\)', ')', swift_code)

    # 10. 余分な括弧を削除
    swift_code = re.sub(r'\(\s*\)', '()', swift_code)

    # 11. if let構文を変換
    swift_code = re.sub(r'if\s+let\s+(\w+)\s*=\s*([^{]+)\s*\{', r'\2?.let { \1 ->\n', swift_code)

    # 12. 文字列補間の修正
    swift_code = re.sub(r'\\\(([^)]+)\)', r'${\1}', swift_code)

    # 13. 修飾子の連鎖を修正
    # 修飾子の後に直接別の修飾子が続く場合に修正
    swift_code = re.sub(r'(\.\w+\([^)]*\))(\.\w+)', r'\1\n\2', swift_code)

    # 14. 変数参照の修正 - self.を削除
    swift_code = re.sub(r'self\.(\w+)', r'viewModel.\1', swift_code)

    # 15. 空のチェックを修正
    swift_code = re.sub(r'\.isEmpty', '.isEmpty()', swift_code)
    swift_code = re.sub(r'\.empty', '.isEmpty()', swift_code)

    # 16. 空の変数チェックを修正 - 変数名が欠落している場合の対策
    swift_code = re.sub(r'if\s+\(!([^.]+)\.isEmpty\)', r'if (!\1.isEmpty())', swift_code)
    swift_code = re.sub(r'if\s+\(!\.isEmpty\)', r'if (!viewModel.code.isEmpty())', swift_code)
    swift_code = re.sub(r'if\s+\(\.isEmpty\)', r'if (viewModel.code.isEmpty())', swift_code)

    # 17. Box修飾子の括弧不一致を事前に修正
    swift_code = re.sub(r'Box\(modifier\s*=\s*Modifier\.fillMaxWidth\(\)\s*\{', r'Box(modifier = Modifier.fillMaxWidth()) {', swift_code)
    swift_code = re.sub(r'Box\(modifier\s*=\s*([^)]+)\)\s*\{', r'Box(modifier = \1) {', swift_code)

    compose_code = []

    # SwiftUIの主要コンポーネントの変換マッピング
    component_mappings = {
        # テキスト
        r'Text\("([^"]+)"\)': lambda m: f'Text(text = "{m.group(1)}")',
        r'Text\(([^)]+)\)': lambda m: f'Text(text = {m.group(1)})',

        # ボタン
        r'Button\("([^"]+)"\)\s*{\s*([^}]+)\s*}': lambda m: f'Button(onClick = {{ {convert_action(m.group(2))} }}) {{ Text(text = "{m.group(1)}") }}',
        r'Button\(action:\s*{\s*([^}]+)\s*}\)\s*{\s*Text\("([^"]+)"\)\s*}': lambda m: f'Button(onClick = {{ {convert_action(m.group(1))} }}) {{ Text(text = "{m.group(2)}") }}',
        r'Button\(action:\s*{\s*([^}]+)\s*}\)\s*{\s*([^}]+)\s*}': lambda m: f'Button(onClick = {{ {convert_action(m.group(1))} }}) {{ {m.group(2)} }}',
        r'Button\(\)\s*{\s*([^}]+)\s*}': lambda m: f'Button(onClick = {{ /* TODO */ }}) {{ {m.group(1)} }}',

        # 画像
        r'Image\("([^"]+)"\)': lambda m: f'Image(painter = painterResource(id = R.drawable.{m.group(1).replace(".", "_")}), contentDescription = null)',
        r'Image\(systemName:\s*"([^"]+)"\)': lambda m: f'Icon(imageVector = Icons.Default.{map_system_icon(m.group(1))}, contentDescription = null)',

        # レイアウト
        r'VStack(\([^)]*\))?\s*{': 'Column(modifier = Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {',
        r'HStack(\([^)]*\))?\s*{': 'Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {',
        r'ZStack(\([^)]*\))?\s*{': 'Box(modifier = Modifier.fillMaxWidth()) {',

        # TabView関連
        r'// TabView START': 'Scaffold(\n    bottomBar = {\n        BottomNavigation {',
        r'// Tab Item': '            BottomNavigationItem(\n                icon = { Icon(Icons.Default.Home, contentDescription = null) },\n                label = { Text("Home") },\n                selected = false,\n                onClick = { /* TODO */ }\n            )',
        r'Label\(\s*"([^"]+)",\s*imageVector = Icons.Default.([^)]+)\)': lambda m: f'BottomNavigationItem(\n    icon = {{ Icon(Icons.Default.{m.group(2)}, contentDescription = null) }},\n    label = {{ Text("{m.group(1)}") }},\n    selected = false,\n    onClick = {{ /* TODO */ }}\n)',

        # スペーサー
        r'Spacer\(\)': 'Spacer(modifier = Modifier.weight(1f))',
        r'Spacer\(\).frame\(height:\s*(\d+)\)': lambda m: f'Spacer(modifier = Modifier.height({m.group(1)}.dp))',
        r'Spacer\(\).frame\(width:\s*(\d+)\)': lambda m: f'Spacer(modifier = Modifier.width({m.group(1)}.dp))',

        # パディング
        r'\.padding\((\d+)\)': lambda m: f'.padding({m.group(1)}.dp)',
        r'\.padding\(\[\.(\w+), \.(\w+)\], (\d+)\)': lambda m: f'.padding({map_edge_insets(m.group(1), m.group(2), m.group(3))})',
        r'\.padding\(\)': '.padding(8.dp)',
        r'\.padding\(\.(\w+)\)': lambda m: f'.padding(PaddingValues({m.group(1).lower()} = 8.dp))',
        r'\.padding\(\.(\w+), (\d+)\)': lambda m: f'.padding(PaddingValues({m.group(1).lower()} = {m.group(2)}.dp))',

        # フレーム
        r'\.frame\(width:\s*(\d+),\s*height:\s*(\d+)\)': lambda m: f'.size({m.group(1)}.dp, {m.group(2)}.dp)',
        r'\.frame\(width:\s*(\d+)\)': lambda m: f'.width({m.group(1)}.dp)',
        r'\.frame\(height:\s*(\d+)\)': lambda m: f'.height({m.group(1)}.dp)',
        r'\.frame\(\)': '.fillMaxWidth()',
        r'\.frame\(\.infinity\)': '.fillMaxWidth()',
        r'\.frame\(\.infinity, \.(\w+)\)': lambda m: f'.fillMaxWidth().align(Alignment.{m.group(1).capitalize()})',

        # 背景色
        r'\.background\(Color\.(\w+)\)': lambda m: f'.background({map_color(m.group(1))})',
        r'\.background\(([^)]+)\)': '.background(MaterialTheme.colorScheme.surface)',

        # 条件文
        r'if\s+([^{]+)\s*{': lambda m: f'if ({convert_condition(m.group(1))}) {{',
        r'if\s+let\s+(\w+)\s*=\s*([^{]+)\s*{': lambda m: f'{m.group(2)}?.let {{ {m.group(1)} ->',

        # ForEach
        r'ForEach\(([^,]+),\s*id:\s*\\\.self\)\s*{\s*(\w+)\s*in': lambda m: f'items({m.group(1)}) {{ {m.group(2)} ->',
        r'ForEach\(([^)]+)\)\s*{\s*(\w+)\s*in': lambda m: f'items(/* {m.group(1)} */) {{ {m.group(2)} ->',

        # NavigationLink
        r'NavigationLink\(destination:\s*([^)]+)\)\s*{': lambda m: f'Button(onClick = {{ /* Navigate to {m.group(1)} */ }}) {{',
        r'NavigationLink\("([^"]+)",\s*destination:\s*([^)]+)\)': lambda m: f'Button(onClick = {{ /* Navigate to {m.group(2)} */ }}) {{ Text(text = "{m.group(1)}") }}',

        # TextField
        r'TextField\("([^"]+)",\s*text:\s*\$([^)]+)\)': lambda m: f'TextField(value = {m.group(2)}, onValueChange = {{ {m.group(2)} = it }}, label = {{ Text("{m.group(1)}") }})',

        # Toggle
        r'Toggle\("([^"]+)",\s*isOn:\s*\$([^)]+)\)': lambda m: f'Switch(checked = {m.group(2)}, onCheckedChange = {{ {m.group(2)} = it }}, label = {{ Text("{m.group(1)}") }})',

        # Picker
        r'Picker\("([^"]+)",\s*selection:\s*\$([^)]+)\)\s*{': lambda m: f'// Picker for {m.group(1)}, selection: {m.group(2)}\nColumn {{',

        # List
        r'List\s*{': 'LazyColumn {',
        r'List\(([^)]+)\)\s*{': 'LazyColumn { // List of {m.group(1)}',

        # ScrollView
        r'ScrollView\s*{': 'LazyColumn {',
        r'ScrollView\(\.horizontal\)\s*{': 'LazyRow {',
        r'ScrollView\(\.vertical\)\s*{': 'LazyColumn {',

        # Divider
        r'Divider\(\)': 'Divider()',

        # 修飾子
        r'\.foregroundColor\(\.(\w+)\)': lambda m: f'.color({map_color(m.group(1))})',
        r'\.foregroundColor\(([^)]+)\)': '.color(MaterialTheme.colorScheme.onSurface)',
        r'\.font\(\.(\w+)\)': lambda m: f'.style(MaterialTheme.typography.{map_font_style(m.group(1))})',
        r'\.font\(([^)]+)\)': '.style(MaterialTheme.typography.bodyMedium)',
        r'\.bold\(\)': '.fontWeight(FontWeight.Bold)',
        r'\.italic\(\)': '.fontStyle(FontStyle.Italic)',
        r'\.opacity\(([^)]+)\)': lambda m: f'.alpha({m.group(1)}f)',
        r'\.cornerRadius\(([^)]+)\)': lambda m: f'.clip(RoundedCornerShape({m.group(1)}.dp))',
        r'\.shadow\(radius:\s*([^)]+)\)': lambda m: f'.shadow(elevation = {m.group(1)}.dp)',
        r'\.disabled\(([^)]+)\)': lambda m: f'.enabled(!({m.group(1)}))',

        # 環境変数
        r'\.environment\([^)]*\)': '',
        r'\.environmentObject\([^)]*\)': '',

        # バインディング
        r'\$(\w+)': r'\1',

        # スタイル修飾子の連鎖を修正
        r'\.style\(([^)]+)\);?\)': lambda m: f'.style({m.group(1)})',
        r'\.color\(([^)]+)\);?\)': lambda m: f'.color({m.group(1)})',

        # 空のチェック
        r'\.isEmpty\(\)': '.isEmpty()',
        r'\.empty\(\)': '.isEmpty()',
        r'!([^.]+)\.isEmpty\(\)': '!\1.isEmpty()',
        r'!([^.]+)\.empty\(\)': '!\1.isEmpty()',
    }

    # 行ごとに処理
    lines = swift_code.split('\n')
    tab_view_mode = False

    # 括弧のバランスを追跡
    open_braces = 0
    open_parens = 0

    for line in lines:
        # インデントを保持
        indent = len(line) - len(line.lstrip())
        indent_str = ' ' * indent
        line = line.strip()

        # 空行をスキップ
        if not line:
            compose_code.append('')
            continue

        # コメント行はそのまま追加
        if line.startswith('//'):
            if "TabView START" in line:
                tab_view_mode = True
                compose_code.append(indent_str + "Scaffold(")
                compose_code.append(indent_str + "    bottomBar = {")
                compose_code.append(indent_str + "        BottomNavigation {")
                continue
            elif "Tab Item" in line and tab_view_mode:
                compose_code.append(indent_str + "            BottomNavigationItem(")
                compose_code.append(indent_str + "                icon = { Icon(Icons.Default.Home, contentDescription = null) },")
                compose_code.append(indent_str + "                label = { Text(\"Home\") },")
                compose_code.append(indent_str + "                selected = false,")
                compose_code.append(indent_str + "                onClick = { /* TODO */ }")
                compose_code.append(indent_str + "            )")
                continue
            else:
                compose_code.append(indent_str + line)
                continue

        # 各マッピングを適用
        original_line = line
        for pattern, replacement in component_mappings.items():
            if callable(replacement):
                line = re.sub(pattern, replacement, line)
            else:
                line = re.sub(pattern, replacement, line)

        # 変換されなかった行にはコメントを追加
        if line == original_line and not (line == '{' or line == '}' or line.startswith('import') or line.startswith('package')):
            line = f"// TODO: Convert SwiftUI: {line}"

        # セミコロンが残っている場合は削除
        line = line.replace(';', '')

        # 括弧のバランスを追跡
        open_braces += line.count('{') - line.count('}')
        open_parens += line.count('(') - line.count(')')

        # 不正なトークンを修正
        line = line.replace('${(', '${')
        line = line.replace(')}', '}')

        # 修飾子の閉じ括弧が欠落している場合を修正
        if '.padding(PaddingValues(' in line and not line.endswith(')'):
            line += ')'

        # 条件式の修正 - 変数名が欠落している場合
        if 'if (!.isEmpty()' in line:
            line = line.replace('if (!.isEmpty()', 'if (!viewModel.code.isEmpty()')
        elif 'if (.isEmpty()' in line:
            line = line.replace('if (.isEmpty()', 'if (viewModel.code.isEmpty()')
        elif 'if (!viewModel.isEmpty()' in line:
            line = line.replace('if (!viewModel.isEmpty()', 'if (!viewModel.code.isEmpty()')

        # Box修飾子の括弧不一致を修正
        if 'Box(modifier = Modifier.fillMaxWidth() {' in line:
            line = line.replace('Box(modifier = Modifier.fillMaxWidth() {', 'Box(modifier = Modifier.fillMaxWidth()) {')
        elif 'Box(modifier = ' in line and ') {' not in line and '}) {' not in line:
            line = re.sub(r'Box\(modifier\s*=\s*([^{]+)\{', r'Box(modifier = \1) {', line)

        compose_code.append(indent_str + line)

    # TabViewの閉じ括弧を追加
    if tab_view_mode:
        compose_code.append("        }")
        compose_code.append("    }")
        compose_code.append(") { paddingValues ->")
        compose_code.append("    // Content goes here")
        compose_code.append("    Box(modifier = Modifier.padding(paddingValues)) {")
        compose_code.append("        // Main content")
        compose_code.append("        Text(\"Main Content\")")
        compose_code.append("    }")
        compose_code.append("}")

    # 閉じ括弧のバランスを確認して修正
    result = '\n'.join(compose_code)

    # 不適切な構文を修正
    result = result.replace('.style(MaterialTheme.typography.bodyMedium);)', '.style(MaterialTheme.typography.bodyMedium))')
    result = result.replace('.color(Color.Blue)', '.color(Color.Blue)')

    # if let 構文の修正
    result = re.sub(r'if \(let (\w+) = ([^)]+)\) \{', r'\2?.let { \1 ->', result)

    # 文字列補間の修正
    result = re.sub(r'\\(version)', r'${version}', result)
    result = re.sub(r'\\([\w.]+)', r'${\1}', result)

    # 追加の文字列補間修正
    result = re.sub(r'\$\{(\w+)\}\)', r'${\1})', result)
    result = re.sub(r'\$\{([^}]+)\}\)', r'${\1})', result)
    result = re.sub(r'\$\(([^)]+)\)', r'${\1}', result)

    # 修飾子の連鎖を修正
    result = re.sub(r'Image\(([^)]+)\)\s*\n\s*\.style\(([^)]+)\)', r'Text(\1, style = \2)', result)
    result = re.sub(r'Text\(([^)]+)\)\s*\n\s*\.style\(([^)]+)\)', r'Text(\1, style = \2)', result)
    result = re.sub(r'Text\(([^)]+)\)\s*\n\s*\.color\(([^)]+)\)', r'Text(\1, color = \2)', result)

    # 修飾子の連鎖を修正（追加）
    result = re.sub(r'(Text\([^)]+\))\s*\n\s*\.([a-zA-Z]+)\(([^)]+)\)', r'\1.\2(\3)', result)
    result = re.sub(r'(Image\([^)]+\))\s*\n\s*\.([a-zA-Z]+)\(([^)]+)\)', r'\1.\2(\3)', result)
    result = re.sub(r'(Button\([^)]+\))\s*\n\s*\.([a-zA-Z]+)\(([^)]+)\)', r'\1.\2(\3)', result)

    # 修飾子の連鎖を修正（Modifier）
    result = re.sub(r'\.padding\(([^)]+)\)\s*\n\s*\.([a-zA-Z]+)\(([^)]+)\)', r'.padding(\1).\2(\3)', result)
    result = re.sub(r'\.size\(([^)]+)\)\s*\n\s*\.([a-zA-Z]+)\(([^)]+)\)', r'.size(\1).\2(\3)', result)
    result = re.sub(r'\.width\(([^)]+)\)\s*\n\s*\.([a-zA-Z]+)\(([^)]+)\)', r'.width(\1).\2(\3)', result)
    result = re.sub(r'\.height\(([^)]+)\)\s*\n\s*\.([a-zA-Z]+)\(([^)]+)\)', r'.height(\1).\2(\3)', result)
    result = re.sub(r'\.background\(([^)]+)\)\s*\n\s*\.([a-zA-Z]+)\(([^)]+)\)', r'.background(\1).\2(\3)', result)

    # 空のチェックを修正
    result = re.sub(r'\.isEmpty\(\)', '.isEmpty()', result)
    result = re.sub(r'\.empty\(\)', '.isEmpty()', result)
    result = re.sub(r'!([^.]+)\.isEmpty\(\)', '!\1.isEmpty()', result)
    result = re.sub(r'!([^.]+)\.empty\(\)', '!\1.isEmpty()', result)
    result = re.sub(r'if \(([^.]+)\.isEmpty\(\)\)', r'if (\1.isEmpty())', result)
    result = re.sub(r'if \(!([^.]+)\.isEmpty\(\)\)', r'if (!\1.isEmpty())', result)

    # 余分な閉じ括弧を削除
    result = re.sub(r'\}\s*\}\s*\}', '}\n}', result)

    # 連続する閉じ括弧を修正
    result = re.sub(r'\)\)', ')', result)
    result = re.sub(r'\}\}', '}', result)

    # 不完全な括弧のバランスを修正
    if open_braces > 0:
        result += '\n' + '}' * open_braces

    # 括弧のバランスを修正
    if open_parens > close_parens:
        result += ')' * (open_parens - close_parens)

    # 不正なトークンを修正
    result = result.replace('${(', '${')
    result = result.replace(')}', '}')

    return result

def convert_condition(swift_condition: str) -> str:
    """SwiftUIの条件式をKotlinの条件式に変換します"""
    if not swift_condition:
        return "true"

    # 変数名が欠落している場合の対策
    if swift_condition.strip() == '!.isEmpty()':
        return '!viewModel.code.isEmpty()'
    elif swift_condition.strip() == '.isEmpty()':
        return 'viewModel.code.isEmpty()'

    # 三項演算子の変換
    # settings.isJapanese ? "ホーム" : "Home" → if (settings.isJapanese) "ホーム" else "Home"
    ternary_pattern = r'(.+)\s*\?\s*"([^"]+)"\s*:\s*"([^"]+)"'
    ternary_match = re.match(ternary_pattern, swift_condition)
    if ternary_match:
        condition = ternary_match.group(1)
        true_value = ternary_match.group(2)
        false_value = ternary_match.group(3)
        return f'if ({condition}) "{true_value}" else "{false_value}"'

    # 基本的な変換
    kotlin_condition = swift_condition.strip()

    # == nilをnull比較に変換
    kotlin_condition = re.sub(r'==\s*nil', '== null', kotlin_condition)

    # != nilをnull比較に変換
    kotlin_condition = re.sub(r'!=\s*nil', '!= null', kotlin_condition)

    # 不正な構文を修正
    kotlin_condition = kotlin_condition.replace('${(', '${')
    kotlin_condition = kotlin_condition.replace(')}', '}')

    # 括弧のバランスを確認
    open_parens = kotlin_condition.count('(')
    close_parens = kotlin_condition.count(')')
    if open_parens > close_parens:
        kotlin_condition += ')' * (open_parens - close_parens)

    return kotlin_condition

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
    # 引数が空の場合は処理しない
    if not edge1 or not edge2 or not value:
        return 'all = 8.dp'

    # 数値以外の値が含まれている場合は修正
    if not value.isdigit():
        try:
            # 数値に変換できるか試みる
            float(value)
        except ValueError:
            # 数値に変換できない場合はデフォルト値を使用
            value = '8'

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

        # 少なくとも1つのパディングがない場合は、デフォルト値を追加
        if not padding_parts:
            padding_parts.append(f'all = {value}.dp')

        return ', '.join(padding_parts)

def convert_action(swift_action: str) -> str:
    """SwiftUIのアクションをJetpack Composeのラムダにマッピングします"""
    # 基本的な変換
    kotlin_action = swift_action.strip()

    # self.method() → viewModel.method()
    kotlin_action = re.sub(r'self\.(\w+)\(\)', r'viewModel.\1()', kotlin_action)

    # isActive.toggle() → isActive = !isActive
    kotlin_action = re.sub(r'(\w+)\.toggle\(\)', r'\1 = !\1', kotlin_action)

    # 文字列補間の修正 (${version}) → ${version}
    kotlin_action = re.sub(r'\$\{(\w+)\}\)', r'${\1}', kotlin_action)

    # 文字列補間の追加修正
    kotlin_action = re.sub(r'\$\{([^}]+)\}\)', r'${\1}', kotlin_action)

    # 不正な文字列補間パターンを修正
    kotlin_action = re.sub(r'\$\(([^)]+)\)', r'${\1}', kotlin_action)

    # Swift文字列補間を修正
    kotlin_action = re.sub(r'\\([^)]+)', r'${\1}', kotlin_action)

    # 括弧のバランスを確認
    open_parens = kotlin_action.count('(')
    close_parens = kotlin_action.count(')')
    if open_parens > close_parens:
        kotlin_action += ')' * (open_parens - close_parens)

    # 中括弧のバランスを確認
    open_braces = kotlin_action.count('{')
    close_braces = kotlin_action.count('}')
    if open_braces > close_braces:
        kotlin_action += '}' * (open_braces - close_braces)

    # 不正なトークンを修正
    kotlin_action = kotlin_action.replace('${(', '${')
    kotlin_action = kotlin_action.replace(')}', '}')

    # 連続する閉じ括弧を修正
    kotlin_action = re.sub(r'\)\)', ')', kotlin_action)

    # 不正な文字列補間を修正
    kotlin_action = re.sub(r'\$\{\s*\$\{', '${', kotlin_action)
    kotlin_action = re.sub(r'\}\s*\}', '}', kotlin_action)

    # 変数参照の修正
    kotlin_action = re.sub(r'(?<!\.)(\b(?:settings|translatedText|workoutTypes|swiftUICode|isJapanese|isForceUpdate|storeVersion)\b)', r'viewModel.\1', kotlin_action)

    # 末尾のセミコロンを削除
    kotlin_action = kotlin_action.rstrip(';')

    return kotlin_action