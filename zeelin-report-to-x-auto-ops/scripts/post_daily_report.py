#!/usr/bin/env python3
import json
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path

import requests

REPORT_SITE = "https://thu-nmrc.github.io/THU-ZeeLin-Reports/"
STATE_FILE = os.path.expanduser("~/.openclaw/memory/zeelin_last_report.json")
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
TWEET_SCRIPT = REPO_ROOT / "zeelin-twitter-x-auto-ops" / "scripts" / "tweet.sh"

os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)


def maybe_randomized_delay():
    if os.getenv("AUTO_OPS_DELAY_ENABLED", "1") != "1":
        return

    try:
        min_seconds = int(os.getenv("AUTO_OPS_DELAY_MIN_SECONDS", "600"))
        max_seconds = int(os.getenv("AUTO_OPS_DELAY_MAX_SECONDS", "2400"))
    except ValueError:
        print("Skip randomized delay: invalid AUTO_OPS_DELAY_* configuration")
        return

    if max_seconds < min_seconds:
        wait_seconds = min_seconds
    else:
        wait_seconds = random.randint(min_seconds, max_seconds)

    print(f"Randomized publish delay: {wait_seconds}s")
    time.sleep(wait_seconds)

# Load state
posted = set()
if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        posted = set(json.load(f).get("posted", []))

html = requests.get(REPORT_SITE, timeout=20).text

titles = re.findall(r'heading "([^"]+)"', html)

if not titles:
    print("No reports found")
    exit(0)

latest = titles[0]

if latest in posted:
    print("Report already posted")
    exit(0)

# Try to extract the first meaningful paragraph as summary
summary = None
m = re.search(r'<p[^>]*>([^<]{80,500})</p>', html)
if m:
    summary = m.group(1).strip()

# Try to extract a couple of bullet-style insights
bullets = []
for p in re.findall(r'<p[^>]*>([^<]{40,200})</p>', html):
    text = p.strip()
    if len(text) > 60 and len(bullets) < 2:
        bullets.append(text)

if bullets:
    summary = "\n".join(["• " + b[:120] for b in bullets])

if not summary:
    summary = "A new AI research report analyzing recent developments in AI systems and governance."

tweet = f"New AI research report released.\n\n{latest}\n\n{summary}\n\nReport:\n{REPORT_SITE}\n\n#AI #TechTwitter"

maybe_randomized_delay()

if not TWEET_SCRIPT.exists():
    print(f"Tweet script not found: {TWEET_SCRIPT}", file=sys.stderr)
    sys.exit(1)

result = subprocess.run(["bash", str(TWEET_SCRIPT), tweet, "https://x.com"], check=False)
if result.returncode != 0:
    print(f"Tweet publish failed with exit code {result.returncode}", file=sys.stderr)
    sys.exit(result.returncode)

posted.add(latest)
with open(STATE_FILE, "w") as f:
    json.dump({"posted": sorted(posted)}, f)

print("Posted report:", latest)
