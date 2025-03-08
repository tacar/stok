#!/bin/bash

# Kotlinエラーをリスト化するスクリプト

# 現在のディレクトリを取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# エラーファイルの名前
ERROR_FILE="kotlin_errors_list.txt"

# ヘルプメッセージの表示
show_help() {
    echo "使用方法: $0 [オプション]"
    echo ""
    echo "オプション:"
    echo "  -h, --help     ヘルプメッセージを表示"
    echo "  -o, --output   出力ファイル名を指定 (デフォルト: kotlin_errors_list.txt)"
    echo ""
    echo "例:"
    echo "  $0             Gradleビルドを実行し、エラーをリスト化"
    echo "  $0 -o errors.txt  指定したファイルにエラーを出力"
}

# コマンドライン引数の解析
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -o|--output)
            if [[ -n "$2" && ! "$2" =~ ^- ]]; then
                ERROR_FILE="$2"
                shift 2
            else
                echo "エラー: --output オプションには引数が必要です。"
                exit 1
            fi
            ;;
        *)
            echo "不明なオプション: $1"
            show_help
            exit 1
            ;;
    esac
done

echo "Gradleビルドを実行中..."
./gradlew build > build_output_temp.txt 2>&1 || true

# エラーを抽出してファイルに保存
echo "エラーを抽出中..."
grep "e: file://" build_output_temp.txt | sort | uniq > "$ERROR_FILE"

# エラーの数を数える
ERROR_COUNT=$(wc -l < "$ERROR_FILE")
echo "合計 $ERROR_COUNT 件のユニークなエラーを検出しました。"
echo "エラーリストは $ERROR_FILE に保存されました。"

# 一時ファイルを削除
rm build_output_temp.txt

echo "完了しました。"