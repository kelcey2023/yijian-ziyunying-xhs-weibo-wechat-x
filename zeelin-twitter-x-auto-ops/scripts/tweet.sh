#!/bin/bash
# tweet.sh - post a tweet via direct CDP (primary) or openclaw CLI (fallback).
# NOTE: Direct CDP mode has been verified operational in this environment.
# It connects directly to Chrome DevTools Protocol on port 9222 and publishes
# tweets without relying on the OpenClaw browser relay. This avoids snapshot
# issues and makes auto‑publish stable.
# Usage: bash tweet.sh "tweet content" "base_url"

set -euo pipefail

TWEET_TEXT="${1:-}"
MEDIA_PATH="${3:-}"

# Enforce safe Twitter length while preserving URLs (X safe margin)
MAX_LEN=240
URL=$(echo "$TWEET_TEXT" | grep -oE 'https?://[^ ]+' || true)

if [ -n "$URL" ]; then
  BASE_TEXT=$(echo "$TWEET_TEXT" | sed "s|$URL||")
  LIMIT=$((MAX_LEN - ${#URL} - 2))
  if [ ${#BASE_TEXT} -gt $LIMIT ]; then
    BASE_TEXT="${BASE_TEXT:0:$LIMIT}…"
  fi
  TWEET_TEXT="${BASE_TEXT}
${URL}"
else
  if [ ${#TWEET_TEXT} -gt $MAX_LEN ]; then
    TWEET_TEXT="${TWEET_TEXT:0:$MAX_LEN}…"
  fi
fi
BASE_URL="${2:-https://x.com}"
CDP_PORT="${OPENCLAW_CDP_PORT:-9222}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -z "$TWEET_TEXT" ]; then
  echo "Error: Tweet content is required"
  exit 1
fi

# Check browser is reachable
if ! curl -s --max-time 3 "http://127.0.0.1:${CDP_PORT}/json/version" >/dev/null 2>&1; then
  echo "Error: Chrome not reachable on CDP port ${CDP_PORT}."
  echo "Fix: Start Chrome with --remote-debugging-port=${CDP_PORT}"
  exit 1
fi
echo "Browser reachable on CDP port ${CDP_PORT}."

# Primary method: direct CDP (bypasses openclaw CLI gateway round-trip)
echo "Posting via direct CDP..."
CDP_ARGS=("$TWEET_TEXT" --port "$CDP_PORT" --base-url "$BASE_URL")
if [ -n "$MEDIA_PATH" ] && [ -f "$MEDIA_PATH" ]; then
  echo "Will attach media: $MEDIA_PATH"
  CDP_ARGS+=(--image "$MEDIA_PATH")
fi

if python3 "$SCRIPT_DIR/cdp_tweet.py" "${CDP_ARGS[@]}"; then
  exit 0
fi

echo "CDP direct method failed, falling back to CLI method..."
if [ -n "$MEDIA_PATH" ]; then
  echo "Warning: CLI fallback does not support media upload. Posting text only."
fi

# Fallback: openclaw browser CLI
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

find_textbox_ref() {
  local snap="$1"
  local ref
  ref="$(
    echo "$snap" \
      | grep -Ei 'textbox' \
      | grep -Ei '帖子文本|post text|tweet text|what is happening|有什么新鲜事|发生了什么|compose post' \
      | extract_first_ref
  )"
  if [ -z "$ref" ]; then
    ref="$(
      echo "$snap" \
        | grep -Ei 'textbox' \
        | extract_first_ref
    )"
  fi
  printf "%s" "$ref"
}

find_enabled_post_button() {
  local snap="$1"
  echo "$snap" \
    | grep -E 'button.*(发帖|发布|Post|Tweet)' \
    | grep -v '\[disabled\]' \
    | extract_first_ref
}

find_success_signal() {
  local snap="$1"
  echo "$snap" | grep -qE 'Your post was sent|已发送|帖子已发送|Post sent|已发布'
}

# Activate X tab via CDP before using CLI
activate_x_tab() {
  local target
  target=$(
    curl -s --max-time 3 "http://127.0.0.1:${CDP_PORT}/json" 2>/dev/null \
      | grep -B5 'compose/post' | grep '"id"' | head -1 | grep -oE '[A-F0-9]{32}' || true
  )
  if [ -z "$target" ]; then
    target=$(
      curl -s --max-time 3 "http://127.0.0.1:${CDP_PORT}/json" 2>/dev/null \
        | grep -B5 'x\.com' | grep '"id"' | head -1 | grep -oE '[A-F0-9]{32}' || true
    )
  fi
  if [ -n "$target" ]; then
    curl -s --max-time 3 "http://127.0.0.1:${CDP_PORT}/json/activate/${target}" >/dev/null 2>&1 || true
  fi
}

$CLI start >/dev/null 2>&1 || true
$CLI open "${BASE_URL}/compose/post" >/dev/null 2>&1 || true
sleep 2
activate_x_tab
sleep 1

SNAPSHOT=""
for _ in 1 2 3 4 5 6 7 8; do
  SNAPSHOT="$(get_snapshot)"
  if [ -n "$SNAPSHOT" ] && echo "$SNAPSHOT" | grep -qi "textbox"; then
    break
  fi
  if [ -z "$SNAPSHOT" ]; then
    activate_x_tab
  fi
  sleep 1
done

if [ -z "$SNAPSHOT" ]; then
  echo "Error: No browser snapshot available."
  exit 1
fi

TEXTBOX_REF="$(find_textbox_ref "$SNAPSHOT")"
if [ -z "$TEXTBOX_REF" ]; then
  echo "Error: Could not find tweet input box"
  exit 1
fi

$CLI click "$TEXTBOX_REF" >/dev/null 2>&1 || true
$CLI type "$TEXTBOX_REF" "$TWEET_TEXT" >/dev/null 2>&1 || true
sleep 1

for _ in 1 2 3 4 5; do
  SNAP="$(get_snapshot)"
  if find_success_signal "$SNAP"; then
    echo "Tweet published successfully."
    exit 0
  fi
  BTN="$(find_enabled_post_button "$SNAP")"
  if [ -n "$BTN" ]; then
    $CLI click "$BTN" >/dev/null 2>&1 || true
    sleep 2
  fi
  sleep 1
done

echo "Post attempted but success signal not detected. Check timeline."
