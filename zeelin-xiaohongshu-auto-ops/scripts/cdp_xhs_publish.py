#!/usr/bin/env python3
"""
Xiaohongshu creator — fill title + body via CDP, including content inside iframes.

- Walks Page.getFrameTree, uses Page.createIsolatedWorld + Runtime.evaluate per frame.
- After focus, uses Input.insertText (focus must be in the target frame).
- Supports optional image/video upload through hidden file inputs on the publish page.
- Does NOT click「发布」unless env XHS_NO_PUBLISH is unset or false.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import time
import urllib.request

import websocket


def port() -> int:
    return int(os.environ.get("OPENCLAW_CDP_PORT", "9222"))


def list_tabs(p: int):
    with urllib.request.urlopen(f"http://127.0.0.1:{p}/json", timeout=8) as r:
        return json.loads(r.read())


def activate(p: int, tid: str):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{p}/json/activate/{tid}", timeout=5)
    except Exception:
        pass


def find_xhs(p: int):
    for t in list_tabs(p):
        if t.get("type") == "page" and "creator.xiaohongshu.com" in t.get("url", ""):
            return t
    for t in list_tabs(p):
        if t.get("type") == "page" and "xiaohongshu.com" in t.get("url", ""):
            return t
    return None


def connect_ws(ws_url: str, p: int):
    return websocket.create_connection(ws_url, timeout=15, origin=f"http://127.0.0.1:{p}")


def cdp_send(ws, method: str, params=None, timeout=25):
    msg_id = int(time.time() * 1000) % 1_000_000_000
    ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
    deadline = time.time() + timeout
    while time.time() < deadline:
        ws.settimeout(max(0.5, deadline - time.time()))
        try:
            raw = ws.recv()
        except websocket.WebSocketTimeoutException:
            continue
        data = json.loads(raw)
        if data.get("id") == msg_id:
            if "error" in data:
                raise RuntimeError(str(data["error"]))
            return data.get("result", {})
    raise TimeoutError(method)


def collect_frame_ids(tree: dict) -> list[str]:
    out: list[str] = []
    frame = tree.get("frame") or {}
    fid = frame.get("id")
    if fid:
        out.append(fid)
    for child in tree.get("childFrames") or []:
        out.extend(collect_frame_ids(child))
    return out


def create_ctx(ws, frame_id: str) -> int:
    r = cdp_send(
        ws,
        "Page.createIsolatedWorld",
        {
            "frameId": frame_id,
            "worldName": "__openclaw_xhs__",
            "grantUniverseAccess": True,
        },
    )
    return int(r["executionContextId"])


def js_eval_ctx(ws, execution_context_id: int, expr: str, timeout=20):
    r = cdp_send(
        ws,
        "Runtime.evaluate",
        {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": False,
            "executionContextId": execution_context_id,
        },
        timeout=timeout,
    )
    res = r.get("result", {})
    if res.get("type") == "string":
        return res.get("value", "")
    if res.get("type") == "boolean":
        return res.get("value", False)
    if res.get("type") == "number":
        return res.get("value", 0)
    return res.get("value", "")


def js_eval(ws, expr: str, timeout=20):
    r = cdp_send(
        ws,
        "Runtime.evaluate",
        {"expression": expr, "returnByValue": True, "awaitPromise": False},
        timeout=timeout,
    )
    res = r.get("result", {})
    if res.get("type") == "string":
        return res.get("value", "")
    if res.get("type") == "boolean":
        return res.get("value", False)
    if res.get("type") == "number":
        return res.get("value", 0)
    return res.get("value", "")


PROBE_JS = """
(() => {
    const inputs = document.querySelectorAll('input, textarea');
    const ce = document.querySelectorAll('[contenteditable="true"]');
    let titleLike = 0;
    for (const i of inputs) {
        const ph = (i.placeholder || '') + (i.getAttribute('aria-label') || '');
        if (/标题|topic|title/i.test(ph) || i.maxLength === 20) titleLike++;
    }
    return JSON.stringify({
        inputs: inputs.length,
        ce: ce.length,
        titleLike: titleLike,
        path: location.pathname,
        href: location.href.substring(0, 80)
    });
})()
"""

FOCUS_TITLE_JS = """
(() => {
    const bad = new Set(['hidden', 'file', 'checkbox', 'radio', 'submit']);
    const sels = [
        'textarea[placeholder*="标题"]',
        'textarea[placeholder*="填写标题"]',
        'input[placeholder*="标题"]',
        'input[placeholder*="填写标题"]',
        'input[maxlength="20"]',
        'input.d-text',
        '.d-input input',
        '.title-container input',
        'input[type="text"]'
    ];
    for (const s of sels) {
        for (const el of document.querySelectorAll(s)) {
            if (!el.offsetParent) continue;
            if (el.tagName === 'INPUT' && bad.has(el.type)) continue;
            el.focus();
            el.click();
            return "OK_TITLE:" + s;
        }
    }
    const vis = [...document.querySelectorAll("input, textarea")].filter(
        i => i.offsetParent && !bad.has(i.type));
    if (vis[0]) {
        vis[0].focus();
        vis[0].click();
        return "OK_TITLE:first-visible";
    }
    return "ERROR:NO_TITLE";
})()
"""

FOCUS_BODY_JS = """
(() => {
    const sels = [
        '.tiptap.ProseMirror',
        '.ProseMirror[contenteditable="true"]',
        '.ql-editor',
        '.note-editor [contenteditable="true"]',
        '[data-placeholder*="正文"]',
        '[data-placeholder*="分享"]',
        'div.d-input-editor [contenteditable="true"]',
        '[contenteditable="true"]',
        'textarea'
    ];
    for (const s of sels) {
        for (const el of document.querySelectorAll(s)) {
            if (!el.offsetParent) continue;
            const h = el.getBoundingClientRect().height;
            if (s === '[contenteditable="true"]' && h < 30) continue;
            el.focus();
            el.click();
            return "OK_BODY:" + s;
        }
    }
    return "ERROR:NO_BODY";
})()
"""

PUBLISH_JS = """
(() => {
    const labels = ['发布', '立即发布', '定时发布'];
    const isMenuPublish = (text, cls) => text === '发布笔记' || /btn-wrapper|btn-inner|btn-text/.test(cls || '');
    for (const n of document.querySelectorAll('button, [role="button"], div[class*="publish"], div[class*="submit"], span[class*="publish"]')) {
        if (!n.offsetParent) continue;
        const t = (n.textContent || '').replace(/\\s+/g, '').trim();
        const cls = n.className || '';
        if (isMenuPublish(t, cls)) continue;
        for (const lb of labels) {
            if (t === lb) {
                n.click();
                return 'CLICK:' + t;
            }
        }
    }
    return 'SKIP';
})()
"""

CONFIRM_DIALOG_JS = """
(() => {
    const labels = ['确认发布', '确认', '继续发布', '确定发布', '确定', '立即发布'];
    for (const n of document.querySelectorAll('button, [role="button"], div[class*="btn"], span[class*="btn"]')) {
        if (!n.offsetParent) continue;
        const t = (n.textContent || '').trim();
        for (const lb of labels) {
            if (t === lb) {
                n.click();
                return 'CONFIRM:' + t;
            }
        }
    }
    for (const n of document.querySelectorAll('button, [role="button"], div[class*="btn"], span[class*="btn"]')) {
        if (!n.offsetParent) continue;
        const t = (n.textContent || '').trim();
        const cls = n.className || '';
        if (isMenuPublish(t, cls)) continue;
        for (const lb of labels) {
            if (t.includes(lb)) {
                n.click();
                return 'CONFIRM_PARTIAL:' + t;
            }
        }
    }
    return 'NO_DIALOG';
})()
"""

CHECK_SUCCESS_JS = """
(() => {
    const text = document.body.innerText || '';
    if (/发布成功|笔记已发布|审核中|内容已提交|已发布/.test(text)) return 'SUCCESS';
    const url = location.href;
    if (/\/notes|\/published|note-manage/.test(url)) return 'SUCCESS_URL';
    return 'STILL_ON_PAGE';
})()
"""

CHECK_MEDIA_READY_JS = """
(() => {
    const text = (document.body.innerText || '').replace(/\\s+/g, '');
    const fileInput = document.querySelector('input[type="file"]');
    const files = fileInput && fileInput.files ? fileInput.files.length : 0;
    const hasPreview = !!document.querySelector(
        '.upload-preview-container img, .upload-preview img, .preview-img, .media-card img, .recommend-item img'
    );
    const hasVideo = !!document.querySelector('.upload-preview-container video, .player-container video, video');
    const hasEditor = document.querySelectorAll('textarea, [contenteditable="true"]').length > 1;
    if (hasPreview || hasVideo || hasEditor) return 'MEDIA_READY';
    if (/替换|重新上传|继续编辑|封面设置|裁剪|上传成功|预览/.test(text)) return 'MEDIA_READY_TEXT';
    if (files > 0) return 'FILE_SELECTED_WAITING';
    return 'MEDIA_PENDING';
})()
"""

CHECK_UPLOAD_STAGE_JS = """
(() => {
    const text = (document.body.innerText || '').replace(/\\s+/g, '');
    const files = document.querySelector('input[type="file"]')?.files?.length || 0;
    const editorInputs = document.querySelectorAll('textarea, [contenteditable="true"]').length;
    return {
        files,
        editorInputs,
        stillUploader: /上传图片，或写文字生成图片|上传图片|文字配图/.test(text),
        hasNext: /下一步|继续/.test(text),
        hasTitle: /标题/.test(text),
    };
})()
"""


def score_probe(probe_str: str) -> int:
    try:
        o = json.loads(probe_str)
        return int(o.get("ce", 0)) * 10 + int(o.get("titleLike", 0)) * 5 + int(o.get("inputs", 0))
    except Exception:
        return 0


def best_frame_for_editor(ws) -> str | None:
    """Returns frame_id for the subtree that looks most like the editor."""
    tree = cdp_send(ws, "Page.getFrameTree", {})
    frame_tree = tree.get("frameTree", {})
    ids = collect_frame_ids(frame_tree)
    cdp_send(ws, "Runtime.enable", {})

    best_score = -1
    best_fid: str | None = None

    for fid in ids:
        try:
            ctx = create_ctx(ws, fid)
            probe = js_eval_ctx(ws, ctx, PROBE_JS)
            sc = score_probe(probe)
            if sc > best_score:
                best_score = sc
                best_fid = fid
        except Exception:
            continue

    if best_fid is None or best_score < 1:
        return None
    return best_fid


def prepare_page(ws, media_kind: str = "image"):
    def probe_main():
        return js_eval(ws, PROBE_JS)

    p0 = probe_main()
    print("Main-frame probe:", p0)
    try:
        o = json.loads(p0)
        href = str(o.get("href", ""))
        if "creator.xiaohongshu.com" not in href or "publish" not in href:
            cdp_send(
                ws,
                "Page.navigate",
                {"url": "https://creator.xiaohongshu.com/publish/publish?source=official&from=menu"},
            )
            time.sleep(5)
            print("After navigate:", probe_main())
        elif int(o.get("ce", 0)) < 1 and int(o.get("inputs", 0)) < 2:
            cdp_send(
                ws,
                "Page.navigate",
                {"url": "https://creator.xiaohongshu.com/publish/publish?source=official&from=menu"},
            )
            time.sleep(5)
            print("After navigate:", probe_main())
    except Exception:
        cdp_send(
            ws,
            "Page.navigate",
            {"url": "https://creator.xiaohongshu.com/publish/publish?source=official&from=menu"},
        )
        time.sleep(5)

    select_publish_mode(ws, media_kind)


def media_kind_for_path(media_path: str) -> str:
    ext = pathlib.Path(media_path).suffix.lower()
    if ext in {".mp4", ".mov", ".m4v", ".webm"}:
        return "video"
    return "image"


def select_publish_mode(ws, media_kind: str):
    if media_kind == "video":
        labels = ["上传视频", "视频笔记", "发视频", "发布视频"]
    else:
        labels = ["上传图文", "图文笔记", "写图文", "发布图文", "长文"]

    js = f"""
    (() => {{
        const labels = {json.dumps(labels, ensure_ascii=False)};
        const clickNode = (node) => {{
            if (!node || !node.offsetParent) return false;
            const target = node.closest('.creator-tab') || node;
            const rect = target.getBoundingClientRect();
            target.dispatchEvent(new MouseEvent('mouseover', {{bubbles: true, cancelable: true, clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2}}));
            target.dispatchEvent(new MouseEvent('mousedown', {{bubbles: true, cancelable: true, clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2}}));
            target.dispatchEvent(new MouseEvent('mouseup', {{bubbles: true, cancelable: true, clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2}}));
            target.click();
            return true;
        }};

        for (const tab of document.querySelectorAll('.creator-tab')) {{
            const t = (tab.textContent || '').replace(/\\s+/g,'').trim();
            for (const label of labels) {{
                if (t === label || t.includes(label)) {{
                    clickNode(tab);
                    const active = document.querySelector('.creator-tab.active');
                    return 'OPEN_TAB:' + label + ':' + ((active && active.textContent) || '');
                }}
            }}
        }}
        for (const n of document.querySelectorAll('div,button,span,a')) {{
            if (!n.offsetParent) continue;
            const t = (n.textContent || '').replace(/\\s+/g,'').trim();
            for (const label of labels) {{
                if (t === label || t.includes(label)) {{
                    clickNode(n);
                    const active = document.querySelector('.creator-tab.active');
                    return 'OPEN_FALLBACK:' + label + ':' + ((active && active.textContent) || '');
                }}
            }}
        }}
        return 'SKIP';
    }})()
    """
    result = js_eval(ws, js)
    print("Mode select:", result)
    time.sleep(1.5)


def upload_media(ws, media_path: str):
    absolute_path = os.path.abspath(media_path)
    if not os.path.isfile(absolute_path):
        raise FileNotFoundError(f"media file not found: {absolute_path}")

    media_kind = media_kind_for_path(absolute_path)
    target_node = 0
    for attempt in range(4):
        if media_kind == "image":
            select_publish_mode(ws, "image")
        cdp_send(ws, "DOM.enable", {})
        root = cdp_send(ws, "DOM.getDocument", {"depth": -1, "pierce": True})
        root_id = root.get("root", {}).get("nodeId")
        if not root_id:
            raise RuntimeError("failed to access DOM root for XHS upload")

        query = cdp_send(ws, "DOM.querySelectorAll", {"nodeId": root_id, "selector": 'input[type="file"]'})
        node_ids = query.get("nodeIds", [])
        if not node_ids:
            time.sleep(1)
            continue

        for node_id in node_ids:
            try:
                attrs = cdp_send(ws, "DOM.getAttributes", {"nodeId": node_id}).get("attributes", [])
            except Exception:
                continue
            attr_map = dict(zip(attrs[::2], attrs[1::2]))
            accept = (attr_map.get("accept") or "").lower()
            if media_kind == "image" and any(token in accept for token in ("image", ".png", ".jpg", ".jpeg", ".webp")):
                target_node = node_id
                break
            if media_kind == "video" and any(token in accept for token in ("video", ".mp4", ".mov", ".m4v", ".webm")):
                target_node = node_id
                break
        if target_node:
            break
        time.sleep(1)

    if not target_node:
        raise RuntimeError(f"no matching {media_kind} file input found on XHS publish page")

    cdp_send(ws, "DOM.setFileInputFiles", {"nodeId": target_node, "files": [absolute_path]})
    print(f"Upload started: {absolute_path}")

    wait_seconds = 15 if media_kind_for_path(absolute_path) == "video" else 8
    for attempt in range(wait_seconds):
        state = js_eval(ws, CHECK_MEDIA_READY_JS)
        print(f"  Media state {attempt+1}/{wait_seconds}: {state}")
        if "MEDIA_READY" in str(state):
            return
        time.sleep(1)
    stage = js_eval(ws, CHECK_UPLOAD_STAGE_JS)
    raise RuntimeError(f"media upload did not become ready in time: {stage}")


def type_into_focused(ws, text: str):
    cdp_send(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "a", "code": "KeyA", "modifiers": 2})
    cdp_send(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "a", "code": "KeyA", "modifiers": 2})
    cdp_send(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Backspace", "code": "Backspace"})
    cdp_send(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "Backspace", "code": "Backspace"})
    time.sleep(0.12)
    cdp_send(ws, "Input.insertText", {"text": text})


def fill_in_context(ws, ctx_id: int, title: str, body: str) -> bool:
    r1 = js_eval_ctx(ws, ctx_id, FOCUS_TITLE_JS)
    print("(iframe) Title focus:", r1)
    if "OK" not in str(r1):
        return False
    type_into_focused(ws, title)
    time.sleep(0.4)

    r2 = js_eval_ctx(ws, ctx_id, FOCUS_BODY_JS)
    print("(iframe) Body focus:", r2)
    if "OK" not in str(r2):
        return False
    type_into_focused(ws, body)
    return True


def fill_in_main(ws, title: str, body: str) -> bool:
    r1 = js_eval(ws, FOCUS_TITLE_JS)
    print("Title focus:", r1)
    if "OK" not in str(r1):
        return False
    type_into_focused(ws, title)
    time.sleep(0.4)
    r2 = js_eval(ws, FOCUS_BODY_JS)
    print("Body focus:", r2)
    if "OK" not in str(r2):
        return False
    type_into_focused(ws, body)
    return True


def main():
    if len(sys.argv) < 3:
        print("Usage: cdp_xhs_publish.py <title> <body> [media_path]", file=sys.stderr)
        sys.exit(1)

    title = sys.argv[1]
    body = sys.argv[2]
    media_path = sys.argv[3] if len(sys.argv) > 3 else ""
    p = port()
    tab = find_xhs(p)
    if not tab:
        print("ERROR: No xiaohongshu.com tab in CDP Chrome.", file=sys.stderr)
        sys.exit(1)

    activate(p, tab["id"])
    time.sleep(0.3)
    ws = connect_ws(tab["webSocketDebuggerUrl"], p)
    try:
        cdp_send(ws, "Page.enable", {})
        preferred_kind = media_kind_for_path(media_path) if media_path else "image"
        prepare_page(ws, preferred_kind)
        if media_path:
            upload_media(ws, media_path)

        ok = fill_in_main(ws, title, body)
        if not ok:
            print("Main frame incomplete, trying iframe contexts...")
            fid = best_frame_for_editor(ws)
            if not fid:
                print("ERROR: No suitable editor iframe found.", file=sys.stderr)
                sys.exit(1)
            print(f"Using iframe frameId={fid[:16]}...")
            ctx_id = create_ctx(ws, fid)
            if not fill_in_context(ws, ctx_id, title, body):
                print("ERROR: Could not fill title/body in iframe.", file=sys.stderr)
                sys.exit(1)

        time.sleep(0.8)
        no_publish = os.environ.get("XHS_NO_PUBLISH", "").strip() in ("1", "true", "yes")
        if no_publish:
            print("XHS: content filled. Skipping publish (XHS_NO_PUBLISH=1).")
        else:
            # scroll to bottom so 发布 / 下一步 buttons are visible
            js_eval(ws, "(function(){window.scrollTo(0,document.body.scrollHeight);return 'SCROLLED';})()")
            time.sleep(1)

            # some flows have 下一步 before 发布
            next_js = """
            (() => {
                for (const n of document.querySelectorAll('button, [role="button"]')) {
                    const t = (n.textContent || '').trim();
                    if (t === '下一步' && n.offsetParent !== null) {
                        n.click();
                        return 'CLICK:下一步';
                    }
                }
                return 'SKIP';
            })()
            """
            next_r = js_eval(ws, next_js)
            print("Next step:", next_r)
            if "CLICK" in str(next_r):
                time.sleep(3)
                js_eval(ws, "(function(){window.scrollTo(0,document.body.scrollHeight);return 'SCROLLED';})()")
                time.sleep(1)

            r3 = js_eval(ws, PUBLISH_JS)
            print("Publish click:", r3)

            success = False
            for attempt in range(5):
                time.sleep(2)
                confirm_r = js_eval(ws, CONFIRM_DIALOG_JS)
                print(f"  Confirm dialog (attempt {attempt+1}):", confirm_r)
                if "CONFIRM" in str(confirm_r):
                    time.sleep(3)

                check_r = js_eval(ws, CHECK_SUCCESS_JS)
                print(f"  Status:", check_r)
                if "SUCCESS" in str(check_r):
                    success = True
                    break

                if "STILL_ON_PAGE" in str(check_r) and attempt < 4:
                    js_eval(ws, PUBLISH_JS)
                    time.sleep(1)
                    js_eval(ws, CONFIRM_DIALOG_JS)
                    print(f"  Retry publish+confirm (attempt {attempt+2})")

            if success:
                print("Xiaohongshu publish SUCCESS.")
            else:
                print("WARN: Publish may not have completed. Check creator center.", file=sys.stderr)
        print("Xiaohongshu flow completed.")
    finally:
        ws.close()


if __name__ == "__main__":
    main()
