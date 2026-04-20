#!/bin/bash
# Fetch simple X tech trends via public search page titles

TOPIC="${1:-AI}"

curl -s "https://x.com/search?q=$TOPIC&src=typed_query&f=live" \
 | grep -oE '>[A-Za-z0-9 ,\-]{20,120}<' \
 | sed 's/[><]//g' \
 | head -5
