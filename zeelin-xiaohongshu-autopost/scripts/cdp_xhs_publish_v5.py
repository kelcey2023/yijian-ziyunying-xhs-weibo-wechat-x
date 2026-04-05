#!/usr/bin/env python3
import sys,json,time,requests,websocket

TITLE=sys.argv[1][:64] if len(sys.argv)>1 else "AI自动发布测试"
BODY=sys.argv[2] if len(sys.argv)>2 else "这是ZeeLin小红书自动发布流程测试。"

CDP="http://127.0.0.1:9222/json"

def find_tab():
    for t in requests.get(CDP).json():
        if "xiaohongshu" in t.get("url",""):
            return t
    return None

def send(ws,method,params=None):
    ws.send(json.dumps({"id":1,"method":method,"params":params or {}}))
    return json.loads(ws.recv())

def click_text(ws,text):
    js=f"""
    (function(){{
      const nodes=[...document.querySelectorAll('button,div,span')];
      for(const n of nodes){{
        if(n.innerText && n.innerText.includes('{text}')){{
          n.click();
          return true;
        }}
      }}
      return false;
    }})();
    """
    send(ws,"Runtime.evaluate",{"expression":js})

# connect

tab=find_tab()
if not tab:
    raise SystemExit("No Xiaohongshu tab found")

ws=websocket.create_connection(tab["webSocketDebuggerUrl"])

send(ws,"Page.bringToFront")

# workflow
click_text(ws,"创作中心")
time.sleep(2)

click_text(ws,"发布笔记")
time.sleep(2)

click_text(ws,"写长文")
time.sleep(2)

click_text(ws,"新的创作")
time.sleep(3)

# title
send(ws,"Runtime.evaluate",{"expression":"document.querySelector('input')?.focus()"})
send(ws,"Input.insertText",{"text":TITLE})

time.sleep(1)

# body
send(ws,"Runtime.evaluate",{"expression":"document.querySelector('[contenteditable],textarea,div[class*=editor]')?.focus()"})
send(ws,"Input.insertText",{"text":"\n"+BODY})

time.sleep(1)

click_text(ws,"一键排版")
time.sleep(1)

click_text(ws,"简约")
time.sleep(1)

click_text(ws,"下一步")
time.sleep(2)

# Step 1: click 发布
click_text(ws,"发布")
click_text(ws,"发布笔记")
time.sleep(2)

# Step 2: handle confirmation dialog (确认发布 / 确认 / 继续发布)
for label in ["确认发布", "确认", "继续发布", "确定发布", "确定"]:
    click_text(ws, label)
time.sleep(3)

# ---- publish success detection ----

def check_publish_success(ws):
    js="""
    (function(){
        var text = document.body.innerText || '';
        return text.includes('发布成功') ||
               text.includes('笔记已发布') ||
               text.includes('审核中') ||
               text.includes('内容已提交');
    })();
    """
    r = send(ws,"Runtime.evaluate",{"expression":js,"returnByValue":True})
    return r.get("result",{}).get("value",False)

success=False
for i in range(5):
    if check_publish_success(ws):
        success=True
        print("XHS publish success")
        break
    # retry: click publish + confirm again
    click_text(ws,"发布")
    time.sleep(2)
    for label in ["确认发布", "确认", "继续发布", "确定"]:
        click_text(ws, label)
    time.sleep(3)

if not success:
    print("XHS publish: confirm dialog may need manual check")