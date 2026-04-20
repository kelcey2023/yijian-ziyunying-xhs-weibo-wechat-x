#!/bin/bash
# Auto tweet from a topic: fetch simple tech signals + generate tweet + publish
# Usage: bash auto_topic_tweet.sh "topic"

set -euo pipefail

TOPIC="${1:-}"
BASE_URL="https://x.com"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TWEET_SCRIPT="$SCRIPT_DIR/tweet.sh"

if [ -z "$TOPIC" ]; then
  echo "Usage: auto_topic_tweet.sh \"topic\""
  exit 1
fi

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

# --- Step 1: get lightweight signals (Hacker News titles mentioning topic) ---
SIGNALS=$(curl -s "https://hn.algolia.com/api/v1/search?query=$TOPIC&tags=story" \
  | grep -o '"title":"[^"]*"' \
  | head -5 \
  | sed 's/"title":"//;s/"//')

# --- Step 2: build a tweet ---
TWEET="Hot topic in AI dev circles: $TOPIC.\n\nRecent signals from the tech community:\n"

while read -r line; do
  [ -z "$line" ] && continue
  TWEET+="• $line\n"
done <<< "$SIGNALS"

TWEET+="\nThis shows how fast the AI tooling ecosystem is evolving."
TWEET+="\n\n#AI #AIDev #Tech"

# --- Step 3: publish ---

echo "Generated tweet:"
echo "----------------"
echo "$TWEET"
echo "----------------"

randomized_delay

bash "$TWEET_SCRIPT" "$TWEET" "$BASE_URL"
