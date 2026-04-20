# THUQX-AutoOps-for-OpenClaw

THUQX Auto Ops for OpenClaw 1.0 是一组基于 OpenClaw 的 AI 账号自动运营 skills。

它的定位不是单点“自动发内容”，而是围绕一句话主题或一个运营目标，帮助用户把多平台账号的内容生产、运营执行、互动分发和持续运营流程先自动跑起来。

一句话理解：

> 给它一个主题或任务，它就按既定流程帮你持续运营多个账号，而不只是发一条内容。

当前仓库里的自动运营主链当前重点覆盖以下平台组合：

- `zeelin-twitter-x-auto-ops`：Twitter/X 账号自动运营，覆盖内容生成、发帖、回关、互动、涨粉动作
- `zeelin-xiaohongshu-auto-ops`：小红书账号自动运营，覆盖热点选题、文案生成、网页运营执行
- `微信公号`：已接入差异化内容生成与带图草稿导出
- `微博`：已接入差异化内容生成与带图草稿导出

仓库同时提供统一入口脚本：

- `scripts/run_autoops_engine.sh`：AutoOps 总控脚本，按 topic 编排当前仓库中可运行的运营模块
- `scripts/generate_autoops_content.py`：生成一轮 AutoOps brief，沉淀本次运营主题、平台目标和执行记录
- `scripts/generate_autoops_media.py`：通过即梦 `dreamina` CLI 生成共享图片/视频素材，并输出 manifest 给各平台脚本消费

## 当前能力边界

- 已经跑通的是“自动运营链路”，重点是让账号自己持续工作
- 当前素材抓取与热点信号主要依赖公开 Web 搜索和轻量信号源，内容质量仍在持续迭代
- 现阶段更适合做“先跑通、先持续、先解放人工”的自动运营，而不是承诺一步到位的顶级内容质量
- 仓库目录、slug 与脚本入口已统一切换到 `AutoOps / 自动运营` 命名体系

## 目录结构

```text
.
├── scripts/
├── zeelin-twitter-x-auto-ops/
├── zeelin-xiaohongshu-auto-ops/
├── zeelin-xianyu-auto-ops/
└── zeelin-report-to-x-auto-ops/
```

## 使用说明

1. 安装并配置 OpenClaw。
2. 进入对应 skill 目录查看 `SKILL.md`。
3. 按 skill 文档准备浏览器登录状态、脚本依赖与环境参数。
4. 给出一个主题、目标账号或运营任务，让 skill 自动执行对应运营动作。
5. 如需定时运行，建议配合 `cron` 或 OpenClaw 定时任务，并开启随机延迟，避免固定整点触发。

## AutoOps Engine

如果你希望用“一句话主题 -> 自动运营流程”的方式来跑当前仓库，直接使用：

```bash
bash scripts/run_autoops_engine.sh "你的主题"
```

常用环境变量：

```bash
AUTO_OPS_MAX_CYCLES=3
AUTO_OPS_ENABLE_X=1
AUTO_OPS_ENABLE_XHS=1
AUTO_OPS_ENABLE_WECHAT=1
AUTO_OPS_ENABLE_WEIBO=1
AUTO_OPS_ENABLE_DREAMINA_MEDIA=1
AUTO_OPS_ENABLE_DREAMINA_IMAGE=1
AUTO_OPS_ENABLE_DREAMINA_VIDEO=0
AUTO_OPS_DELAY_ENABLED=1
AUTO_OPS_DELAY_MIN_SECONDS=1800
AUTO_OPS_DELAY_MAX_SECONDS=9000
```

说明：

- 当前总控会先生成四平台差异化内容 manifest，再分发到各平台链路
- 当 `AUTO_OPS_ENABLE_DREAMINA_MEDIA=1` 时，总控会先尝试调用即梦 `dreamina` 生成共享素材
- 当前 X 发布链路已支持附带即梦图片；小红书总控在有素材时会切到 CDP 图文/视频笔记发布器，无素材时仍走原有长文发布流
- 微信公号与微博当前已支持“差异化文案 + 配图路径”的草稿包导出，后续可继续补网页自动发布器
- 即梦视频能力已接到 manifest 流程，默认关闭，避免无意消耗额度；按需设置 `AUTO_OPS_ENABLE_DREAMINA_VIDEO=1`

## 说明

- 仓库默认保留 skill 文档、脚本与必要资源文件。
- 已排除本地运行产物、缓存目录与临时备份文件。
- 推荐对外仓库名称使用：`THUQX-AutoOps-for-OpenClaw`
