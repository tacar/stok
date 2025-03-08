#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ktor を使用したネットワーク設定を行うモジュール
"""

import os
from typing import Dict, List, Any

from utils.file_utils import read_file, write_file

def setup_network(package_dir: str, project_info: Dict[str, Any], package_name: str) -> None:
    """
    Ktor を使用したネットワーク設定を行います。

    Args:
        package_dir: 変換先の Android パッケージディレクトリ
        project_info: プロジェクト情報
        package_name: Android アプリのパッケージ名
    """
    print("Ktor ネットワーク設定を行っています...")

    # API クライアントを作成
    create_api_client(package_dir, package_name)

    # API サービスを作成
    create_api_service(package_dir, package_name)

    print("Ktor ネットワーク設定が完了しました。")

def create_api_client(package_dir: str, package_name: str) -> None:
    """
    API クライアントを作成します。

    Args:
        package_dir: 変換先の Android パッケージディレクトリ
        package_name: Android アプリのパッケージ名
    """
    # API クライアントディレクトリを作成
    api_dir = os.path.join(package_dir, 'api')
    os.makedirs(api_dir, exist_ok=True)

    # API クライアントのファイルパス
    api_client_path = os.path.join(api_dir, 'ApiClient.kt')

    # API クライアントの内容
    api_client_content = f"""package {package_name}.api

import io.ktor.client.*
import io.ktor.client.engine.android.*
import io.ktor.client.features.*
import io.ktor.client.features.json.*
import io.ktor.client.features.json.serializer.*
import io.ktor.client.features.logging.*
import io.ktor.client.request.*
import io.ktor.http.*

/**
 * API クライアント
 */
object ApiClient {{
    private const val BASE_URL = "https://api.example.com" // TODO: 実際の API URL に変更

    /**
     * HTTP クライアントを作成します。
     */
    fun create(): HttpClient {{
        return HttpClient(Android) {{
            // JSON シリアライザ
            install(JsonFeature) {{
                serializer = KotlinxSerializer(kotlinx.serialization.json.Json {{
                    prettyPrint = true
                    isLenient = true
                    ignoreUnknownKeys = true
                }})
            }}

            // ロギング
            install(Logging) {{
                logger = Logger.DEFAULT
                level = LogLevel.HEADERS
            }}

            // タイムアウト設定
            install(HttpTimeout) {{
                requestTimeoutMillis = 30000
                connectTimeoutMillis = 30000
                socketTimeoutMillis = 30000
            }}

            // デフォルトリクエスト設定
            defaultRequest {{
                url {{
                    protocol = URLProtocol.HTTPS
                    host = BASE_URL.removePrefix("https://")
                }}
                contentType(ContentType.Application.Json)
            }}
        }}
    }}
}}
"""

    # API クライアントを書き込み
    write_file(api_client_path, api_client_content)
    print(f"API クライアントを作成しました: {api_client_path}")

def create_api_service(package_dir: str, package_name: str) -> None:
    """
    API サービスを作成します。

    Args:
        package_dir: 変換先の Android パッケージディレクトリ
        package_name: Android アプリのパッケージ名
    """
    # API サービスディレクトリを作成
    api_dir = os.path.join(package_dir, 'api')
    os.makedirs(api_dir, exist_ok=True)

    # API サービスのファイルパス
    api_service_path = os.path.join(api_dir, 'ApiService.kt')

    # API サービスの内容
    api_service_content = f"""package {package_name}.api

import io.ktor.client.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import {package_name}.models.*

/**
 * API サービスのインターフェース
 */
interface ApiService {{
    suspend fun <T> get(endpoint: String, responseType: Class<T>): Result<T>
    suspend fun <T, R> post(endpoint: String, body: T, responseType: Class<R>): Result<R>
    suspend fun <T, R> put(endpoint: String, body: T, responseType: Class<R>): Result<R>
    suspend fun delete(endpoint: String): Result<Boolean>
}}

/**
 * API サービスの実装
 */
class ApiServiceImpl(
    private val client: HttpClient
) : ApiService {{

    private val json = Json {{ ignoreUnknownKeys = true }}

    override suspend fun <T> get(endpoint: String, responseType: Class<T>): Result<T> = withContext(Dispatchers.IO) {{
        try {{
            val response = client.get<HttpResponse>(endpoint)
            if (response.status.isSuccess()) {{
                val responseText = response.readText()
                val result = json.decodeFromString(responseText) as T
                Result.success(result)
            }} else {{
                Result.failure(Exception("API エラー: ${{response.status.value}}"))
            }}
        }} catch (e: Exception) {{
            Result.failure(e)
        }}
    }}

    override suspend fun <T, R> post(endpoint: String, body: T, responseType: Class<R>): Result<R> = withContext(Dispatchers.IO) {{
        try {{
            val response = client.post<HttpResponse>(endpoint) {{
                contentType(ContentType.Application.Json)
                body = body
            }}
            if (response.status.isSuccess()) {{
                val responseText = response.readText()
                val result = json.decodeFromString(responseText) as R
                Result.success(result)
            }} else {{
                Result.failure(Exception("API エラー: ${{response.status.value}}"))
            }}
        }} catch (e: Exception) {{
            Result.failure(e)
        }}
    }}

    override suspend fun <T, R> put(endpoint: String, body: T, responseType: Class<R>): Result<R> = withContext(Dispatchers.IO) {{
        try {{
            val response = client.put<HttpResponse>(endpoint) {{
                contentType(ContentType.Application.Json)
                body = body
            }}
            if (response.status.isSuccess()) {{
                val responseText = response.readText()
                val result = json.decodeFromString(responseText) as R
                Result.success(result)
            }} else {{
                Result.failure(Exception("API エラー: ${{response.status.value}}"))
            }}
        }} catch (e: Exception) {{
            Result.failure(e)
        }}
    }}

    override suspend fun delete(endpoint: String): Result<Boolean> = withContext(Dispatchers.IO) {{
        try {{
            val response = client.delete<HttpResponse>(endpoint)
            Result.success(response.status.isSuccess())
        }} catch (e: Exception) {{
            Result.failure(e)
        }}
    }}
}}
"""

    # API サービスを書き込み
    write_file(api_service_path, api_service_content)
    print(f"API サービスを作成しました: {api_service_path}")

    # API モデルディレクトリを作成
    api_models_dir = os.path.join(api_dir, 'models')
    os.makedirs(api_models_dir, exist_ok=True)

    # API レスポンスモデルのファイルパス
    api_response_path = os.path.join(api_models_dir, 'ApiResponse.kt')

    # API レスポンスモデルの内容
    api_response_content = f"""package {package_name}.api.models

import kotlinx.serialization.Serializable

/**
 * API レスポンスの基本モデル
 */
@Serializable
data class ApiResponse<T>(
    val success: Boolean,
    val data: T? = null,
    val error: ApiError? = null
)

/**
 * API エラーモデル
 */
@Serializable
data class ApiError(
    val code: String,
    val message: String
)
"""

    # API レスポンスモデルを書き込み
    write_file(api_response_path, api_response_content)
    print(f"API レスポンスモデルを作成しました: {api_response_path}")