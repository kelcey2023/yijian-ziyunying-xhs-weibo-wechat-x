#!/usr/bin/env python3
"""
Generate platform-specific content payloads for AutoOps.

The output is a single manifest JSON that downstream platform scripts can read.
When a chat model is available through `hermes`, it is used to produce more
natural platform-native copy; otherwise the script falls back to deterministic
templates that still preserve platform differentiation.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(args: list[str]) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return 127, "command not found"
    return proc.returncode, proc.stdout


def ask_hermes(prompt: str) -> str:
    if shutil.which("hermes") is None:
        return ""
    code, output = run_command(["hermes", "chat", "-q", prompt, "-Q"])
    if code != 0:
        return ""
    return output.strip()


def generate_with_model(topic: str) -> dict | None:
    prompt = f"""
你是多平台内容运营总编。请围绕主题《{topic}》生成四个平台的差异化内容，必须严格输出 JSON，不要 markdown，不要解释。

JSON schema:
{{
  "x": {{
    "text": "适合 X/Twitter 的短帖，2-5 句，信息浓缩，可讨论，可附 2-4 个英文标签"
  }},
  "xiaohongshu": {{
    "title": "14-20 字中文标题",
    "body": "350-650 字正文，口语化、场景化，适合种草或经验分享",
    "tags": ["中文标签1", "中文标签2", "中文标签3", "中文标签4", "中文标签5"]
  }},
  "wechat": {{
    "title": "适合微信公众号的中文标题",
    "summary": "公众号导语 80-140 字",
    "body": "800-1600 字中文正文，结构完整、观点清晰、适合公号阅读"
  }},
  "weibo": {{
    "text": "适合微博的中文短帖，强话题、强传播、短促有记忆点，可附 2-4 个话题标签"
  }}
}}

要求：
1. 四个平台绝不能同文。
2. X 要更快、更短、更像观点帖。
3. 小红书要更生活化、更完整。
4. 微信公号要更完整、更适合深度阅读。
5. 微博要更短、更抓眼球、更有传播性。
""".strip()
    raw = ask_hermes(prompt)
    if not raw:
        return None
    try:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            return None
        return json.loads(raw[start : end + 1])
    except Exception:
        return None


def fallback_manifest(topic: str) -> dict:
    return {
        "x": {
            "text": (
                f"{topic} is turning into a real conversation across product, marketing, and creator workflows.\n\n"
                "The teams that win will package it into repeatable content systems, not one-off experiments.\n\n"
                "#AI #Creators #Growth"
            )
        },
        "xiaohongshu": {
            "title": f"{topic}到底怎么做才更有效",
            "body": (
                f"最近很多人都在聊“{topic}”，但大多数内容的问题是：看起来很热闹，真正落到执行时却很空。"
                "如果你是想做账号增长、内容运营或者产品种草，其实更重要的不是追一个关键词，而是把它翻译成用户能立刻感知的场景。\n\n"
                f"我更建议把“{topic}”拆成三步来做：第一步先确定谁最需要这个主题，第二步把它放进真实使用场景里，第三步再把内容写成用户一眼能看懂、愿意收藏和转发的形式。"
                "很多时候不是内容不行，而是表达方式太像汇报，不像分享。\n\n"
                "如果你想让内容更容易出效果，可以优先抓三个点：有没有具体场景、有没有明确收益、有没有降低决策成本。"
                "用户不是不想看，而是不想费力理解。\n\n"
                f"所以与其泛泛地讲“{topic}很重要”，不如直接告诉用户：它能帮你省什么时间、解决什么麻烦、带来什么结果。"
                "一旦表达具体了，内容的点击、停留和转化一般都会明显改善。\n\n"
                "如果是你来做这个主题，你会更想把它写成经验分享，还是做成种草内容？"
            ),
            "tags": ["内容运营", "自媒体", "小红书运营", "品牌表达", topic],
        },
        "wechat": {
            "title": f"关于{topic}，真正值得做的不是跟风，而是形成方法",
            "summary": (
                f"很多团队都在讨论“{topic}”，但真正拉开差距的并不是谁先说，而是谁能把它沉淀成可复用的方法和内容系统。"
            ),
            "body": (
                f"这段时间，“{topic}”几乎成了内容和运营圈里绕不开的话题。很多人第一反应是追热点、抢表达、做概念，但真正有价值的动作，往往不是更快发声，而是更早形成结构。\n\n"
                "为什么同样一个主题，有的人只是跟风，有的人却能持续拿到流量和转化？核心差别在于，前者是在消费热点，后者是在搭建方法。"
                "当一个主题进入大众注意力之后，真正值得做的是把它拆成受众、场景、表达、分发四个层次，再反过来设计内容，而不是先写再找角度。\n\n"
                f"以“{topic}”为例，如果只停留在概念介绍，用户很快就会划走；但如果你能告诉用户，它和自己当下的问题有什么关系，能节省什么时间、减少什么损失、带来什么更明确的收益，内容的穿透力就完全不同。"
                "这也是为什么现在很多优质账号开始从“讲知识”转向“讲场景”，因为场景比抽象判断更容易让人代入。\n\n"
                "如果要把这个主题做成稳定的内容能力，我更建议按三步来：第一步先明确目标受众；第二步确定最容易被理解的切入场景；第三步为不同平台准备不同表达版本。"
                "这样做的好处是，内容不再只是一次性输出，而是可以变成一个可复用的素材池。\n\n"
                f"回到“{topic}”本身，真正能拉开差距的，不是知道这个词，而是能不能把它变成一整套更高效的生产与分发动作。"
                "当你开始用系统思维看待内容时，热点才会真正成为资产，而不是稍纵即逝的噪音。"
            ),
        },
        "weibo": {
            "text": (
                f"大家都在聊“{topic}”，但真正拉开差距的从来不是谁先发，而是谁先把它做成方法。"
                "热点会过去，系统能力不会。"
                f"如果你还在把{topic}当一次性内容点，可能已经慢了半步。"
                f"#{topic} #内容运营 #品牌增长"
            )
        },
    }


def main() -> int:
    topic = sys.argv[1].strip() if len(sys.argv) > 1 else ""
    if not topic:
        print('Usage: generate_autoops_platform_content.py "topic"', file=sys.stderr)
        return 1

    manifest = {
        "topic": topic,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "generator": "fallback",
        "platforms": {},
    }

    model_result = generate_with_model(topic)
    if model_result:
        manifest["generator"] = "hermes"
        manifest["platforms"] = model_result
    else:
        manifest["platforms"] = fallback_manifest(topic)

    output_path = Path(
        os.getenv(
            "AUTO_OPS_PLATFORM_CONTENT_PATH",
            Path(__file__).resolve().parents[1] / "output" / "autoops" / "platform_content.json",
        )
    ).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(output_path.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
