#!/bin/bash
# V3 Auto tweet: topic -> multi-source trends -> tweet -> publish

set -euo pipefail

TOPIC="${1:-AI}"
IMAGE_PATH="${2:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FETCH_AI="$SCRIPT_DIR/fetch_ai_signals.sh"
FETCH_X="$SCRIPT_DIR/fetch_x_trends.sh"
TWEET_SCRIPT="$SCRIPT_DIR/tweet.sh"
X_TEXT_FILE="${AUTO_OPS_X_TEXT_FILE:-}"

TMP="/tmp/ai_topic_signals.txt"
> $TMP

randomized_delay() {
 local enabled="${AUTO_OPS_DELAY_ENABLED:-1}"
 local min_seconds="${AUTO_OPS_DELAY_MIN_SECONDS:-600}"
 local max_seconds="${AUTO_OPS_DELAY_MAX_SECONDS:-2400}"
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

if [ -n "$X_TEXT_FILE" ] && [ -f "$X_TEXT_FILE" ]; then
  TWEET="$(cat "$X_TEXT_FILE")"
else
  bash "$FETCH_AI" "$TOPIC" >> $TMP
  bash "$FETCH_X" "$TOPIC" >> $TMP

  SIGNALS=$(cat $TMP | head -6)

  TWEET="Developers are talking about: $TOPIC.\n\nKey signals across the AI ecosystem:\n"

  while read -r line; do
   [ -z "$line" ] && continue
   TWEET+="• $line\n"
  done <<< "$SIGNALS"

  TWEET+="\nThis topic is gaining traction across dev communities."
  TWEET+="\n\n#AI #Tech #Developers"
fi

echo "Generated tweet:" 
echo "$TWEET"

# --- Ensure browser is reachable via CDP ---
CDP_PORT="${OPENCLAW_CDP_PORT:-9222}"
export OPENCLAW_CDP_PORT="$CDP_PORT"

openclaw browser start >/dev/null 2>&1 || true

if ! curl -s --max-time 3 "http://127.0.0.1:${CDP_PORT}/json/version" >/dev/null 2>&1; then
  echo "Warning: Browser CDP port ${CDP_PORT} not reachable. Ensure Chrome is running with --remote-debugging-port=${CDP_PORT}"
fi

# --- publish tweet ---
randomized_delay

if [ -n "$IMAGE_PATH" ]; then
  bash "$TWEET_SCRIPT" "$TWEET" "https://x.com" "$IMAGE_PATH"
else
  bash "$TWEET_SCRIPT" "$TWEET" "https://x.com"
fi
