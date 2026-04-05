#!/bin/bash
# Advanced auto tweet generator from AI signals
# Usage: bash auto_topic_tweet_v2.sh "topic"

set -euo pipefail

TOPIC="${1:-AI}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SIGNAL_SCRIPT="$SCRIPT_DIR/fetch_ai_signals.sh"
TWEET_SCRIPT="$SCRIPT_DIR/tweet.sh"

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

bash "$TWEET_SCRIPT" "$TWEET" "https://x.com"
