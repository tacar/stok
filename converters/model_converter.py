#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Swift のモデルを Kotlin のモデルに変換するモジュール
"""

import os
import re
from typing import Dict, List, Any

from utils.file_utils import read_file, write_file, get_filename
from utils.parser import parse_swift_file, swift_type_to_kotlin

def convert_models(from_dir: str, package_dir: str, project_info: Dict[str, Any], package_name: str) -> None:
    """
    Swift のモデルを Kotlin のモデルに変換します。

    Args:
        from_dir: 変換元の iOS プロジェクトディレクトリ
        package_dir: 変換先の Android パッケージディレクトリ
        project_info: プロジェクト情報
        package_name: Android アプリのパッケージ名
    """
    print("モデルを変換しています...")

    models_dir = os.path.join(package_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)

    for model_path in project_info['models']:
        full_path = os.path.join(from_dir, model_path)
        if not os.path.exists(full_path):
            print(f"警告: モデルファイルが見つかりません: {full_path}")
            continue

        print(f"モデルを変換しています: {model_path}")

        # Swift ファイルを解析
        swift_content = read_file(full_path)
        model_info = parse_swift_file(swift_content)

        # Kotlin モデルを生成
        kotlin_content = generate_kotlin_model(model_info, package_name)

        # ファイル名を決定
        filename = get_filename(model_path)
        if filename.endswith('Model'):
            kotlin_filename = f"{filename}.kt"
        else:
            kotlin_filename = f"{filename}Model.kt"

        # Kotlin ファイルを書き込み
        kotlin_path = os.path.join(models_dir, kotlin_filename)
        write_file(kotlin_path, kotlin_content)

        print(f"モデルを変換しました: {kotlin_path}")

def generate_kotlin_model(model_info: Dict[str, Any], package_name: str) -> str:
    """
    Swift のモデル情報から Kotlin のモデルを生成します。

    Args:
        model_info: Swift モデルの情報
        package_name: Android アプリのパッケージ名

    Returns:
        生成された Kotlin モデルのコード
    """
    class_name = model_info['class_name']

    # ViewModel クラスの場合は特別な処理
    is_viewmodel = class_name.endswith('ViewModel')

    # パッケージとインポート
    if is_viewmodel:
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
            f"import {package_name}.repositories.*",
            "import javax.inject.Inject",
            "import dagger.hilt.android.lifecycle.HiltViewModel"
        ]
    else:
        lines = [
            f"package {package_name}.models",
            "",
            "import kotlinx.serialization.Serializable"
        ]

    # SwiftData を使用している場合は SQLDelight 用のインポートを追加
    if model_info['uses_swiftdata']:
        lines.extend([
            "import app.cash.sqldelight.ColumnAdapter",
            "import kotlinx.serialization.json.Json"
        ])

    lines.append("")

    # クラス定義
    if is_viewmodel:
        # ViewModel クラスの場合
        lines.append("@HiltViewModel")
        lines.append(f"class {class_name} @Inject constructor() : ViewModel() {{")

        # 状態を表す StateFlow
        lines.append("    // 状態")

        # プロパティを追加
        for prop in model_info['properties']:
            prop_name = prop['name']
            swift_type = prop['type']

            # 型を推測
            if "String" in swift_type:
                kotlin_type = "String"
            elif "Int" in swift_type:
                kotlin_type = "Int"
            elif "Bool" in swift_type or "Boolean" in swift_type:
                kotlin_type = "Boolean"
            elif "Float" in swift_type or "Double" in swift_type:
                kotlin_type = "Float"
            elif "Date" in swift_type:
                kotlin_type = "java.util.Date"
            elif "UUID" in swift_type:
                kotlin_type = "java.util.UUID"
            elif "List" in swift_type or "Array" in swift_type:
                kotlin_type = "List<Any>"
            elif "Map" in swift_type or "Dictionary" in swift_type:
                kotlin_type = "Map<String, Any>"
            else:
                kotlin_type = "Any"

            # Published プロパティを StateFlow に変換
            if prop['is_published']:
                lines.extend([
                    f"    private val _{prop_name} = MutableStateFlow<{kotlin_type}>(/* 初期値 */)",
                    f"    val {prop_name}: StateFlow<{kotlin_type}> = _{prop_name}.asStateFlow()",
                    ""
                ])
            else:
                lines.extend([
                    f"    private val _{prop_name} = MutableStateFlow<{kotlin_type}>(/* 初期値 */)",
                    f"    val {prop_name}: StateFlow<{kotlin_type}> = _{prop_name}",
                    ""
                ])

        # 初期化ブロック
        lines.extend([
            "    init {",
            "        // 初期化処理",
            "        loadData()",
            "    }",
            "",
            "    private fun loadData() {",
            "        viewModelScope.launch {",
            "            try {",
            "                // TODO: データの読み込み処理",
            "            } catch (e: Exception) {",
            "                // エラー処理",
            "            }",
            "        }",
            "    }",
            "}"
        ])
    elif model_info['is_struct'] or model_info['is_class']:
        # データクラスの場合
        lines.append("@Serializable")
        lines.append(f"data class {class_name}(")

        # プロパティ
        for i, prop in enumerate(model_info['properties']):
            prop_name = prop['name']
            swift_type = prop['type']

            # 特殊なジェネリック型パターンを処理
            if ":" in swift_type and not "=" in swift_type:
                # List<UUID: Bool> → Map<UUID, Boolean> のような変換
                if swift_type.startswith("List<") and ":" in swift_type:
                    pattern = r'List<(\w+):\s*(\w+)>'
                    match = re.match(pattern, swift_type)
                    if match:
                        key_type = match.group(1)
                        value_type = match.group(2)
                        kotlin_key_type = swift_type_to_kotlin(key_type)
                        kotlin_value_type = swift_type_to_kotlin(value_type)
                        kotlin_type = f"Map<{kotlin_key_type}, {kotlin_value_type}>"
                    else:
                        kotlin_type = swift_type_to_kotlin(swift_type)
                else:
                    # T: Value のような形式を処理
                    pattern = r'(\w+):\s*(\w+)'
                    match = re.match(pattern, swift_type)
                    if match:
                        key_type = match.group(1)
                        value_type = match.group(2)
                        kotlin_key_type = swift_type_to_kotlin(key_type)
                        kotlin_value_type = swift_type_to_kotlin(value_type)
                        kotlin_type = f"Map<{kotlin_key_type}, {kotlin_value_type}>"
                    else:
                        kotlin_type = swift_type_to_kotlin(swift_type)
            # Swift形式の辞書型を処理
            elif "[" in swift_type and ":" in swift_type and "]" in swift_type and not "=" in swift_type:
                # [String: Any]形式を処理
                pattern = r'\[(\w+):\s*(\w+)\]'
                match = re.match(pattern, swift_type)
                if match:
                    key_type = match.group(1)
                    value_type = match.group(2)
                    kotlin_key_type = swift_type_to_kotlin(key_type)
                    kotlin_value_type = swift_type_to_kotlin(value_type)
                    kotlin_type = f"Map<{kotlin_key_type}, {kotlin_value_type}>"
                else:
                    kotlin_type = swift_type_to_kotlin(swift_type)
            else:
                kotlin_type = swift_type_to_kotlin(swift_type)

            # val または var を決定
            val_or_var = "val"

            # デフォルト値があるかどうかを確認
            default_value = ""
            if "=" in swift_type:
                type_parts = swift_type.split("=")
                swift_type = type_parts[0].strip()
                default_value = type_parts[1].strip()
                kotlin_type = swift_type_to_kotlin(swift_type)

                # Swift のデフォルト値を Kotlin のデフォルト値に変換
                if default_value == "[]":
                    default_value = " = emptyList()"
                elif default_value == "{}":
                    default_value = " = emptyMap()"
                elif default_value == "\"\"":
                    default_value = " = \"\""
                elif default_value == "0":
                    default_value = " = 0"
                elif default_value == "false":
                    default_value = " = false"
                elif default_value == "true":
                    default_value = " = true"
                elif default_value == "nil" or default_value == "null":
                    default_value = " = null"
                else:
                    default_value = ""

            # プロパティ行を追加
            comma = "," if i < len(model_info['properties']) - 1 else ""
            lines.append(f"    {val_or_var} {prop_name}: {kotlin_type}{default_value}{comma}")

        lines.append(")")

    # 列挙型の場合
    elif model_info['is_enum']:
        lines.append("@Serializable")
        lines.append(f"enum class {class_name} {{")

        # 列挙型の値を抽出
        enum_pattern = r'case\s+(\w+)(?:\s*=\s*(.+))?'
        enum_matches = re.findall(enum_pattern, swift_content)

        for i, enum_match in enumerate(enum_matches):
            name = enum_match[0]
            value = enum_match[1] if len(enum_match) > 1 else ""

            comma = "," if i < len(enum_matches) - 1 else ""
            if value:
                lines.append(f"    {name.upper()}({value}){comma}")
            else:
                lines.append(f"    {name.upper()}{comma}")

        lines.append("}")

    # SQLDelight 用のアダプターを追加（SwiftData を使用している場合）
    if model_info['uses_swiftdata']:
        lines.extend([
            "",
            f"object {class_name}Adapter {{",
            f"    val adapter = object : ColumnAdapter<{class_name}, String> {{",
            f"        private val json = Json {{ ignoreUnknownKeys = true }}",
            "",
            f"        override fun decode(databaseValue: String): {class_name} {{",
            f"            return json.decodeFromString<{class_name}>(databaseValue)",
            f"        }}",
            "",
            f"        override fun encode(value: {class_name}): String {{",
            f"            return json.encodeToString({class_name}.serializer(), value)",
            f"        }}",
            f"    }}",
            f"}}"
        ])

    return "\n".join(lines)