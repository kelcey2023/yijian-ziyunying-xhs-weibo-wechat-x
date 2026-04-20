#!/bin/bash
# Unified AutoOps engine for the runnable modules in this repository.
# Usage:
#   bash scripts/run_autoops_engine.sh "主题"
#   AUTO_OPS_MAX_CYCLES=3 bash scripts/run_autoops_engine.sh "主题"

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TOPIC="${1:-}"
MAX_CYCLES="${AUTO_OPS_MAX_CYCLES:-1}"
ENABLE_X="${AUTO_OPS_ENABLE_X:-1}"
ENABLE_XHS="${AUTO_OPS_ENABLE_XHS:-1}"
ENABLE_WECHAT="${AUTO_OPS_ENABLE_WECHAT:-1}"
ENABLE_WEIBO="${AUTO_OPS_ENABLE_WEIBO:-1}"
BRIEF_DIR="${AUTO_OPS_BRIEF_DIR:-$ROOT_DIR/output/autoops}"
ENABLE_DREAMINA_MEDIA="${AUTO_OPS_ENABLE_DREAMINA_MEDIA:-1}"
MEDIA_DIR="${AUTO_OPS_MEDIA_DIR:-$ROOT_DIR/output/autoops/media}"
CONTENT_DIR="${AUTO_OPS_CONTENT_DIR:-$ROOT_DIR/output/autoops/content}"
CONTENT_MANIFEST_DIR="${AUTO_OPS_CONTENT_MANIFEST_DIR:-$ROOT_DIR/output/autoops/content_manifests}"
CHANNEL_DRAFTS_DIR="${AUTO_OPS_DRAFTS_DIR:-$ROOT_DIR/output/autoops/drafts}"

if [ -z "$TOPIC" ]; then
  echo 'Usage: run_autoops_engine.sh "topic"'
  exit 1
fi

mkdir -p "$BRIEF_DIR"

randomized_cycle_delay() {
  local enabled="${AUTO_OPS_DELAY_ENABLED:-1}"
  local min_seconds="${AUTO_OPS_DELAY_MIN_SECONDS:-1800}"
  local max_seconds="${AUTO_OPS_DELAY_MAX_SECONDS:-9000}"
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

  echo "AutoOps cycle delay: ${wait_seconds}s"
  sleep "$wait_seconds"
}

run_cycle() {
  local cycle="$1"
  local ts brief_path media_manifest_path content_manifest_path x_image_path xhs_media_path weibo_image_path wechat_image_path x_text_file xhs_draft_json weibo_text_file wechat_json_file

  ts="$(date +%Y%m%d_%H%M%S)"
  brief_path="$BRIEF_DIR/brief_${ts}_cycle${cycle}.json"
  media_manifest_path="$MEDIA_DIR/manifest_${ts}_cycle${cycle}.json"
  content_manifest_path="$CONTENT_MANIFEST_DIR/platform_content_${ts}_cycle${cycle}.json"
  x_image_path=""
  xhs_media_path=""
  weibo_image_path=""
  wechat_image_path=""
  x_text_file=""
  xhs_draft_json=""
  weibo_text_file=""
  wechat_json_file=""

  echo "== AutoOps cycle ${cycle} =="
  AUTO_OPS_BRIEF_PATH="$brief_path" python3 "$ROOT_DIR/scripts/generate_autoops_content.py" "$TOPIC"
  echo "AutoOps brief saved: $brief_path"

  echo "[Content] Generating platform-specific copy"
  AUTO_OPS_PLATFORM_CONTENT_PATH="$content_manifest_path" \
    python3 "$ROOT_DIR/scripts/generate_autoops_platform_content.py" "$TOPIC"
  echo "Platform content manifest saved: $content_manifest_path"

  if [ "$ENABLE_DREAMINA_MEDIA" = "1" ]; then
    echo "[Dreamina] Generating shared media assets"
    AUTO_OPS_MEDIA_MANIFEST_PATH="$media_manifest_path" \
      AUTO_OPS_MEDIA_DIR="$MEDIA_DIR" \
      python3 "$ROOT_DIR/scripts/generate_autoops_media.py" "$TOPIC"
    echo "Dreamina media manifest saved: $media_manifest_path"
    if [ -f "$media_manifest_path" ]; then
      x_image_path="$(python3 - "$media_manifest_path" <<'PY'
import json, sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    data = json.load(handle)
print(data.get("platform_assets", {}).get("x", {}).get("image_path", ""))
PY
)"
      xhs_media_path="$(python3 - "$media_manifest_path" <<'PY'
import json, sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    data = json.load(handle)
asset = data.get("platform_assets", {}).get("xiaohongshu", {})
print(asset.get("image_path", "") or asset.get("video_path", ""))
PY
)"
      weibo_image_path="$(python3 - "$media_manifest_path" <<'PY'
import json, sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    data = json.load(handle)
asset = data.get("platform_assets", {}).get("weibo", {})
print(asset.get("image_path", "") or asset.get("video_path", ""))
PY
)"
      wechat_image_path="$(python3 - "$media_manifest_path" <<'PY'
import json, sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    data = json.load(handle)
asset = data.get("platform_assets", {}).get("wechat", {})
print(asset.get("image_path", "") or asset.get("video_path", ""))
PY
)"
    fi
  fi

  if [ ! -f "$media_manifest_path" ]; then
    python3 - "$media_manifest_path" <<'PY'
import json, sys
payload = {
    "platform_assets": {
        "x": {"image_path": "", "video_path": ""},
        "xiaohongshu": {"image_path": "", "video_path": ""},
        "wechat": {"image_path": "", "video_path": ""},
        "weibo": {"image_path": "", "video_path": ""},
    }
}
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, indent=2)
PY
  fi

  if [ -f "$content_manifest_path" ]; then
    mkdir -p "$CONTENT_DIR"
    x_text_file="$CONTENT_DIR/x_${ts}_cycle${cycle}.txt"
    xhs_draft_json="$CONTENT_DIR/xiaohongshu_${ts}_cycle${cycle}.json"
    weibo_text_file="$CONTENT_DIR/weibo_${ts}_cycle${cycle}.txt"
    wechat_json_file="$CONTENT_DIR/wechat_${ts}_cycle${cycle}.json"
    python3 - "$content_manifest_path" "$x_text_file" "$xhs_draft_json" "$weibo_text_file" "$wechat_json_file" <<'PY'
import json, sys
manifest_path, x_text_path, xhs_json_path, weibo_text_path, wechat_json_path = sys.argv[1:6]
with open(manifest_path, "r", encoding="utf-8") as handle:
    data = json.load(handle)
platforms = data.get("platforms", {})
with open(x_text_path, "w", encoding="utf-8") as handle:
    handle.write(platforms.get("x", {}).get("text", ""))
with open(xhs_json_path, "w", encoding="utf-8") as handle:
    json.dump(platforms.get("xiaohongshu", {}), handle, ensure_ascii=False, indent=2)
with open(weibo_text_path, "w", encoding="utf-8") as handle:
    handle.write(platforms.get("weibo", {}).get("text", ""))
with open(wechat_json_path, "w", encoding="utf-8") as handle:
    json.dump(platforms.get("wechat", {}), handle, ensure_ascii=False, indent=2)
PY
  fi

  if [ "$ENABLE_X" = "1" ]; then
    echo "[X] Running topic-to-post flow"
    AUTO_OPS_X_TEXT_FILE="$x_text_file" \
      bash "$ROOT_DIR/zeelin-twitter-x-auto-ops/scripts/auto_topic_tweet_v3.sh" "$TOPIC" "${x_image_path:-}"
  fi

  if [ "$ENABLE_XHS" = "1" ]; then
    echo "[Xiaohongshu] Running topic-to-post flow"
    AUTO_OPS_XHS_DRAFT_JSON="$xhs_draft_json" \
      bash "$ROOT_DIR/zeelin-xiaohongshu-auto-ops/scripts/auto_topic_post_xiaohongshu.sh" "$TOPIC" "${xhs_media_path:-}"
  fi

  if [ "$ENABLE_WECHAT" = "1" ] || [ "$ENABLE_WEIBO" = "1" ]; then
    echo "[Wechat/Weibo] Exporting platform draft packages"
    AUTO_OPS_DRAFTS_DIR="$CHANNEL_DRAFTS_DIR" \
      python3 "$ROOT_DIR/scripts/export_autoops_channel_drafts.py" "$content_manifest_path" "$media_manifest_path"
  fi

  if [ "$ENABLE_WECHAT" = "1" ] && [ -n "$wechat_json_file" ] && [ -f "$wechat_json_file" ]; then
    echo "[WeChat] Filling article draft"
    python3 - "$ROOT_DIR" "$wechat_json_file" "$wechat_image_path" <<'PY'
import json, subprocess, sys
root, payload_path, image_path = sys.argv[1:4]
with open(payload_path, "r", encoding="utf-8") as handle:
    payload = json.load(handle)
cmd = [
    "python3",
    f"{root}/scripts/publish_wechat_cdp.py",
    "--title", payload.get("title", ""),
    "--summary", payload.get("summary", ""),
    "--body", payload.get("body", ""),
]
if image_path:
    cmd.extend(["--image", image_path])
raise SystemExit(subprocess.run(cmd, check=False).returncode)
PY
  fi

  if [ "$ENABLE_WEIBO" = "1" ] && [ -n "$weibo_text_file" ] && [ -f "$weibo_text_file" ]; then
    echo "[Weibo] Running topic-to-post flow"
    if [ -n "$weibo_image_path" ]; then
      python3 "$ROOT_DIR/scripts/publish_weibo_cdp.py" "$(cat "$weibo_text_file")" --image "$weibo_image_path"
    else
      python3 "$ROOT_DIR/scripts/publish_weibo_cdp.py" "$(cat "$weibo_text_file")"
    fi
  fi
}

if ! [[ "$MAX_CYCLES" =~ ^[0-9]+$ ]] || [ "$MAX_CYCLES" -lt 1 ]; then
  echo "Error: AUTO_OPS_MAX_CYCLES must be a positive integer"
  exit 1
fi

cycle=1
while [ "$cycle" -le "$MAX_CYCLES" ]; do
  run_cycle "$cycle"

  if [ "$cycle" -lt "$MAX_CYCLES" ]; then
    randomized_cycle_delay
  fi

  cycle=$((cycle + 1))
done

echo "AutoOps engine completed ${MAX_CYCLES} cycle(s)."
