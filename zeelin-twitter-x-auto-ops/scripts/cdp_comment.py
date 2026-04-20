#!/usr/bin/env python3
"""
Post a reply to a specific X/Twitter post via Chrome DevTools Protocol (CDP).

Usage:
  python3 cdp_comment.py "reply text" "status url" [--port 9222] [--base-url https://x.com]
"""

import argparse
import json
import time
import urllib.request

import websocket


def cdp_send(ws, method, params=None, timeout=15):
    msg_id = int(time.time() * 1000) % 1_000_000
    payload = {"id": msg_id, "method": method, "params": params or {}}
    ws.send(json.dumps(payload))
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
                raise RuntimeError(f"CDP error: {data['error']}")
            return data.get("result", {})
    raise TimeoutError(f"CDP call {method} timed out after {timeout}s")


def list_tabs(port):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=5) as resp:
        return json.loads(resp.read())


def activate_tab(port, target_id):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/activate/{target_id}", timeout=5):
            pass
    except Exception:
        pass


def find_tab(tabs, url_fragment):
    exact = [t for t in tabs if url_fragment in t.get("url", "") and t.get("type") == "page"]
    return exact[0] if exact else None


def js_eval(ws, expression, timeout=10):
    result = cdp_send(
        ws,
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True, "awaitPromise": True},
        timeout=timeout,
    )
    value = result.get("result", {})
    return value.get("value", value.get("description", ""))


JS_CHECK_LOGIN = r"""
(() => {
    const body = document.body.innerText || '';
    if (/Sign in|登录 X|Create account|创建账号/.test(body)) return "LOGIN_REQUIRED";
    return "LOGGED_IN";
})()
"""

JS_CLICK_REPLY_ENTRY = r"""
(() => {
    const selectors = [
        '[data-testid="reply"]',
        '[aria-label="Reply"]',
        '[aria-label="回复"]',
    ];
    for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el) {
            el.click();
            return "OK";
        }
    }
    const allBtns = document.querySelectorAll('button, [role="button"]');
    for (const btn of allBtns) {
        const text = (btn.textContent || '').trim();
        if (/^Reply$|^回复$/.test(text)) {
            btn.click();
            return "OK";
        }
    }
    return "ERROR:REPLY_ENTRY_NOT_FOUND";
})()
"""

JS_FOCUS_TEXTBOX = r"""
(() => {
    const selectors = [
        '[data-testid="tweetTextarea_0"]',
        '[role="textbox"][aria-label]',
        '[contenteditable="true"][role="textbox"]',
    ];
    for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el && el.offsetParent !== null) {
            el.focus();
            el.click();
            return "OK";
        }
    }
    return "ERROR:TEXTBOX_NOT_FOUND";
})()
"""

JS_CLICK_SUBMIT = r"""
(async () => {
    const selectors = [
        '[data-testid="tweetButton"]',
        '[data-testid="tweetButtonInline"]',
    ];
    for (const sel of selectors) {
        const btn = document.querySelector(sel);
        if (btn && !btn.disabled && btn.getAttribute('aria-disabled') !== 'true') {
            btn.click();
            await new Promise(r => setTimeout(r, 2000));
            const body = document.body.innerText || '';
            if (/Your reply was sent|Your post was sent|回复已发送|帖子已发送|Reply sent|Post sent/i.test(body)) {
                return "SUCCESS";
            }
            return "CLICKED";
        }
    }
    const allBtns = document.querySelectorAll('button, [role="button"]');
    for (const btn of allBtns) {
        const text = (btn.textContent || '').trim();
        if (/^(Reply|回复|Post|发帖|发布)$/.test(text) && !btn.disabled) {
            btn.click();
            await new Promise(r => setTimeout(r, 2000));
            return "CLICKED";
        }
    }
    return "ERROR:SUBMIT_NOT_FOUND";
})()
"""


def post_reply(comment_text, status_url, port=9222, base_url="https://x.com"):
    print(f"CDP port: {port}")
    tabs = [tab for tab in list_tabs(port) if tab.get("type") == "page"]
    print(f"Found {len(tabs)} page tabs")

    target = find_tab(tabs, "x.com") or find_tab(tabs, "twitter.com")
    if not target:
      if not tabs:
          print("ERROR: No page tabs available")
          return False
      target = tabs[0]

    activate_tab(port, target["id"])
    ws = websocket.create_connection(
        target["webSocketDebuggerUrl"], timeout=10, origin=f"http://127.0.0.1:{port}"
    )
    print(f"Activated tab: {target.get('url', '')[:60]}")

    try:
        cdp_send(ws, "Page.enable")
        cdp_send(ws, "Page.navigate", {"url": status_url})
        time.sleep(3)

        for _ in range(10):
            ready = js_eval(ws, "document.readyState")
            if ready == "complete":
                break
            time.sleep(1)

        time.sleep(2)

        login_status = js_eval(ws, JS_CHECK_LOGIN)
        if login_status == "LOGIN_REQUIRED":
            print("ERROR: X login required. Please login first.")
            return False

        entry_result = js_eval(ws, JS_CLICK_REPLY_ENTRY)
        print(f"Open reply composer: {entry_result}")
        if "ERROR" in str(entry_result):
            return False

        time.sleep(2)

        focus_result = js_eval(ws, JS_FOCUS_TEXTBOX)
        print(f"Focus textbox: {focus_result}")
        if "ERROR" in str(focus_result):
            return False

        cdp_send(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "a", "code": "KeyA", "modifiers": 2})
        cdp_send(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "a", "code": "KeyA", "modifiers": 2})
        cdp_send(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Backspace", "code": "Backspace"})
        cdp_send(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "Backspace", "code": "Backspace"})
        time.sleep(0.3)

        cdp_send(ws, "Input.insertText", {"text": comment_text})
        time.sleep(1)
        print(f"Text inserted ({len(comment_text)} chars)")

        for attempt in range(5):
            submit_result = js_eval(ws, JS_CLICK_SUBMIT)
            print(f"Reply attempt {attempt + 1}: {submit_result}")
            if "SUCCESS" in str(submit_result):
                print("Reply published successfully.")
                return True
            if "ERROR:SUBMIT_NOT_FOUND" in str(submit_result):
                time.sleep(2)
                continue
            if "CLICKED" in str(submit_result):
                time.sleep(3)
                verify = js_eval(
                    ws,
                    """
                    (() => {
                        const body = document.body.innerText || '';
                        if (/Your reply was sent|Your post was sent|回复已发送|帖子已发送|Reply sent|Post sent/i.test(body)) {
                            return "SUCCESS";
                        }
                        return "LIKELY_SUCCESS";
                    })()
                    """,
                )
                print(f"Verify: {verify}")
                if "SUCCESS" in str(verify) or "LIKELY_SUCCESS" in str(verify):
                    print("Reply published successfully.")
                    return True

        print("Reply attempted but success signal not detected. Check the thread.")
        return True
    finally:
        ws.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post a reply via CDP")
    parser.add_argument("comment", help="Reply text to post")
    parser.add_argument("status_url", help="Target X/Twitter status URL")
    parser.add_argument("--port", type=int, default=int(__import__("os").environ.get("OPENCLAW_CDP_PORT", "9222")))
    parser.add_argument("--base-url", default="https://x.com")
    args = parser.parse_args()
    raise SystemExit(0 if post_reply(args.comment, args.status_url, port=args.port, base_url=args.base_url) else 1)
