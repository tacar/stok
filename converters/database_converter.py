#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQLDelight データベース設定を行うモジュール
"""

import os
from typing import Dict, List, Any

from utils.file_utils import read_file, write_file

def setup_database(output_dir: str, package_dir: str, project_info: Dict[str, Any], package_name: str) -> None:
    """
    SQLDelight データベースの設定を行います。

    Args:
        output_dir: 出力先ディレクトリ
        package_dir: 変換先の Android パッケージディレクトリ
        project_info: プロジェクト情報
        package_name: Android アプリのパッケージ名
    """
    print("SQLDelight データベースの設定を行っています...")

    # build.gradle.kts に SQLDelight の依存関係を追加
    update_build_gradle(output_dir, package_name)

    # SQLDelight のスキーマファイルを作成
    create_sqldelight_schema(output_dir, project_info, package_name)

    # データベースクラスを作成
    create_database_class(package_dir, package_name)

    # ローカルデータソースを作成
    create_local_data_source(package_dir, package_name)

    print("SQLDelight データベースの設定が完了しました。")

def update_build_gradle(output_dir: str, package_name: str) -> None:
    """
    build.gradle.kts に SQLDelight の依存関係を追加します。

    Args:
        output_dir: 出力先ディレクトリ
        package_name: Android アプリのパッケージ名
    """
    app_build_gradle_path = os.path.join(output_dir, 'app/build.gradle.kts')

    if not os.path.exists(app_build_gradle_path):
        print(f"警告: build.gradle.kts が見つかりません: {app_build_gradle_path}")
        return

    # build.gradle.kts の内容を読み込み
    content = read_file(app_build_gradle_path)

    # SQLDelight の依存関係を追加
    sqldelight_dependencies = """
    // SQLDelight
    implementation("app.cash.sqldelight:android-driver:2.0.0")
    implementation("app.cash.sqldelight:coroutines-extensions:2.0.0")
    implementation("app.cash.sqldelight:primitive-adapters:2.0.0")
"""

    # 依存関係セクションを探して SQLDelight の依存関係を追加
    if "dependencies {" in content:
        content = content.replace("dependencies {", "dependencies {" + sqldelight_dependencies)
    else:
        print("警告: dependencies セクションが見つかりません。SQLDelight の依存関係を追加できませんでした。")

    # プラグインセクションを探して SQLDelight のプラグインを追加
    if "plugins {" in content:
        sqldelight_plugin = """
    id("app.cash.sqldelight") version "2.0.0"
"""
        content = content.replace("plugins {", "plugins {" + sqldelight_plugin)
    else:
        print("警告: plugins セクションが見つかりません。SQLDelight のプラグインを追加できませんでした。")

    # SQLDelight の設定を追加
    sqldelight_config = f"""
sqldelight {{
    databases {{
        create("{package_name.split('.')[-1]}Database") {{
            packageName = "{package_name}.data.local"
        }}
    }}
}}
"""

    # android セクションの後に SQLDelight の設定を追加
    if "android {" in content:
        android_end_index = content.find("}", content.find("android {")) + 1
        content = content[:android_end_index] + "\n" + sqldelight_config + content[android_end_index:]
    else:
        # android セクションが見つからない場合は最後に追加
        content += "\n" + sqldelight_config

    # 更新した内容を書き込み
    write_file(app_build_gradle_path, content)

def create_sqldelight_schema(output_dir: str, project_info: Dict[str, Any], package_name: str) -> None:
    """
    SQLDelight のスキーマファイルを作成します。

    Args:
        output_dir: 出力先ディレクトリ
        project_info: プロジェクト情報
        package_name: Android アプリのパッケージ名
    """
    # SQLDelight のスキーマディレクトリを作成
    app_name = package_name.split('.')[-1]
    sqldelight_dir = os.path.join(output_dir, f'app/src/main/sqldelight/{app_name}Database')
    os.makedirs(sqldelight_dir, exist_ok=True)

    # モデルごとにテーブルを作成
    for model_path in project_info['models']:
        model_name = os.path.splitext(os.path.basename(model_path))[0]

        # モデル名から "Model" を削除
        if model_name.endswith('Model'):
            table_name = model_name[:-5]
        else:
            table_name = model_name

        # スキーマファイルのパス
        schema_path = os.path.join(sqldelight_dir, f'{table_name}.sq')

        # スキーマファイルの内容
        schema_content = f"""-- {table_name} テーブルの定義
CREATE TABLE {table_name} (
    id TEXT PRIMARY KEY NOT NULL,
    data TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

-- すべての {table_name} を取得
selectAll:
SELECT * FROM {table_name};

-- ID で {table_name} を取得
selectById:
SELECT * FROM {table_name} WHERE id = ?;

-- {table_name} を挿入
insert:
INSERT OR REPLACE INTO {table_name} (id, data, created_at, updated_at)
VALUES (?, ?, ?, ?);

-- {table_name} を削除
delete:
DELETE FROM {table_name} WHERE id = ?;

-- すべての {table_name} を削除
deleteAll:
DELETE FROM {table_name};
"""

        # スキーマファイルを書き込み
        write_file(schema_path, schema_content)
        print(f"SQLDelight スキーマファイルを作成しました: {schema_path}")

def create_database_class(package_dir: str, package_name: str) -> None:
    """
    データベースクラスを作成します。

    Args:
        package_dir: 変換先の Android パッケージディレクトリ
        package_name: Android アプリのパッケージ名
    """
    # データベースディレクトリを作成
    data_local_dir = os.path.join(package_dir, 'data/local')
    os.makedirs(data_local_dir, exist_ok=True)

    # データベースクラスのファイルパス
    database_path = os.path.join(data_local_dir, 'AppDatabase.kt')

    # アプリ名を取得
    app_name = package_name.split('.')[-1]

    # データベースクラスの内容
    database_content = f"""package {package_name}.data.local

import android.content.Context
import app.cash.sqldelight.driver.android.AndroidSqliteDriver
import app.cash.sqldelight.db.SqlDriver
import kotlinx.serialization.json.Json

/**
 * アプリケーションのデータベースクラス
 */
class AppDatabase private constructor(context: Context) {{

    private val driver: SqlDriver = AndroidSqliteDriver(
        schema = {app_name}Database.Schema,
        context = context,
        name = "app.db"
    )

    val {app_name.lower()}Database: {app_name}Database = {app_name}Database(
        driver = driver
    )

    companion object {{
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getInstance(context: Context): AppDatabase {{
            return INSTANCE ?: synchronized(this) {{
                INSTANCE ?: AppDatabase(context).also {{ INSTANCE = it }}
            }}
        }}
    }}
}}
"""

    # データベースクラスを書き込み
    write_file(database_path, database_content)
    print(f"データベースクラスを作成しました: {database_path}")

def create_local_data_source(package_dir: str, package_name: str) -> None:
    """
    ローカルデータソースを作成します。

    Args:
        package_dir: 変換先の Android パッケージディレクトリ
        package_name: Android アプリのパッケージ名
    """
    # データソースディレクトリを作成
    data_local_dir = os.path.join(package_dir, 'data/local')
    os.makedirs(data_local_dir, exist_ok=True)

    # ローカルデータソースのファイルパス
    local_data_source_path = os.path.join(data_local_dir, 'LocalDataSource.kt')

    # アプリ名を取得
    app_name = package_name.split('.')[-1]

    # ローカルデータソースの内容
    local_data_source_content = f"""package {package_name}.data.local

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import {package_name}.models.*

/**
 * ローカルデータソースのインターフェース
 */
interface LocalDataSource {{
    suspend fun <T> getData(id: String, modelClass: Class<T>): T?
    suspend fun <T> getAllData(modelClass: Class<T>): List<T>
    suspend fun <T> saveData(id: String, data: T)
    suspend fun deleteData(id: String)
    suspend fun deleteAllData()
}}

/**
 * ローカルデータソースの実装
 */
class LocalDataSourceImpl(
    private val database: {app_name}Database
) : LocalDataSource {{

    private val json = Json {{ ignoreUnknownKeys = true }}

    override suspend fun <T> getData(id: String, modelClass: Class<T>): T? = withContext(Dispatchers.IO) {{
        // TODO: 実装
        // データベースからデータを取得し、モデルクラスにデシリアライズする
        null
    }}

    override suspend fun <T> getAllData(modelClass: Class<T>): List<T> = withContext(Dispatchers.IO) {{
        // TODO: 実装
        // データベースからすべてのデータを取得し、モデルクラスのリストにデシリアライズする
        emptyList()
    }}

    override suspend fun <T> saveData(id: String, data: T) = withContext(Dispatchers.IO) {{
        // TODO: 実装
        // モデルクラスをシリアライズし、データベースに保存する
    }}

    override suspend fun deleteData(id: String) = withContext(Dispatchers.IO) {{
        // TODO: 実装
        // データベースからデータを削除する
    }}

    override suspend fun deleteAllData() = withContext(Dispatchers.IO) {{
        // TODO: 実装
        // データベースからすべてのデータを削除する
    }}
}}
"""

    # ローカルデータソースを書き込み
    write_file(local_data_source_path, local_data_source_content)
    print(f"ローカルデータソースを作成しました: {local_data_source_path}")

    # リモートデータソースのファイルパス
    remote_data_source_dir = os.path.join(package_dir, 'data/remote')
    os.makedirs(remote_data_source_dir, exist_ok=True)
    remote_data_source_path = os.path.join(remote_data_source_dir, 'RemoteDataSource.kt')

    # リモートデータソースの内容
    remote_data_source_content = f"""package {package_name}.data.remote

import io.ktor.client.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import {package_name}.models.*

/**
 * リモートデータソースのインターフェース
 */
interface RemoteDataSource {{
    suspend fun <T> fetchData(endpoint: String, modelClass: Class<T>): T?
    suspend fun <T> fetchAllData(endpoint: String, modelClass: Class<T>): List<T>
    suspend fun <T> postData(endpoint: String, data: T): Boolean
    suspend fun deleteData(endpoint: String, id: String): Boolean
}}

/**
 * リモートデータソースの実装
 */
class RemoteDataSourceImpl(
    private val client: HttpClient
) : RemoteDataSource {{

    private val json = Json {{ ignoreUnknownKeys = true }}
    private val baseUrl = "https://api.example.com" // TODO: 実際の API URL に変更

    override suspend fun <T> fetchData(endpoint: String, modelClass: Class<T>): T? = withContext(Dispatchers.IO) {{
        try {{
            val response = client.get("$baseUrl/$endpoint")
            if (response.status.isSuccess()) {{
                val responseText = response.bodyAsText()
                json.decodeFromString(responseText) as T
            }} else {{
                null
            }}
        }} catch (e: Exception) {{
            null
        }}
    }}

    override suspend fun <T> fetchAllData(endpoint: String, modelClass: Class<T>): List<T> = withContext(Dispatchers.IO) {{
        try {{
            val response = client.get("$baseUrl/$endpoint")
            if (response.status.isSuccess()) {{
                val responseText = response.bodyAsText()
                json.decodeFromString<List<T>>(responseText)
            }} else {{
                emptyList()
            }}
        }} catch (e: Exception) {{
            emptyList()
        }}
    }}

    override suspend fun <T> postData(endpoint: String, data: T): Boolean = withContext(Dispatchers.IO) {{
        try {{
            val response = client.post("$baseUrl/$endpoint") {{
                contentType(ContentType.Application.Json)
                setBody(data)
            }}
            response.status.isSuccess()
        }} catch (e: Exception) {{
            false
        }}
    }}

    override suspend fun deleteData(endpoint: String, id: String): Boolean = withContext(Dispatchers.IO) {{
        try {{
            val response = client.delete("$baseUrl/$endpoint/$id")
            response.status.isSuccess()
        }} catch (e: Exception) {{
            false
        }}
    }}
}}
"""

    # リモートデータソースを書き込み
    write_file(remote_data_source_path, remote_data_source_content)
    print(f"リモートデータソースを作成しました: {remote_data_source_path}")