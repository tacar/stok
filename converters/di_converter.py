#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Koin を使用した依存性注入モジュールを作成するモジュール
"""

import os
from typing import Dict, List, Any

from utils.file_utils import write_file

def setup_dependency_injection(package_dir: str, project_info: Dict[str, Any], package_name: str) -> None:
    """
    Koin を使用した依存性注入モジュールを作成します。

    Args:
        package_dir: 変換先の Android パッケージディレクトリ
        project_info: プロジェクト情報
        package_name: Android アプリのパッケージ名
    """
    print("依存性注入モジュールを作成しています...")

    di_dir = os.path.join(package_dir, 'di')
    os.makedirs(di_dir, exist_ok=True)

    # AppModule.kt を作成
    app_module_path = os.path.join(di_dir, 'AppModule.kt')
    app_module_content = generate_app_module(project_info, package_name)
    write_file(app_module_path, app_module_content)
    print(f"依存性注入モジュールを作成しました: {app_module_path}")

    # ViewModelModule.kt を作成
    viewmodel_module_path = os.path.join(di_dir, 'ViewModelModule.kt')
    viewmodel_module_content = generate_viewmodel_module(project_info, package_name)
    write_file(viewmodel_module_path, viewmodel_module_content)
    print(f"ViewModel モジュールを作成しました: {viewmodel_module_path}")

    # RepositoryModule.kt を作成
    repository_module_path = os.path.join(di_dir, 'RepositoryModule.kt')
    repository_module_content = generate_repository_module(project_info, package_name)
    write_file(repository_module_path, repository_module_content)
    print(f"リポジトリモジュールを作成しました: {repository_module_path}")

    # ServiceModule.kt を作成
    service_module_path = os.path.join(di_dir, 'ServiceModule.kt')
    service_module_content = generate_service_module(project_info, package_name)
    write_file(service_module_path, service_module_content)
    print(f"サービスモジュールを作成しました: {service_module_path}")

    # DataModule.kt を作成
    data_module_path = os.path.join(di_dir, 'DataModule.kt')
    data_module_content = generate_data_module(project_info, package_name)
    write_file(data_module_path, data_module_content)
    print(f"データモジュールを作成しました: {data_module_path}")

def generate_app_module(project_info: Dict[str, Any], package_name: str) -> str:
    """
    Koin の AppModule を生成します。

    Args:
        project_info: プロジェクト情報
        package_name: Android アプリのパッケージ名

    Returns:
        生成された AppModule のコード
    """
    lines = [
        f"package {package_name}.di",
        "",
        "import android.content.Context",
        "import org.koin.android.ext.koin.androidContext",
        "import org.koin.dsl.module",
        "import io.ktor.client.*",
        "import io.ktor.client.engine.android.*",
        "import io.ktor.client.features.json.*",
        "import io.ktor.client.features.json.serializer.*",
        "import io.ktor.client.features.logging.*",
        f"import {package_name}.data.local.AppDatabase",
        "",
        "val appModule = module {",
        "    // HTTP クライアント",
        "    single {",
        "        HttpClient(Android) {",
        "            install(JsonFeature) {",
        "                serializer = KotlinxSerializer(kotlinx.serialization.json.Json {",
        "                    prettyPrint = true",
        "                    isLenient = true",
        "                    ignoreUnknownKeys = true",
        "                })",
        "            }",
        "            install(Logging) {",
        "                level = LogLevel.BODY",
        "            }",
        "        }",
        "    }",
        "",
        "    // データベース",
        "    single { AppDatabase.getInstance(androidContext()) }",
        "",
        "    // データソース",
        f"    single {{ get<AppDatabase>().{package_name.split('.')[-1]}Database }}",
        "}"
    ]

    return "\n".join(lines)

def generate_viewmodel_module(project_info: Dict[str, Any], package_name: str) -> str:
    """
    Koin の ViewModelModule を生成します。

    Args:
        project_info: プロジェクト情報
        package_name: Android アプリのパッケージ名

    Returns:
        生成された ViewModelModule のコード
    """
    lines = [
        f"package {package_name}.di",
        "",
        "import org.koin.androidx.viewmodel.dsl.viewModel",
        "import org.koin.dsl.module",
        f"import {package_name}.viewmodels.*",
        "",
        "val viewModelModule = module {"
    ]

    # ViewModel の依存関係を追加
    for viewmodel_path in project_info['viewmodels']:
        filename = os.path.basename(viewmodel_path)
        viewmodel_name = os.path.splitext(filename)[0]

        lines.append(f"    viewModel {{ {viewmodel_name}(get()) }}")

    # デフォルトの ViewModel を追加
    if not project_info['viewmodels']:
        lines.extend([
            "    viewModel { MainViewModel(get()) }",
            "    viewModel { HomeViewModel(get()) }",
            "    viewModel { SettingsViewModel(get()) }"
        ])

    lines.append("}")

    return "\n".join(lines)

def generate_repository_module(project_info: Dict[str, Any], package_name: str) -> str:
    """
    Koin の RepositoryModule を生成します。

    Args:
        project_info: プロジェクト情報
        package_name: Android アプリのパッケージ名

    Returns:
        生成された RepositoryModule のコード
    """
    lines = [
        f"package {package_name}.di",
        "",
        "import org.koin.dsl.module",
        f"import {package_name}.repositories.*",
        f"import {package_name}.data.local.*",
        f"import {package_name}.data.remote.*",
        "",
        "val repositoryModule = module {"
    ]

    # リポジトリの依存関係を追加
    for repo_path in project_info['repositories']:
        filename = os.path.basename(repo_path)
        repo_name = os.path.splitext(filename)[0]
        interface_name = repo_name.replace("Repository", "")

        lines.append(f"    single<{interface_name}Repository> {{ {repo_name}Impl(get(), get()) }}")

    # デフォルトのリポジトリを追加
    if not project_info['repositories']:
        lines.extend([
            "    single<UserRepository> { UserRepositoryImpl(get(), get()) }",
            "    single<DataRepository> { DataRepositoryImpl(get(), get()) }"
        ])

    lines.append("}")

    return "\n".join(lines)

def generate_service_module(project_info: Dict[str, Any], package_name: str) -> str:
    """
    Koin の ServiceModule を生成します。

    Args:
        project_info: プロジェクト情報
        package_name: Android アプリのパッケージ名

    Returns:
        生成された ServiceModule のコード
    """
    lines = [
        f"package {package_name}.di",
        "",
        "import org.koin.dsl.module",
        f"import {package_name}.services.*",
        "",
        "val serviceModule = module {"
    ]

    # サービスの依存関係を追加
    for service_path in project_info['services']:
        filename = os.path.basename(service_path)
        service_name = os.path.splitext(filename)[0]

        lines.append(f"    single<{service_name}> {{ {service_name}Impl() }}")

    # デフォルトのサービスを追加
    if not project_info['services']:
        lines.extend([
            "    single<ApiService> { ApiServiceImpl() }",
            "    single<AuthService> { AuthServiceImpl() }"
        ])

    lines.append("}")

    return "\n".join(lines)

def generate_data_module(project_info: Dict[str, Any], package_name: str) -> str:
    """
    Koin の DataModule を生成します。

    Args:
        project_info: プロジェクト情報
        package_name: Android アプリのパッケージ名

    Returns:
        生成された DataModule のコード
    """
    lines = [
        f"package {package_name}.di",
        "",
        "import org.koin.dsl.module",
        f"import {package_name}.data.local.*",
        f"import {package_name}.data.remote.*",
        "",
        "val dataModule = module {",
        "    // ローカルデータソース",
        "    single<LocalDataSource> { LocalDataSourceImpl(get()) }",
        "",
        "    // リモートデータソース",
        "    single<RemoteDataSource> { RemoteDataSourceImpl(get()) }",
        "}"
    ]

    return "\n".join(lines)