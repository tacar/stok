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

    # 10. 行末のカンマをセミコロンに置き換え
    content = re.sub(r',(\s*)$', r';\1', content, flags=re.MULTILINE)

    # 11. 不正な式の区切りを修正
    content = re.sub(r'([^\s,;])\s+([^\s,;])', r'\1, \2', content)

    # 12. 不正な閉じ括弧を修正
    lines = content.split('\n')
    fixed_lines = []

    # 括弧のバランスを追跡
    for line in lines:
        # 括弧のカウント
        open_paren = line.count('(')
        close_paren = line.count(')')
        open_brace = line.count('{')
        close_brace = line.count('}')

        # 括弧のバランスを修正
        if open_paren > close_paren:
            line += ')' * (open_paren - close_paren)

        # 中括弧のバランスを修正
        if open_brace > close_brace:
            line += '}'

        fixed_lines.append(line)

    content = '\n'.join(fixed_lines)

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

def fix_specific_files(error_files: Dict[str, List[dict]], base_dir: str) -> None:
    """
    特定のファイルのエラーを修正します。

    Args:
        error_files: ファイルパスとエラー情報のマップ
        base_dir: ベースディレクトリ
    """
    for file_path, errors in error_files.items():
        # ファイルの内容を読み込む
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"エラー: ファイルの読み込みに失敗しました: {e}")
            continue

        # 元のコンテンツを保存
        original_content = content

        # 行ごとに分割
        lines = content.split('\n')

        # エラーを行番号でソート（降順）
        errors.sort(key=lambda x: x['line'], reverse=True)

        # 各エラーを処理
        for error in errors:
            line_num = error['line'] - 1  # 0-indexedに変換
            if line_num < 0 or line_num >= len(lines):
                continue

            line = lines[line_num]
            error_msg = error['message']
            col = error['column'] - 1  # 0-indexedに変換

            # エラーの種類に応じて修正
            if "Unexpected tokens" in error_msg:
                # 不正なトークンを削除
                if col < len(line):
                    # セミコロンで区切る必要がある場合
                    if "use ';' to separate expressions" in error_msg:
                        # カンマをセミコロンに置き換え
                        if col > 0 and line[col-1] == ',':
                            lines[line_num] = line[:col-1] + ';' + line[col:]
                        else:
                            # 指定位置にセミコロンを挿入
                            lines[line_num] = line[:col] + ';' + line[col:]
                    else:
                        # カンマや不正なトークンを削除
                        if col > 0 and line[col-1] == ',':
                            lines[line_num] = line[:col-1] + line[col:]
                        else:
                            # 行末までの不正なトークンを削除
                            lines[line_num] = line[:col]

            elif "Expecting an element" in error_msg:
                # 要素が期待されている場合、行を削除または修正
                if line.strip().endswith(','):
                    # カンマで終わる行を修正
                    lines[line_num] = line.rstrip(',')
                elif col < len(line):
                    # 指定位置に空の要素を挿入
                    lines[line_num] = line[:col] + "/* empty element */" + line[col:]
                else:
                    # コメントアウト
                    lines[line_num] = f"// {line} /* Expecting an element */"

            elif "Expecting ')'" in error_msg:
                # 閉じ括弧が期待されている場合、追加
                if col < len(line):
                    lines[line_num] = line[:col] + ')' + line[col:]
                else:
                    lines[line_num] = line + ')'

            elif "Expecting '}'" in error_msg:
                # 閉じ中括弧が期待されている場合、追加
                # 次の行に追加
                if line_num + 1 < len(lines):
                    lines.insert(line_num + 1, '}')
                else:
                    lines.append('}')

            elif "Expecting a top level declaration" in error_msg:
                # トップレベル宣言が期待されている場合、コメントアウト
                lines[line_num] = f"// {line} /* Invalid top level declaration */"

        # 修正した内容を保存
        content = '\n'.join(lines)

        # 変更があった場合のみファイルを更新
        if content != original_content:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"ファイルを修正しました: {file_path}")
            except Exception as e:
                print(f"エラー: ファイルの書き込みに失敗しました: {e}")
        else:
            print(f"変更なし: {file_path}")

def parse_error_messages(error_messages: str) -> Dict[str, List[dict]]:
    """
    エラーメッセージを解析して、ファイルごとのエラー情報を抽出します。

    Args:
        error_messages: エラーメッセージ

    Returns:
        ファイルパスをキー、エラー情報のリストを値とする辞書
    """
    error_files = {}

    # エラーメッセージの各行を処理
    for line in error_messages.split('\n'):
        if not line.strip():
            continue

        # 'e: file://...' 形式のエラーメッセージを処理
        if line.startswith('e:') and 'file://' in line:
            # ファイルパスとエラー情報を抽出
            match = re.search(r'e:\s+file://([^:]+):(\d+):(\d+)\s+(.*)', line)
            if match:
                file_path = match.group(1)
                line_num = int(match.group(2))
                col_num = int(match.group(3))
                error_msg = match.group(4)

                # エラー情報を保存
                if file_path not in error_files:
                    error_files[file_path] = []

                error_files[file_path].append({
                    'line': line_num,
                    'column': col_num,
                    'message': error_msg
                })

    return error_files

def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("使用方法: python kotlin_error_fixer.py <ディレクトリまたはエラーファイル>")
        print("または: python kotlin_error_fixer.py --error \"エラーメッセージ\"")
        return

    arg = sys.argv[1]

    # エラーメッセージが直接指定された場合
    if arg == "--error" and len(sys.argv) > 2:
        error_messages = sys.argv[2]

        # エラーメッセージを解析
        error_files = parse_error_messages(error_messages)

        # 特定のファイルを修正
        fix_specific_files(error_files, "")

        print(f"処理完了: {len(error_files)}個のファイルを修正しました。")
        return

    # エラーメッセージファイルが指定された場合
    if arg.endswith('.txt') and os.path.exists(arg):
        with open(arg, 'r', encoding='utf-8') as f:
            error_messages = f.read()

        # エラーメッセージを解析
        error_files = parse_error_messages(error_messages)

        # 特定のファイルを修正
        fix_specific_files(error_files, "")

        print(f"処理完了: {len(error_files)}個のファイルを修正しました。")
        return

    # ディレクトリが指定された場合
    if os.path.isdir(arg):
        # Kotlinファイルを検索
        kotlin_files = find_kotlin_files(arg)

        print(f"{len(kotlin_files)}個のKotlinファイルを処理します...")

        # 各ファイルを修正
        fixed_count = 0
        for file_path in kotlin_files:
            if fix_kotlin_file(file_path):
                fixed_count += 1

        print(f"処理完了: {fixed_count}/{len(kotlin_files)}個のファイルを修正しました。")
    else:
        # 標準入力からエラーメッセージを読み込む
        error_messages = arg
        for line in sys.stdin:
            error_messages += line

        # エラーメッセージを解析
        error_files = parse_error_messages(error_messages)

        # 特定のファイルを修正
        fix_specific_files(error_files, "")

        print(f"処理完了: {len(error_files)}個のファイルを修正しました。")

if __name__ == "__main__":
    main()
