#!/usr/bin/env python3
"""
Generate a lightweight AutoOps brief from a single topic.

This script does not publish anything by itself. It creates a normalized
operations brief that the AutoOps engine can log before dispatching
platform-specific scripts.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime


def build_brief(topic: str) -> dict:
    base_tags = ["AI运营", "AutoOps", "内容自动化"]
    return {
        "topic": topic,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": f"围绕主题“{topic}”执行一轮账号自动运营。",
        "signals": [
            "优先结合公开热点和轻量 Web 信号源选角度",
            "同主题内容按平台做差异化表达，不直接四端同文",
            "先确保持续运行，再逐步提升内容质量",
        ],
        "platforms": {
            "x": {
                "goal": "输出短内容，兼顾互动与曝光",
                "style": "信息浓缩、适合转发讨论",
                "tags": base_tags + ["X运营"],
            },
            "xiaohongshu": {
                "goal": "输出种草型或经验型长文内容",
                "style": "口语化、场景化、可直接发布",
                "tags": base_tags + ["小红书运营"],
            },
            "wechat": {
                "goal": "输出适合公众号的深度文章",
                "style": "完整结构、观点清晰、适合长阅读",
                "tags": base_tags + ["微信公号运营"],
            },
            "weibo": {
                "goal": "输出高传播的热点短帖",
                "style": "更短、更快、更有话题性",
                "tags": base_tags + ["微博运营"],
            },
        },
    }


def main() -> int:
    topic = sys.argv[1].strip() if len(sys.argv) > 1 else ""
    if not topic:
        print('Usage: generate_autoops_content.py "topic"', file=sys.stderr)
        return 1

    brief = build_brief(topic)
    output_path = os.getenv("AUTO_OPS_BRIEF_PATH", "").strip()
    payload = json.dumps(brief, ensure_ascii=False, indent=2)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(payload)
        print(output_path)
    else:
        print(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
