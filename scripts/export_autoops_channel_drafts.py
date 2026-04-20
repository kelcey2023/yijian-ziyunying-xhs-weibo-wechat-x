#!/usr/bin/env python3
"""
Export platform-specific draft packages from content/media manifests.

This gives WeChat and Weibo a practical output even before dedicated web
publishers are added, and also leaves a clear audit trail for every cycle.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: export_autoops_channel_drafts.py <content_manifest> <media_manifest>", file=sys.stderr)
        return 1

    content_manifest = load_json(sys.argv[1])
    media_manifest = load_json(sys.argv[2])
    topic = content_manifest.get("topic", "topic")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    drafts_dir = Path(
        os.getenv(
            "AUTO_OPS_DRAFTS_DIR",
            Path(__file__).resolve().parents[1] / "output" / "autoops" / "drafts",
        )
    ).expanduser()

    platforms = content_manifest.get("platforms", {})
    assets = media_manifest.get("platform_assets", {})

    wechat = platforms.get("wechat", {})
    wechat_asset = assets.get("wechat", {})
    wechat_md = "\n".join(
        [
            f"# {wechat.get('title', topic)}",
            "",
            f"> 导语：{wechat.get('summary', '')}",
            "",
            wechat.get("body", ""),
            "",
            "## 配图",
            f"- 图片: {wechat_asset.get('image_path', '')}",
            f"- 视频: {wechat_asset.get('video_path', '')}",
        ]
    ).strip() + "\n"
    write_text(drafts_dir / f"wechat_{ts}.md", wechat_md)

    weibo = platforms.get("weibo", {})
    weibo_asset = assets.get("weibo", {})
    weibo_md = "\n".join(
        [
            f"# 微博草稿：{topic}",
            "",
            weibo.get("text", ""),
            "",
            "## 配图",
            f"- 图片: {weibo_asset.get('image_path', '')}",
            f"- 视频: {weibo_asset.get('video_path', '')}",
        ]
    ).strip() + "\n"
    write_text(drafts_dir / f"weibo_{ts}.md", weibo_md)

    payload = {
        "topic": topic,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "wechat": {
            "title": wechat.get("title", ""),
            "summary": wechat.get("summary", ""),
            "body": wechat.get("body", ""),
            "image_path": wechat_asset.get("image_path", ""),
            "video_path": wechat_asset.get("video_path", ""),
        },
        "weibo": {
            "text": weibo.get("text", ""),
            "image_path": weibo_asset.get("image_path", ""),
            "video_path": weibo_asset.get("video_path", ""),
        },
    }
    json_path = drafts_dir / f"channel_drafts_{ts}.json"
    write_text(json_path, json.dumps(payload, ensure_ascii=False, indent=2))
    print(str(json_path.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
