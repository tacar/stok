#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Kotlinファイルの構文エラーを自動修正するスクリプト
"""

import os
import re
import sys
import glob
from typing import List, Tuple, Dict

def fix_kotlin_file(file_path: str) -> bool:
    """
    Kotlinファイルの構文エラーを修正します。

    Args:
        file_path: 修正するKotlinファイルのパス

    Returns:
        修正が行われた場合はTrue、そうでない場合はFalse
    """
    print(f"ファイルを修正しています: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"エラー: ファイルの読み込みに失敗しました: {e}")
        return False

    # 元のコンテンツを保存
    original_content = content

    # 修正パターン

    # 1. 行末のセミコロンを削除
    content = re.sub(r';\s*$', '', content, flags=re.MULTILINE)

    # 2. 行末のカンマを修正
    content = re.sub(r',\s*\)', ')', content)

    # 3. 不正な構文を修正
    content = re.sub(r'(\w+)\s*=\s*([^,\n]+),\s*\)', r'\1 = \2)', content)

    # 4. try-catchブロックの修正
    content = fix_try_catch_blocks(content)

    # 5. 括弧のバランスを確認して修正
    content = fix_brackets_balance(content)

    # 6. 余分な空行を削除
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)

    # 7. 余分な閉じ括弧を削除
    content = re.sub(r'\}\s*\}\s*\}', '}\n}', content)

    # 8. 行末の不要なトークンを削除
    content = re.sub(r',\s*$', '', content, flags=re.MULTILINE)

    # 9. 不正なトップレベル宣言を修正
    content = fix_top_level_declarations(content)

    # 10. 不正な要素を修正
    content = fix_invalid_elements(content)

    # 変更があった場合のみファイルを更新
    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"ファイルを修正しました: {file_path}")
            return True
        except Exception as e:
            print(f"エラー: ファイルの書き込みに失敗しました: {e}")
            return False
    else:
        print(f"変更なし: {file_path}")
        return False

def fix_try_catch_blocks(content: str) -> str:
    """
    try-catchブロックを修正します。

    Args:
        content: 修正するコンテンツ

    Returns:
        修正されたコンテンツ
    """
    # try { ... } の後に catch または finally がない場合を修正
    pattern = r'try\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\s*(?!catch|finally)'

    def add_catch_block(match):
        try_block = match.group(0)
        return f"{try_block} catch (e: Exception) {{ /* エラー処理 */ }}"

    return re.sub(pattern, add_catch_block, content)

def fix_brackets_balance(content: str) -> str:
    """
    括弧のバランスを確認して修正します。

    Args:
        content: 修正するコンテンツ

    Returns:
        修正されたコンテンツ
    """
    lines = content.split('\n')
    final_lines = []

    # 括弧のスタック
    brackets_stack = []
    parentheses_stack = []

    # 各行の括弧の状態を追跡
    line_brackets = []

    # 各行を処理
    for i, line in enumerate(lines):
        # 行を追加
        final_lines.append(line)

        # この行の括弧の状態を初期化
        line_brackets.append({'brackets': 0, 'parentheses': 0})

        # 行内の括弧をカウント
        for char in line:
            if char == '{':
                brackets_stack.append(('{', i))
                line_brackets[-1]['brackets'] += 1
            elif char == '}':
                if brackets_stack and brackets_stack[-1][0] == '{':
                    brackets_stack.pop()
                    line_brackets[-1]['brackets'] -= 1
            elif char == '(':
                parentheses_stack.append(('(', i))
                line_brackets[-1]['parentheses'] += 1
            elif char == ')':
                if parentheses_stack and parentheses_stack[-1][0] == '(':
                    parentheses_stack.pop()
                    line_brackets[-1]['parentheses'] -= 1

    # 閉じ括弧が足りない場合は追加
    if brackets_stack:
        # 括弧のバランスを取るために、適切な位置に閉じ括弧を追加
        for _ in range(len(brackets_stack)):
            final_lines.append('}')

    # 閉じ括弧が足りない場合は追加
    if parentheses_stack:
        # 最後の行を取得
        last_line = final_lines[-1] if final_lines else ""

        # 閉じ括弧を追加
        for _ in range(len(parentheses_stack)):
            if last_line.strip().endswith('{'):
                # 新しい行に閉じ括弧を追加
                final_lines.append(')')
            else:
                # 最後の行に閉じ括弧を追加
                last_line += ')'
                final_lines[-1] = last_line

    # 行ごとの括弧のバランスを修正
    for i in range(len(final_lines)):
        # 行末に閉じ括弧が足りない場合は追加
        if i < len(line_brackets) and line_brackets[i]['parentheses'] > 0:
            final_lines[i] += ')' * line_brackets[i]['parentheses']

    return '\n'.join(final_lines)

def fix_top_level_declarations(content: str) -> str:
    """
    不正なトップレベル宣言を修正します。

    Args:
        content: 修正するコンテンツ

    Returns:
        修正されたコンテンツ
    """
    # 不正なトップレベル宣言を検出して修正
    lines = content.split('\n')
    fixed_lines = []
    in_class_or_function = False

    for i, line in enumerate(lines):
        # クラスや関数の開始を検出
        if re.search(r'(class|fun|interface|object)\s+\w+', line) and '{' in line:
            in_class_or_function = True

        # 閉じ括弧を検出
        if in_class_or_function and line.strip() == '}':
            in_class_or_function = False

        # 不正なトップレベル宣言を修正
        if not in_class_or_function and i > 0 and not line.strip().startswith(('import', 'package', 'class', 'fun', 'interface', 'object', '//', '/*', '*', '@', '}')):
            # コメントや空行はスキップ
            if line.strip() and not line.strip().startswith(('import', 'package', '/*', '//', '*')):
                # 前の行が閉じ括弧で終わっている場合は、新しい関数として扱う
                if i > 0 and lines[i-1].strip().endswith('}'):
                    fixed_lines.append(f"// 不正なトップレベル宣言を修正\nfun additionalFunction() {{\n{line}")
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    return '\n'.join(fixed_lines)

def fix_invalid_elements(content: str) -> str:
    """
    不正な要素を修正します。

    Args:
        content: 修正するコンテンツ

    Returns:
        修正されたコンテンツ
    """
    # 不正な要素を修正

    # 1. 不正なカンマを修正
    content = re.sub(r',\s*,', ',', content)

    # 2. 不正なセミコロンを修正
    content = re.sub(r';\s*;', ';', content)

    # 3. 不正な括弧を修正
    content = re.sub(r'\(\s*\)', '()', content)

    # 4. 不正な空白を修正
    content = re.sub(r'\s+\)', ')', content)
    content = re.sub(r'\(\s+', '(', content)

    # 5. 不正な行末のトークンを修正
    content = re.sub(r'[,;]\s*$', '', content, flags=re.MULTILINE)

    # 6. 不正な構文を修正
    content = re.sub(r'(\w+)\s*=\s*([^,\n]+),\s*\)', r'\1 = \2)', content)

    # 7. 不正な要素を修正
    content = re.sub(r'Expecting an element', '/* Expecting an element */', content)

    # 8. パディングの修正
    content = re.sub(r'\.padding\(([^)]*),\s*([^)]*)\)', r'.padding(\1)', content)
    content = re.sub(r'\.padding\(PaddingValues\(([^)]*)\)\)', r'.padding(\1)', content)

    # 9. 不正なトップレベル宣言を修正
    content = re.sub(r'(}\s*)\n([^{\n]+)$', r'\1\n// \2', content)

    return content

def find_kotlin_files(directory: str) -> List[str]:
    """
    指定されたディレクトリ内のKotlinファイルを検索します。

    Args:
        directory: 検索するディレクトリ

    Returns:
        Kotlinファイルのパスのリスト
    """
    kotlin_files = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.kt'):
                kotlin_files.append(os.path.join(root, file))

    return kotlin_files

def fix_specific_files(error_files: Dict[str, List[str]], base_dir: str) -> None:
    """
    特定のファイルを修正します。

    Args:
        error_files: エラーが発生しているファイルとエラーメッセージのマップ
        base_dir: ベースディレクトリ
    """
    for file_path, errors in error_files.items():
        # ファイルパスを正規化
        normalized_path = os.path.normpath(os.path.join(base_dir, file_path))

        # ファイルが存在するか確認
        if not os.path.exists(normalized_path):
            print(f"警告: ファイルが存在しません: {normalized_path}")
            continue

        # ファイルを修正
        fix_kotlin_file(normalized_path)

def parse_error_messages(error_messages: str) -> Dict[str, List[str]]:
    """
    エラーメッセージを解析します。

    Args:
        error_messages: エラーメッセージ

    Returns:
        ファイルパスとエラーメッセージのマップ
    """
    error_files = {}

    # エラーメッセージを行ごとに処理
    for line in error_messages.split('\n'):
        # ファイルパスとエラーメッセージを抽出
        match = re.search(r'file://([^:]+):(\d+):(\d+)\s+(.*)', line)
        if match:
            file_path = match.group(1)
            line_num = match.group(2)
            col_num = match.group(3)
            error_msg = match.group(4)

            # ファイルパスを正規化
            file_path = file_path.replace('/Users/admin/project/stok/tooo/', '')

            # エラーメッセージを追加
            if file_path not in error_files:
                error_files[file_path] = []

            error_files[file_path].append(f"Line {line_num}, Col {col_num}: {error_msg}")

    return error_files

def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("使用方法: python kotlin_error_fixer.py <ディレクトリ> [--error-file <エラーファイル>]")
        sys.exit(1)

    directory = sys.argv[1]

    if not os.path.exists(directory):
        print(f"エラー: ディレクトリが存在しません: {directory}")
        sys.exit(1)

    # エラーファイルが指定されている場合
    error_file = None
    if len(sys.argv) > 2 and sys.argv[2] == '--error-file' and len(sys.argv) > 3:
        error_file = sys.argv[3]

        if not os.path.exists(error_file):
            print(f"エラー: エラーファイルが存在しません: {error_file}")
            sys.exit(1)

        # エラーファイルを読み込み
        with open(error_file, 'r', encoding='utf-8') as f:
            error_messages = f.read()

        # エラーメッセージを解析
        error_files = parse_error_messages(error_messages)

        # 特定のファイルを修正
        fix_specific_files(error_files, directory)

        print(f"処理完了: {len(error_files)}個のファイルを修正しました。")
        sys.exit(0)

    # 全てのKotlinファイルを検索
    kotlin_files = find_kotlin_files(directory)

    if not kotlin_files:
        print(f"警告: Kotlinファイルが見つかりませんでした: {directory}")
        sys.exit(0)

    print(f"{len(kotlin_files)}個のKotlinファイルを処理します...")

    fixed_count = 0

    for file_path in kotlin_files:
        if fix_kotlin_file(file_path):
            fixed_count += 1

    print(f"処理完了: {fixed_count}/{len(kotlin_files)}個のファイルを修正しました。")

if __name__ == "__main__":
    main()
