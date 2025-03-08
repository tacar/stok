#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ファイル操作用のユーティリティ関数
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional

def ensure_directory(directory: str) -> None:
    """
    ディレクトリが存在しない場合は作成します。

    Args:
        directory: 作成するディレクトリのパス
    """
    os.makedirs(directory, exist_ok=True)

def read_file(file_path: str) -> str:
    """
    ファイルの内容を読み込みます。

    Args:
        file_path: 読み込むファイルのパス

    Returns:
        ファイルの内容
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(file_path: str, content: str) -> None:
    """
    ファイルに内容を書き込みます。

    Args:
        file_path: 書き込むファイルのパス
        content: 書き込む内容
    """
    # 絶対パスに変換
    file_path_abs = os.path.abspath(file_path)

    try:
        # ディレクトリが存在しない場合は作成
        dir_path = os.path.dirname(file_path_abs)
        os.makedirs(dir_path, exist_ok=True)

        # ファイルに書き込み
        with open(file_path_abs, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"警告: ファイルの書き込み中にエラーが発生しました: {file_path_abs}: {e}")
        # エラーが発生した場合でも続行

def copy_file(src: str, dst: str) -> None:
    """
    ファイルをコピーします。

    Args:
        src: コピー元のファイルパス
        dst: コピー先のファイルパス
    """
    # コピー先のディレクトリが存在しない場合は作成
    os.makedirs(os.path.dirname(dst), exist_ok=True)

    shutil.copy2(src, dst)

def copy_directory(src: str, dst: str, exclude: Optional[List[str]] = None) -> None:
    """
    ディレクトリをコピーします。

    Args:
        src: コピー元のディレクトリパス
        dst: コピー先のディレクトリパス
        exclude: 除外するファイルやディレクトリのリスト
    """
    if exclude is None:
        exclude = []

    # 絶対パスに変換
    src_abs = os.path.abspath(src)
    dst_abs = os.path.abspath(dst)

    # コピー元が存在しない場合はエラー
    if not os.path.exists(src_abs):
        print(f"警告: コピー元ディレクトリが存在しません: {src_abs}")
        return

    # コピー先のディレクトリが存在しない場合は作成
    try:
        os.makedirs(dst_abs, exist_ok=True)
    except Exception as e:
        print(f"警告: コピー先ディレクトリの作成中にエラーが発生しました: {e}")
        return

    # ディレクトリ内の各アイテムをコピー
    try:
        for item in os.listdir(src_abs):
            # 除外リストにあるアイテムはスキップ
            if item in exclude:
                continue

            s = os.path.join(src_abs, item)
            d = os.path.join(dst_abs, item)

            try:
                if os.path.isdir(s):
                    copy_directory(s, d, exclude)
                else:
                    # コピー先のディレクトリが存在しない場合は作成
                    os.makedirs(os.path.dirname(d), exist_ok=True)
                    shutil.copy2(s, d)
            except Exception as e:
                print(f"警告: アイテムのコピー中にエラーが発生しました: {s} -> {d}: {e}")
                # 個別のアイテムのエラーは無視して続行
    except Exception as e:
        print(f"警告: ディレクトリのコピー中にエラーが発生しました: {src_abs} -> {dst_abs}: {e}")
        # エラーが発生した場合でも可能な限り続行

def get_file_extension(file_path: str) -> str:
    """
    ファイルの拡張子を取得します。

    Args:
        file_path: ファイルパス

    Returns:
        拡張子（ドットを含む）
    """
    return os.path.splitext(file_path)[1]

def get_filename(file_path: str) -> str:
    """
    ファイル名（拡張子なし）を取得します。

    Args:
        file_path: ファイルパス

    Returns:
        ファイル名（拡張子なし）
    """
    return os.path.splitext(os.path.basename(file_path))[0]

def list_files(directory: str, extension: Optional[str] = None) -> List[str]:
    """
    ディレクトリ内のファイルを再帰的にリストアップします。

    Args:
        directory: 検索するディレクトリ
        extension: フィルタリングする拡張子（例: '.swift'）

    Returns:
        ファイルパスのリスト
    """
    result = []

    for root, _, files in os.walk(directory):
        for file in files:
            if extension is None or file.endswith(extension):
                result.append(os.path.join(root, file))

    return result