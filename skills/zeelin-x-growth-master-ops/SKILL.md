---
name: zeelin-x-growth-master-ops
description: Unified ZeeLin X/Twitter growth operations skill for @Gsdata5566. Use when Codex needs to run, audit, repair, or improve compliant X growth toward daily +20 net followers and year-end 10000 followers, including public replies, AI-tech posts, OpenHarness-aware community exposure, readiness gates, artifact-health holds, post-action measurement, follower-loss analysis, and self-evolving loop discipline.
---

# ZeeLin X Growth Master Ops

This skill is the authoritative operating contract for compliant X growth work for `@Gsdata5566`. It consolidates:

- Local `ZeeLin X Growth Ops` safety and script workflow.
- Hardened `x-twitter-growth` strategy rules.
- Local `loop-engineering` self-learning discipline.
- Daily +20 net follower target and year-end `10000` follower trajectory.
- OpenHarness discovery rules for `https://github.com/thu-nmrc/OpenHarness`.

Do not weaken this skill with generic growth advice. Safety gates, evidence, and reputation win over volume.

## Account And Workspace

- X account: `@Gsdata5566`
- X base URL: `https://x.com`
- Chrome CDP port: `9222`
- Workspace: `/Users/youke/Desktop/Codex 驾驭工程/THUQX-智能传播技能套件1.0`
- OpenHarness repo: `https://github.com/thu-nmrc/OpenHarness`
- Daily target: `+20` net followers, verified from current evidence.
- Year-end trajectory target: `10000` followers.
- Primary ledger: `output/x-growth-YYYY-MM-DD.md`
- Machine artifacts: `output/x-growth-machine/`

## Non-Negotiable Conduct Rules

- Never use DMs.
- Never buy followers or stars.
- Never ask for follows, stars, likes, reposts, or engagement trades.
- Never use follower trains, giveaways, bot farms, fake accounts, crypto/Web3/NFT/token/airdrop/pump bait, NSFW, or political/religious fights.
- Never scrape private data, request cookies/tokens, evade rate limits, or bypass X/GitHub controls.
- Never publish filler just to hit a quota.
- Never open an X composer or perform any public action when a hard gate is blocked.
- Never claim growth, publication, freshness, or goal completion without direct evidence.

## Public Copy Rules

For public X copy:

- English only.
- No Chinese text or Chinese punctuation.
- Replies should be `1-3` sentences.
- Start with concrete technical value: observation, risk, example, caveat, implementation implication, or practical tradeoff.
- Vary wording and avoid boilerplate.
- Prefer topics: AI agents, coding agents, automation, agent reliability, evals, benchmarks, persistent state, recovery, rollback, scheduled or long-running workflows, developer tools, workflow infrastructure.
- Mention OpenHarness only when directly relevant to agent reliability, persistent state, evals, recovery, scheduled execution, or long-running automation.
- If linking OpenHarness from GitHub, disclose relationship naturally and avoid generic repo promotion.

## Mandatory First Gate

Before any publish-capable path, run from the workspace:

```bash
/usr/bin/python3 scripts/ops_readiness_snapshot.py --date "$(date +%F)" --workspace .
```

Then read:

```bash
output/x-growth-machine/ops-readiness-snapshot-latest.json
```

If `decision.blockers` or the printed `blockers` contains any of these, do not publish, reply, follow, research a target for immediate posting, generate media, or open composer:

- `outside_public_window`
- `cdp_unreachable`
- `active_publish_or_monitor_process`
- `artifact_health_not_ready`

Treat `artifact_health_not_ready` as stronger than a public window and stronger than reachable CDP. Public actions require both:

- `artifacts_ready_for_preflight=true`
- `public_actions_allowed_now=true`

If blocked, write the blocker to `output/x-growth-YYYY-MM-DD.md` and stop or continue read-only diagnostics only.

## Public Window

- Public replies and posts are allowed only during `08:00-22:00 Asia/Shanghai`.
- Publish-mode runs must still have at least `120` seconds before `22:00`.
- Outside the public window, run only health checks, ledger repair, strategy drafts, artifact recovery diagnostics, and safe planning.

## Active Process Guard

Before any publish-capable path, check for active X/four-platform/image2/THU report processes:

- `x_growth_machine.py`
- `cdp_comment.py`
- `comment.sh`
- `tweet.sh`
- `follow_back.sh`
- `x_daily_growth_runner.py`
- `x_growth_heartbeat_orchestrator.py`
- `generate_image2_asset`
- `run_daily_editorial_batch`
- `four_platform_materialization`
- `post_daily_report.py`

If a real publish or monitor process is active, hold and log it. Ignore false positives where a long `git add` command merely contains script filenames in its argument list.

## Artifact Health And Disk Pressure

When artifacts are slow, unreadable, compressed/dataless, or readiness says `artifact_health_not_ready`, run:

```bash
python3 zeelin-twitter-x-auto-ops/scripts/x_artifact_health_check.py --date "$(date +%F)" --append-ledger
```

If the health check says `artifacts_ready_for_preflight=false`, do not publish. If disk pressure is the only blocker, use the generated cleanup helper only as a human-approved recovery path:

```bash
bash output/x-growth-machine/disk-cleanup-approval-YYYY-MM-DD.sh
```

The apply command requires explicit approval:

```bash
bash output/x-growth-machine/disk-cleanup-approval-YYYY-MM-DD.sh --apply --i-understand-rebuildable-temp-cleanup
```

Do not delete user documents, Desktop/Downloads, project files, chat data, office data, cloud-sync containers, Codex sessions, memories, plugins, config files, or databases. The helper may remove matched rebuildable Chrome `code_sign_clone` temp targets only after approval.

After cleanup or external disk recovery, rerun artifact health and readiness before any public action.

## Preflight Before Publishing

When readiness and artifact health pass, check:

1. Chrome CDP: `http://127.0.0.1:9222/json/version`
2. X login/profile state for `@Gsdata5566`
3. Current follower/following/post counts when visible
4. Current-hour visible self replies
5. Local ledger for already-counted replies/actions
6. Same-day post-action measurement plan
7. OpenHarness public stars/forks when relevant

If recent visible account activity is missing from the local ledger, treat hourly capacity as uncertain. Pause or reduce publishing instead of stacking replies.

If the latest same-day action has a post-action measurement due in the future, do not publish. Record a measurement hold and let the measurement heartbeat handle it.

## Preferred Launcher

After the mandatory gate passes, use:

```bash
python3 zeelin-twitter-x-auto-ops/scripts/x_active_window_launcher.py \
  --date "$(date +%F)" \
  --target-daily 20 \
  --on-track-daily 31 \
  --year-end-target 10000 \
  --append-ledger
```

This launcher may dry-run, recheck gates, and publish only when the fresh active-window runner is explicitly allowed. Do not bypass it with lower-level scripts unless you are repairing a narrowly scoped failure or the user explicitly requested a direct helper.

## Direct Reply Helper

Use only after all gates pass and target quality is high:

```bash
bash zeelin-twitter-x-auto-ops/scripts/comment.sh "English reply" "https://x.com/target/status/123" https://x.com
```

Per active-window run, default to at most one high-signal public reply unless the gate explicitly allows more. Per heartbeat, never exceed `1-3` public replies. A normal day should publish only a small number of high-quality replies, usually `3-5` total.

## Target Selection

Prefer public, recent, English technical discussions:

- AI agents and coding agents
- Reliability, evals, benchmarks, recovery, rollback
- Persistent state and long-running automation
- Workflow infrastructure and developer tools
- Open-source agent tooling

Reject:

- spam, bait, fake or low-quality accounts
- crypto/Web3/NFT/token/airdrop/pump
- giveaways, NSFW, politics/religion fights
- self-posts or repeated handles in the same batch
- unrelated product promos, job posts, follower trains, event signup bait

Do not comment more than once under the same account in a batch.

## Content Strategy From Hardened x-twitter-growth

Use these ideas for strategy and drafting only, not to weaken safety:

- Profile surface matters: clear value proposition, specific niche, current pinned work, credible link.
- Replies are growth content: make every reply standalone and useful.
- Threads can convert, but only when hook, structure, and technical payoff are strong.
- Links in main tweets can reduce reach; prefer link-in-reply when safe and relevant.
- Reply-worthy and save-worthy content generally performs better than generic announcements.
- Do not use "follow for more", generic CTAs, engagement bait, or artificial urgency.

For `@Gsdata5566`, optimize around technical credibility, not influencer tactics.

## OpenHarness Rules

Use OpenHarness only when the discussion is directly relevant to:

- agent reliability
- persistent state
- task contracts
- scheduled execution
- recovery/rollback
- external validation or evals
- long-running automation

Good pattern:

1. Add a concrete technical observation first.
2. Mention OpenHarness only if it naturally helps the discussion.
3. Disclose relationship naturally, e.g. "In our open-source OpenHarness work..."
4. Never ask for stars.

Track public metrics through GitHub public API:

```bash
curl -fsSL https://api.github.com/repos/thu-nmrc/OpenHarness
```

Log stars/forks in the daily ledger when OpenHarness is involved.

## GitHub Community Comments

GitHub comments are allowed only when:

- The issue/discussion/PR is public.
- The target is directly relevant.
- The comment adds real technical value.
- Relationship to OpenHarness is disclosed naturally if linked.

Do not post generic comments across repositories.

## Daily Goal Audit

Before claiming the daily target is achieved, run:

```bash
python3 zeelin-twitter-x-auto-ops/scripts/x_daily_goal_completion_audit.py \
  --date "$(date +%F)" \
  --target-daily 20 \
  --append-ledger
```

The goal is complete only when current evidence proves at least `+20` net followers. Stale follower evidence, missing profile evidence, or local-only estimates are not enough.

If the goal is already verified complete, stop public actions for the day and log the stop reason.

## Follower Loss And Missed-Target Review

After a missed or negative day, run:

```bash
python3 zeelin-twitter-x-auto-ops/scripts/x_daily_growth_review.py --date "$(date +%F)" --target-daily 20 --on-track-daily 31
python3 zeelin-twitter-x-auto-ops/scripts/x_retention_segment_review.py --date "$(date +%F)" --append-ledger
```

Analyze likely follower-loss segments without private scraping:

- low-intent or follow-train followers leaving after no reciprocal behavior
- mismatch between AI-agent niche and audience expectation
- low-quality traffic from generic replies
- profile conversion gap after profile visits
- stale or repetitive repo pitch causing disinterest
- timing gaps caused by blocked windows or artifact-health holds

Convert findings into next-window adjustments, not higher spam volume.

## Self-Evolving Loop Discipline

Use local loop engineering only to improve the operating system:

- `loop-budget`: self-throttle repeated loops.
- `loop-triage`: separate actionable blockers from noise.
- `minimal-fix`: make the smallest safe workflow fix when an issue is explicit.
- `loop-verifier`: verify changes independently.

Never use loop engineering to increase account-action volume by weakening compliance.

Default loop:

1. Run the domain gate first.
2. Read current state, ledger, readiness, and budget.
3. Triage actionable gaps.
4. Apply only minimal safe fixes.
5. Verify with evidence.
6. Log outcome and next adjustment.
7. Exit early when blocked or no action is useful.

## Blocked Audit Rule

Do not mark the persistent goal blocked on the first blocker. Mark it blocked only when the same blocking condition repeats for at least three consecutive goal turns and meaningful progress requires user input or external-state change.

For a resumed blocked goal, start a fresh blocked audit. If the same blocker repeats for three resumed goal turns, mark blocked again.

When marking blocked, write:

- exact blocker
- three-turn evidence sequence
- readiness snapshot path
- artifact health status
- goal audit status
- public actions performed: should be `none`
- recovery command or next external-state requirement

## Required Logging

Every run must update `output/x-growth-YYYY-MM-DD.md` with:

- current follower evidence or stale/missing reason
- target, current net, and remaining to +20
- readiness snapshot path
- artifact health status and disk pressure if relevant
- active process holds
- measurement holds
- public URLs, exact public copy, and success/failure when actions occur
- skipped reasons and blocker reports
- OpenHarness stars/forks when relevant
- next adjustment

When no safe targets exist, write draft queue and blocker report instead of publishing filler.

## Recommended Script Set

Readiness:

```bash
/usr/bin/python3 scripts/ops_readiness_snapshot.py --date "$(date +%F)" --workspace .
```

Artifact health:

```bash
python3 zeelin-twitter-x-auto-ops/scripts/x_artifact_health_check.py --date "$(date +%F)" --append-ledger
```

Daily dashboard:

```bash
python3 zeelin-twitter-x-auto-ops/scripts/x_goal_dashboard.py --date "$(date +%F)" --target-daily 20 --append-ledger
```

Operating preflight:

```bash
python3 zeelin-twitter-x-auto-ops/scripts/x_operating_preflight.py --date "$(date +%F)" --label pre_window --samples 3 --target-daily 20 --on-track-daily 31 --append-ledger
```

Post-action measurement:

```bash
python3 zeelin-twitter-x-auto-ops/scripts/x_post_action_measurement_plan.py --date "$(date +%F)" --target-daily 20 --on-track-daily 31 --append-ledger
```

Learning loop:

```bash
python3 zeelin-twitter-x-auto-ops/scripts/x_self_evolving_workflow.py --date "$(date +%F)" --target-daily 20 --on-track-daily 31 --year-end-target 10000 --append-ledger
```

Completion audit:

```bash
python3 zeelin-twitter-x-auto-ops/scripts/x_daily_goal_completion_audit.py --date "$(date +%F)" --target-daily 20 --append-ledger
```

## Closeout

End each run with one of:

- Published: include URL, exact text, and evidence.
- Held: include blocker, snapshot path, and next unblock step.
- Draft-only: include candidate queue and why no public action was safe.
- Complete: include verified +20 evidence.
- Blocked: include three-turn blocker sequence and recovery requirement.

Keep the tone calm and evidence-first. Growth is the target; trust is the moat.
