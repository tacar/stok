#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Swift のサービスを Kotlin のサービスに変換するモジュール
"""

import os
import re
from typing import Dict, List, Any

from utils.file_utils import read_file, write_file, get_filename
from utils.parser import parse_swift_file, swift_type_to_kotlin, swift_method_to_kotlin

def convert_services(from_dir: str, package_dir: str, project_info: Dict[str, Any], package_name: str) -> None:
    """
    Swift のサービスを Kotlin のサービスに変換します。

    Args:
        from_dir: 変換元の iOS プロジェクトディレクトリ
        package_dir: 変換先の Android パッケージディレクトリ
        project_info: プロジェクト情報
        package_name: Android アプリのパッケージ名
    """
    print("サービスを変換しています...")

    services_dir = os.path.join(package_dir, 'services')
    os.makedirs(services_dir, exist_ok=True)

    for service_path in project_info['services']:
        full_path = os.path.join(from_dir, service_path)
        if not os.path.exists(full_path):
            print(f"警告: サービスファイルが見つかりません: {full_path}")
            continue

        print(f"サービスを変換しています: {service_path}")

        # Swift ファイルを解析
        swift_content = read_file(full_path)
        service_info = parse_swift_file(swift_content)

        # Kotlin サービスを生成
        kotlin_content = generate_kotlin_service(service_info, package_name, project_info)

        # ファイル名を決定
        filename = get_filename(service_path)
        kotlin_filename = f"{filename}.kt"

        # Kotlin ファイルを書き込み
        kotlin_path = os.path.join(services_dir, kotlin_filename)
        write_file(kotlin_path, kotlin_content)

        print(f"サービスを変換しました: {kotlin_path}")

def generate_kotlin_service(service_info: Dict[str, Any], package_name: str, project_info: Dict[str, Any]) -> str:
    """
    Swift のサービス情報から Kotlin のサービスを生成します。

    Args:
        service_info: Swift サービスの情報
        package_name: Android アプリのパッケージ名
        project_info: プロジェクト情報

    Returns:
        生成された Kotlin サービスのコード
    """
    class_name = service_info['class_name']

    # パッケージとインポート
    lines = [
        f"package {package_name}.services",
        "",
        "import kotlinx.coroutines.Dispatchers",
        "import kotlinx.coroutines.withContext",
        f"import {package_name}.models.*"
    ]

    # Firebase を使用している場合
    if service_info['uses_firebase'] or project_info['uses_firebase']:
        lines.extend([
            "import com.google.firebase.auth.FirebaseAuth",
            "import com.google.firebase.auth.FirebaseUser",
            "import kotlinx.coroutines.tasks.await"
        ])

    # ネットワーク関連のインポート
    lines.extend([
        "import io.ktor.client.*",
        "import io.ktor.client.engine.android.*",
        "import io.ktor.client.features.json.*",
        "import io.ktor.client.features.json.serializer.*",
        "import io.ktor.client.request.*",
        "import io.ktor.http.*",
        "import javax.inject.Inject"
    ])

    lines.append("")

    # インターフェース定義
    interface_name = class_name
    lines.extend([
        f"interface {interface_name} {{",
    ])

    # メソッドのインターフェース定義
    for method in service_info['methods']:
        method_name = method['name']
        parameters = method['parameters'] if method['parameters'] else ""
        return_type = method['return_type']

        # Swift形式の辞書型パラメータを処理
        if parameters and '[' in parameters and ':' in parameters and ']' in parameters:
            # [String: Any]形式を処理
            dict_pattern = r'\[(\w+):\s*(\w+)\]'
            parameters = re.sub(dict_pattern, r'Map<\1, \2>', parameters)

        # 引数ラベルを処理
        if parameters and ' ' in parameters and ':' in parameters:
            # from userInput: String → userInput: String
            label_pattern = r'(\w+)\s+(\w+):\s*(\w+)'
            parameters = re.sub(label_pattern, r'\2: \3', parameters)

        # パラメータが空の場合は空文字列に設定
        if not parameters or parameters.strip() == "":
            parameters = ""

        # 特殊なケースを処理
        if "[String: Any]" in parameters:
            parameters = "params: Map<String, Any>"
        elif "from prompt: String" in parameters:
            parameters = "prompt: String"
        elif "from userInput: String" in parameters:
            parameters = "userInput: String"

        # Swift のメソッドを Kotlin のメソッドに変換
        kotlin_method_name, kotlin_parameters, kotlin_return_type = swift_method_to_kotlin(
            method_name, parameters, return_type
        )

        # None型をUnitに変換
        if kotlin_return_type == 'None' or kotlin_return_type == 'Void' or kotlin_return_type is None:
            kotlin_return_type = 'Unit'

        # メソッド定義
        if kotlin_parameters and kotlin_parameters.strip() != "":
            lines.append(f"    suspend fun {kotlin_method_name}({kotlin_parameters}): {kotlin_return_type}")
        else:
            lines.append(f"    suspend fun {kotlin_method_name}(): {kotlin_return_type}")

    lines.append("}")
    lines.append("")

    # 実装クラス
    lines.extend([
        f"class {class_name}Impl @Inject constructor() : {interface_name} {{",
        "    private val client = HttpClient(Android) {",
        "        install(JsonFeature) {",
        "            serializer = KotlinxSerializer(kotlinx.serialization.json.Json {",
        "                prettyPrint = true",
        "                isLenient = true",
        "                ignoreUnknownKeys = true",
        "            })",
        "        }",
        "    }",
        ""
    ])

    # Firebase を使用している場合
    if service_info['uses_firebase'] or project_info['uses_firebase']:
        lines.extend([
            "    private val auth = FirebaseAuth.getInstance()",
            ""
        ])

    # メソッドの実装
    for method in service_info['methods']:
        method_name = method['name']
        parameters = method['parameters'] if method['parameters'] else ""
        return_type = method['return_type']

        # Swift形式の辞書型パラメータを処理
        if parameters and '[' in parameters and ':' in parameters and ']' in parameters:
            # [String: Any]形式を処理
            dict_pattern = r'\[(\w+):\s*(\w+)\]'
            parameters = re.sub(dict_pattern, r'Map<\1, \2>', parameters)

        # 引数ラベルを処理
        if parameters and ' ' in parameters and ':' in parameters:
            # from userInput: String → userInput: String
            label_pattern = r'(\w+)\s+(\w+):\s*(\w+)'
            parameters = re.sub(label_pattern, r'\2: \3', parameters)

        # パラメータが空の場合は空文字列に設定
        if not parameters or parameters.strip() == "":
            parameters = ""

        # 特殊なケースを処理
        if "[String: Any]" in parameters:
            parameters = "params: Map<String, Any>"
        elif "from prompt: String" in parameters:
            parameters = "prompt: String"
        elif "from userInput: String" in parameters:
            parameters = "userInput: String"

        # Swift のメソッドを Kotlin のメソッドに変換
        kotlin_method_name, kotlin_parameters, kotlin_return_type = swift_method_to_kotlin(
            method_name, parameters, return_type
        )

        # None型をUnitに変換
        if kotlin_return_type == 'None' or kotlin_return_type == 'Void' or kotlin_return_type is None:
            kotlin_return_type = 'Unit'

        # メソッド実装
        if kotlin_parameters and kotlin_parameters.strip() != "":
            lines.append(f"    override suspend fun {kotlin_method_name}({kotlin_parameters}): {kotlin_return_type} {{")
        else:
            lines.append(f"    override suspend fun {kotlin_method_name}(): {kotlin_return_type} {{")

        # メソッドの内容
        if kotlin_return_type == 'Unit':
            lines.extend([
                "        return withContext(Dispatchers.IO) {",
                "            try {",
                "                // TODO: 実装",
                "                // API リクエストの例:",
                "                // client.post<Unit> {",
                "                //     url(\"https://api.example.com/endpoint\")",
                "                //     contentType(ContentType.Application.Json)",
                "                // }",
                "            } catch (e: Exception) {",
                "                // エラー処理",
                "                throw e",
                "            }",
                "        }",
            ])
        elif kotlin_return_type == 'String':
            lines.extend([
                "        return withContext(Dispatchers.IO) {",
                "            try {",
                "                // TODO: 実装",
                "                // API リクエストの例:",
                "                // client.get<String> {",
                "                //     url(\"https://api.example.com/endpoint\")",
                "                //     contentType(ContentType.Application.Json)",
                "                // }",
                "                \"\"  // 仮の戻り値",
                "            } catch (e: Exception) {",
                "                // エラー処理",
                "                throw e",
                "            }",
                "        }",
            ])
        else:
            lines.extend([
                "        return withContext(Dispatchers.IO) {",
                "            try {",
                "                // TODO: 実装",
                "                // API リクエストの例:",
                "                // client.get<ResponseType> {",
                "                //     url(\"https://api.example.com/endpoint\")",
                "                //     contentType(ContentType.Application.Json)",
                "                // }",
                "                null  // 仮の戻り値",
                "            } catch (e: Exception) {",
                "                // エラー処理",
                "                throw e",
                "            }",
                "        }",
            ])

        lines.append("    }")
        lines.append("")

    lines.append("}")

    return "\n".join(lines)