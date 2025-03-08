#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Firebase 設定を行うモジュール
"""

import os
import shutil
from typing import Dict, List, Any

from utils.file_utils import read_file, write_file

def setup_firebase(output_dir: str, package_name: str) -> None:
    """
    Firebase の設定を行います。

    Args:
        output_dir: 出力先ディレクトリ
        package_name: Android アプリのパッケージ名
    """
    print("Firebase の設定を行っています...")

    # build.gradle.kts に Firebase の依存関係を追加
    update_build_gradle(output_dir, package_name)

    # Firebase 認証サービスを作成
    create_firebase_auth_service(output_dir, package_name)

    print("Firebase の設定が完了しました。")

def update_build_gradle(output_dir: str, package_name: str) -> None:
    """
    build.gradle.kts に Firebase の依存関係を追加します。

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

    # Firebase の依存関係を追加
    firebase_dependencies = """
    // Firebase
    implementation(platform("com.google.firebase:firebase-bom:32.0.0"))
    implementation("com.google.firebase:firebase-auth-ktx")
    implementation("com.google.firebase:firebase-analytics-ktx")
    implementation("com.google.firebase:firebase-crashlytics-ktx")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-play-services:1.6.4")
"""

    # 依存関係セクションを探して Firebase の依存関係を追加
    if "dependencies {" in content:
        content = content.replace("dependencies {", "dependencies {" + firebase_dependencies)
    else:
        print("警告: dependencies セクションが見つかりません。Firebase の依存関係を追加できませんでした。")

    # プラグインセクションを探して Firebase のプラグインを追加
    if "plugins {" in content:
        firebase_plugins = """
    id("com.google.gms.google-services")
    id("com.google.firebase.crashlytics")
"""
        content = content.replace("plugins {", "plugins {" + firebase_plugins)
    else:
        print("警告: plugins セクションが見つかりません。Firebase のプラグインを追加できませんでした。")

    # 更新した内容を書き込み
    write_file(app_build_gradle_path, content)

    # プロジェクトの build.gradle.kts にも Firebase のプラグインを追加
    project_build_gradle_path = os.path.join(output_dir, 'build.gradle.kts')

    if os.path.exists(project_build_gradle_path):
        content = read_file(project_build_gradle_path)

        # buildscript セクションを探して Firebase のプラグインを追加
        if "dependencies {" in content:
            firebase_classpath = """
        classpath("com.google.gms:google-services:4.3.15")
        classpath("com.google.firebase:firebase-crashlytics-gradle:2.9.4")
"""
            content = content.replace("dependencies {", "dependencies {" + firebase_classpath)

            # 更新した内容を書き込み
            write_file(project_build_gradle_path, content)
        else:
            print("警告: dependencies セクションが見つかりません。Firebase のプラグインを追加できませんでした。")

def create_firebase_auth_service(output_dir: str, package_name: str) -> None:
    """
    Firebase 認証サービスを作成します。

    Args:
        output_dir: 出力先ディレクトリ
        package_name: Android アプリのパッケージ名
    """
    # パッケージディレクトリを取得
    package_path = package_name.replace('.', '/')
    services_dir = os.path.join(output_dir, f'app/src/main/java/{package_path}/services')
    os.makedirs(services_dir, exist_ok=True)

    # Firebase 認証サービスのファイルパス
    auth_service_path = os.path.join(services_dir, 'FirebaseAuthService.kt')

    # Firebase 認証サービスの内容
    auth_service_content = f"""package {package_name}.services

import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseUser
import kotlinx.coroutines.tasks.await
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Firebase 認証サービスのインターフェース
 */
interface AuthService {{
    val currentUser: StateFlow<FirebaseUser?>

    suspend fun signIn(email: String, password: String): Result<FirebaseUser>
    suspend fun signUp(email: String, password: String): Result<FirebaseUser>
    suspend fun signOut()
    suspend fun resetPassword(email: String): Result<Unit>
}}

/**
 * Firebase 認証サービスの実装
 */
class FirebaseAuthService : AuthService {{
    private val auth = FirebaseAuth.getInstance()

    private val _currentUser = MutableStateFlow<FirebaseUser?>(auth.currentUser)
    override val currentUser: StateFlow<FirebaseUser?> = _currentUser.asStateFlow()

    init {{
        // 認証状態の変更を監視
        auth.addAuthStateListener {{ firebaseAuth ->
            _currentUser.value = firebaseAuth.currentUser
        }}
    }}

    override suspend fun signIn(email: String, password: String): Result<FirebaseUser> {{
        return try {{
            val authResult = auth.signInWithEmailAndPassword(email, password).await()
            Result.success(authResult.user!!)
        }} catch (e: Exception) {{
            Result.failure(e)
        }}
    }}

    override suspend fun signUp(email: String, password: String): Result<FirebaseUser> {{
        return try {{
            val authResult = auth.createUserWithEmailAndPassword(email, password).await()
            Result.success(authResult.user!!)
        }} catch (e: Exception) {{
            Result.failure(e)
        }}
    }}

    override suspend fun signOut() {{
        auth.signOut()
    }}

    override suspend fun resetPassword(email: String): Result<Unit> {{
        return try {{
            auth.sendPasswordResetEmail(email).await()
            Result.success(Unit)
        }} catch (e: Exception) {{
            Result.failure(e)
        }}
    }}
}}
"""

    # Firebase 認証サービスを書き込み
    write_file(auth_service_path, auth_service_content)

    # google-services.json をコピー（存在する場合）
    source_google_services = os.path.join(output_dir, 'google-services.json')
    dest_google_services = os.path.join(output_dir, 'app/google-services.json')

    if os.path.exists(source_google_services):
        shutil.copy2(source_google_services, dest_google_services)
        print(f"google-services.json をコピーしました: {dest_google_services}")
    else:
        print("警告: google-services.json が見つかりません。Firebase の設定が完了していない可能性があります。")
        # サンプルの google-services.json を作成
        sample_google_services = """
{
  "project_info": {
    "project_number": "000000000000",
    "project_id": "your-project-id",
    "storage_bucket": "your-project-id.appspot.com"
  },
  "client": [
    {
      "client_info": {
        "mobilesdk_app_id": "1:000000000000:android:0000000000000000000000",
        "android_client_info": {
          "package_name": "%s"
        }
      },
      "oauth_client": [],
      "api_key": [
        {
          "current_key": "your-api-key"
        }
      ],
      "services": {
        "appinvite_service": {
          "other_platform_oauth_client": []
        }
      }
    }
  ],
  "configuration_version": "1"
}
""" % package_name

        write_file(dest_google_services, sample_google_services)
        print(f"サンプルの google-services.json を作成しました: {dest_google_services}")
        print("警告: 実際の Firebase プロジェクトの google-services.json に置き換えてください。")