#!/bin/bash
# auto_topic_post_xiaohongshu.sh
# One-command flow: search-driven copywriting -> publish to Xiaohongshu
# Usage:
#   bash auto_topic_post_xiaohongshu.sh "主题"
#   bash auto_topic_post_xiaohongshu.sh "主题" "/tmp/openclaw/uploads/cover.jpg"

set -euo pipefail

TOPIC="${1:-}"
MEDIA_PATH="${2:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
POST_SCRIPT="$SCRIPT_DIR/post_xiaohongshu.sh"
CDP_POST_SCRIPT="$SCRIPT_DIR/run_xhs_publish.sh"
DRAFT_JSON="${AUTO_OPS_XHS_DRAFT_JSON:-}"

if [ -z "$TOPIC" ]; then
  echo "Error: topic is required"
  exit 1
fi

randomized_delay() {
  local enabled="${AUTO_OPS_DELAY_ENABLED:-1}"
  local min_seconds="${AUTO_OPS_DELAY_MIN_SECONDS:-900}"
  local max_seconds="${AUTO_OPS_DELAY_MAX_SECONDS:-3600}"
  local wait_seconds

  if [ "$enabled" != "1" ]; then
    return 0
  fi

  if ! [[ "$min_seconds" =~ ^[0-9]+$ && "$max_seconds" =~ ^[0-9]+$ ]]; then
    echo "Skip randomized delay: invalid AUTO_OPS_DELAY_* configuration"
    return 0
  fi

  if [ "$max_seconds" -lt "$min_seconds" ]; then
    wait_seconds="$min_seconds"
  else
    wait_seconds=$(( min_seconds + RANDOM % (max_seconds - min_seconds + 1) ))
  fi

  echo "Randomized publish delay: ${wait_seconds}s"
  sleep "$wait_seconds"
}

PROMPT="你是小红书爆文运营专家。围绕主题【${TOPIC}】先基于公开热点信号进行选题，再生成一篇软性带货小红书图文文案。必须包含人性驱动（痛点、损失厌恶、从众、即时收益）。\n\n要求：\n1) 先在脑内完成热点抽取与选题，选择最优角度；\n2) 标题14-20字，口语化，不夸张；\n3) 正文350-650字，结构：场景痛点->原因->3条解决路径->软性植入->结果->互动问题；\n4) 标签6-10个；\n5) 禁止硬广与绝对化承诺。\n\n输出格式必须严格如下，不要任何额外解释：\n<TITLE>标题</TITLE>\n<CONTENT>正文</CONTENT>\n<TAGS>标签1,标签2,标签3</TAGS>"

echo "Generating Xiaohongshu copy for topic: $TOPIC"

generate_copy() {
  local output=""
  local response_json=""

  has_required_markup() {
    printf "%s" "$1" | rg -q '<TITLE>.*</TITLE>' && printf "%s" "$1" | rg -q '<CONTENT>'
  }

  if command -v hermes >/dev/null 2>&1; then
    output="$(hermes chat -q "$PROMPT" -Q 2>&1 || true)"
    if [ -n "$output" ] && ! printf "%s" "$output" | rg -q 'Session not found' && has_required_markup "$output"; then
      printf "%s" "$output"
      return 0
    fi
  fi

  if command -v openclaw >/dev/null 2>&1; then
    response_json="$(openclaw agent --local --agent main --message "$PROMPT" --json 2>/dev/null || true)"
    output="$(printf "%s" "$response_json" | jq -r '.result.payloads[0].text // empty')"
    if [ -n "$output" ] && ! printf "%s" "$output" | rg -q 'Session not found' && has_required_markup "$output"; then
      printf "%s" "$output"
      return 0
    fi

    response_json="$(openclaw agent --agent main --message "$PROMPT" --json 2>&1 || true)"
    if ! printf "%s" "$response_json" | rg -q 'Session not found'; then
      output="$(printf "%s" "$response_json" | jq -r '.result.payloads[0].text // empty' 2>/dev/null || true)"
      if [ -n "$output" ] && has_required_markup "$output"; then
        printf "%s" "$output"
        return 0
      fi
    fi
  fi

  return 1
}

if [ -n "$DRAFT_JSON" ] && [ -f "$DRAFT_JSON" ]; then
  TITLE="$(python3 - <<'PY' "$DRAFT_JSON"
import json, sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    data = json.load(handle)
print(data.get("title", ""))
PY
)"
  CONTENT="$(python3 - <<'PY' "$DRAFT_JSON"
import json, sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    data = json.load(handle)
print(data.get("body", ""))
PY
)"
  TAGS_LINE="$(python3 - <<'PY' "$DRAFT_JSON"
import json, sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    data = json.load(handle)
tags = data.get("tags", []) or []
print(" ".join(f"#{tag}" for tag in tags))
PY
)"
else
  TEXT="$(generate_copy || true)"

  if [ -z "$TEXT" ]; then
    echo "Error: failed to generate copy. Hermes/OpenClaw returned no usable stateless response."
    exit 1
  fi

  TITLE="$(printf "%s" "$TEXT" | awk 'match($0, /<TITLE>.*<\/TITLE>/){s=substr($0,RSTART,RLENGTH); gsub(/<\/?TITLE>/, "", s); print s; exit}')"
  CONTENT="$(printf "%s" "$TEXT" | awk '
    BEGIN{flag=0}
    /<CONTENT>/{
      flag=1
      sub(/.*<CONTENT>/, "")
    }
    flag{print}
    /<\/CONTENT>/{
      flag=0
    }
  ' | sed '$s:</CONTENT>.*::')"
  TAGS_RAW="$(printf "%s" "$TEXT" | awk 'match($0, /<TAGS>.*<\/TAGS>/){s=substr($0,RSTART,RLENGTH); gsub(/<\/?TAGS>/, "", s); print s; exit}')"
  TAGS_LINE="$(printf "%s" "$TAGS_RAW" | tr ',' '\n' | sed 's/^ *//;s/ *$//' | sed '/^$/d' | awk '{print "#" $0}' | paste -sd ' ' -)"
fi

if [ -z "$TITLE" ] || [ -z "$CONTENT" ]; then
  echo "Error: model output missing <TITLE> or <CONTENT>"
  echo "Raw output:"
  echo "$TEXT"
  exit 1
fi

FINAL_CONTENT="$CONTENT"
if [ -n "$TAGS_LINE" ]; then
  printf -v FINAL_CONTENT "%s\n\n%s" "$CONTENT" "$TAGS_LINE"
fi

mkdir -p "$ROOT_DIR/output"
TS="$(date +%Y%m%d_%H%M%S)"
DRAFT_FILE="$ROOT_DIR/output/draft_${TS}.md"
{
  echo "# $TITLE"
  echo
  echo "$FINAL_CONTENT"
} > "$DRAFT_FILE"

echo "Draft saved: $DRAFT_FILE"

randomized_delay

echo "Publishing..."
if [ -n "$MEDIA_PATH" ]; then
  bash "$CDP_POST_SCRIPT" "$TITLE" "$FINAL_CONTENT" "$MEDIA_PATH"
else
  bash "$POST_SCRIPT" "$TITLE" "$FINAL_CONTENT"
fi

echo "Done: topic -> copy -> publish flow completed"
