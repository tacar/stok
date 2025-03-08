#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Swift のリポジトリを Kotlin のリポジトリに変換するモジュール
"""

import os
import re
from typing import Dict, List, Any

from utils.file_utils import read_file, write_file, get_filename
from utils.parser import parse_swift_file, swift_type_to_kotlin, swift_method_to_kotlin

def convert_repositories(from_dir: str, package_dir: str, project_info: Dict[str, Any], package_name: str) -> None:
    """
    Swift のリポジトリを Kotlin のリポジトリに変換します。

    Args:
        from_dir: 変換元の iOS プロジェクトディレクトリ
        package_dir: 変換先の Android パッケージディレクトリ
        project_info: プロジェクト情報
        package_name: Android アプリのパッケージ名
    """
    print("リポジトリを変換しています...")

    repositories_dir = os.path.join(package_dir, 'repositories')
    os.makedirs(repositories_dir, exist_ok=True)

    for repo_path in project_info['repositories']:
        full_path = os.path.join(from_dir, repo_path)
        if not os.path.exists(full_path):
            print(f"警告: リポジトリファイルが見つかりません: {full_path}")
            continue

        print(f"リポジトリを変換しています: {repo_path}")

        # Swift ファイルを解析
        swift_content = read_file(full_path)
        repo_info = parse_swift_file(swift_content)

        # Kotlin リポジトリを生成
        kotlin_content = generate_kotlin_repository(repo_info, package_name, project_info)

        # ファイル名を決定
        filename = get_filename(repo_path)
        kotlin_filename = f"{filename}.kt"

        # Kotlin ファイルを書き込み
        kotlin_path = os.path.join(repositories_dir, kotlin_filename)
        write_file(kotlin_path, kotlin_content)

        print(f"リポジトリを変換しました: {kotlin_path}")

def generate_kotlin_repository(repo_info: Dict[str, Any], package_name: str, project_info: Dict[str, Any]) -> str:
    """
    Swift のリポジトリ情報から Kotlin のリポジトリを生成します。

    Args:
        repo_info: Swift リポジトリの情報
        package_name: Android アプリのパッケージ名
        project_info: プロジェクト情報

    Returns:
        生成された Kotlin リポジトリのコード
    """
    class_name = repo_info['class_name']

    # パッケージとインポート
    lines = [
        f"package {package_name}.repositories",
        "",
        "import kotlinx.coroutines.Dispatchers",
        "import kotlinx.coroutines.flow.Flow",
        "import kotlinx.coroutines.flow.flow",
        "import kotlinx.coroutines.flow.flowOn",
        "import kotlinx.coroutines.withContext",
        f"import {package_name}.models.*",
        f"import {package_name}.data.local.*",
        f"import {package_name}.data.remote.*"
    ]

    # SwiftData を使用している場合
    if repo_info['uses_swiftdata'] or project_info['uses_swiftdata']:
        lines.append("import app.cash.sqldelight.coroutines.asFlow")
        lines.append("import app.cash.sqldelight.coroutines.mapToList")

    # Firebase を使用している場合
    if repo_info['uses_firebase'] or project_info['uses_firebase']:
        lines.append("import com.google.firebase.auth.FirebaseAuth")

    lines.append("")

    # インターフェース定義
    interface_name = class_name.replace("Repository", "")
    lines.extend([
        f"interface {interface_name}Repository {{",
    ])

    # メソッドのインターフェース定義
    for method in repo_info['methods']:
        method_name = method['name']
        parameters = method['parameters']
        return_type = method['return_type']

        # Swift のメソッドを Kotlin のメソッドに変換
        kotlin_method_name, kotlin_parameters, kotlin_return_type = swift_method_to_kotlin(
            method_name, parameters, return_type
        )

        # Flow を使用する場合
        if kotlin_return_type and ('List' in kotlin_return_type or kotlin_return_type.endswith('?')):
            kotlin_return_type = f"Flow<{kotlin_return_type}>"

        # メソッド定義
        if kotlin_parameters:
            lines.append(f"    suspend fun {kotlin_method_name}({kotlin_parameters}): {kotlin_return_type}")
        else:
            lines.append(f"    suspend fun {kotlin_method_name}(): {kotlin_return_type}")

    lines.append("}")
    lines.append("")

    # 実装クラス
    lines.extend([
        f"class {class_name}Impl(",
        "    private val localDataSource: LocalDataSource,",
        "    private val remoteDataSource: RemoteDataSource",
        f") : {interface_name}Repository {{",
    ])

    # メソッドの実装
    for method in repo_info['methods']:
        method_name = method['name']
        parameters = method['parameters']
        return_type = method['return_type']

        # Swift のメソッドを Kotlin のメソッドに変換
        kotlin_method_name, kotlin_parameters, kotlin_return_type = swift_method_to_kotlin(
            method_name, parameters, return_type
        )

        # Flow を使用する場合
        use_flow = kotlin_return_type and ('List' in kotlin_return_type or kotlin_return_type.endswith('?'))
        if use_flow:
            original_return_type = kotlin_return_type
            kotlin_return_type = f"Flow<{kotlin_return_type}>"

        # メソッド実装
        if kotlin_parameters:
            lines.append(f"    override suspend fun {kotlin_method_name}({kotlin_parameters}): {kotlin_return_type} {{")
        else:
            lines.append(f"    override suspend fun {kotlin_method_name}(): {kotlin_return_type} {{")

        # メソッドの内容
        if use_flow:
            lines.extend([
                "        return flow {",
                "            try {",
                "                // ローカルデータソースからデータを取得",
                f"                val localData = localDataSource.get{interface_name}()",
                "                emit(localData)",
                "",
                "                // リモートデータソースからデータを取得",
                f"                val remoteData = remoteDataSource.fetch{interface_name}()",
                "",
                "                // ローカルデータソースを更新",
                f"                localDataSource.save{interface_name}(remoteData)",
                "",
                "                // 更新されたデータを送信",
                "                emit(remoteData)",
                "            } catch (e: Exception) {",
                "                // エラー処理",
                "            }",
                "        }.flowOn(Dispatchers.IO)"
            ])
        else:
            lines.extend([
                "        return withContext(Dispatchers.IO) {",
                "            try {",
                "                // TODO: 実装",
                f"                // ローカルデータソースからデータを取得",
                f"                val localData = localDataSource.get{interface_name}()",
                f"                ",
                f"                // リモートデータソースからデータを取得",
                f"                val remoteData = remoteDataSource.fetch{interface_name}()",
                f"                ",
                f"                // ローカルデータソースを更新",
                f"                localDataSource.save{interface_name}(remoteData)",
                f"                ",
                f"                remoteData",
                "            } catch (e: Exception) {",
                "                // エラー処理",
                "                throw e",
                "            }",
                "        }"
            ])

        lines.append("    }")
        lines.append("")

    lines.append("}")

    return "\n".join(lines)