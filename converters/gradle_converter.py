#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gradle 設定を行うモジュール
"""

import os
import re
from typing import Dict, List, Any

from utils.file_utils import read_file, write_file

def setup_gradle(output_dir: str, project_info: Dict[str, Any], package_name: str, app_name: str) -> None:
    """
    Gradle 設定を行います。

    Args:
        output_dir: 出力先ディレクトリ
        project_info: プロジェクト情報
        package_name: Android アプリのパッケージ名
        app_name: アプリケーション名
    """
    print("Gradle 設定を行っています...")

    # tmpkotlinディレクトリのパス
    tmpkotlin_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'tmpkotlin')

    try:
        # 1. build.gradle.kts をコピー
        src_build_gradle = os.path.join(tmpkotlin_dir, 'build.gradle.kts')
        dst_build_gradle = os.path.join(output_dir, 'build.gradle.kts')
        if os.path.exists(src_build_gradle):
            content = read_file(src_build_gradle)
            write_file(dst_build_gradle, content)
            print(f"build.gradle.kts をコピーしました: {dst_build_gradle}")
        else:
            print(f"警告: tmpkotlinのbuild.gradle.ktsが見つかりません: {src_build_gradle}")

        # 2. app/build.gradle.kts を作成
        src_app_build_gradle = os.path.join(tmpkotlin_dir, 'app/build.gradle.kts')
        dst_app_build_gradle = os.path.join(output_dir, 'app/build.gradle.kts')
        if os.path.exists(src_app_build_gradle):
            # テンプレートファイルを読み込む
            content = read_file(src_app_build_gradle)

            # パッケージ名を置換
            content = content.replace("com.company.amap", package_name)

            # releaseビルドタイプのisDebuggable設定を必ずfalseに設定
            content = re.sub(
                r'(release\s*\{[^}]*isDebuggable\s*=\s*)true([^}]*\})',
                r'\1false\2',
                content
            )

            # SQLDelightの設定を修正

            # 1. プラグインの修正: app.cash.sqldelightを削除し、com.squareup.sqldelightを使用
            plugins_pattern = r'plugins\s*\{([^}]*)\}'
            plugins_match = re.search(plugins_pattern, content)
            if plugins_match:
                plugins_block = plugins_match.group(1)
                # app.cash.sqldelightプラグインを削除
                plugins_block = re.sub(
                    r'\s*id\(["\']app\.cash\.sqldelight["\']\).*?\n',
                    '\n',
                    plugins_block
                )
                # com.squareup.sqldelightプラグインが既にあるか確認
                if 'id("com.squareup.sqldelight")' not in plugins_block:
                    plugins_block = plugins_block.rstrip() + '\n    id("com.squareup.sqldelight")\n'
                content = content.replace(plugins_match.group(1), plugins_block)

            # 2. defaultConfig内のSQLDelightブロックを削除
            content = re.sub(
                r'(defaultConfig\s*\{[^}]*?)sqldelight\s*\{[^}]*?\}\s*\}([^}]*?\})',
                r'\1\2',
                content,
                flags=re.DOTALL
            )

            # 3. 依存関係の修正: app.cash.sqldelightの依存関係を削除し、com.squareup.sqldelightの依存関係を追加
            dependencies_pattern = r'dependencies\s*\{([^}]*)\}'
            dependencies_match = re.search(dependencies_pattern, content, re.DOTALL)
            if dependencies_match:
                dependencies_block = dependencies_match.group(1)

                # app.cash.sqldelightの依存関係を削除
                dependencies_block = re.sub(
                    r'\s*\/\/\s*SQLDelight\s*\n\s*implementation\(["\']app\.cash\.sqldelight:.*?\n\s*implementation\(["\']app\.cash\.sqldelight:.*?\n\s*implementation\(["\']app\.cash\.sqldelight:.*?\n',
                    '\n',
                    dependencies_block,
                    flags=re.DOTALL
                )

                # com.squareup.sqldelightの依存関係がなければ追加
                if 'com.squareup.sqldelight:android-driver' not in dependencies_block:
                    sqldelight_deps = """
    // SQLDelight
    implementation("com.squareup.sqldelight:android-driver:1.5.5")
    implementation("com.squareup.sqldelight:coroutines-extensions:1.5.5")
    implementation("com.squareup.sqldelight:runtime-jvm:1.5.5")
"""
                    dependencies_block = dependencies_block.rstrip() + sqldelight_deps

                content = content.replace(dependencies_match.group(1), dependencies_block)

            # 4. ファイル末尾のSQLDelightブロックを修正
            sqldelight_block_pattern = r'sqldelight\s*\{[^}]*\}\s*\}'
            if re.search(sqldelight_block_pattern, content, re.DOTALL):
                # 既存のSQLDelightブロックを削除
                content = re.sub(sqldelight_block_pattern, '', content, flags=re.DOTALL)

            # 新しいSQLDelightブロックを追加
            sqldelight_block = f"""
sqldelight {{
    database("{app_name}Database") {{
        packageName = "{package_name}.database"
        sourceFolders = listOf("sqldelight")
        schemaOutputDirectory = file("build/dbs")
        verifyMigrations = true
    }}
}}
"""
            # kspブロックの前に追加
            ksp_pattern = r'ksp\s*\{[^}]*\}'
            if re.search(ksp_pattern, content, re.DOTALL):
                content = re.sub(
                    ksp_pattern,
                    sqldelight_block + '\n' + re.search(ksp_pattern, content, re.DOTALL).group(0),
                    content,
                    flags=re.DOTALL
                )
            else:
                # kspブロックがなければ最後に追加
                content += '\n' + sqldelight_block

            # SQLDelightディレクトリを作成
            os.makedirs(os.path.join(output_dir, 'app/sqldelight'), exist_ok=True)

            write_file(dst_app_build_gradle, content)
            print(f"app/build.gradle.kts を作成しました: {dst_app_build_gradle}")
        else:
            print(f"警告: tmpkotlinのapp/build.gradle.ktsが見つかりません: {src_app_build_gradle}")

        # 3. settings.gradle.kts をコピー
        src_settings_gradle = os.path.join(tmpkotlin_dir, 'settings.gradle.kts')
        dst_settings_gradle = os.path.join(output_dir, 'settings.gradle.kts')
        if os.path.exists(src_settings_gradle):
            content = read_file(src_settings_gradle)
            # プロジェクト名を置換
            content = re.sub(
                r'rootProject\.name\s*=\s*"[^"]*"',
                f'rootProject.name = "{app_name.lower()}"',
                content
            )

            # settings.gradle.ktsを完全に書き直す（構文エラーを防ぐため）
            settings_content = f"""// settings.gradle.kts
pluginManagement {{
    repositories {{
        google()
        mavenCentral()
        gradlePluginPortal()
        maven(url = "https://maven.pkg.jetbrains.space/public/p/compose/dev")
    }}
}}

dependencyResolutionManagement {{
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {{
        google()
        mavenCentral()
        maven {{ url = uri("https://oss.sonatype.org/content/repositories/snapshots/") }}
        maven(url = "https://maven.pkg.jetbrains.space/public/p/compose/dev")
    }}
}}

rootProject.name = "{app_name.lower()}"
include(":app")
enableFeaturePreview("STABLE_CONFIGURATION_CACHE")
"""
            write_file(dst_settings_gradle, settings_content)
            print(f"settings.gradle.kts を作成しました: {dst_settings_gradle}")
        else:
            print(f"警告: tmpkotlinのsettings.gradle.ktsが見つかりません: {src_settings_gradle}")

        # 4. gradle.properties をコピー
        src_gradle_properties = os.path.join(tmpkotlin_dir, 'gradle.properties')
        dst_gradle_properties = os.path.join(output_dir, 'gradle.properties')
        if os.path.exists(src_gradle_properties):
            content = read_file(src_gradle_properties)
            write_file(dst_gradle_properties, content)
            print(f"gradle.properties をコピーしました: {dst_gradle_properties}")
        else:
            print(f"警告: tmpkotlinのgradle.propertiesが見つかりません: {src_gradle_properties}")

        # 5. keystore.properties をコピー
        src_keystore_properties = os.path.join(tmpkotlin_dir, 'keystore.properties')
        dst_keystore_properties = os.path.join(output_dir, 'keystore.properties')
        if os.path.exists(src_keystore_properties):
            content = read_file(src_keystore_properties)
            write_file(dst_keystore_properties, content)
            print(f"keystore.properties をコピーしました: {dst_keystore_properties}")
        else:
            print(f"警告: tmpkotlinのkeystore.propertiesが見つかりません: {src_keystore_properties}")

        # 6. キーストアファイルをコピー
        src_keystore_file = os.path.join(tmpkotlin_dir, 'amap.jks')
        dst_keystore_file = os.path.join(output_dir, 'amap.jks')
        if os.path.exists(src_keystore_file):
            import shutil
            shutil.copy2(src_keystore_file, dst_keystore_file)
            print(f"キーストアファイルをコピーしました: {dst_keystore_file}")
        else:
            print(f"警告: tmpkotlinのキーストアファイルが見つかりません: {src_keystore_file}")

        # 7. gradle-wrapper.properties をコピー
        src_wrapper_dir = os.path.join(tmpkotlin_dir, 'gradle/wrapper')
        dst_wrapper_dir = os.path.join(output_dir, 'gradle/wrapper')
        os.makedirs(dst_wrapper_dir, exist_ok=True)

        src_wrapper_properties = os.path.join(src_wrapper_dir, 'gradle-wrapper.properties')
        dst_wrapper_properties = os.path.join(dst_wrapper_dir, 'gradle-wrapper.properties')
        if os.path.exists(src_wrapper_properties):
            content = read_file(src_wrapper_properties)
            write_file(dst_wrapper_properties, content)
            print(f"gradle-wrapper.properties をコピーしました: {dst_wrapper_properties}")
        else:
            print(f"警告: tmpkotlinのgradle-wrapper.propertiesが見つかりません: {src_wrapper_properties}")

        # 8. gradle-wrapper.jar をコピー
        src_wrapper_jar = os.path.join(src_wrapper_dir, 'gradle-wrapper.jar')
        dst_wrapper_jar = os.path.join(dst_wrapper_dir, 'gradle-wrapper.jar')
        if os.path.exists(src_wrapper_jar):
            import shutil
            shutil.copy2(src_wrapper_jar, dst_wrapper_jar)
            print(f"gradle-wrapper.jar をコピーしました: {dst_wrapper_jar}")
        else:
            print(f"警告: tmpkotlinのgradle-wrapper.jarが見つかりません: {src_wrapper_jar}")

        # 9. gradlew と gradlew.bat をコピー
        src_gradlew = os.path.join(tmpkotlin_dir, 'gradlew')
        dst_gradlew = os.path.join(output_dir, 'gradlew')
        if os.path.exists(src_gradlew):
            import shutil
            shutil.copy2(src_gradlew, dst_gradlew)
            # 実行権限を付与
            os.chmod(dst_gradlew, 0o755)
            print(f"gradlew をコピーしました: {dst_gradlew}")
        else:
            print(f"警告: tmpkotlinのgradlewが見つかりません: {src_gradlew}")

        src_gradlew_bat = os.path.join(tmpkotlin_dir, 'gradlew.bat')
        dst_gradlew_bat = os.path.join(output_dir, 'gradlew.bat')
        if os.path.exists(src_gradlew_bat):
            import shutil
            shutil.copy2(src_gradlew_bat, dst_gradlew_bat)
            print(f"gradlew.bat をコピーしました: {dst_gradlew_bat}")
        else:
            print(f"警告: tmpkotlinのgradlew.batが見つかりません: {src_gradlew_bat}")

        # 10. google-services.json をコピー
        src_google_services = os.path.join(tmpkotlin_dir, 'app/google-services.json')
        dst_google_services = os.path.join(output_dir, 'app/google-services.json')
        if os.path.exists(src_google_services):
            import shutil
            shutil.copy2(src_google_services, dst_google_services)
            print(f"google-services.json をコピーしました: {dst_google_services}")

            # google-services.jsonファイル内のパッケージ名を更新
            try:
                import json
                with open(dst_google_services, 'r') as f:
                    google_services_data = json.load(f)

                # クライアント情報のパッケージ名を更新
                if 'client' in google_services_data and len(google_services_data['client']) > 0:
                    for client in google_services_data['client']:
                        if 'client_info' in client and 'android_client_info' in client['client_info']:
                            client['client_info']['android_client_info']['package_name'] = package_name

                # 更新したデータを書き込み
                with open(dst_google_services, 'w') as f:
                    json.dump(google_services_data, f, indent=2)

                print(f"google-services.json のパッケージ名を {package_name} に更新しました")
            except Exception as e:
                print(f"警告: google-services.json の更新中にエラーが発生しました: {e}")
        else:
            print(f"警告: tmpkotlinのgoogle-services.jsonが見つかりません: {src_google_services}")

            # google-services.jsonがない場合は、Firebaseプラグインを無効化
            try:
                # app/build.gradle.ktsからFirebaseプラグインを無効化
                app_build_gradle = os.path.join(output_dir, 'app/build.gradle.kts')
                if os.path.exists(app_build_gradle):
                    content = read_file(app_build_gradle)

                    # Firebaseプラグインを無効化（コメントアウト）
                    content = content.replace('id("com.google.gms.google-services")', '// id("com.google.gms.google-services")')
                    content = content.replace('id("com.google.firebase.crashlytics")', '// id("com.google.firebase.crashlytics")')

                    # Firebase依存関係をコメントアウト
                    content = re.sub(
                        r'(implementation\(platform\(libs\.firebase\.bom\)\))',
                        r'// \1',
                        content
                    )
                    content = re.sub(
                        r'(implementation\(libs\.firebase\.[^)]+\))',
                        r'// \1',
                        content
                    )
                    content = re.sub(
                        r'(implementation\("com\.google\.firebase:[^)]+\))',
                        r'// \1',
                        content
                    )
                    content = re.sub(
                        r'(implementation\("com\.firebaseui:[^)]+\))',
                        r'// \1',
                        content
                    )
                    content = re.sub(
                        r'(implementation\("com\.google\.android\.datatransport:[^)]+\))',
                        r'// \1',
                        content
                    )

                    write_file(app_build_gradle, content)
                    print("Firebaseプラグインと依存関係を無効化しました")
            except Exception as e:
                print(f"警告: Firebaseプラグインの無効化中にエラーが発生しました: {e}")

        print("Gradle 設定が完了しました。")
    except Exception as e:
        print(f"Gradle 設定中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()