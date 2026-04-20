#!/usr/bin/env python3
"""
Create/fill a WeChat Official Account article draft via CDP.

This script intentionally stops at the draft stage by default. It can:
- open the "new article" editor from the existing home tab
- fill title / summary / body
- upload a cover image
- optionally save as draft
"""

from __future__ import annotations

import argparse
import json
import os
import time
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


def connect(tab, port):
    activate(port, tab["id"])
    return websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=10, origin=f"http://127.0.0.1:{port}")


def js_eval(ws, expression, timeout=15):
    result = cdp_send(
        ws,
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True, "awaitPromise": True},
        timeout=timeout,
    )
    payload = result.get("result", {})
    return payload.get("value", payload.get("description", ""))


def find_tab(port, url_part):
    for tab in list_tabs(port):
        if tab.get("type") == "page" and url_part in tab.get("url", ""):
            return tab
    return None


def open_new_editor(port):
    home_tab = find_tab(port, "home?t=home/index")
    if not home_tab:
        raise RuntimeError("no WeChat home tab found")
    ws = connect(home_tab, port)
    try:
        cdp_send(ws, "Page.enable", {})
        cdp_send(ws, "DOM.enable", {})
        root = cdp_send(ws, "DOM.getDocument", {"depth": -1, "pierce": True})["root"]["nodeId"]
        node = cdp_send(ws, "DOM.querySelector", {"nodeId": root, "selector": ".new-creation__menu-item"}).get("nodeId")
        if not node:
            raise RuntimeError("article entry not found on WeChat home")
        box = cdp_send(ws, "DOM.getBoxModel", {"nodeId": node})["model"]["content"]
        xs = box[0::2]
        ys = box[1::2]
        x = sum(xs) / len(xs)
        y = sum(ys) / len(ys)
        for typ in ("mouseMoved", "mousePressed", "mouseReleased"):
            params = {"type": typ, "x": x, "y": y, "button": "left", "clickCount": 1}
            if typ == "mousePressed":
                params["buttons"] = 1
            cdp_send(ws, "Input.dispatchMouseEvent", params)
            time.sleep(0.1)
    finally:
        ws.close()

    time.sleep(3)
    tab = find_tab(port, "appmsg_edit_v2")
    if not tab:
        raise RuntimeError("WeChat editor tab did not open")
    return tab


def ensure_editor_tab(port):
    tab = find_tab(port, "appmsg_edit_v2")
    if tab:
        return tab
    return open_new_editor(port)


def insert_text(ws, text):
    cdp_send(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "a", "code": "KeyA", "modifiers": 2})
    cdp_send(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "a", "code": "KeyA", "modifiers": 2})
    cdp_send(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Backspace", "code": "Backspace"})
    cdp_send(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "Backspace", "code": "Backspace"})
    cdp_send(ws, "Input.insertText", {"text": text})


def focus_selector(ws, selector):
    return js_eval(
        ws,
        f"""
        (() => {{
            const el = document.querySelector({json.dumps(selector)});
            if (!el || !el.offsetParent) return "ERROR";
            el.focus();
            el.click();
            return "OK";
        }})()
        """,
    )


def visible_texts(ws, patterns):
    joined = "|".join(patterns)
    return js_eval(
        ws,
        f"""
        (() => {{
            const out = [];
            for (const el of document.querySelectorAll('body *')) {{
                const text = (el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim();
                if (!text || !/{joined}/.test(text)) continue;
                const rect = el.getBoundingClientRect();
                const style = getComputedStyle(el);
                if (rect.width < 5 || rect.height < 5 || style.display === 'none' || style.visibility === 'hidden') continue;
                out.push(text.slice(0, 160));
            }}
            return out.slice(0, 20);
        }})()
        """,
    )


def click_first_visible_text(ws, labels):
    return js_eval(
        ws,
        f"""
        (() => {{
            const labels = {json.dumps(labels)};
            for (const label of labels) {{
                for (const el of document.querySelectorAll('button,a,div,span')) {{
                    const text = (el.innerText || el.textContent || '').replace(/\\s+/g, '').trim();
                    const rect = el.getBoundingClientRect();
                    const style = getComputedStyle(el);
                    if (rect.width < 5 || rect.height < 5 || style.display === 'none' || style.visibility === 'hidden') continue;
                    if (text === label || text.endsWith(label)) {{
                        el.click();
                        return 'CLICK:' + label;
                    }}
                }}
            }}
            return 'NO_MATCH';
        }})()
        """,
    )


def dismiss_common_dialogs(ws, passes=3):
    clicks = []
    labels = ["我知道了", "取消", "关闭", "确定"]
    for _ in range(passes):
        result = click_first_visible_text(ws, labels)
        if not str(result).startswith("CLICK:"):
            break
        clicks.append(result)
        time.sleep(0.5)
    return clicks


def fill_editor(ws, title, summary, body):
    if "OK" not in str(focus_selector(ws, "textarea.js_title")):
        raise RuntimeError("WeChat title input not found")
    insert_text(ws, title[:64])
    time.sleep(0.2)

    if summary:
        if "OK" in str(focus_selector(ws, "textarea.js_desc")):
            insert_text(ws, summary[:120])
            time.sleep(0.2)

    body_focus = js_eval(
        ws,
        """
        (() => {
            const el = document.querySelector('.ProseMirror[contenteditable="true"]');
            if (!el || !el.offsetParent) return "ERROR";
            el.focus();
            el.click();
            return "OK";
        })()
        """,
    )
    if "OK" not in str(body_focus):
        raise RuntimeError("WeChat body editor not found")
    cdp_send(ws, "Input.insertText", {"text": body})


def upload_body_image(ws, image_path):
    absolute_path = os.path.abspath(image_path)
    if not os.path.isfile(absolute_path):
        raise FileNotFoundError(f"WeChat image not found: {absolute_path}")
    # Prefer the editor toolbar image path so WeChat treats the file as a正文图片.
    js_eval(
        ws,
        """
        (() => {
            for (const el of document.querySelectorAll('a,div,span,button')) {
                const text = (el.innerText || el.textContent || '').replace(/\\s+/g,'').trim();
                const cls = el.className || '';
                const rect = el.getBoundingClientRect();
                const style = getComputedStyle(el);
                if (rect.width < 5 || rect.height < 5 || style.display === 'none' || style.visibility === 'hidden') continue;
                if (text === '图片' || cls.includes('jsInsertIcon img')) {
                    el.click();
                    return 'CLICK:图片';
                }
            }
            return 'NO_IMAGE_BUTTON';
        })()
        """,
    )
    time.sleep(1)
    cdp_send(ws, "DOM.enable", {})
    root = cdp_send(ws, "DOM.getDocument", {"depth": -1, "pierce": True})["root"]["nodeId"]
    nodes = cdp_send(ws, "DOM.querySelectorAll", {"nodeId": root, "selector": 'input[type="file"]'}).get("nodeIds", [])
    if not nodes:
        raise RuntimeError("WeChat image upload input not found")
    for node_id in nodes:
        try:
            cdp_send(ws, "DOM.setFileInputFiles", {"nodeId": node_id, "files": [absolute_path]})
        except RuntimeError:
            continue
    time.sleep(2)
    return visible_texts(ws, ["上传中", "系统繁忙", "图片不能为空", "关闭"])


def save_draft(ws):
    dismiss_common_dialogs(ws, passes=6)
    result = click_first_visible_text(ws, ["保存为草稿", "保存草稿"])
    time.sleep(2)
    status = visible_texts(ws, ["已保存", "保存成功", "登录态已过期", "系统无法保存", "手动保存"])
    return {"action": result, "status": status}


def publish_article(ws):
    click_result = js_eval(
        ws,
        """
        (() => {
            for (const el of document.querySelectorAll('button,a,div,span')) {
                const text = (el.textContent || '').replace(/\\s+/g,'').trim();
                if ((text === '发表' || text === '发布') && el.offsetParent) {
                    el.click();
                    return 'CLICK:' + text;
                }
            }
            return 'ERROR:NO_PUBLISH_BUTTON';
        })()
        """,
    )
    time.sleep(2)
    confirm_result = js_eval(
        ws,
        """
        (() => {
            const labels = ['确定', '发表', '发布', '继续', '确认'];
            for (const el of document.querySelectorAll('button,a,div,span')) {
                const text = (el.textContent || '').replace(/\\s+/g,'').trim();
                for (const label of labels) {
                    if ((text === label || text.endsWith(label)) && el.offsetParent) {
                        el.click();
                        return 'CONFIRM:' + text;
                    }
                }
            }
            return 'NO_CONFIRM';
        })()
        """,
    )
    return click_result, confirm_result


def fill_wechat(title, summary, body, image_path=None, port=9222):
    tab = ensure_editor_tab(port)
    ws = connect(tab, port)
    try:
        cdp_send(ws, "Page.enable", {})
        dismiss_common_dialogs(ws, passes=6)
        fill_editor(ws, title, summary, body)
        if image_path:
            upload_status = upload_body_image(ws, image_path)
            print(f"Body image attached: {image_path}")
            if upload_status:
                print("WeChat upload hints:", upload_status)

        if os.environ.get("WECHAT_NO_SAVE", "").strip() in ("1", "true", "yes"):
            print("WECHAT: content filled. Skipping draft save (WECHAT_NO_SAVE=1).")
            return True

        if os.environ.get("WECHAT_PUBLISH", "").strip() in ("1", "true", "yes"):
            publish_result, confirm_result = publish_article(ws)
            print("Publish action:", publish_result)
            print("Publish confirm:", confirm_result)
            return "CLICK:" in str(publish_result)

        draft_result = save_draft(ws)
        print("Draft result:", draft_result)
        status_text = " ".join(draft_result.get("status", []))
        if "登录态已过期" in status_text or "系统无法保存" in status_text:
            print("WECHAT: login expired before draft could be reliably saved.")
            return False
        return "CLICK:" in str(draft_result.get("action", ""))
    finally:
        ws.close()


def main():
    parser = argparse.ArgumentParser(description="Fill WeChat article draft via CDP")
    parser.add_argument("--title", required=True)
    parser.add_argument("--summary", default="")
    parser.add_argument("--body", required=True)
    parser.add_argument("--image", default="")
    parser.add_argument("--port", type=int, default=int(os.environ.get("OPENCLAW_CDP_PORT", "9222")))
    args = parser.parse_args()
    ok = fill_wechat(
        title=args.title,
        summary=args.summary,
        body=args.body,
        image_path=args.image.strip() or None,
        port=args.port,
    )
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
