#!/bin/bash

# Kotlinエラーを自動的にリスト化し、AIプロンプトを生成するスクリプト

# 現在のディレクトリを取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# エラーファイルとプロンプトファイルの名前
ERROR_FILE="kotlin_errors_list.txt"
PROMPT_FILE="ai_kotlin_fix_prompt.md"
OUTPUT_FILE="ai_kotlin_fix_prompt_with_errors.md"

# ヘルプメッセージの表示
show_help() {
    echo "使用方法: $0 [オプション]"
    echo ""
    echo "オプション:"
    echo "  -h, --help     ヘルプメッセージを表示"
    echo "  -o, --output   出力プロンプトファイル名を指定 (デフォルト: ai_kotlin_fix_prompt_with_errors.md)"
    echo "  -c, --clipboard 生成したプロンプトをクリップボードにコピー"
    echo ""
    echo "例:"
    echo "  $0             エラーリストを生成し、AIプロンプトを作成"
    echo "  $0 -o custom_prompt.md  指定したファイルにAIプロンプトを出力"
    echo "  $0 -c          生成したプロンプトをクリップボードにコピー"
}

# デフォルト値
COPY_TO_CLIPBOARD=false

# コマンドライン引数の解析
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -o|--output)
            if [[ -n "$2" && ! "$2" =~ ^- ]]; then
                OUTPUT_FILE="$2"
                shift 2
            else
                echo "エラー: --output オプションには引数が必要です。"
                exit 1
            fi
            ;;
        -c|--clipboard)
            COPY_TO_CLIPBOARD=true
            shift
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

# プロンプトテンプレートを作成
echo "AIプロンプトを生成中..."
cat > "$OUTPUT_FILE" << EOL
# Kotlinエラー修正依頼プロンプト

## エラーリスト
\`\`\`
$(cat "$ERROR_FILE")
\`\`\`

上記をすべて修正してください。
よろしくお願いします。
EOL

echo "AIプロンプトは $OUTPUT_FILE に保存されました。"

# クリップボードにコピー（オプション）
if [ "$COPY_TO_CLIPBOARD" = true ]; then
    if command -v pbcopy > /dev/null; then
        # macOS
        cat "$OUTPUT_FILE" | pbcopy
        echo "プロンプトをクリップボードにコピーしました。"
    elif command -v xclip > /dev/null; then
        # Linux with xclip
        cat "$OUTPUT_FILE" | xclip -selection clipboard
        echo "プロンプトをクリップボードにコピーしました。"
    elif command -v clip > /dev/null; then
        # Windows
        cat "$OUTPUT_FILE" | clip
        echo "プロンプトをクリップボードにコピーしました。"
    else
        echo "警告: クリップボードへのコピーに対応するコマンドが見つかりませんでした。"
    fi
fi

# 一時ファイルを削除
rm build_output_temp.txt

echo "完了しました。"
echo "生成AIに依頼するには、$OUTPUT_FILE の内容をコピーして貼り付けてください。"