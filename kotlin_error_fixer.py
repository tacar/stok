#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import sys
import argparse
from typing import List, Dict, Tuple, Optional

class KotlinErrorFixer:
    """Kotlinのコンパイルエラーを解析して修正するクラス"""

    def __init__(self, verbose: bool = False, file_not_found_callback=None):
        self.verbose = verbose
        self.file_not_found_callback = file_not_found_callback
        # エラーパターンの定義
        self.error_patterns = {
            "unresolved_reference": r"e: file:///(.*?):(\d+):(\d+) Unresolved reference: (.*?)$",
            "type_mismatch": r"e: file:///(.*?):(\d+):(\d+) Type mismatch: inferred type is (.*) but (.*) was expected$",
            "missing_import": r"e: file:///(.*?):(\d+):(\d+) Cannot access class '(.*)'. Check your module classpath$",
            "serializer_not_found": r"e: file:///(.*?):(\d+):(\d+) Serializer has not been found for type '(.*?)'. To use context serializer as fallback, explicitly annotate type or property with @Contextual$",
            "redeclaration": r"e: file:///(.*?):(\d+):(\d+) Redeclaration: (.*?)$",
            "cannot_find_parameter": r"e: file:///(.*?):(\d+):(\d+) Cannot find a parameter with this name: (.*?)$",
            "overrides_nothing": r"e: file:///(.*?):(\d+):(\d+) '(.*)' overrides nothing$",
            "null_for_nonnull": r"e: file:///(.*?):(\d+):(\d+) Null can not be a value of a non-null type (.*?)$",
            "final_type": r"e: file:///(.*?):(\d+):(\d+) This type is final, so it cannot be inherited from$",
        }
        # 修正方法の定義
        self.fixes = {
            "unresolved_reference": self.fix_unresolved_reference,
            "type_mismatch": self.fix_type_mismatch,
            "missing_import": self.fix_missing_import,
            "serializer_not_found": self.fix_serializer_not_found,
            "redeclaration": self.fix_redeclaration,
            "cannot_find_parameter": self.fix_cannot_find_parameter,
            "overrides_nothing": self.fix_overrides_nothing,
            "null_for_nonnull": self.fix_null_for_nonnull,
            "final_type": self.fix_final_type,
        }

    def parse_error(self, error_line: str) -> Optional[Dict]:
        """エラーメッセージを解析する"""
        # 「Ask Gemini」を削除
        error_line = error_line.replace("Ask Gemini", "").strip()

        if self.verbose:
            print(f"解析中のエラー: {error_line}")

        # 特定のエラーパターンを直接チェック
        if "Unresolved reference:" in error_line:
            # Unresolved reference エラー
            match = re.search(r'e: file:///(.*?):(\d+):(\d+) Unresolved reference: (.*?)($|\s)', error_line)
            if match:
                file_path, line, column, reference = match.groups()[0:4]
                return {
                    "type": "unresolved_reference",
                    "file_path": file_path,
                    "line": int(line),
                    "column": int(column),
                    "reference": reference.strip()
                }

        elif "Serializer has not been found for type" in error_line:
            # Serializer not found エラー
            match = re.search(r'e: file:///(.*?):(\d+):(\d+) Serializer has not been found for type \'(.*?)\'', error_line)
            if match:
                file_path, line, column, type_info = match.groups()
                return {
                    "type": "serializer_not_found",
                    "file_path": file_path,
                    "line": int(line),
                    "column": int(column),
                    "reference": type_info
                }

        elif "Type mismatch:" in error_line:
            # Type mismatch エラー
            match = re.search(r'e: file:///(.*?):(\d+):(\d+) Type mismatch: inferred type is (.*) but (.*) was expected', error_line)
            if match:
                file_path, line, column, inferred_type, expected_type = match.groups()
                return {
                    "type": "type_mismatch",
                    "file_path": file_path,
                    "line": int(line),
                    "column": int(column),
                    "inferred_type": inferred_type,
                    "expected_type": expected_type
                }

        elif "Redeclaration:" in error_line:
            # Redeclaration エラー
            match = re.search(r'e: file:///(.*?):(\d+):(\d+) Redeclaration: (.*?)($|\s)', error_line)
            if match:
                file_path, line, column, class_name = match.groups()[0:4]
                return {
                    "type": "redeclaration",
                    "file_path": file_path,
                    "line": int(line),
                    "column": int(column),
                    "reference": class_name.strip()
                }

        elif "Cannot find a parameter with this name:" in error_line:
            # Cannot find parameter エラー
            match = re.search(r'e: file:///(.*?):(\d+):(\d+) Cannot find a parameter with this name: (.*?)($|\s)', error_line)
            if match:
                file_path, line, column, param_name = match.groups()[0:4]
                return {
                    "type": "cannot_find_parameter",
                    "file_path": file_path,
                    "line": int(line),
                    "column": int(column),
                    "reference": param_name.strip()
                }

        elif "overrides nothing" in error_line:
            # Overrides nothing エラー
            match = re.search(r'e: file:///(.*?):(\d+):(\d+) \'(.*?)\' overrides nothing', error_line)
            if match:
                file_path, line, column, method_name = match.groups()
                return {
                    "type": "overrides_nothing",
                    "file_path": file_path,
                    "line": int(line),
                    "column": int(column),
                    "reference": method_name
                }

        elif "Null can not be a value of a non-null type" in error_line:
            # Null for non-null エラー
            match = re.search(r'e: file:///(.*?):(\d+):(\d+) Null can not be a value of a non-null type (.*?)($|\s)', error_line)
            if match:
                file_path, line, column, type_name = match.groups()[0:4]
                return {
                    "type": "null_for_nonnull",
                    "file_path": file_path,
                    "line": int(line),
                    "column": int(column),
                    "reference": type_name.strip()
                }

        elif "This type is final, so it cannot be inherited from" in error_line:
            # Final type エラー
            match = re.search(r'e: file:///(.*?):(\d+):(\d+) This type is final, so it cannot be inherited from', error_line)
            if match:
                file_path, line, column = match.groups()
                return {
                    "type": "final_type",
                    "file_path": file_path,
                    "line": int(line),
                    "column": int(column),
                    "reference": "final_type"
                }

        # 一般的なエラーパターンの処理
        for error_type, pattern in self.error_patterns.items():
            match = re.search(pattern, error_line)
            if match:
                if error_type == "unresolved_reference":
                    file_path, line, column, reference = match.groups()
                    return {
                        "type": error_type,
                        "file_path": file_path,
                        "line": int(line),
                        "column": int(column),
                        "reference": reference.strip()
                    }
                elif error_type == "type_mismatch":
                    file_path, line, column, inferred_type, expected_type = match.groups()
                    return {
                        "type": error_type,
                        "file_path": file_path,
                        "line": int(line),
                        "column": int(column),
                        "inferred_type": inferred_type,
                        "expected_type": expected_type
                    }
                elif error_type == "missing_import":
                    file_path, line, column, class_name = match.groups()
                    return {
                        "type": error_type,
                        "file_path": file_path,
                        "line": int(line),
                        "column": int(column),
                        "class_name": class_name
                    }

        # エラーパターンに一致しない場合、ファイルパスだけでも抽出を試みる
        file_path_match = re.search(r'e: file:///(.*?):\d+:\d+', error_line)
        if file_path_match:
            file_path = file_path_match.group(1)
            line_match = re.search(r'e: file:///.*?:(\d+):\d+', error_line)
            column_match = re.search(r'e: file:///.*?:\d+:(\d+)', error_line)

            if line_match and column_match:
                line = int(line_match.group(1))
                column = int(column_match.group(1))

                # エラーメッセージの残りの部分を取得
                message_match = re.search(r'e: file:///.*?:\d+:\d+ (.*?)$', error_line)
                message = message_match.group(1) if message_match else "不明なエラー"

                if "Unresolved reference:" in message:
                    ref_match = re.search(r'Unresolved reference: (.*?)($|\s)', message)
                    if ref_match:
                        reference = ref_match.group(1).strip()
                        return {
                            "type": "unresolved_reference",
                            "file_path": file_path,
                            "line": line,
                            "column": column,
                            "reference": reference
                        }

                return {
                    "type": "unknown_error",
                    "file_path": file_path,
                    "line": line,
                    "column": column,
                    "message": message
                }

        if self.verbose:
            print(f"解析できないエラー: {error_line}")

        return None

    def fix_unresolved_reference(self, error_info: Dict, file_content: List[str]) -> Tuple[List[str], str]:
        """未解決の参照エラーを修正する"""
        line_num = error_info["line"] - 1  # 0-indexedに変換
        reference = error_info["reference"]
        line_content = file_content[line_num]

        if self.verbose:
            print(f"未解決の参照を修正: {reference} (行 {error_info['line']})")
            print(f"行の内容: {line_content}")

        # 一般的なインポートのマッピング
        common_imports = {
            "Modifier": "androidx.compose.ui.Modifier",
            "Preview": "androidx.compose.ui.tooling.preview.Preview",
            "remember": "androidx.compose.runtime.remember",
            "mutableStateOf": "androidx.compose.runtime.mutableStateOf",
            "LaunchedEffect": "androidx.compose.runtime.LaunchedEffect",
            "Column": "androidx.compose.foundation.layout.Column",
            "Row": "androidx.compose.foundation.layout.Row",
            "Box": "androidx.compose.foundation.layout.Box",
            "Text": "androidx.compose.material.Text",
            "Button": "androidx.compose.material.Button",
            "Image": "androidx.compose.foundation.Image",
            "Spacer": "androidx.compose.foundation.layout.Spacer",
            "fillMaxWidth": "androidx.compose.foundation.layout.fillMaxWidth",
            "fillMaxHeight": "androidx.compose.foundation.layout.fillMaxHeight",
            "fillMaxSize": "androidx.compose.foundation.layout.fillMaxSize",
            "padding": "androidx.compose.foundation.layout.padding",
            "width": "androidx.compose.foundation.layout.width",
            "height": "androidx.compose.foundation.layout.height",
            "size": "androidx.compose.foundation.layout.size",
            "align": "androidx.compose.ui.Alignment",
            "Alignment": "androidx.compose.ui.Alignment",
            "Color": "androidx.compose.ui.graphics.Color",
            "MaterialTheme": "androidx.compose.material.MaterialTheme",
            "ViewModel": "androidx.lifecycle.ViewModel",
            "viewModel": "androidx.lifecycle.viewModel",
            "LiveData": "androidx.lifecycle.LiveData",
            "MutableLiveData": "androidx.lifecycle.MutableLiveData",
            "Context": "android.content.Context",
            "Activity": "android.app.Activity",
            "Intent": "android.content.Intent",
            "Bundle": "android.os.Bundle",
            "Parcelable": "android.os.Parcelable",
            "Serializable": "java.io.Serializable",
            "List": "kotlin.collections.List",
            "MutableList": "kotlin.collections.MutableList",
            "Map": "kotlin.collections.Map",
            "MutableMap": "kotlin.collections.MutableMap",
            "Set": "kotlin.collections.Set",
            "MutableSet": "kotlin.collections.MutableSet",
            "Pair": "kotlin.Pair",
            "Triple": "kotlin.Triple",
            "Unit": "kotlin.Unit",
            "Any": "kotlin.Any",
            "Nothing": "kotlin.Nothing",
            "Throwable": "kotlin.Throwable",
            "Exception": "kotlin.Exception",
            "RuntimeException": "kotlin.RuntimeException",
            "IllegalArgumentException": "kotlin.IllegalArgumentException",
            "IllegalStateException": "kotlin.IllegalStateException",
            "NumberFormatter": "java.text.NumberFormatter",
            "Product": "com.example.app.models.Product",
            "StoreKitService": "com.example.app.services.StoreKitService",
            "GenerationState": "com.example.app.models.GenerationState",
            "JsonFeature": "io.ktor.client.features.json.JsonFeature",
            "KotlinxSerializer": "io.ktor.client.features.json.serializer.KotlinxSerializer",
            "serializer": "kotlinx.serialization.serializer",
            "ColumnAdapter": "app.cash.sqldelight.ColumnAdapter",
            "features": "io.ktor.client.features",
            "app": "com.example.app",
        }

        # ViewModelの特殊ケース
        if reference.endswith("ViewModel"):
            base_name = reference.replace("ViewModel", "")
            import_line = f"import com.example.app.viewmodels.{reference}"

            # importセクションを探す
            import_section_end = 0
            for i, line in enumerate(file_content):
                if line.startswith("import "):
                    import_section_end = i + 1

            # 既に同じimportがないか確認
            for line in file_content:
                if line.strip() == import_line:
                    return file_content, f"行 {error_info['line']}: '{import_line}'は既に存在します"

            # importを追加
            if import_section_end > 0:
                file_content.insert(import_section_end, import_line)
                return file_content, f"行 {import_section_end + 1}: '{import_line}'を追加しました"
            else:
                # パッケージ行の後にimportを追加
                for i, line in enumerate(file_content):
                    if line.startswith("package "):
                        file_content.insert(i + 1, "")
                        file_content.insert(i + 2, import_line)
                        return file_content, f"行 {i + 3}: '{import_line}'を追加しました"

                # パッケージ行がない場合はファイルの先頭に追加
                file_content.insert(0, import_line)
                return file_content, f"行 1: '{import_line}'を追加しました"

        # 一般的なインポートの処理
        if reference in common_imports:
            import_line = f"import {common_imports[reference]}"

            # importセクションを探す
            import_section_end = 0
            for i, line in enumerate(file_content):
                if line.startswith("import "):
                    import_section_end = i + 1

            # 既に同じimportがないか確認
            for line in file_content:
                if line.strip() == import_line:
                    return file_content, f"行 {error_info['line']}: '{import_line}'は既に存在します"

            # importを追加
            if import_section_end > 0:
                file_content.insert(import_section_end, import_line)
                return file_content, f"行 {import_section_end + 1}: '{import_line}'を追加しました"
            else:
                # パッケージ行の後にimportを追加
                for i, line in enumerate(file_content):
                    if line.startswith("package "):
                        file_content.insert(i + 1, "")
                        file_content.insert(i + 2, import_line)
                        return file_content, f"行 {i + 3}: '{import_line}'を追加しました"

                # パッケージ行がない場合はファイルの先頭に追加
                file_content.insert(0, import_line)
                return file_content, f"行 1: '{import_line}'を追加しました"

        # 特定のケースに対する修正
        if reference == "modifier":
            # 'modifier'を'Modifier'に修正（大文字小文字の間違い）

            # パラメータとして使用されている場合
            if re.search(r'(\s)modifier(\s*=)', line_content):
                file_content[line_num] = re.sub(r'(\s)modifier(\s*=)', r'\1Modifier\2', line_content)
                return file_content, f"行 {error_info['line']}: 'modifier'を'Modifier'に修正しました"

            # 単語の境界を考慮して置換（最後の手段）
            file_content[line_num] = re.sub(r'\bmodifier\b', 'Modifier', line_content)
            return file_content, f"行 {error_info['line']}: 'modifier'を'Modifier'に修正しました"

        # toViewModelの特殊ケース
        if reference == "toViewModel":
            # 拡張関数として定義
            extension_function = """
fun Any.toViewModel(): ViewModel {
    // TODO: 適切な実装を追加
    return ViewModel()
}
"""
            # クラス定義の後に追加
            for i, line in enumerate(file_content):
                if line.strip().startswith("class ") or line.strip().startswith("data class "):
                    # クラスの終わりを探す
                    brace_count = 0
                    for j in range(i, len(file_content)):
                        if "{" in file_content[j]:
                            brace_count += file_content[j].count("{")
                        if "}" in file_content[j]:
                            brace_count -= file_content[j].count("}")
                        if brace_count == 0 and j > i:
                            file_content.insert(j + 1, extension_function)
                            return file_content, f"行 {j + 2}: 'toViewModel'拡張関数を追加しました"

            # クラスが見つからない場合はファイルの最後に追加
            file_content.append(extension_function)
            return file_content, f"行 {len(file_content)}: 'toViewModel'拡張関数を追加しました"

        # 最後の手段：ファイル内容から推測
        # ファイル名からクラス名を推測
        file_name = os.path.basename(error_info["file_path"])
        if file_name.endswith(".kt"):
            class_name = file_name[:-3]

            # ViewModelの場合
            if class_name.endswith("ViewModel") and reference.endswith("ViewModel"):
                import_line = f"import com.example.app.viewmodels.{reference}"

                # importセクションを探す
                import_section_end = 0
                for i, line in enumerate(file_content):
                    if line.startswith("import "):
                        import_section_end = i + 1

                # importを追加
                if import_section_end > 0:
                    file_content.insert(import_section_end, import_line)
                    return file_content, f"行 {import_section_end + 1}: '{import_line}'を追加しました"

        return file_content, f"行 {error_info['line']}: 未解決の参照 '{reference}' を修正できませんでした"

    def fix_type_mismatch(self, error_info: Dict, file_content: List[str]) -> Tuple[List[str], str]:
        """型の不一致エラーを修正する"""
        line_num = error_info["line"] - 1  # 0-indexedに変換
        inferred_type = error_info["inferred_type"]
        expected_type = error_info["expected_type"]

        # 特定のケースに対する修正を実装
        # ここでは簡単な例として、型変換を追加する

        return file_content, f"行 {error_info['line']}: 型の不一致 (推論された型: {inferred_type}, 期待される型: {expected_type}) を修正できませんでした"

    def fix_missing_import(self, error_info: Dict, file_content: List[str]) -> Tuple[List[str], str]:
        """不足しているimportを修正する"""
        class_name = error_info["class_name"]

        # クラス名からパッケージを推測
        package_guess = ""
        if "compose" in class_name.lower():
            if "preview" in class_name.lower():
                package_guess = "androidx.compose.ui.tooling.preview"
            else:
                package_guess = "androidx.compose.ui"
        elif "view" in class_name.lower():
            package_guess = "com.example.app.views"
        elif "model" in class_name.lower():
            package_guess = "com.example.app.models"

        if package_guess:
            import_line = f"import {package_guess}.{class_name.split('.')[-1]}"

            # 既に同じimportがないか確認
            for line in file_content:
                if line.strip() == import_line:
                    return file_content, f"行 {error_info['line']}: '{import_line}'は既に存在します"

            # importセクションを探す
            import_section_end = 0
            for i, line in enumerate(file_content):
                if line.startswith("import "):
                    import_section_end = i + 1

            # importを追加
            if import_section_end > 0:
                file_content.insert(import_section_end, import_line)
                return file_content, f"行 {import_section_end + 1}: '{import_line}'を追加しました"

        return file_content, f"行 {error_info['line']}: 不足しているimport '{class_name}' を修正できませんでした"

    def fix_serializer_not_found(self, error_info: Dict, file_content: List[str]) -> Tuple[List[str], str]:
        """シリアライザが見つからないエラーを修正する"""
        line_num = error_info["line"] - 1  # 0-indexedに変換
        type_info = error_info["reference"]
        line_content = file_content[line_num]

        # @Contextualアノテーションを追加
        # 変数宣言を探す
        var_declaration_match = re.search(r'(val|var)\s+(\w+)\s*:', line_content)
        if var_declaration_match:
            var_name = var_declaration_match.group(2)
            # @Contextualアノテーションが既にあるか確認
            if "@Contextual" not in line_content:
                # アノテーションを追加
                indentation = re.match(r'^\s*', line_content).group(0)
                file_content.insert(line_num, f"{indentation}@Contextual")
                return file_content, f"行 {error_info['line']}: '@Contextual'アノテーションを追加しました"

        # 型名を抽出
        type_name_match = re.search(r'\[Error type: Unresolved type for (.*?)\]', type_info)
        if type_name_match:
            type_name = type_name_match.group(1)

            # 対応するimportを追加
            import_mapping = {
                "NumberFormatter": "java.text.NumberFormatter",
                "Product": "com.example.app.models.Product",
                "StoreKitService": "com.example.app.services.StoreKitService",
                "GenerationState": "com.example.app.models.GenerationState",
            }

            if type_name in import_mapping:
                import_line = f"import {import_mapping[type_name]}"

                # importセクションを探す
                import_section_end = 0
                for i, line in enumerate(file_content):
                    if line.startswith("import "):
                        import_section_end = i + 1

                # 既に同じimportがないか確認
                for line in file_content:
                    if line.strip() == import_line:
                        return file_content, f"行 {error_info['line']}: '{import_line}'は既に存在します"

                # importを追加
                if import_section_end > 0:
                    file_content.insert(import_section_end, import_line)
                    return file_content, f"行 {import_section_end + 1}: '{import_line}'を追加しました"
                else:
                    # パッケージ行の後にimportを追加
                    for i, line in enumerate(file_content):
                        if line.startswith("package "):
                            file_content.insert(i + 1, "")
                            file_content.insert(i + 2, import_line)
                            return file_content, f"行 {i + 3}: '{import_line}'を追加しました"

                    # パッケージ行がない場合はファイルの先頭に追加
                    file_content.insert(0, import_line)
                    return file_content, f"行 1: '{import_line}'を追加しました"

        # kotlinx.serializationのimportを追加
        serialization_imports = [
            "import kotlinx.serialization.*",
            "import kotlinx.serialization.json.*"
        ]

        # importセクションを探す
        import_section_end = 0
        for i, line in enumerate(file_content):
            if line.startswith("import "):
                import_section_end = i + 1

        # importを追加
        if import_section_end > 0:
            added = False
            for import_line in serialization_imports:
                # 既に同じimportがないか確認
                if not any(line.strip() == import_line for line in file_content):
                    file_content.insert(import_section_end, import_line)
                    import_section_end += 1
                    added = True

            if added:
                return file_content, f"行 {error_info['line']}: 'kotlinx.serialization'のimportを追加しました"

        return file_content, f"行 {error_info['line']}: シリアライザが見つからない '{type_info}' を修正できませんでした"

    def fix_redeclaration(self, error_info: Dict, file_content: List[str]) -> Tuple[List[str], str]:
        """再宣言エラーを修正する"""
        line_num = error_info["line"] - 1  # 0-indexedに変換
        class_name = error_info["reference"]

        # 特定のケースに対する修正を実装
        # ここでは簡単な例として、型変換を追加する

        return file_content, f"行 {error_info['line']}: 再宣言 '{class_name}' を修正できませんでした"

    def fix_cannot_find_parameter(self, error_info: Dict, file_content: List[str]) -> Tuple[List[str], str]:
        """パラメータが見つからないエラーを修正する"""
        line_num = error_info["line"] - 1  # 0-indexedに変換
        parameter_name = error_info["reference"]

        # 特定のケースに対する修正を実装
        # ここでは簡単な例として、型変換を追加する

        return file_content, f"行 {error_info['line']}: パラメータ '{parameter_name}' を修正できませんでした"

    def fix_overrides_nothing(self, error_info: Dict, file_content: List[str]) -> Tuple[List[str], str]:
        """オーバーライドがないエラーを修正する"""
        line_num = error_info["line"] - 1  # 0-indexedに変換
        class_name = error_info["reference"]

        # 特定のケースに対する修正を実装
        # ここでは簡単な例として、型変換を追加する

        return file_content, f"行 {error_info['line']}: オーバーライドがない '{class_name}' を修正できませんでした"

    def fix_null_for_nonnull(self, error_info: Dict, file_content: List[str]) -> Tuple[List[str], str]:
        """nullを非null型に代入するエラーを修正する"""
        line_num = error_info["line"] - 1  # 0-indexedに変換
        type_name = error_info["reference"]

        # 特定のケースに対する修正を実装
        # ここでは簡単な例として、型変換を追加する

        return file_content, f"行 {error_info['line']}: nullを非null型 '{type_name}' に代入するエラーを修正できませんでした"

    def fix_final_type(self, error_info: Dict, file_content: List[str]) -> Tuple[List[str], str]:
        """final型の継承エラーを修正する"""
        line_num = error_info["line"] - 1  # 0-indexedに変換
        type_name = error_info["reference"]

        # 特定のケースに対する修正を実装
        # ここでは簡単な例として、型変換を追加する

        return file_content, f"行 {error_info['line']}: final型 '{type_name}' を継承するエラーを修正できませんでした"

    def fix_errors(self, error_lines: List[str]) -> None:
        """エラーを修正する"""
        # エラーをファイルごとにグループ化
        errors_by_file = {}

        # エラーメッセージを結合（「Ask Gemini」を含む複数行のエラーメッセージに対応）
        combined_errors = []
        current_error = ""
        in_ask_gemini = False

        # エラーメッセージの前処理
        processed_lines = []
        for line in error_lines:
            line = line.strip()
            if line and not line.startswith("BUILD FAILED") and not line.startswith("FAILURE:") and not line.startswith("* What went wrong:"):
                processed_lines.append(line)

        # エラーメッセージの抽出
        for line in processed_lines:
            # 新しいエラーメッセージの開始
            if line.startswith("e: file://"):
                if current_error:
                    combined_errors.append(current_error)
                current_error = line
                in_ask_gemini = False
            # Ask Gemini行の処理
            elif line == "Ask Gemini":
                in_ask_gemini = True
                # Ask Geminiの行は無視するが、現在のエラーメッセージは保持する
            # 空行の処理
            elif not line:
                # 空行は無視
                pass
            # 現在のエラーメッセージに追加
            elif current_error and not in_ask_gemini:
                current_error += " " + line

        if current_error:
            combined_errors.append(current_error)

        if self.verbose:
            print(f"解析されたエラーメッセージ数: {len(combined_errors)}")
            for i, error in enumerate(combined_errors[:10]):  # 最初の10個だけ表示
                print(f"エラー {i+1}: {error}")
            if len(combined_errors) > 10:
                print(f"... 他 {len(combined_errors) - 10} 件のエラー")

        # 実際のファイルパスを保存するディクショナリ
        real_file_paths = {}

        # 結合したエラーメッセージを解析
        for error_line in combined_errors:
            error_info = self.parse_error(error_line)
            if error_info:
                # ファイルパスを修正（相対パスに変換）
                file_path = error_info["file_path"]

                # file:/// 形式のURIからパスを抽出
                if file_path.startswith("file:///"):
                    file_path = file_path[8:]  # "file:///" を削除

                # 先頭に / がない場合は追加
                if not file_path.startswith("/") and not os.path.isabs(file_path):
                    file_path = "/" + file_path

                # 重複パスのチェックと修正
                workspace_path = os.getcwd()

                # 重複パスの検出と修正（例: /path/to/project/path/to/project/file.kt）
                if workspace_path in file_path and file_path.count(workspace_path) > 1:
                    # 最初の出現位置を見つける
                    first_occurrence = file_path.find(workspace_path)
                    # 最後の出現位置を見つける
                    last_occurrence = file_path.rfind(workspace_path)

                    if first_occurrence != last_occurrence:
                        # 重複を削除（最初の出現位置から始まるパスを使用）
                        file_path = file_path[first_occurrence:]
                        if self.verbose:
                            print(f"重複パスを修正: {file_path}")

                # パスの正規化（重複や .. などを解決）
                file_path = os.path.normpath(file_path)

                # 実際にファイルが存在するか確認
                if not os.path.exists(file_path):
                    # ワークスペースパスからの相対パスを試す
                    app_path = "app/src/main/java/com/example/app"
                    if app_path in file_path:
                        # 相対パスを試す
                        relative_path = os.path.join(workspace_path, app_path + file_path.split(app_path)[-1])
                        if os.path.exists(relative_path):
                            file_path = relative_path
                            if self.verbose:
                                print(f"相対パスに変換: {file_path}")
                        else:
                            # ファイル名だけを抽出して検索
                            file_name = os.path.basename(file_path)
                            if self.verbose:
                                print(f"ファイル名で検索: {file_name}")
                            # find コマンドでファイルを検索
                            try:
                                import subprocess
                                result = subprocess.run(
                                    ["find", workspace_path, "-name", file_name],
                                    capture_output=True,
                                    text=True
                                )
                                if result.stdout.strip():
                                    # 最初に見つかったファイルを使用
                                    found_path = result.stdout.strip().split("\n")[0]
                                    file_path = found_path
                                    if self.verbose:
                                        print(f"ファイルを見つけました: {file_path}")
                            except Exception as e:
                                if self.verbose:
                                    print(f"ファイル検索エラー: {str(e)}")

                # 元のファイルパスと実際のファイルパスのマッピングを保存
                original_path = error_info["file_path"]
                real_file_paths[original_path] = file_path

                error_info["file_path"] = file_path

                if file_path not in errors_by_file:
                    errors_by_file[file_path] = []
                errors_by_file[file_path].append(error_info)

        # ファイルごとにエラーを修正
        for file_path, errors in errors_by_file.items():
            if self.verbose:
                print(f"\n処理中: {file_path}")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read().splitlines()

                # エラーを修正
                modified = False
                for error_info in errors:
                    error_type = error_info["type"]
                    if error_type in self.fixes:
                        try:
                            new_content, message = self.fixes[error_type](error_info, file_content)
                            if new_content != file_content:
                                file_content = new_content
                                modified = True
                                print(message)
                        except Exception as e:
                            print(f"エラー修正中に例外が発生しました: {str(e)}")
                            if self.verbose:
                                import traceback
                                traceback.print_exc()

                # 修正があれば保存
                if modified:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(file_content))
                    print(f"ファイルを保存しました: {file_path}")
                else:
                    print(f"修正は必要ありませんでした: {file_path}")

            except FileNotFoundError:
                print(f"エラー: ファイルが見つかりません: {file_path}")
                print(f"  - 絶対パス: {os.path.abspath(file_path)}")
                print(f"  - ファイルの存在確認: {os.path.exists(file_path)}")
                print(f"  - 現在の作業ディレクトリ: {os.getcwd()}")

                # コールバックがあれば呼び出す
                if self.file_not_found_callback:
                    self.file_not_found_callback(file_path)

                # ファイルの親ディレクトリが存在するか確認
                parent_dir = os.path.dirname(file_path)
                if not os.path.exists(parent_dir):
                    print(f"  - 親ディレクトリが存在しません: {parent_dir}")
                    # 親ディレクトリの作成を試みる
                    try:
                        os.makedirs(parent_dir, exist_ok=True)
                        print(f"  - 親ディレクトリを作成しました: {parent_dir}")
                    except Exception as e:
                        print(f"  - 親ディレクトリの作成に失敗しました: {str(e)}")

            except Exception as e:
                print(f"エラー: {file_path} の処理中に問題が発生しました: {str(e)}")
                if self.verbose:
                    import traceback
                    traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='Kotlinのコンパイルエラーを自動修正するツール')
    parser.add_argument('error_file', help='エラーメッセージを含むファイル')
    parser.add_argument('-v', '--verbose', action='store_true', help='詳細な出力を表示')
    parser.add_argument('-c', '--continuous', action='store_true', help='エラーが解決するまで連続してビルドと修正を実行')
    parser.add_argument('-m', '--max-iterations', type=int, default=10, help='最大繰り返し回数（デフォルト: 10）')
    parser.add_argument('-f', '--force-create', action='store_true', help='見つからないファイルを自動的に作成する')
    args = parser.parse_args()

    max_iterations = args.max_iterations  # 最大繰り返し回数
    iteration = 0
    previous_errors = set()  # 前回のエラーを記録
    consecutive_same_errors = 0  # 同じエラーが連続して発生した回数
    not_found_files = set()  # 見つからないファイルのリスト

    # 見つからないファイルを記録するためのコールバック
    def file_not_found_callback(file_path):
        not_found_files.add(file_path)

    while iteration < max_iterations:
        iteration += 1

        try:
            # エラーファイルが存在するか確認
            if not os.path.exists(args.error_file):
                print(f"エラー: ファイル '{args.error_file}' が見つかりません。")
                return 1

            with open(args.error_file, 'r', encoding='utf-8') as f:
                error_lines = f.read().splitlines()

            # エラーがない場合は終了
            error_count = sum(1 for line in error_lines if line.strip().startswith("e: file://"))
            if error_count == 0:
                print("コンパイルエラーは見つかりませんでした。")
                if args.continuous and iteration > 1:
                    print(f"全てのエラーが修正されました。{iteration-1}回の繰り返しで完了しました。")
                return 0

            # 現在のエラーを集合に変換
            current_errors = set()
            for line in error_lines:
                if line.strip().startswith("e: file://"):
                    current_errors.add(line.strip())

            # 前回と同じエラーが発生しているか確認
            if current_errors == previous_errors and current_errors:
                consecutive_same_errors += 1
                if consecutive_same_errors >= 2:  # 3回連続で同じエラーなら終了
                    print("同じエラーが3回連続で発生しました。自動修正できないエラーがあります。")
                    print(f"残りのエラー数: {len(current_errors)}")
                    print("以下のエラーを手動で修正してください:")
                    for error in sorted(current_errors):
                        print(f"  {error}")

                    # 見つからないファイルがある場合、それを報告
                    if not_found_files:
                        print("\n以下のファイルが見つかりませんでした:")
                        for file_path in sorted(not_found_files):
                            print(f"  {file_path}")

                        # 自動作成オプションが有効な場合
                        if args.force_create:
                            print("\n見つからないファイルを自動作成します...")
                            for file_path in sorted(not_found_files):
                                try:
                                    # ディレクトリが存在しない場合は作成
                                    os.makedirs(os.path.dirname(file_path), exist_ok=True)

                                    # ファイル名からクラス名を推測
                                    class_name = os.path.basename(file_path).replace(".kt", "")

                                    # パッケージ名を推測
                                    package_parts = []
                                    if "com/example/app" in file_path:
                                        path_parts = file_path.split("com/example/app/")
                                        if len(path_parts) > 1:
                                            package_path = path_parts[1].replace("/", ".").rsplit(".", 1)[0]
                                            package_parts = ["com", "example", "app"] + package_path.split(".")

                                    package_name = ".".join(package_parts)

                                    # 基本的なKotlinファイルのテンプレート
                                    template = f"""package {package_name}

/**
 * 自動生成された {class_name} クラス
 */
class {class_name} {{
    // TODO: 実装を追加
}}
"""
                                    # ファイルを作成
                                    with open(file_path, 'w', encoding='utf-8') as f:
                                        f.write(template)
                                    print(f"  - ファイルを作成しました: {file_path}")
                                except Exception as e:
                                    print(f"  - ファイルの作成に失敗しました: {file_path} - {str(e)}")

                    return 1
            else:
                consecutive_same_errors = 0

            # 現在のエラーを記録
            previous_errors = current_errors

            print(f"繰り返し {iteration}/{max_iterations}: エラー修正を開始します（エラー数: {error_count}）...")
            fixer = KotlinErrorFixer(verbose=args.verbose, file_not_found_callback=file_not_found_callback)

            # エラー修正を実行
            fixer.fix_errors(error_lines)

            # 連続モードでない場合は1回で終了
            if not args.continuous:
                return 0

            # 連続モードの場合は再ビルド
            print("再ビルドを実行中...")
            os.system(f"./gradlew build > {args.error_file} 2>&1 || true")

        except Exception as e:
            print(f"エラー: {str(e)}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1

    print(f"最大繰り返し回数({max_iterations}回)に達しました。残りのエラーは手動で修正してください。")
    return 1

if __name__ == "__main__":
    sys.exit(main())