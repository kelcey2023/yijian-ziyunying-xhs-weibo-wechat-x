#!/bin/bash
# V3 Auto tweet: topic -> multi-source trends -> tweet -> publish

set -euo pipefail

TOPIC="${1:-AI}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FETCH_AI="$SCRIPT_DIR/fetch_ai_signals.sh"
FETCH_X="$SCRIPT_DIR/fetch_x_trends.sh"
TWEET_SCRIPT="$SCRIPT_DIR/tweet.sh"

TMP="/tmp/ai_topic_signals.txt"
> $TMP

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
bash "$TWEET_SCRIPT" "$TWEET" "https://x.com"
