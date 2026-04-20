#!/bin/bash
# Advanced auto tweet generator from AI signals
# Usage: bash auto_topic_tweet_v2.sh "topic"

set -euo pipefail

TOPIC="${1:-AI}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SIGNAL_SCRIPT="$SCRIPT_DIR/fetch_ai_signals.sh"
TWEET_SCRIPT="$SCRIPT_DIR/tweet.sh"

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

SIGNALS=$(bash "$SIGNAL_SCRIPT" "$TOPIC" | head -5)

TWEET="AI developers are discussing: $TOPIC.\n\nSignals from the tech ecosystem:\n"

while read -r line; do
 [ -z "$line" ] && continue
 TWEET+="• $line\n"
done <<< "$SIGNALS"

TWEET+="\nThis is a sign of how fast the AI ecosystem is evolving."
TWEET+="\n\n#AI #Tech #AIDev"

echo "Generated tweet:" 
echo "$TWEET"

randomized_delay

bash "$TWEET_SCRIPT" "$TWEET" "https://x.com"
