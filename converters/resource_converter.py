#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
リソースファイルを変換するモジュール
"""

import os
import shutil
from typing import Dict, List, Any

from utils.file_utils import read_file, write_file, copy_file

def convert_resources(from_dir: str, output_dir: str, project_info: Dict[str, Any]) -> None:
    """
    リソースファイルを変換します。

    Args:
        from_dir: 変換元の iOS プロジェクトディレクトリ
        output_dir: 出力先ディレクトリ
        project_info: プロジェクト情報
    """
    print("リソースファイルを変換しています...")

    # リソースディレクトリを作成
    res_dir = os.path.join(output_dir, 'app/src/main/res')
    os.makedirs(res_dir, exist_ok=True)

    # 画像リソースを変換
    convert_image_resources(from_dir, res_dir, project_info)

    # 文字列リソースを変換
    convert_string_resources(from_dir, res_dir, project_info)

    # カラーリソースを変換
    convert_color_resources(from_dir, res_dir, project_info)

    # テーマを作成
    create_theme(res_dir)

    print("リソースファイルの変換が完了しました。")

def convert_image_resources(from_dir: str, res_dir: str, project_info: Dict[str, Any]) -> None:
    """
    画像リソースを変換します。

    Args:
        from_dir: 変換元の iOS プロジェクトディレクトリ
        res_dir: 出力先のリソースディレクトリ
        project_info: プロジェクト情報
    """
    # 画像リソースディレクトリを作成
    drawable_dir = os.path.join(res_dir, 'drawable')
    os.makedirs(drawable_dir, exist_ok=True)

    # iOS のリソースディレクトリ
    ios_resources_dir = os.path.join(from_dir, 'Resources')

    # リソースディレクトリが存在する場合
    if os.path.exists(ios_resources_dir):
        # 画像ファイルをコピー
        for root, _, files in os.walk(ios_resources_dir):
            for file in files:
                if file.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    # ファイルパス
                    file_path = os.path.join(root, file)

                    # ファイル名を Android 形式に変換（小文字、スペースをアンダースコアに）
                    android_filename = file.lower().replace(' ', '_')

                    # 出力先パス
                    output_path = os.path.join(drawable_dir, android_filename)

                    # ファイルをコピー
                    shutil.copy2(file_path, output_path)
                    print(f"画像リソースをコピーしました: {file} -> {android_filename}")

    # Assets.xcassets ディレクトリが存在する場合
    assets_dir = os.path.join(from_dir, 'Assets.xcassets')
    if os.path.exists(assets_dir):
        for root, dirs, _ in os.walk(assets_dir):
            for dir_name in dirs:
                if dir_name.endswith('.imageset'):
                    # イメージセットディレクトリ
                    imageset_dir = os.path.join(root, dir_name)

                    # イメージセット内の画像ファイルを探す
                    for img_root, _, img_files in os.walk(imageset_dir):
                        for img_file in img_files:
                            if img_file.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                                # ファイルパス
                                img_path = os.path.join(img_root, img_file)

                                # ファイル名を Android 形式に変換
                                android_filename = dir_name.replace('.imageset', '').lower().replace(' ', '_') + '.png'

                                # 出力先パス
                                output_path = os.path.join(drawable_dir, android_filename)

                                # ファイルをコピー
                                shutil.copy2(img_path, output_path)
                                print(f"画像リソースをコピーしました: {img_file} -> {android_filename}")
                                break  # 最初の画像ファイルだけをコピー

def convert_string_resources(from_dir: str, res_dir: str, project_info: Dict[str, Any]) -> None:
    """
    文字列リソースを変換します。

    Args:
        from_dir: 変換元の iOS プロジェクトディレクトリ
        res_dir: 出力先のリソースディレクトリ
        project_info: プロジェクト情報
    """
    # 文字列リソースディレクトリを作成
    values_dir = os.path.join(res_dir, 'values')
    os.makedirs(values_dir, exist_ok=True)

    # strings.xml ファイルのパス
    strings_xml_path = os.path.join(values_dir, 'strings.xml')

    # iOS の Localizable.strings ファイルのパス
    localizable_strings_path = os.path.join(from_dir, 'Resources/Localizable.strings')

    # 文字列リソースの内容
    strings_xml_content = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">MyApp</string>
"""

    # Localizable.strings ファイルが存在する場合
    if os.path.exists(localizable_strings_path):
        # ファイルの内容を読み込み
        content = read_file(localizable_strings_path)

        # 文字列リソースを抽出
        for line in content.splitlines():
            line = line.strip()

            # コメント行をスキップ
            if line.startswith('//') or not line:
                continue

            # "key" = "value"; の形式を解析
            if '=' in line and line.endswith(';'):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    key = parts[0].strip().strip('"')
                    value = parts[1].strip().strip(';').strip().strip('"')

                    # Android の文字列リソース名に変換（小文字、スペースをアンダースコアに）
                    android_key = key.lower().replace(' ', '_')

                    # 文字列リソースを追加
                    strings_xml_content += f'    <string name="{android_key}">{value}</string>\n'

    # デフォルトの文字列リソースを追加
    strings_xml_content += """    <string name="hello_world">Hello, World!</string>
    <string name="login">Login</string>
    <string name="signup">Sign Up</string>
    <string name="logout">Logout</string>
    <string name="settings">Settings</string>
    <string name="profile">Profile</string>
    <string name="home">Home</string>
    <string name="search">Search</string>
    <string name="notifications">Notifications</string>
    <string name="error_message">An error occurred. Please try again.</string>
</resources>
"""

    # strings.xml ファイルを書き込み
    write_file(strings_xml_path, strings_xml_content)
    print(f"文字列リソースを作成しました: {strings_xml_path}")

def convert_color_resources(from_dir: str, res_dir: str, project_info: Dict[str, Any]) -> None:
    """
    カラーリソースを変換します。

    Args:
        from_dir: 変換元の iOS プロジェクトディレクトリ
        res_dir: 出力先のリソースディレクトリ
        project_info: プロジェクト情報
    """
    # カラーリソースディレクトリを作成
    values_dir = os.path.join(res_dir, 'values')
    os.makedirs(values_dir, exist_ok=True)

    # colors.xml ファイルのパス
    colors_xml_path = os.path.join(values_dir, 'colors.xml')

    # iOS の Colors.xcassets ディレクトリのパス
    colors_xcassets_path = os.path.join(from_dir, 'Colors.xcassets')

    # カラーリソースの内容
    colors_xml_content = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="primary">#6200EE</color>
    <color name="primary_variant">#3700B3</color>
    <color name="secondary">#03DAC6</color>
    <color name="secondary_variant">#018786</color>
    <color name="background">#FFFFFF</color>
    <color name="surface">#FFFFFF</color>
    <color name="error">#B00020</color>
    <color name="on_primary">#FFFFFF</color>
    <color name="on_secondary">#000000</color>
    <color name="on_background">#000000</color>
    <color name="on_surface">#000000</color>
    <color name="on_error">#FFFFFF</color>
</resources>
"""

    # colors.xml ファイルを書き込み
    write_file(colors_xml_path, colors_xml_content)
    print(f"カラーリソースを作成しました: {colors_xml_path}")

def create_theme(res_dir: str) -> None:
    """
    テーマを作成します。

    Args:
        res_dir: 出力先のリソースディレクトリ
    """
    # テーマディレクトリを作成
    values_dir = os.path.join(res_dir, 'values')
    os.makedirs(values_dir, exist_ok=True)

    # themes.xml ファイルのパス
    themes_xml_path = os.path.join(values_dir, 'themes.xml')

    # テーマの内容
    themes_xml_content = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.MyApp" parent="Theme.MaterialComponents.DayNight.NoActionBar">
        <!-- Primary brand color. -->
        <item name="colorPrimary">@color/primary</item>
        <item name="colorPrimaryVariant">@color/primary_variant</item>
        <item name="colorOnPrimary">@color/on_primary</item>
        <!-- Secondary brand color. -->
        <item name="colorSecondary">@color/secondary</item>
        <item name="colorSecondaryVariant">@color/secondary_variant</item>
        <item name="colorOnSecondary">@color/on_secondary</item>
        <!-- Status bar color. -->
        <item name="android:statusBarColor">?attr/colorPrimaryVariant</item>
        <!-- Background colors. -->
        <item name="android:colorBackground">@color/background</item>
        <item name="colorSurface">@color/surface</item>
        <item name="colorOnBackground">@color/on_background</item>
        <item name="colorOnSurface">@color/on_surface</item>
        <!-- Error colors. -->
        <item name="colorError">@color/error</item>
        <item name="colorOnError">@color/on_error</item>
    </style>
</resources>
"""

    # themes.xml ファイルを書き込み
    write_file(themes_xml_path, themes_xml_content)
    print(f"テーマを作成しました: {themes_xml_path}")

    # ナイトモード用のテーマディレクトリを作成
    night_values_dir = os.path.join(res_dir, 'values-night')
    os.makedirs(night_values_dir, exist_ok=True)

    # ナイトモード用の themes.xml ファイルのパス
    night_themes_xml_path = os.path.join(night_values_dir, 'themes.xml')

    # ナイトモード用のテーマの内容
    night_themes_xml_content = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.MyApp" parent="Theme.MaterialComponents.DayNight.NoActionBar">
        <!-- Primary brand color. -->
        <item name="colorPrimary">@color/primary</item>
        <item name="colorPrimaryVariant">@color/primary_variant</item>
        <item name="colorOnPrimary">@color/on_primary</item>
        <!-- Secondary brand color. -->
        <item name="colorSecondary">@color/secondary</item>
        <item name="colorSecondaryVariant">@color/secondary_variant</item>
        <item name="colorOnSecondary">@color/on_secondary</item>
        <!-- Status bar color. -->
        <item name="android:statusBarColor">?attr/colorPrimaryVariant</item>
        <!-- Background colors. -->
        <item name="android:colorBackground">#121212</item>
        <item name="colorSurface">#121212</item>
        <item name="colorOnBackground">#FFFFFF</item>
        <item name="colorOnSurface">#FFFFFF</item>
        <!-- Error colors. -->
        <item name="colorError">@color/error</item>
        <item name="colorOnError">@color/on_error</item>
    </style>
</resources>
"""

    # ナイトモード用の themes.xml ファイルを書き込み
    write_file(night_themes_xml_path, night_themes_xml_content)
    print(f"ナイトモード用のテーマを作成しました: {night_themes_xml_path}")