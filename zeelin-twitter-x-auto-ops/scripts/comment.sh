#!/bin/bash
# comment.sh - post a reply to a specific X/Twitter post via direct CDP (primary)
# or openclaw browser CLI (fallback).
# Usage: bash comment.sh "reply content" "status url" "base_url"

set -euo pipefail

COMMENT_TEXT="${1:-}"
STATUS_URL="${2:-}"
BASE_URL="${3:-https://x.com}"
CDP_PORT="${OPENCLAW_CDP_PORT:-9222}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -z "$COMMENT_TEXT" ] || [ -z "$STATUS_URL" ]; then
  echo "Error: comment content and status URL are required"
  exit 1
fi

if ! [[ "$STATUS_URL" =~ ^https?:// ]]; then
  echo "Error: status URL must start with http:// or https://"
  exit 1
fi

MAX_LEN=240
if [ ${#COMMENT_TEXT} -gt $MAX_LEN ]; then
  COMMENT_TEXT="${COMMENT_TEXT:0:$MAX_LEN}…"
fi

if ! curl -s --max-time 3 "http://127.0.0.1:${CDP_PORT}/json/version" >/dev/null 2>&1; then
  echo "Error: Chrome not reachable on CDP port ${CDP_PORT}."
  echo "Fix: Start Chrome with --remote-debugging-port=${CDP_PORT}"
  exit 1
fi
echo "Browser reachable on CDP port ${CDP_PORT}."

echo "Posting reply via direct CDP..."
if python3 "$SCRIPT_DIR/cdp_comment.py" "$COMMENT_TEXT" "$STATUS_URL" --port "$CDP_PORT" --base-url "$BASE_URL"; then
  exit 0
fi

echo "CDP direct method failed, falling back to CLI method..."

CLI="${OPENCLAW_CLI:-openclaw browser}"

get_snapshot() {
  local snap
  snap="$($CLI snapshot 2>/dev/null || true)"
  if [ -z "$snap" ]; then
    snap="$($CLI snapshot --interactive 2>/dev/null || true)"
  fi
  printf "%s" "$snap"
}

extract_first_ref() {
  grep -oE 'ref=e[0-9]+' | head -1 | sed 's/ref=//' || true
}

find_reply_button_ref() {
  local snap="$1"
  local ref
  ref="$(
    echo "$snap" \
      | grep -E 'button.*(回复|Reply)' \
      | grep -v '查看回复|Show replies|Replying to' \
      | extract_first_ref
  )"
  if [ -z "$ref" ]; then
    ref="$(
      echo "$snap" \
        | grep -E 'reply' \
        | grep -oE 'ref=e[0-9]+' \
        | head -1 \
        | sed 's/ref=//'
    )"
  fi
  printf "%s" "$ref"
}

find_textbox_ref() {
  local snap="$1"
  local ref
  ref="$(
    echo "$snap" \
      | grep -Ei 'textbox' \
      | grep -Ei 'post text|tweet text|reply text|回复|有什么新鲜事|发生了什么|post your reply' \
      | extract_first_ref
  )"
  if [ -z "$ref" ]; then
    ref="$(echo "$snap" | grep -Ei 'textbox' | extract_first_ref)"
  fi
  printf "%s" "$ref"
}

find_submit_ref() {
  local snap="$1"
  local ref
  ref="$(
    echo "$snap" \
      | grep -E 'button.*(回复|Reply|Post)' \
      | grep -v '\[disabled\]' \
      | extract_first_ref
  )"
  printf "%s" "$ref"
}

find_success_signal() {
  local snap="$1"
  echo "$snap" | grep -qE 'Your reply was sent|Your post was sent|回复已发送|帖子已发送|Reply sent|Post sent'
}

activate_x_tab() {
  local target
  target="$(
    curl -s --max-time 3 "http://127.0.0.1:${CDP_PORT}/json" 2>/dev/null \
      | grep -B5 'x\.com' | grep '"id"' | head -1 | grep -oE '[A-F0-9]{32}' || true
  )"
  if [ -n "$target" ]; then
    curl -s --max-time 3 "http://127.0.0.1:${CDP_PORT}/json/activate/${target}" >/dev/null 2>&1 || true
  fi
}

$CLI start >/dev/null 2>&1 || true
$CLI open "$STATUS_URL" >/dev/null 2>&1 || true
sleep 2
activate_x_tab
sleep 1

SNAPSHOT=""
for _ in 1 2 3 4 5 6; do
  SNAPSHOT="$(get_snapshot)"
  if [ -n "$SNAPSHOT" ]; then
    break
  fi
  sleep 1
done

if [ -z "$SNAPSHOT" ]; then
  echo "Error: No browser snapshot available."
  exit 1
fi

REPLY_REF="$(find_reply_button_ref "$SNAPSHOT")"
if [ -n "$REPLY_REF" ]; then
  $CLI click "$REPLY_REF" >/dev/null 2>&1 || true
  sleep 2
  SNAPSHOT="$(get_snapshot)"
fi

TEXTBOX_REF=""
for _ in 1 2 3 4 5; do
  TEXTBOX_REF="$(find_textbox_ref "$SNAPSHOT")"
  [ -n "$TEXTBOX_REF" ] && break
  sleep 1
  SNAPSHOT="$(get_snapshot)"
done

if [ -z "$TEXTBOX_REF" ]; then
  echo "Error: Could not find reply input box"
  exit 1
fi

$CLI click "$TEXTBOX_REF" >/dev/null 2>&1 || true
$CLI type "$TEXTBOX_REF" "$COMMENT_TEXT" >/dev/null 2>&1 || true
sleep 1

for _ in 1 2 3 4 5; do
  SNAPSHOT="$(get_snapshot)"
  if find_success_signal "$SNAPSHOT"; then
    echo "Reply published successfully."
    exit 0
  fi
  SUBMIT_REF="$(find_submit_ref "$SNAPSHOT")"
  if [ -n "$SUBMIT_REF" ]; then
    $CLI click "$SUBMIT_REF" >/dev/null 2>&1 || true
    sleep 2
  fi
  sleep 1
done

echo "Reply attempted but success signal not detected. Check the thread."
