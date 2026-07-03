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

## @Gsdata5566 当前合规运营覆盖层

当目标是运营 `@Gsdata5566`、OpenHarness 曝光、每天净涨粉 `+20`、或 2026 年涨到 `10000` 粉丝时，优先使用仓库内的自学习增长闭环，而不是旧的泛用互关/涨粉帖打法：

```bash
/usr/bin/python3 zeelin-twitter-x-auto-ops/scripts/x_daily_growth_runner.py --date "$(date +%F)" --label pre_window_runner --target-daily 20 --on-track-daily 31
```

- 默认只做读写分离的 preflight、decision、goal status、dashboard；只有显式加 `--publish` 且 fresh gates 全部干净时，才允许进入单条高质量公开回复。
- 如果当日净涨粉低于 `+20`，runner 会自动刷新 daily review、retention review、profile readiness、experiment tracker、profile operator card、next-window runbook、decision、dashboard。
- 默认禁用 connect/followback/follower-train 搜索；除非用户明确重新批准，否则不要使用本文件里的泛用互关涨粉流程运营 `@Gsdata5566`。
- OpenHarness 只能在目标讨论直接涉及 agent reliability、evals、persistent state、recovery、scheduled execution、long-running automation 时自然提及；不要索要 star/follow/like/repost。
- 主页 bio、主帖、pin 变更必须先生成并通过 profile experiment operator card，且要有用户明确批准；不要把 bio、pin、多条回复混在同一小时里归因。

## ZeeLin X Growth Master Ops 合并层

本节合入 `zeelin-x-growth-master-ops` 的内容方法论，但必须服从上面的 `@Gsdata5566` 合规覆盖层。它只增强选题、hook、线程结构、回复质量、复盘与视觉内容，不允许降低安全门槛。

### 任务路由

当用户只要单条文案、线程、hook 优化或复盘时，不跑完整发布链路；当用户要求运营、发布或互动时，必须先跑仓库级 gate，再决定是否允许公开动作。

| 任务 | 默认路径 |
|---|---|
| 单条推文 | hook 选择 → 单帖结构 → 自检 |
| 线程 | hook 选择 → 线程骨架 → 自检 |
| 今日计划 | 算法模型 → 今日主题/节奏 → 不自动发布 |
| 回复运营 | reply-quality rubric → gate 通过后至多单条高质量回复 |
| 复盘 | 读取 ledger/state → missed-target/retention/profile review |
| 带图内容 | 先写内容，再生成图像提示；只有 gate 允许时才进入发布 |

### X 算法模型

优先优化真实技术读者的停留、回复、资料页点击和关注转化，而不是低质量互动量。

- 高权重信号：高质量回复、作者二次回复链、资料页点击后关注、转发/引用、长停留、收藏。
- 低权重信号：普通点赞、泛泛评论、无上下文的表情互动。
- 常见惩罚：主帖外链、早期窗口沉默、明显 engagement bait、标签堆砌、快速重复回复、关注/取关 churn、删帖重发同内容。
- 对 `@Gsdata5566` 的硬化规则：不要写 `follow for more`、不要求关注/转发/点赞、不要参加 follower train，不用互关话术换粉。

### Hook 与内容结构

每条公开内容必须先服务一个具体技术读者。优先使用以下 hook 池，并根据 ledger 中的真实表现迭代：

| 结构 | 用法 |
|---|---|
| Contrarian | 反驳一个常见但危险的技术共识 |
| Result-first | 先给结果、数字、实验或观察，再解释 |
| Curiosity gap | 暴露一个读者想补上的技术缺口 |
| Teardown | 拆解论文、工具、架构或失败案例 |
| Hot take + stakes | 明确立场，并说明忽略它的代价 |
| Build-in-public | 展示项目过程、踩坑和下一步 |
| Correction question | 提出一个专家愿意纠正或补充的问题 |

单帖结构：

```text
[Sharp hook]

[1-2 concrete observations or implications]

[Reply driver or practical caveat, not engagement bait]
```

线程结构：

```text
Tweet 1: hook + promise, no outbound link
Tweet 2: why it matters now
Tweet 3: strongest concrete point
Tweets 4-N-2: one idea per tweet, screenshot-worthy
Tweet N-1: caveat or what can go wrong
Tweet N: recap; link only here or in a reply if needed
```

### Reply-Then-Follow Loop 的合规版

下载版 skill 的 reply loop 只保留“高质量早期回复借用受众”的部分，不保留任何刷粉、互关或 follow/unfollow 行为。

- 只选公开、近期、英文、技术相关讨论。
- 每条回复都必须补充原帖没有说清楚的技术点、风险、例子或权衡。
- 每批不重复同一账号，不评论自帖，不碰 spam/crypto/政治宗教/NSFW/求关注帖。
- 每条回复必须独特，禁止模板化复制。
- 对 `@Gsdata5566` 默认不执行主动 follow-back；只有用户明确批准并且 gate 干净时才考虑谨慎回关。

回复质量检查：

- 是否具体到原帖，而不是通用赞美？
- 原作者是否有理由继续回复？
- 是否体现 agent reliability、evals、workflow infrastructure 等账号定位？
- 是否 1-3 句、无链接、无 hashtags、无中文标点？

### 数据回流与自进化

不要凭感觉“加大力度”。每次运营都要留下可复盘证据，后续选题、hook 和节奏只按证据调整。

- 运行前读：`output/x-growth-YYYY-MM-DD.md`、`output/x-growth-machine/latest_queue.json`、goal/dashboard/review artifacts。
- 运行后记：公开 URL、精确文案、目标类型、hook 类型、是否含图、粉丝净变化、阻塞原因、下一步调整。
- 24 小时后补：impressions、replies、profile clicks、follows、bookmarks；没有真实数字就写 `TBD`，绝不编造。
- 至少 5 次真实样本后再提升或淘汰某个 hook/格式。
- 账号自己的数据优先于通用增长建议。

推荐复盘输出：

```markdown
## Week XX retro - @Gsdata5566
- follows delta:
- top post/reply:
- what worked:
- what failed:
- variant changes:
- next 3 bets:
```

### 视觉内容规则

带图内容只作为增强，不绕过 gate。图像应强化技术论点，而不是做装饰。

- 优先类型：概念图、对比卡、agent workflow stack、before/after、bold text card。
- 移动端可读：深色背景、单一强调色、高对比、标签少而清晰。
- 图像要附一行 alt text。
- 如果图片生成/上传链路不确定，停止在 draft，不发布 text-only 替代品。

### 发前四层自检

1. 算法合规：无主帖外链、无 engagement bait、无标签堆砌、结尾有真实讨论价值。
2. Hook 强度：第一行具体、有冲突或缺口、无铺垫。
3. 技术实质：不是重写常识；至少有一个只有实战者会写出的细节。
4. 人味：删除品牌腔和 AI 腔，例如 `delve`、`leverage`、`game-changer`、`revolutionize`、过度对称句。

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

#### 涨粉优先的内容策略

如果用户明确目标是「涨粉 / 提升互动 / 做账号增长」，发帖不要只追求“发出去”，而要优先采用以下结构：

- **价值型短帖**：1 个强钩子 + 3 个要点 + 1 个轻 CTA
- **教程线程**：适合经验、方法论、工具清单、拆解案例
- **观点帖**：针对行业共识给出鲜明立场，适合引发讨论
- **过程帖**：公开自己的项目进展、踩坑、复盘，更容易建立人设

默认优先级：

1. 有明确方法论或经验时，优先发 **教程线程**
2. 有鲜明判断时，优先发 **观点帖**
3. 只有单个洞察时，优先发 **短帖**
4. 用户在做项目或连续输出时，穿插 **过程帖**

#### 发帖文案优化规则

- 第一行必须是钩子，不要平铺直叙
- 尽量具体，少用空泛表达，优先数字、结果、时长、对象
- 单条短帖优先控制在 **70–180 字符**
- 线程首条要明确承诺价值，例如「这里是我如何做到 X 的 5 步」
- 非必要不要把外链放进主帖正文
- CTA 以轻引导为主；运营 `@Gsdata5566` 时优先用真实问题、 caveat 或下一步观察，不使用“关注我”“回 1”“转发点赞”这类 engagement bait，例如：
  - 「The brittle part is usually the recovery path, not the prompt.」
  - 「Which failure mode would you test first in production?」
  - 「The next useful step is measuring how often the agent recovers without human cleanup.」
- 避免使用明显机器味表达：过度对称句式、堆砌口号、空泛赞美

#### 推荐发帖模版

**1. 涨粉短帖**

```text
[钩子]

我发现真正拉开差距的不是 [常见误区]，
而是：

1. [动作一]
2. [动作二]
3. [动作三]

[轻 CTA]
```

**2. 教程线程**

```text
Tweet 1:
[结果/问题/反常识钩子]

这里是我用来做到 [目标] 的 5 步：

Tweet 2-6:
每条只讲一步，包含动作 + 原因 + 常见坑

Final tweet:
总结一句核心原则 + 真实问题或下一步观察
```

**3. 观点帖**

```text
Unpopular opinion:
[鲜明观点]

原因很简单：
- [原因 1]
- [原因 2]
- [原因 3]

[你主张的替代做法]
```

#### 语言与风格默认值

除非用户另有要求，否则：

- 中文账号：写成自然中文，不要机翻感
- 英文账号：用简洁、口语化英文，避免长句
- 语气优先选择：`清晰 > 有观点 > 可读 > 俏皮`
- 把自己写成「正在实战的人」，而不是高高在上的导师

#### 涨粉运营节奏

如果用户说「今天做下推特运营」「帮我涨粉」，默认按下面节奏执行：

1. 发 1 条主帖或 1 组线程
2. 找 3–5 条相关帖子做高质量回复或引用转推
3. 视情况执行回关 / 认证关注者回关
4. 汇总今天发了什么、互动了什么、下一条建议发什么

#### 发前自检清单

发布前快速检查：

- 这条内容第一行是否能让人停下来？
- 是否有一个明确价值点，而不是泛泛表达？
- 是否能让新访客一眼看出你擅长什么？
- 是否包含互动入口（问题、CTA、悬念）？
- 是否和最近 3 条内容主题一致，能强化账号定位？

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

## 高质量互动优化

如果目标是涨粉，评论区互动不要只写「nice」「great post」「互关」。

优先使用以下三类评论：

- **补充型**：在原帖观点基础上补一个有用信息点
- **共鸣型**：结合自己的真实经历表达赞同
- **提问型**：抛出一个能让对方愿意回复的问题

示例：

- 「这点很认同，尤其是 `先做可验证的小实验`。很多人一上来就想做大，其实更容易失速。」
- 「我最近也在用这个思路，最大的变化是回复率明显上来了。你觉得最该先优化的是 hook 还是 CTA？」
- 「同意。比起发更多，先把账号主题做窄，反而更容易被记住。」

规则：

- 评论尽量 1–3 句
- 至少带一个具体点，避免空话
- 尽量和自己的账号定位一致，让旁观者看完就知道你在这个领域有东西
- 单次互动宁少勿滥，优先质量

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

## 数据复盘与持续优化

如果用户连续多天运营同一个账号，Agent 应该在每日总结中顺手记录：

- 今天发帖类型：短帖 / 线程 / 观点 / 过程
- 今天互动动作：评论数、回关数、主动打招呼数
- 初步反馈：哪条更像会带来关注、回复、资料私信

连续运行时，优先沿着表现更好的方向迭代：

- 观点帖互动高 → 增加鲜明立场内容
- 教程线程收藏/转发高 → 增加步骤型干货
- 过程帖回复高 → 增加项目更新和复盘
- 互关帖带来低质量粉丝太多 → 降低占比，把重心转向高质量回复与引用转推

---

## TL;DR

- 用户说「发推」→ 发推脚本
- 用户说「回关」→ `follow_back.sh`
- 用户说「蓝V互关」→ 当前仓库需先补专用脚本
- 用户说「评论这条」→ `comment.sh`
- 用户说「找涨粉帖互动」→ 搜 3～5 条 + 逐条 `comment.sh`
- 用户说「围绕一个主题持续跑账号」→ 可由仓库级 `scripts/run_autoops_engine.sh` 统一编排
