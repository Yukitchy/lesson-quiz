#!/bin/bash
# 板書Google Docの冒頭に単語クイズのリンク（リッチテキスト・リンク埋め込み済み）を挿入する
# 使い方: ./insert_quiz_link.sh <Student> <docUrl> <quizUrl>
# 仕組み: HTML→RTF→クリップボード→Chromeでdocを開く→Cmd+Up→Cmd+V→先頭3行コピーして検証
set -u
STUDENT="$1"; DOC_URL="$2"; QUIZ_URL="$3"
TMP="/private/tmp/claude-501/-Users-yuki/0006018d-dfe7-471b-979c-f88f3bd575b2/scratchpad"
mkdir -p "$TMP"

# 1) 挿入するリッチテキストを作る（貼り付け側の書式を持ち込む＝板書のタイトル書式を継承しない）
cat > "$TMP/snippet.html" <<EOF
<span style="font-family: Arial; font-size: 11pt;"><b>📱 Vocabulary Quiz</b>: <a href="$QUIZ_URL">$QUIZ_URL</a><br>Practice words from our lessons &#8212; new words are added automatically after each class. Works great on your phone!<br><br></span>
EOF
textutil -convert rtf "$TMP/snippet.html" -output "$TMP/snippet.rtf" || exit 1
osascript -e "set the clipboard to (read (POSIX file \"$TMP/snippet.rtf\") as «class RTF »)" || exit 1

# 2) Chromeでdocを開き、docのあるウィンドウを前面化して読み込み完了を待つ
DOC_ID=$(echo "$DOC_URL" | sed -E 's#.*document/d/([^/]+).*#\1#')
osascript <<APPLESCRIPT || exit 1
tell application "Google Chrome"
  activate
  open location "$DOC_URL"
  delay 2
  -- docタブを含むウィンドウを探して前面化＆そのタブをアクティブに
  set found to false
  repeat with wi from 1 to (count of windows)
    repeat with ti from 1 to (count of tabs of window wi)
      if URL of tab ti of window wi contains "$DOC_ID" then
        set active tab index of window wi to ti
        set index of window wi to 1
        set found to true
        exit repeat
      end if
    end repeat
    if found then exit repeat
  end repeat
  if not found then error "doc tab not found"
  -- 読み込み待ち
  repeat with i from 1 to 40
    if not (loading of active tab of front window) then exit repeat
    delay 0.5
  end repeat
end tell
delay 5
APPLESCRIPT

# 2.5) 安全ゲート: 前面ウィンドウのアクティブタブが本当に対象docでなければ打鍵しない
FRONT_URL=$(osascript -e 'tell application "Google Chrome" to get URL of active tab of front window')
if ! echo "$FRONT_URL" | grep -q "$DOC_ID"; then
  echo "SAFETY_ABORT: 前面タブが対象docでない ($FRONT_URL)"
  exit 3
fi

# 3) 文頭へ移動して貼り付け
osascript <<'APPLESCRIPT' || exit 1
tell application "System Events"
  key code 126 using {command down} -- Cmd+Up = 文書の先頭へ
  delay 1
  keystroke "v" using {command down} -- 貼り付け
  delay 2.5
end tell
APPLESCRIPT

# 4) 検証: 先頭3行を選択コピーして中身を照合
osascript <<'APPLESCRIPT' || exit 1
tell application "System Events"
  key code 126 using {command down} -- 先頭へ
  delay 0.5
  key code 125 using {shift down} -- Shift+Down ×3
  key code 125 using {shift down}
  key code 125 using {shift down}
  keystroke "c" using {command down}
  delay 1
  key code 124 -- 右矢印で選択解除
end tell
APPLESCRIPT

HEAD=$(pbpaste | head -c 400)
echo "---- 先頭3行の実内容 ----"
echo "$HEAD"
if echo "$HEAD" | grep -q "Vocabulary Quiz"; then
  echo "VERIFY_OK: $STUDENT"
  # タブを閉じる（Docsは自動保存）
  osascript -e 'tell application "Google Chrome" to close active tab of front window'
  exit 0
else
  echo "VERIFY_FAIL: $STUDENT — タブは開いたまま残す（目視確認用）"
  exit 2
fi
