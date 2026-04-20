#!/usr/bin/env python3
"""
Generate shared media assets for AutoOps via Dreamina CLI when available.

This script is designed to be safe in mixed environments:
- It always writes a manifest with prompts and status.
- If Dreamina CLI is installed and logged in, it attempts generation.
- If Dreamina is unavailable or unauthenticated, it degrades to prompt-only mode.
"""

from __future__ import annotations

import json
import os
import re
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


def slugify(value: str) -> str:
    value = re.sub(r"\s+", "-", value.strip().lower())
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff_-]", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "topic"


def extract_submit_id(output: str) -> str:
    patterns = [
        r'"submit_id"\s*:\s*"([^"]+)"',
        r"\bsubmit_id\b\s*[:=]\s*([A-Za-z0-9-]+)",
        r"\bsubmit id\b\s*[:=]\s*([A-Za-z0-9-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, output, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def list_files(path: Path) -> list[str]:
    if not path.exists():
        return []
    files = [str(item.resolve()) for item in path.rglob("*") if item.is_file()]
    return sorted(files)


def build_prompts(topic: str) -> dict[str, str]:
    image_prompt = (
        f"围绕主题“{topic}”生成一张适合社媒传播的高完成度主视觉，"
        "主体明确，构图干净，具备品牌感与话题感，中文互联网审美，"
        "适合小红书封面与 X 配图，电影感光影，高清细节，"
        "画面中不要出现任何可读文字、中文、英文、数字、logo、水印，"
        "不要出现“可可”两个字。"
    )
    video_prompt = (
        f"围绕主题“{topic}”生成一支适合社媒传播的短视频，"
        "单镜头或轻运镜，节奏干净，主体突出，画面有故事感，"
        "适合做小红书/社媒短视频素材，"
        "避免字幕、中文、英文、数字、水印，不要出现“可可”两个字。"
    )
    return {"image": image_prompt, "video": video_prompt}


def create_local_fallback_image(topic: str, asset_dir: Path) -> list[str]:
    from PIL import Image, ImageDraw, ImageFilter

    width, height = 1600, 900
    image = Image.new("RGB", (width, height), "#f6efe6")
    draw = ImageDraw.Draw(image)

    # Warm "Claude design" inspired palette without text or logos.
    draw.rectangle((0, 0, width, height), fill="#f5efe7")
    draw.ellipse((-180, 60, 640, 860), fill="#e6843a")
    draw.ellipse((420, -120, 1500, 640), fill="#f2d7b5")
    draw.ellipse((980, 260, 1700, 1020), fill="#cc5a17")
    draw.rounded_rectangle((240, 180, 1220, 760), radius=96, fill="#fbf7f1")
    draw.rounded_rectangle((310, 250, 1090, 690), radius=72, fill="#eadcc7")
    draw.ellipse((1060, 180, 1440, 560), fill="#1f1a17")

    # Layer a few organic curves to make the graphic feel intentional.
    for offset, color in ((0, "#2b231e"), (24, "#4a3b31"), (48, "#8d6a4d")):
        draw.arc((180 + offset, 130 + offset, 1180 + offset, 800 + offset), 210, 330, fill=color, width=10)

    image = image.filter(ImageFilter.GaussianBlur(radius=0.6))
    out_path = asset_dir / "local_fallback_claude_design.png"
    image.save(out_path)
    return [str(out_path.resolve())]


def dreamina_logged_in() -> tuple[bool, str]:
    if shutil.which("dreamina") is None:
        return False, "dreamina CLI not found in PATH"
    code, output = run_command(["dreamina", "user_credit"])
    if code == 0:
        return True, output.strip()
    return False, output.strip()


def query_and_collect(submit_id: str, download_dir: Path) -> tuple[int, str, list[str]]:
    before = set(list_files(download_dir))
    code, output = run_command(
        [
            "dreamina",
            "query_result",
            f"--submit_id={submit_id}",
            f"--download_dir={download_dir}",
        ]
    )
    after = set(list_files(download_dir))
    new_files = sorted(after - before) or sorted(after)
    return code, output, new_files


def generate_asset(
    kind: str,
    prompt: str,
    topic: str,
    output_dir: Path,
    model_version: str,
    ratio: str,
    resolution_type: str,
    duration: int,
    enabled: bool,
) -> dict:
    asset_dir = output_dir / kind
    asset_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "enabled": enabled,
        "status": "disabled" if not enabled else "pending",
        "prompt": prompt,
        "submit_id": "",
        "files": [],
        "primary_file": "",
        "raw_submit_output": "",
        "raw_query_output": "",
        "error": "",
    }
    if not enabled:
        return record

    command = ["dreamina", f"text2{kind}", f"--prompt={prompt}", "--poll=10"]
    if ratio:
        command.append(f"--ratio={ratio}")
    if kind == "image":
        if model_version:
            command.append(f"--model_version={model_version}")
        if resolution_type:
            command.append(f"--resolution_type={resolution_type}")
    else:
        if model_version:
            command.append(f"--model_version={model_version}")
        command.append(f"--duration={duration}")

    submit_code, submit_output = run_command(command)
    record["raw_submit_output"] = submit_output.strip()
    if submit_code != 0:
        record["status"] = "submit_failed"
        record["error"] = submit_output.strip() or f"submit failed with exit code {submit_code}"
        return record

    submit_id = extract_submit_id(submit_output)
    record["submit_id"] = submit_id
    if not submit_id:
        record["status"] = "submitted_without_id"
        record["error"] = "submit succeeded but submit_id was not found in output"
        return record

    query_code, query_output, files = query_and_collect(submit_id, asset_dir)
    record["raw_query_output"] = query_output.strip()
    record["files"] = files
    record["primary_file"] = files[0] if files else ""
    if query_code == 0 and files:
        record["status"] = "downloaded"
    elif query_code == 0:
        record["status"] = "queried_without_files"
        record["error"] = "query_result returned successfully but no media file was downloaded"
    else:
        record["status"] = "query_failed"
        record["error"] = query_output.strip() or f"query failed with exit code {query_code}"
    return record


def main() -> int:
    topic = sys.argv[1].strip() if len(sys.argv) > 1 else ""
    if not topic:
        print('Usage: generate_autoops_media.py "topic"', file=sys.stderr)
        return 1

    root_dir = Path(__file__).resolve().parents[1]
    media_root = Path(os.getenv("AUTO_OPS_MEDIA_DIR", root_dir / "output" / "autoops" / "media")).expanduser()
    topic_dir = media_root / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{slugify(topic)[:40]}"
    topic_dir.mkdir(parents=True, exist_ok=True)

    prompts = build_prompts(topic)
    image_enabled = os.getenv("AUTO_OPS_ENABLE_DREAMINA_IMAGE", "1").strip() == "1"
    video_enabled = os.getenv("AUTO_OPS_ENABLE_DREAMINA_VIDEO", "0").strip() == "1"

    manifest = {
        "topic": topic,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "media_dir": str(topic_dir.resolve()),
        "dreamina": {
            "available": False,
            "logged_in": False,
            "status": "",
        },
        "prompts": prompts,
        "assets": {
            "image": {
                "enabled": image_enabled,
                "status": "skipped",
                "prompt": prompts["image"],
            },
            "video": {
                "enabled": video_enabled,
                "status": "skipped",
                "prompt": prompts["video"],
            },
        },
        "platform_assets": {
            "x": {"image_path": "", "video_path": ""},
            "xiaohongshu": {"image_path": "", "video_path": ""},
            "wechat": {"image_path": "", "video_path": ""},
            "weibo": {"image_path": "", "video_path": ""},
        },
    }

    logged_in, status_output = dreamina_logged_in()
    manifest["dreamina"]["available"] = shutil.which("dreamina") is not None
    manifest["dreamina"]["logged_in"] = logged_in
    manifest["dreamina"]["status"] = status_output

    if not manifest["dreamina"]["available"] or not logged_in:
        reason = "dreamina_not_available_or_logged_out"
        if image_enabled:
            image_dir = topic_dir / "image"
            image_dir.mkdir(parents=True, exist_ok=True)
            files = create_local_fallback_image(topic, image_dir)
            manifest["assets"]["image"] = {
                "enabled": True,
                "status": "local_fallback",
                "prompt": prompts["image"],
                "submit_id": "",
                "files": files,
                "primary_file": files[0] if files else "",
                "raw_submit_output": "",
                "raw_query_output": "",
                "error": reason,
            }
        if video_enabled:
            manifest["assets"]["video"]["status"] = reason
    else:
        manifest["assets"]["image"] = generate_asset(
            kind="image",
            prompt=prompts["image"],
            topic=topic,
            output_dir=topic_dir,
            model_version=os.getenv("AUTO_OPS_DREAMINA_IMAGE_MODEL", "4.5").strip(),
            ratio=os.getenv("AUTO_OPS_DREAMINA_IMAGE_RATIO", "3:4").strip(),
            resolution_type=os.getenv("AUTO_OPS_DREAMINA_IMAGE_RESOLUTION", "2k").strip(),
            duration=0,
            enabled=image_enabled,
        )
        manifest["assets"]["video"] = generate_asset(
            kind="video",
            prompt=prompts["video"],
            topic=topic,
            output_dir=topic_dir,
            model_version=os.getenv("AUTO_OPS_DREAMINA_VIDEO_MODEL", "seedance2.0fast").strip(),
            ratio=os.getenv("AUTO_OPS_DREAMINA_VIDEO_RATIO", "9:16").strip(),
            resolution_type="",
            duration=int(os.getenv("AUTO_OPS_DREAMINA_VIDEO_DURATION", "5").strip() or "5"),
            enabled=video_enabled,
        )

    image_path = manifest["assets"]["image"].get("primary_file", "")
    video_path = manifest["assets"]["video"].get("primary_file", "")
    for platform in manifest["platform_assets"].values():
        platform["image_path"] = image_path
        platform["video_path"] = video_path

    manifest_path = Path(os.getenv("AUTO_OPS_MEDIA_MANIFEST_PATH", topic_dir / "manifest.json")).expanduser()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(manifest_path.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
