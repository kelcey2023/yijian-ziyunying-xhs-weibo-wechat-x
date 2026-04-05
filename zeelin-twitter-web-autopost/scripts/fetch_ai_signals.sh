#!/bin/bash
# Fetch AI signals from multiple public sources

TOPIC="${1:-AI}"

TMP="/tmp/ai_signals.txt"
> $TMP

# HackerNews
curl -s "https://hn.algolia.com/api/v1/search?query=$TOPIC&tags=story" \
 | grep -o '"title":"[^"]*"' \
 | head -5 \
 | sed 's/"title":"//;s/"//' >> $TMP

# GitHub trending via API mirror
curl -s https://ghapi.huchen.dev/repositories \
 | grep -o '"name":"[^"]*"' \
 | head -5 \
 | sed 's/"name":"//;s/"//' >> $TMP

# arXiv simple query
curl -s "http://export.arxiv.org/api/query?search_query=all:$TOPIC&start=0&max_results=5" \
 | grep -o '<title>[^<]*' \
 | sed 's/<title>//' \
 | tail -5 >> $TMP

cat $TMP