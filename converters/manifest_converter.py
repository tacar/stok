#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AndroidManifest.xml を生成するモジュール
"""

import os
from typing import Dict, List, Any

from utils.file_utils import write_file

def generate_manifest(output_dir: str, package_name: str, app_name: str) -> None:
    """
    AndroidManifest.xml を生成します。

    Args:
        output_dir: 出力先ディレクトリ
        package_name: Android アプリのパッケージ名
        app_name: アプリケーション名
    """
    print("AndroidManifest.xml を生成しています...")

    # AndroidManifest.xml のパス
    manifest_path = os.path.join(output_dir, 'app/src/main/AndroidManifest.xml')

    # AndroidManifest.xml の内容
    manifest_content = f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools"
    package="{package_name}">

    <!-- インターネット接続のパーミッション -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

    <application
        android:name=".MyApplication"
        android:allowBackup="true"
        android:dataExtractionRules="@xml/data_extraction_rules"
        android:fullBackupContent="@xml/backup_rules"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.MyApp"
        tools:targetApi="31">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:label="@string/app_name"
            android:theme="@style/Theme.MyApp">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

    </application>

</manifest>
"""

    # AndroidManifest.xml を書き込み
    write_file(manifest_path, manifest_content)
    print(f"AndroidManifest.xml を生成しました: {manifest_path}")

    # MyApplication.kt を生成
    generate_application_class(output_dir, package_name)

    # MainActivity.kt を生成
    generate_main_activity(output_dir, package_name)

    # data_extraction_rules.xml を生成
    generate_data_extraction_rules(output_dir)

    # backup_rules.xml を生成
    generate_backup_rules(output_dir)

def generate_application_class(output_dir: str, package_name: str) -> None:
    """
    アプリケーションクラスを生成します。

    Args:
        output_dir: 出力先ディレクトリ
        package_name: Android アプリのパッケージ名
    """
    # パッケージディレクトリを取得
    package_path = package_name.replace('.', '/')
    java_dir = os.path.join(output_dir, f'app/src/main/java/{package_path}')
    os.makedirs(java_dir, exist_ok=True)

    # MyApplication.kt のパス
    application_path = os.path.join(java_dir, 'MyApplication.kt')

    # MyApplication.kt の内容
    application_content = f"""package {package_name}

import android.app.Application
import org.koin.android.ext.koin.androidContext
import org.koin.android.ext.koin.androidLogger
import org.koin.core.context.startKoin
import org.koin.core.logger.Level
import {package_name}.di.*

/**
 * アプリケーションクラス
 */
class MyApplication : Application() {{

    override fun onCreate() {{
        super.onCreate()

        // Koin の初期化
        startKoin {{
            // ログレベルを設定
            androidLogger(Level.ERROR)

            // Android コンテキストを設定
            androidContext(this@MyApplication)

            // モジュールを登録
            modules(
                appModule,
                viewModelModule,
                repositoryModule,
                serviceModule,
                dataModule
            )
        }}
    }}
}}
"""

    # MyApplication.kt を書き込み
    write_file(application_path, application_content)
    print(f"アプリケーションクラスを生成しました: {application_path}")

def generate_main_activity(output_dir: str, package_name: str) -> None:
    """
    メインアクティビティを生成します。

    Args:
        output_dir: 出力先ディレクトリ
        package_name: Android アプリのパッケージ名
    """
    # パッケージディレクトリを取得
    package_path = package_name.replace('.', '/')
    java_dir = os.path.join(output_dir, f'app/src/main/java/{package_path}')
    os.makedirs(java_dir, exist_ok=True)

    # MainActivity.kt のパス
    activity_path = os.path.join(java_dir, 'MainActivity.kt')

    # MainActivity.kt の内容
    activity_content = f"""package {package_name}

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.navigation.compose.rememberNavController
import {package_name}.ui.theme.AppTheme
import {package_name}.ui.navigation.AppNavHost

/**
 * メインアクティビティ
 */
class MainActivity : ComponentActivity() {{

    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)

        setContent {{
            AppTheme {{
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {{
                    val navController = rememberNavController()
                    AppNavHost(navController = navController)
                }}
            }}
        }}
    }}
}}
"""

    # MainActivity.kt を書き込み
    write_file(activity_path, activity_content)
    print(f"メインアクティビティを生成しました: {activity_path}")

    # ナビゲーションを生成
    generate_navigation(output_dir, package_name)

    # テーマを生成
    generate_theme(output_dir, package_name)

def generate_navigation(output_dir: str, package_name: str) -> None:
    """
    ナビゲーションを生成します。

    Args:
        output_dir: 出力先ディレクトリ
        package_name: Android アプリのパッケージ名
    """
    # パッケージディレクトリを取得
    package_path = package_name.replace('.', '/')
    navigation_dir = os.path.join(output_dir, f'app/src/main/java/{package_path}/ui/navigation')
    os.makedirs(navigation_dir, exist_ok=True)

    # AppNavHost.kt のパス
    nav_host_path = os.path.join(navigation_dir, 'AppNavHost.kt')

    # AppNavHost.kt の内容
    nav_host_content = f"""package {package_name}.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import {package_name}.ui.screens.*

/**
 * アプリのナビゲーション定義
 */
@Composable
fun AppNavHost(navController: NavHostController) {{
    NavHost(
        navController = navController,
        startDestination = Screen.Home.route
    ) {{
        composable(Screen.Home.route) {{
            HomeScreen(navController = navController)
        }}

        composable(Screen.Settings.route) {{
            SettingsScreen(navController = navController)
        }}

        // TODO: 他の画面を追加
    }}
}}

/**
 * 画面定義
 */
sealed class Screen(val route: String) {{
    object Home : Screen("home")
    object Settings : Screen("settings")
    // TODO: 他の画面を追加
}}
"""

    # AppNavHost.kt を書き込み
    write_file(nav_host_path, nav_host_content)
    print(f"ナビゲーションを生成しました: {nav_host_path}")

def generate_theme(output_dir: str, package_name: str) -> None:
    """
    テーマを生成します。

    Args:
        output_dir: 出力先ディレクトリ
        package_name: Android アプリのパッケージ名
    """
    # パッケージディレクトリを取得
    package_path = package_name.replace('.', '/')
    theme_dir = os.path.join(output_dir, f'app/src/main/java/{package_path}/ui/theme')
    os.makedirs(theme_dir, exist_ok=True)

    # Theme.kt のパス
    theme_path = os.path.join(theme_dir, 'Theme.kt')

    # Theme.kt の内容
    theme_content = f"""package {package_name}.ui.theme

import android.app.Activity
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val LightColorScheme = lightColorScheme(
    primary = md_theme_light_primary,
    onPrimary = md_theme_light_onPrimary,
    primaryContainer = md_theme_light_primaryContainer,
    onPrimaryContainer = md_theme_light_onPrimaryContainer,
    secondary = md_theme_light_secondary,
    onSecondary = md_theme_light_onSecondary,
    secondaryContainer = md_theme_light_secondaryContainer,
    onSecondaryContainer = md_theme_light_onSecondaryContainer,
    tertiary = md_theme_light_tertiary,
    onTertiary = md_theme_light_onTertiary,
    tertiaryContainer = md_theme_light_tertiaryContainer,
    onTertiaryContainer = md_theme_light_onTertiaryContainer,
    error = md_theme_light_error,
    errorContainer = md_theme_light_errorContainer,
    onError = md_theme_light_onError,
    onErrorContainer = md_theme_light_onErrorContainer,
    background = md_theme_light_background,
    onBackground = md_theme_light_onBackground,
    surface = md_theme_light_surface,
    onSurface = md_theme_light_onSurface,
    surfaceVariant = md_theme_light_surfaceVariant,
    onSurfaceVariant = md_theme_light_onSurfaceVariant,
    outline = md_theme_light_outline,
    inverseOnSurface = md_theme_light_inverseOnSurface,
    inverseSurface = md_theme_light_inverseSurface,
    inversePrimary = md_theme_light_inversePrimary,
    surfaceTint = md_theme_light_surfaceTint,
)

private val DarkColorScheme = darkColorScheme(
    primary = md_theme_dark_primary,
    onPrimary = md_theme_dark_onPrimary,
    primaryContainer = md_theme_dark_primaryContainer,
    onPrimaryContainer = md_theme_dark_onPrimaryContainer,
    secondary = md_theme_dark_secondary,
    onSecondary = md_theme_dark_onSecondary,
    secondaryContainer = md_theme_dark_secondaryContainer,
    onSecondaryContainer = md_theme_dark_onSecondaryContainer,
    tertiary = md_theme_dark_tertiary,
    onTertiary = md_theme_dark_onTertiary,
    tertiaryContainer = md_theme_dark_tertiaryContainer,
    onTertiaryContainer = md_theme_dark_onTertiaryContainer,
    error = md_theme_dark_error,
    errorContainer = md_theme_dark_errorContainer,
    onError = md_theme_dark_onError,
    onErrorContainer = md_theme_dark_onErrorContainer,
    background = md_theme_dark_background,
    onBackground = md_theme_dark_onBackground,
    surface = md_theme_dark_surface,
    onSurface = md_theme_dark_onSurface,
    surfaceVariant = md_theme_dark_surfaceVariant,
    onSurfaceVariant = md_theme_dark_onSurfaceVariant,
    outline = md_theme_dark_outline,
    inverseOnSurface = md_theme_dark_inverseOnSurface,
    inverseSurface = md_theme_dark_inverseSurface,
    inversePrimary = md_theme_dark_inversePrimary,
    surfaceTint = md_theme_dark_surfaceTint,
)

@Composable
fun AppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit
) {{
    val colorScheme = when {{
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {{
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }}
        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }}

    val view = LocalView.current
    if (!view.isInEditMode) {{
        SideEffect {{
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.primary.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }}
    }}

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}}
"""

    # Theme.kt を書き込み
    write_file(theme_path, theme_content)
    print(f"テーマを生成しました: {theme_path}")

    # Color.kt のパス
    color_path = os.path.join(theme_dir, 'Color.kt')

    # Color.kt の内容
    color_content = f"""package {package_name}.ui.theme

import androidx.compose.ui.graphics.Color

// Light Theme Colors
val md_theme_light_primary = Color(0xFF6200EE)
val md_theme_light_onPrimary = Color(0xFFFFFFFF)
val md_theme_light_primaryContainer = Color(0xFFE8DDFF)
val md_theme_light_onPrimaryContainer = Color(0xFF21005E)
val md_theme_light_secondary = Color(0xFF03DAC6)
val md_theme_light_onSecondary = Color(0xFF000000)
val md_theme_light_secondaryContainer = Color(0xFFC8F9F3)
val md_theme_light_onSecondaryContainer = Color(0xFF00201C)
val md_theme_light_tertiary = Color(0xFF7D5260)
val md_theme_light_onTertiary = Color(0xFFFFFFFF)
val md_theme_light_tertiaryContainer = Color(0xFFFFD8E4)
val md_theme_light_onTertiaryContainer = Color(0xFF31111D)
val md_theme_light_error = Color(0xFFB00020)
val md_theme_light_errorContainer = Color(0xFFFFDAD6)
val md_theme_light_onError = Color(0xFFFFFFFF)
val md_theme_light_onErrorContainer = Color(0xFF410002)
val md_theme_light_background = Color(0xFFFFFBFF)
val md_theme_light_onBackground = Color(0xFF1C1B1F)
val md_theme_light_surface = Color(0xFFFFFBFF)
val md_theme_light_onSurface = Color(0xFF1C1B1F)
val md_theme_light_surfaceVariant = Color(0xFFE7E0EB)
val md_theme_light_onSurfaceVariant = Color(0xFF49454E)
val md_theme_light_outline = Color(0xFF7A757F)
val md_theme_light_inverseOnSurface = Color(0xFFF4EFF4)
val md_theme_light_inverseSurface = Color(0xFF313033)
val md_theme_light_inversePrimary = Color(0xFFCFBCFF)
val md_theme_light_surfaceTint = Color(0xFF6200EE)

// Dark Theme Colors
val md_theme_dark_primary = Color(0xFFCFBCFF)
val md_theme_dark_onPrimary = Color(0xFF371E73)
val md_theme_dark_primaryContainer = Color(0xFF4F378B)
val md_theme_dark_onPrimaryContainer = Color(0xFFE8DDFF)
val md_theme_dark_secondary = Color(0xFF03DAC6)
val md_theme_dark_onSecondary = Color(0xFF000000)
val md_theme_dark_secondaryContainer = Color(0xFF00504A)
val md_theme_dark_onSecondaryContainer = Color(0xFFC8F9F3)
val md_theme_dark_tertiary = Color(0xFFEFB8C8)
val md_theme_dark_onTertiary = Color(0xFF492532)
val md_theme_dark_tertiaryContainer = Color(0xFF633B48)
val md_theme_dark_onTertiaryContainer = Color(0xFFFFD8E4)
val md_theme_dark_error = Color(0xFFCF6679)
val md_theme_dark_errorContainer = Color(0xFF93000A)
val md_theme_dark_onError = Color(0xFF000000)
val md_theme_dark_onErrorContainer = Color(0xFFFFDAD6)
val md_theme_dark_background = Color(0xFF121212)
val md_theme_dark_onBackground = Color(0xFFE6E1E5)
val md_theme_dark_surface = Color(0xFF121212)
val md_theme_dark_onSurface = Color(0xFFE6E1E5)
val md_theme_dark_surfaceVariant = Color(0xFF49454F)
val md_theme_dark_onSurfaceVariant = Color(0xFFCAC4D0)
val md_theme_dark_outline = Color(0xFF948F99)
val md_theme_dark_inverseOnSurface = Color(0xFF1C1B1F)
val md_theme_dark_inverseSurface = Color(0xFFE6E1E5)
val md_theme_dark_inversePrimary = Color(0xFF6200EE)
val md_theme_dark_surfaceTint = Color(0xFFCFBCFF)
"""

    # Color.kt を書き込み
    write_file(color_path, color_content)
    print(f"カラーを生成しました: {color_path}")

    # Type.kt のパス
    type_path = os.path.join(theme_dir, 'Type.kt')

    # Type.kt の内容
    type_content = f"""package {package_name}.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

// Material 3 タイポグラフィ
val Typography = Typography(
    displayLarge = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.Normal,
        fontSize = 57.sp,
        lineHeight = 64.sp,
        letterSpacing = (-0.25).sp
    ),
    displayMedium = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.Normal,
        fontSize = 45.sp,
        lineHeight = 52.sp,
        letterSpacing = 0.sp
    ),
    displaySmall = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.Normal,
        fontSize = 36.sp,
        lineHeight = 44.sp,
        letterSpacing = 0.sp
    ),
    headlineLarge = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.Normal,
        fontSize = 32.sp,
        lineHeight = 40.sp,
        letterSpacing = 0.sp
    ),
    headlineMedium = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.Normal,
        fontSize = 28.sp,
        lineHeight = 36.sp,
        letterSpacing = 0.sp
    ),
    headlineSmall = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.Normal,
        fontSize = 24.sp,
        lineHeight = 32.sp,
        letterSpacing = 0.sp
    ),
    titleLarge = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.Normal,
        fontSize = 22.sp,
        lineHeight = 28.sp,
        letterSpacing = 0.sp
    ),
    titleMedium = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.Medium,
        fontSize = 16.sp,
        lineHeight = 24.sp,
        letterSpacing = 0.15.sp
    ),
    titleSmall = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.Medium,
        fontSize = 14.sp,
        lineHeight = 20.sp,
        letterSpacing = 0.1.sp
    ),
    bodyLarge = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.Normal,
        fontSize = 16.sp,
        lineHeight = 24.sp,
        letterSpacing = 0.5.sp
    ),
    bodyMedium = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.Normal,
        fontSize = 14.sp,
        lineHeight = 20.sp,
        letterSpacing = 0.25.sp
    ),
    bodySmall = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.Normal,
        fontSize = 12.sp,
        lineHeight = 16.sp,
        letterSpacing = 0.4.sp
    ),
    labelLarge = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.Medium,
        fontSize = 14.sp,
        lineHeight = 20.sp,
        letterSpacing = 0.1.sp
    ),
    labelMedium = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.Medium,
        fontSize = 12.sp,
        lineHeight = 16.sp,
        letterSpacing = 0.5.sp
    ),
    labelSmall = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.Medium,
        fontSize = 11.sp,
        lineHeight = 16.sp,
        letterSpacing = 0.5.sp
    )
)
"""

    # Type.kt を書き込み
    write_file(type_path, type_content)
    print(f"タイポグラフィを生成しました: {type_path}")

def generate_data_extraction_rules(output_dir: str) -> None:
    """
    data_extraction_rules.xml を生成します。

    Args:
        output_dir: 出力先ディレクトリ
    """
    # xml ディレクトリを作成
    xml_dir = os.path.join(output_dir, 'app/src/main/res/xml')
    os.makedirs(xml_dir, exist_ok=True)

    # data_extraction_rules.xml のパス
    rules_path = os.path.join(xml_dir, 'data_extraction_rules.xml')

    # data_extraction_rules.xml の内容
    rules_content = """<?xml version="1.0" encoding="utf-8"?>
<data-extraction-rules>
    <cloud-backup>
        <include domain="sharedpref" path="."/>
        <exclude domain="sharedpref" path="device.xml"/>
    </cloud-backup>
    <device-transfer>
        <include domain="sharedpref" path="."/>
        <exclude domain="sharedpref" path="device.xml"/>
    </device-transfer>
</data-extraction-rules>
"""

    # data_extraction_rules.xml を書き込み
    write_file(rules_path, rules_content)
    print(f"data_extraction_rules.xml を生成しました: {rules_path}")

def generate_backup_rules(output_dir: str) -> None:
    """
    backup_rules.xml を生成します。

    Args:
        output_dir: 出力先ディレクトリ
    """
    # xml ディレクトリを作成
    xml_dir = os.path.join(output_dir, 'app/src/main/res/xml')
    os.makedirs(xml_dir, exist_ok=True)

    # backup_rules.xml のパス
    rules_path = os.path.join(xml_dir, 'backup_rules.xml')

    # backup_rules.xml の内容
    rules_content = """<?xml version="1.0" encoding="utf-8"?>
<full-backup-content>
    <include domain="sharedpref" path="."/>
    <exclude domain="sharedpref" path="device.xml"/>
</full-backup-content>
"""

    # backup_rules.xml を書き込み
    write_file(rules_path, rules_content)
    print(f"backup_rules.xml を生成しました: {rules_path}")