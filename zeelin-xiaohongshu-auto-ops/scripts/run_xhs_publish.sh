#!/bin/bash

# Xiaohongshu CDP publisher wrapper
# Usage:
# run_xhs_publish.sh "title" "content" [/absolute/path/to/media]

TITLE="$1"
BODY="$2"
MEDIA_PATH="${3:-}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -z "$TITLE" ] || [ -z "$BODY" ]; then
  echo "Usage: run_xhs_publish.sh \"title\" \"content\" [/absolute/path/to/media]"
  exit 1
fi

if [ -n "$MEDIA_PATH" ]; then
  python3 "$SCRIPT_DIR/cdp_xhs_publish.py" "$TITLE" "$BODY" "$MEDIA_PATH"
else
  python3 "$SCRIPT_DIR/cdp_xhs_publish.py" "$TITLE" "$BODY"
fi
