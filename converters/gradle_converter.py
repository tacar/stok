#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gradle 設定を行うモジュール
"""

import os
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

    # プロジェクトの build.gradle.kts を更新
    update_project_build_gradle(output_dir)

    # アプリの build.gradle.kts を更新
    update_app_build_gradle(output_dir, project_info, package_name, app_name)

    # settings.gradle.kts を更新
    update_settings_gradle(output_dir, app_name)

    # gradle.properties を更新
    update_gradle_properties(output_dir)

    print("Gradle 設定が完了しました。")

def update_project_build_gradle(output_dir: str) -> None:
    """
    プロジェクトの build.gradle.kts を更新します。

    Args:
        output_dir: 出力先ディレクトリ
    """
    # build.gradle.kts のパス
    build_gradle_path = os.path.join(output_dir, 'build.gradle.kts')

    # tmpkotlinのbuild.gradle.ktsを読み込む
    template_build_gradle_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'tmpkotlin', 'build.gradle.kts')

    if os.path.exists(template_build_gradle_path):
        # テンプレートファイルが存在する場合はそれを使用
        build_gradle_content = read_file(template_build_gradle_path)
        print(f"tmpkotlinのbuild.gradle.ktsを使用します: {template_build_gradle_path}")
    else:
        # テンプレートファイルが存在しない場合はデフォルトの内容を使用
        print(f"警告: tmpkotlinのbuild.gradle.ktsが見つかりません。デフォルトの設定を使用します。")
        build_gradle_content = """// Top-level build file where you can add configuration options common to all sub-projects/modules.
plugins {
    id("com.android.application") version "8.1.0" apply false
    id("com.android.library") version "8.1.0" apply false
    id("org.jetbrains.kotlin.android") version "1.8.10" apply false
    id("org.jetbrains.kotlin.plugin.serialization") version "1.8.10" apply false
    id("com.google.gms.google-services") version "4.3.15" apply false
    id("com.google.firebase.crashlytics") version "2.9.4" apply false
    id("app.cash.sqldelight") version "2.0.0" apply false
}

buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath("com.android.tools.build:gradle:8.1.0")
        classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:1.8.10")
        classpath("com.google.gms:google-services:4.3.15")
        classpath("com.google.firebase:firebase-crashlytics-gradle:2.9.4")
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

tasks.register("clean", Delete::class) {
    delete(rootProject.buildDir)
}
"""

    # build.gradle.kts を書き込み
    write_file(build_gradle_path, build_gradle_content)
    print(f"プロジェクトの build.gradle.kts を更新しました: {build_gradle_path}")

def update_app_build_gradle(output_dir: str, project_info: Dict[str, Any], package_name: str, app_name: str) -> None:
    """
    アプリの build.gradle.kts を更新します。

    Args:
        output_dir: 出力先ディレクトリ
        project_info: プロジェクト情報
        package_name: Android アプリのパッケージ名
        app_name: アプリケーション名
    """
    # app/build.gradle.kts のパス
    app_build_gradle_path = os.path.join(output_dir, 'app/build.gradle.kts')

    # tmpkotlinのapp/build.gradle.ktsを読み込む
    template_app_build_gradle_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'tmpkotlin', 'app', 'build.gradle.kts')

    if os.path.exists(template_app_build_gradle_path):
        # テンプレートファイルが存在する場合はそれを使用し、パッケージ名とアプリケーションIDを置換
        app_build_gradle_content = read_file(template_app_build_gradle_path)

        # パッケージ名とアプリケーションIDを置換
        app_build_gradle_content = app_build_gradle_content.replace("com.company.amap", package_name)

        # SQLDelightのデータベース名を置換（存在する場合）
        if "create(\"" in app_build_gradle_content and "Database\")" in app_build_gradle_content:
            # 既存のデータベース名を抽出
            import re
            db_name_match = re.search(r'create\("([^"]+)Database"\)', app_build_gradle_content)
            if db_name_match:
                existing_db_name = db_name_match.group(1)
                app_build_gradle_content = app_build_gradle_content.replace(
                    f'create("{existing_db_name}Database")',
                    f'create("{app_name}Database")'
                )

        print(f"tmpkotlinのapp/build.gradle.ktsを使用します: {template_app_build_gradle_path}")
    else:
        # テンプレートファイルが存在しない場合はデフォルトの内容を使用
        print(f"警告: tmpkotlinのapp/build.gradle.ktsが見つかりません。デフォルトの設定を使用します。")
        app_build_gradle_content = f"""plugins {{
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.serialization")
    id("com.google.gms.google-services")
    id("com.google.firebase.crashlytics")
    id("app.cash.sqldelight")
}}

android {{
    namespace = "{package_name}"
    compileSdk = 34

    defaultConfig {{
        applicationId = "{package_name}"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables {{
            useSupportLibrary = true
        }}
    }}

    buildTypes {{
        release {{
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }}
    }}

    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }}

    kotlinOptions {{
        jvmTarget = "17"
    }}

    buildFeatures {{
        compose = true
    }}

    composeOptions {{
        kotlinCompilerExtensionVersion = "1.4.3"
    }}

    packaging {{
        resources {{
            excludes += "/META-INF/{{AL2.0,LGPL2.1}}"
        }}
    }}
}}

dependencies {{
    // AndroidX
    implementation("androidx.core:core-ktx:1.10.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.6.1")
    implementation("androidx.activity:activity-compose:1.7.2")

    // Compose
    implementation(platform("androidx.compose:compose-bom:2023.03.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.navigation:navigation-compose:2.7.0")

    // Koin
    implementation("io.insert-koin:koin-android:3.4.0")
    implementation("io.insert-koin:koin-androidx-compose:3.4.0")

    // Ktor
    implementation("io.ktor:ktor-client-android:2.3.2")
    implementation("io.ktor:ktor-client-content-negotiation:2.3.2")
    implementation("io.ktor:ktor-serialization-kotlinx-json:2.3.2")
    implementation("io.ktor:ktor-client-logging:2.3.2")

    // SQLDelight
    implementation("app.cash.sqldelight:android-driver:2.0.0")
    implementation("app.cash.sqldelight:coroutines-extensions:2.0.0")
    implementation("app.cash.sqldelight:primitive-adapters:2.0.0")

    // Firebase
    implementation(platform("com.google.firebase:firebase-bom:32.2.2"))
    implementation("com.google.firebase:firebase-auth-ktx")
    implementation("com.google.firebase:firebase-analytics-ktx")
    implementation("com.google.firebase:firebase-crashlytics-ktx")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-play-services:1.6.4")

    // Kotlinx Serialization
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.5.1")

    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.1")

    // Testing
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
    androidTestImplementation(platform("androidx.compose:compose-bom:2023.03.00"))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")

    // Debug
    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}}

sqldelight {{
    databases {{
        create("{app_name}Database") {{
            packageName = "{package_name}.data.local"
        }}
    }}
}}
"""

    # app/build.gradle.kts を書き込み
    write_file(app_build_gradle_path, app_build_gradle_content)
    print(f"アプリの build.gradle.kts を更新しました: {app_build_gradle_path}")

def update_settings_gradle(output_dir: str, app_name: str) -> None:
    """
    settings.gradle.kts を更新します。

    Args:
        output_dir: 出力先ディレクトリ
        app_name: アプリケーション名
    """
    # settings.gradle.kts のパス
    settings_gradle_path = os.path.join(output_dir, 'settings.gradle.kts')

    # tmpkotlinのsettings.gradle.ktsを読み込む
    template_settings_gradle_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'tmpkotlin', 'settings.gradle.kts')

    if os.path.exists(template_settings_gradle_path):
        # テンプレートファイルが存在する場合はそれを使用し、プロジェクト名を置換
        settings_gradle_content = read_file(template_settings_gradle_path)

        # プロジェクト名を置換
        import re
        settings_gradle_content = re.sub(
            r'rootProject\.name\s*=\s*"[^"]*"',
            f'rootProject.name = "{app_name.lower()}"',
            settings_gradle_content
        )

        print(f"tmpkotlinのsettings.gradle.ktsを使用します: {template_settings_gradle_path}")
    else:
        # テンプレートファイルが存在しない場合はデフォルトの内容を使用
        print(f"警告: tmpkotlinのsettings.gradle.ktsが見つかりません。デフォルトの設定を使用します。")
        settings_gradle_content = f"""pluginManagement {{
    repositories {{
        google()
        mavenCentral()
        gradlePluginPortal()
    }}
}}

dependencyResolutionManagement {{
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {{
        google()
        mavenCentral()
    }}
}}

rootProject.name = "{app_name.lower()}"
include(":app")
"""

    # settings.gradle.kts を書き込み
    write_file(settings_gradle_path, settings_gradle_content)
    print(f"settings.gradle.kts を更新しました: {settings_gradle_path}")

def update_gradle_properties(output_dir: str) -> None:
    """
    gradle.properties を更新します。

    Args:
        output_dir: 出力先ディレクトリ
    """
    # gradle.properties のパス
    gradle_properties_path = os.path.join(output_dir, 'gradle.properties')

    # tmpkotlinのgradle.propertiesを読み込む
    template_gradle_properties_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'tmpkotlin', 'gradle.properties')

    if os.path.exists(template_gradle_properties_path):
        # テンプレートファイルが存在する場合はそれを使用
        gradle_properties_content = read_file(template_gradle_properties_path)
        print(f"tmpkotlinのgradle.propertiesを使用します: {template_gradle_properties_path}")
    else:
        # テンプレートファイルが存在しない場合はデフォルトの内容を使用
        print(f"警告: tmpkotlinのgradle.propertiesが見つかりません。デフォルトの設定を使用します。")
        gradle_properties_content = """# Project-wide Gradle settings.
# IDE (e.g. Android Studio) users:
# Gradle settings configured through the IDE *will override*
# any settings specified in this file.
# For more details on how to configure your build environment visit
# http://www.gradle.org/docs/current/userguide/build_environment.html
# Specifies the JVM arguments used for the daemon process.
# The setting is particularly useful for tweaking memory settings.
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
# When configured, Gradle will run in incubating parallel mode.
# This option should only be used with decoupled projects. More details, visit
# http://www.gradle.org/docs/current/userguide/multi_project_builds.html#sec:decoupled_projects
org.gradle.parallel=true
# AndroidX package structure to make it clearer which packages are bundled with the
# Android operating system, and which are packaged with your app's APK
# https://developer.android.com/topic/libraries/support-library/androidx-rn
android.useAndroidX=true
# Kotlin code style for this project: "official" or "obsolete":
kotlin.code.style=official
# Enables namespacing of each library's R class so that its R class includes only the
# resources declared in the library itself and none from the library's dependencies,
# thereby reducing the size of the R class for that library
android.nonTransitiveRClass=true
"""

    # gradle.properties を書き込み
    write_file(gradle_properties_path, gradle_properties_content)
    print(f"gradle.properties を更新しました: {gradle_properties_path}")