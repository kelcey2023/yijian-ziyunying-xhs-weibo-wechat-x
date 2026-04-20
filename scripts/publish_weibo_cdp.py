#!/usr/bin/env python3
"""
Publish a Weibo post through Chrome DevTools Protocol.

This script is intentionally tolerant of UI variation:
- It searches for visible textarea/contenteditable editors.
- It supports optional media upload via any visible file input.
- It can run in dry-run mode when WEIBO_NO_PUBLISH=1.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request

import websocket


def cdp_send(ws, method, params=None, timeout=20):
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


def list_tabs(port):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=5) as resp:
        return json.loads(resp.read())


def activate(port, target_id):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/json/activate/{target_id}", timeout=5)
    except Exception:
        pass


def open_new_tab(port, url):
    candidates = [
        f"http://127.0.0.1:{port}/json/new?{url}",
        f"http://127.0.0.1:{port}/json/new?{urllib.parse.quote(url, safe='')}",
    ]
    for endpoint in candidates:
        try:
            with urllib.request.urlopen(endpoint, timeout=8) as resp:
                return json.loads(resp.read())
        except Exception:
            continue
    return None


def find_weibo_tab(port):
    tabs = [t for t in list_tabs(port) if t.get("type") == "page"]
    for tab in tabs:
        url = tab.get("url", "")
        if "weibo.com" in url and "passport.weibo.com" not in url:
            return tab
    for tab in tabs:
        url = tab.get("url", "")
        if "weibo.com" in url or "passport.weibo.com" in url:
            return tab
    return None


def js_eval(ws, expression, timeout=15):
    result = cdp_send(
        ws,
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True, "awaitPromise": True},
        timeout=timeout,
    )
    payload = result.get("result", {})
    return payload.get("value", payload.get("description", ""))


def navigate(ws, url):
    cdp_send(ws, "Page.navigate", {"url": url})
    time.sleep(4)


JS_CHECK_LOGIN = r"""
(() => {
    const text = document.body.innerText || '';
    if (/登录|手机号登录|扫码登录|立即登录/.test(text) && !/发布|首页|发现/.test(text)) {
        return 'LOGIN_REQUIRED';
    }
    return 'LOGGED_IN';
})()
"""


JS_FOCUS_EDITOR = r"""
(() => {
    const selectors = [
        'textarea',
        '[contenteditable="true"]',
        'div[role="textbox"]',
    ];
    for (const selector of selectors) {
        for (const el of document.querySelectorAll(selector)) {
            if (!el.offsetParent) continue;
            const rect = el.getBoundingClientRect();
            if (rect.width < 80 || rect.height < 20) continue;
            el.focus();
            el.click();
            return 'OK:' + selector;
        }
    }
    return 'ERROR:NO_EDITOR';
})()
"""


JS_POST_BUTTON = r"""
(() => {
    const labels = ['发布', '发送', '发微博'];
    const nodes = document.querySelectorAll('button, [role="button"], a, span, div');
    for (const node of nodes) {
        if (!node.offsetParent) continue;
        const text = (node.textContent || '').replace(/\s+/g, '').trim();
        for (const label of labels) {
            if (text === label || text.endsWith(label)) {
                node.click();
                return 'CLICK:' + text;
            }
        }
    }
    return 'ERROR:NO_POST_BUTTON';
})()
"""


JS_SUCCESS = r"""
(() => {
    const text = document.body.innerText || '';
    if (/发布成功|微博发布成功|发送成功/.test(text)) return 'SUCCESS';
    return 'UNKNOWN';
})()
"""


def upload_media(ws, media_path):
    absolute_path = os.path.abspath(media_path)
    if not os.path.isfile(absolute_path):
        raise FileNotFoundError(f"media file not found: {absolute_path}")

    cdp_send(ws, "DOM.enable", {})
    root = cdp_send(ws, "DOM.getDocument", {"depth": -1, "pierce": True})
    root_id = root.get("root", {}).get("nodeId")
    query = cdp_send(ws, "DOM.querySelectorAll", {"nodeId": root_id, "selector": 'input[type="file"]'})
    node_ids = query.get("nodeIds", [])
    if not node_ids:
        raise RuntimeError("no visible file input found on weibo page")

    cdp_send(ws, "DOM.setFileInputFiles", {"nodeId": node_ids[0], "files": [absolute_path]})
    time.sleep(3)


def post_weibo(text, image_path=None, port=9222):
    tab = find_weibo_tab(port)
    if not tab:
        tab = open_new_tab(port, "https://weibo.com/")
    if not tab:
        print("ERROR: no Weibo tab found", file=sys.stderr)
        return False

    activate(port, tab["id"])
    ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=10, origin=f"http://127.0.0.1:{port}")
    try:
        cdp_send(ws, "Page.enable", {})
        if "weibo.com" not in tab.get("url", "") or "passport.weibo.com" in tab.get("url", ""):
            fresh_tab = open_new_tab(port, "https://weibo.com/")
            if fresh_tab and fresh_tab.get("webSocketDebuggerUrl") and fresh_tab.get("id") != tab.get("id"):
                ws.close()
                activate(port, fresh_tab["id"])
                ws = websocket.create_connection(
                    fresh_tab["webSocketDebuggerUrl"], timeout=10, origin=f"http://127.0.0.1:{port}"
                )
                cdp_send(ws, "Page.enable", {})
            else:
                navigate(ws, "https://weibo.com/")

        login_state = js_eval(ws, JS_CHECK_LOGIN)
        print("Login state:", login_state)
        if login_state == "LOGIN_REQUIRED":
            print("ERROR: Weibo login required", file=sys.stderr)
            return False

        focus_result = js_eval(ws, JS_FOCUS_EDITOR)
        print("Editor focus:", focus_result)
        if "ERROR" in str(focus_result):
            navigate(ws, "https://weibo.com/")
            focus_result = js_eval(ws, JS_FOCUS_EDITOR)
            print("Retry focus:", focus_result)
            if "ERROR" in str(focus_result):
                print("ERROR: no visible Weibo editor found", file=sys.stderr)
                return False

        cdp_send(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "a", "code": "KeyA", "modifiers": 2})
        cdp_send(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "a", "code": "KeyA", "modifiers": 2})
        cdp_send(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Backspace", "code": "Backspace"})
        cdp_send(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "Backspace", "code": "Backspace"})
        cdp_send(ws, "Input.insertText", {"text": text})
        print(f"Text inserted ({len(text)} chars)")

        if image_path:
            upload_media(ws, image_path)
            print(f"Media attached: {image_path}")

        if os.environ.get("WEIBO_NO_PUBLISH", "").strip() in ("1", "true", "yes"):
            print("WEIBO: content filled. Skipping publish (WEIBO_NO_PUBLISH=1).")
            return True

        click_result = js_eval(ws, JS_POST_BUTTON)
        print("Publish click:", click_result)
        if "ERROR" in str(click_result):
            return False

        time.sleep(3)
        print("Status:", js_eval(ws, JS_SUCCESS))
        return True
    finally:
        ws.close()


def main():
    parser = argparse.ArgumentParser(description="Publish Weibo via CDP")
    parser.add_argument("text", help="Weibo text")
    parser.add_argument("--image", default="", help="Optional media path")
    parser.add_argument("--port", type=int, default=int(os.environ.get("OPENCLAW_CDP_PORT", "9222")))
    args = parser.parse_args()
    ok = post_weibo(args.text, image_path=args.image.strip() or None, port=args.port)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
