#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Swift の ViewModel を Kotlin の ViewModel に変換するモジュール
"""

import os
import re
from typing import Dict, List, Any

from utils.file_utils import read_file, write_file, get_filename
from utils.parser import parse_swift_file, swift_type_to_kotlin

def convert_viewmodels(from_dir: str, package_dir: str, project_info: Dict[str, Any], package_name: str) -> None:
    """
    Swift の ViewModel を Kotlin の ViewModel に変換します。

    Args:
        from_dir: 変換元の iOS プロジェクトディレクトリ
        package_dir: 変換先の Android パッケージディレクトリ
        project_info: プロジェクト情報
        package_name: Android アプリのパッケージ名
    """
    print("ViewModel を変換しています...")

    viewmodels_dir = os.path.join(package_dir, 'viewmodels')
    os.makedirs(viewmodels_dir, exist_ok=True)

    for viewmodel_path in project_info['viewmodels']:
        full_path = os.path.join(from_dir, viewmodel_path)
        if not os.path.exists(full_path):
            print(f"警告: ViewModel ファイルが見つかりません: {full_path}")
            continue

        print(f"ViewModel を変換しています: {viewmodel_path}")

        # Swift ファイルを解析
        swift_content = read_file(full_path)
        viewmodel_info = parse_swift_file(swift_content)

        # Kotlin ViewModel を生成
        kotlin_content = generate_kotlin_viewmodel(viewmodel_info, package_name, project_info)

        # ファイル名を決定
        filename = get_filename(viewmodel_path)
        kotlin_filename = f"{filename}.kt"

        # Kotlin ファイルを書き込み
        kotlin_path = os.path.join(viewmodels_dir, kotlin_filename)
        write_file(kotlin_path, kotlin_content)

        print(f"ViewModel を変換しました: {kotlin_path}")

def generate_kotlin_viewmodel(viewmodel_info: Dict[str, Any], package_name: str, project_info: Dict[str, Any]) -> str:
    """
    Swift の ViewModel 情報から Kotlin の ViewModel を生成します。

    Args:
        viewmodel_info: Swift ViewModel の情報
        package_name: Android アプリのパッケージ名
        project_info: プロジェクト情報

    Returns:
        生成された Kotlin ViewModel のコード
    """
    class_name = viewmodel_info['class_name']

    # パッケージとインポート
    lines = [
        f"package {package_name}.viewmodels",
        "",
        "import androidx.lifecycle.ViewModel",
        "import androidx.lifecycle.viewModelScope",
        "import kotlinx.coroutines.flow.MutableStateFlow",
        "import kotlinx.coroutines.flow.StateFlow",
        "import kotlinx.coroutines.flow.asStateFlow",
        "import kotlinx.coroutines.launch",
        f"import {package_name}.models.*",
        f"import {package_name}.repositories.*"
    ]

    # Firebase を使用している場合
    if viewmodel_info['uses_firebase'] or project_info['uses_firebase']:
        lines.append("import com.google.firebase.auth.FirebaseAuth")

    # リポジトリの依存関係を追加
    repository_name = None
    for prop in viewmodel_info['properties']:
        prop_type = prop['type']
        if 'Repository' in prop_type:
            repository_name = prop_type.replace('?', '').strip()
            break

    lines.append("")

    # クラス定義
    lines.append(f"class {class_name}(")

    # リポジトリの依存関係がある場合は追加
    if repository_name:
        lines.append(f"    private val repository: {repository_name}")

    lines.append(") : ViewModel() {")

    # 状態を表す StateFlow
    lines.append("    // 状態")

    # Published プロパティを StateFlow に変換
    state_properties = []
    for prop in viewmodel_info['properties']:
        if prop['is_published']:
            prop_name = prop['name']
            prop_type = swift_type_to_kotlin(prop['type'].replace('@Published', '').strip())
            state_properties.append((prop_name, prop_type))

    if state_properties:
        for prop_name, prop_type in state_properties:
            lines.extend([
                f"    private val _{prop_name} = MutableStateFlow<{prop_type}>(/* 初期値 */)",
                f"    val {prop_name}: StateFlow<{prop_type}> = _{prop_name}.asStateFlow()",
                ""
            ])
    else:
        # デフォルトの状態
        lines.extend([
            "    private val _uiState = MutableStateFlow(UiState())",
            "    val uiState: StateFlow<UiState> = _uiState.asStateFlow()",
            "",
            "    data class UiState(",
            "        val isLoading: Boolean = false,",
            "        val errorMessage: String? = null",
            "    )",
            ""
        ])

    # 初期化ブロック
    lines.extend([
        "    init {",
        "        // 初期化処理",
        "        loadData()",
        "    }",
        ""
    ])

    # メソッド
    lines.append("    // メソッド")

    # Swift のメソッドを Kotlin のメソッドに変換
    for method in viewmodel_info['methods']:
        method_name = method['name']

        # 特定のメソッド名は無視
        if method_name in ['init', 'deinit']:
            continue

        lines.append(f"    fun {method_name}() {{")
        lines.append("        viewModelScope.launch {")
        lines.append("            try {")
        lines.append("                // TODO: 実装")
        lines.append("            } catch (e: Exception) {")
        lines.append("                // エラー処理")
        lines.append("            }")
        lines.append("        }")
        lines.append("    }")
        lines.append("")

    # デフォルトのデータ読み込みメソッド
    if not any(method['name'] == 'loadData' for method in viewmodel_info['methods']):
        lines.extend([
            "    private fun loadData() {",
            "        viewModelScope.launch {",
            "            try {",
            "                // TODO: データの読み込み処理",
            "            } catch (e: Exception) {",
            "                // エラー処理",
            "            }",
            "        }",
            "    }"
        ])

    lines.append("}")

    return "\n".join(lines)