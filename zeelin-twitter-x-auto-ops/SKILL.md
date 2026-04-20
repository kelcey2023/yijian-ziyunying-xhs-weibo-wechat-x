---
name: ZeeLin Twitter/X Auto Ops
description: "ZeeLin Twitter/X 自动运营技能 — 通过 openclaw browser / Browser Relay 操作网页版 Twitter/X，无需 API Key。用户先在自己的浏览器登录并挂上 Relay，Agent 负责围绕主题自动写内容并发布、回关粉丝、蓝V互关（认证关注者回关）、深度评论、以及在求关注/互关类帖子下主动互动，适合把账号日常运营持续跑起来。支持定时任务与随机延迟，减少固定整点触发痕迹。Keywords: Zeelin, ZeeLin, auto ops, auto tweet, follow back, 回关, 互关, 蓝V互关, 认证关注者, 涨粉, 打招呼, comment, scheduled post, random delay, no API key."
user-invocable: true
metadata: {"openclaw":{"emoji":"🐦","skillKey":"zeelin-twitter-x-auto-ops"}}
---

# ZeeLin Twitter/X 自动运营 🐦

通过 `openclaw browser` / Browser Relay 操作网页版 Twitter/X：支持**内容生成并发布**、**回关**（粉丝列表一键回关）、**蓝V互关**（认证关注者回关）、**深度评论**、以及**在求关注/互关类帖子下主动打招呼**。用户先在自己的浏览器登录并挂上 Relay，Agent 用脚本持续执行账号运营动作，无需 API Key。

这个 skill 的重点不是“只发一条”，而是让账号运营流程自己跑起来。

**飞书下**：发推/评论时优先直接发一个 `exec`；回关/蓝V互关默认带较长超时，减少 request timed out。

## 概述

- **发推**：Agent 撰写推文 → 使用已登录且挂上 Relay 的 X 标签页 → Agent 输入并发布
- **回关**：在关注者列表中自动点击回关
- **蓝V互关**：在认证关注者列表中自动回关
- **深度评论**：对指定帖子写评论并发布
- **涨粉互动**：主动寻找 `follow for follow / f4f / 互关 / 求关注` 类帖子，在下面自然打招呼，增加曝光与涨粉

---

## 何时触发

**发推**
- 「帮我发一条推特/推文」
- 「自动在 X 上发帖」
- 「围绕某个热点写一条推特并发布」
- 「每天 XX 点自动发推」「设置定时推特」

**回关 / 蓝V互关**
- 「回关」「帮我回关」「回关推特」
- 「有人关注我了」「关注者列表回关」
- 「蓝V互关」「认证关注者回关」「蓝V回关」

**互动 / 涨粉**
- 「帮我评论这条推文」
- 「在涨粉推文下打招呼」
- 「帮我找求关注的帖子互动」
- 「今天做下推特运营」

---

## 回关与蓝V互关（必须用 exec，不要用 browser 逐步点）

用户说「回关 / 蓝V互关 / 认证关注者回关」时，**第一反应**：用 `exec` 执行脚本，不要自己用 `browser` 打开页面、snapshot、click。

### 普通回关

```json
{"tool": "exec", "args": {"command": "bash ./zeelin-twitter-x-auto-ops/scripts/follow_back.sh Gsdata5566 https://x.com 5", "timeout": 90000}}
```

### 蓝V互关 / 认证关注者回关

优先调用已合并进本 skill 的运营脚本：

```json
{"tool": "exec", "args": {"command": "bash ./zeelin-twitter-x-auto-ops/scripts/follow_back.sh Gsdata5566 https://x.com 5", "timeout": 90000}}
```

- 当前仓库未附带单独的 `follow_back_verified.sh`，如需蓝V专用流程，需先补脚本再调用
- 飞书下默认建议 **5 人**，更稳
- 执行完后根据输出回报：「已回关 X 人」/「已蓝V互关 X 人」

---

## 总体流程（发推）

### Step 1：确认用户的 X 网址

首次使用时，询问用户：

> 「请提供你访问 X/Twitter 的网址（例如 https://x.com 或 https://twitter.com）」

记住用户提供的 **BASE_URL**，后续所有操作基于它。**不要自行假设网址。**

### Step 2：先准备已登录的 Relay 标签页

1. 让用户在自己的 Chrome 中打开用户提供的 X 网址并登录
2. 让用户在该标签页挂上 OpenClaw Browser Relay，确认 Badge 为 **ON**
3. 后续一律通过 `openclaw browser` / Relay 操作该标签页
4. **不要默认改用 `agent-browser`**，因为它是独立浏览器，不共享用户现有登录 session
5. 只有在用户明确要走独立浏览器，且已经保存过登录态时，才考虑 `agent-browser state load`

### Step 3：撰写推文内容

- 用户给了完整文案 → 直接使用
- 用户给了主题/方向 → 用模型生成（≤240 字符）
- 用户要求全自动 → 自行选热点并撰写

### Step 4：发布推文

优先使用现成脚本：

```bash
bash ./zeelin-twitter-x-auto-ops/scripts/tweet.sh "推文内容" https://x.com
```

如需附带即梦生成的图片：

```bash
bash ./zeelin-twitter-x-auto-ops/scripts/tweet.sh "推文内容" https://x.com /absolute/path/to/jimeng-image.png
```

或在需要时用浏览器流程补救。

### Step 5：回报结果

告诉用户：
- 发布成功/失败
- 推文全文
- 推文 URL（如果能拿到）

---

## 深度评论（用户给帖子链接）

1. 用户给出一条 X 帖子链接
2. 先写一条自然、有信息量、有趣的评论
3. 确认后执行：

```json
{"tool": "exec", "args": {"command": "bash ./zeelin-twitter-x-auto-ops/scripts/comment.sh \"评论内容\" \"帖子URL\" https://x.com", "timeout": 60000}}
```

---

## 涨粉帖打招呼（主动互动）

目标：在 `follow for follow / f4f / 互关 / 求关注 / follow back` 类帖子下友好评论，提升曝光和回关率。

### 推荐流程

1. 用 X 搜索页搜索相关关键词
2. 找 3～5 条帖子即可，不要一次太多
3. 每条写略有变化的友好评论，例如：
   - 「刚看到，已 fo，欢迎回关～」
   - 「有同感，先关注啦，常互动」
   - 「已支持，互相关注一起涨」
4. 逐条执行评论脚本：

```json
{"tool": "exec", "args": {"command": "bash ./zeelin-twitter-x-auto-ops/scripts/comment.sh \"评论内容\" \"https://x.com/xxx/status/123\" https://x.com", "timeout": 60000}}
```

5. 最后汇总告诉用户已互动多少条

**注意：** 单次建议 3～5 条，避免太像机器刷评。

---

## 定时发布

当用户要求定时发推时，使用 `openclaw cron`。

### 随机间隔建议

为了避免每次都在整点或固定分钟触发，定时任务建议配合随机延迟环境变量：

```bash
AUTO_OPS_DELAY_ENABLED=1
AUTO_OPS_DELAY_MIN_SECONDS=600
AUTO_OPS_DELAY_MAX_SECONDS=2400
```

含义：
- 最少延迟 10 分钟
- 最多延迟 40 分钟
- 同一个整点任务每次实际发出时间不同，更像人工运营节奏

### 询问参数

- 频率：每天 / 每周 / 一次性
- 时间：几点
- 时区：默认 Asia/Shanghai
- 内容策略：固定文案 / 每次自动写新的
- 语言：中文 / 英文

### 创建示例

```bash
openclaw cron add \
  --name "daily-tweet" \
  --description "每天自动撰写并发布推文" \
  --cron "0 10 * * *" \
  --tz "Asia/Shanghai" \
  --message "请执行 zeelin-twitter-x-auto-ops skill：用用户的X网址打开推特，围绕主题自动运营账号，生成并发布一条英文AI热点推文，不要与之前重复"
```

---

## exec 命令速查

| 操作 | 命令 |
|------|------|
| 发推 | `bash ./zeelin-twitter-x-auto-ops/scripts/tweet.sh "推文内容" https://x.com` |
| 发推带图 | `bash ./zeelin-twitter-x-auto-ops/scripts/tweet.sh "推文内容" https://x.com /absolute/path/to/jimeng-image.png` |
| 回关 | `bash ./zeelin-twitter-x-auto-ops/scripts/follow_back.sh Gsdata5566 https://x.com 5` |
| 蓝V互关 | 当前仓库未附带专用脚本，需补齐后再自动化 |
| 评论 | `bash ./zeelin-twitter-x-auto-ops/scripts/comment.sh "评论内容" "帖子URL" https://x.com` |

以上均通过 `exec` 执行；回关/蓝V互关建议 `timeout: 90000`，评论建议 `timeout: 60000`。

---

## 安全与风控

- 不要自动输入密码，登录由用户自己完成
- 这个 skill 默认依赖 `openclaw browser` / Browser Relay，不要切到 `agent-browser` 去要求用户重新登录
- 不发违法、仇恨、违规内容
- 发帖频率建议每天不超过 3–5 条
- 主动互动单次建议 3–5 条，避免刷屏
- 失败最多重试 1–2 次

---

## TL;DR

- 用户说「发推」→ 发推脚本
- 用户说「回关」→ `follow_back.sh`
- 用户说「蓝V互关」→ 当前仓库需先补专用脚本
- 用户说「评论这条」→ `comment.sh`
- 用户说「找涨粉帖互动」→ 搜 3～5 条 + 逐条 `comment.sh`
- 用户说「围绕一个主题持续跑账号」→ 可由仓库级 `scripts/run_autoops_engine.sh` 统一编排
