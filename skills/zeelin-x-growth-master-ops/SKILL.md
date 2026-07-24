---
name: zeelin-x-growth-master-ops
description: Run, audit, repair, and improve compliant X/Twitter growth operations with readiness gates, evidence-first replies, cautious follow-back, duplicate and capacity checks, artifact-health holds, measurement, and safe self-evolving loops. Use for @Gsdata5566 operations, hourly follower-reply heartbeats, AI-tech community engagement, OpenHarness-aware outreach, or X growth automation reviews.
---

# ZeeLin X Growth Master Ops

Operate X growth as a reputation and reliability system, not a volume game. Public actions require fresh evidence, clean gates, strong candidates, and a verifiable result.

## Default Scope

- Account: `@Gsdata5566`
- Public window: `08:00-22:00 Asia/Shanghai`
- Daily objective: `+20` net followers
- Trajectory objective: `10000` followers by year end
- Primary ledger: `output/x-growth-YYYY-MM-DD.md`
- Machine artifacts: `output/x-growth-machine/`
- Local automation: `zeelin-twitter-x-auto-ops/scripts/`

If the workspace, account, or goals differ, discover them from local configuration or ask only when the choice has material consequences.

## Non-Negotiable Rules

- Never use DMs, bought engagement, follower trains, engagement trades, bot farms, fake accounts, or follow/unfollow churn.
- Never ask for follows, stars, likes, reposts, or reciprocal engagement.
- Never evade rate limits, bypass platform controls, scrape private data, or request cookies or tokens.
- Never publish filler to hit a quota.
- Never claim a publication, follow, follower count, measurement, or goal result without direct evidence.
- Never open or interact with a composer when a hard gate is blocked.
- Treat safety, technical credibility, and audience fit as stronger objectives than action volume.

## Mandatory First Gate

When the local THUQX integration exists, run this before any publish-capable path:

```bash
/usr/bin/python3 scripts/ops_readiness_snapshot.py --date "$(date +%F)" --workspace .
```

Read:

```text
output/x-growth-machine/ops-readiness-snapshot-latest.json
```

Hard-stop public actions when `decision.blockers` contains any of:

- `outside_public_window`
- `cdp_unreachable`
- `active_publish_or_monitor_process`
- `artifact_health_not_ready`
- `automation_contract_not_ready`

Public actions require all of:

- `decision.public_actions_allowed_now=true`
- `artifact_health.artifacts_ready_for_preflight=true`
- CDP reachable and the intended X profile logged in
- no conflicting publisher, monitor, image, report, or editorial process
- enough time to finish safely before the public window closes

If blocked, log the exact blocker and continue read-only diagnostics only. Do not research a target for immediate posting, generate media, follow, reply, or open a composer.

If the readiness script is absent, the portable skill remains useful for strategy, drafts, audits, and candidate scoring, but automatic public actions are unavailable until the user provides a trusted control and verification path.

## Pre-Publish Sequence

After the mandatory gate passes:

1. Read the same-day ledger and latest action artifacts.
2. Record any pending post-action measurement without modifying it.
3. Check real execution processes, not filenames merely present in `git diff` or command arguments.
4. Verify CDP, login, profile URL, and follower/following/post counts.
5. Reconcile current-hour visible self activity with the ledger.
6. Check duplicate targets, repeated handles, stale queues, and hourly capacity.
7. Inspect the candidate and score its quality.
8. Recheck gates immediately before the public action.
9. Perform no more than the allowed action count.
10. Verify the final visible state and log exact evidence.

Treat visible unlogged activity, stale candidates, weak context, ambiguous account state, or uncertain capacity as a safe skip.

## Preferred Local Launcher

After hard gates pass, prefer the guarded launcher:

```bash
/usr/bin/python3 zeelin-twitter-x-auto-ops/scripts/x_active_window_launcher.py \
  --date "$(date +%F)" \
  --target-daily 20 \
  --on-track-daily 31 \
  --year-end-target 10000 \
  --append-ledger \
  --ignore-post-action-measurement
```

For the authorized hourly growth loop, a pending post-action measurement is an observation-only warning:

- record its label and due time;
- do not edit the measurement artifact;
- do not claim it completed;
- do not let it override a hard gate;
- use `--ignore-post-action-measurement` only when the active contract explicitly authorizes it.

Do not bypass the launcher with a lower-level publisher unless repairing a narrow failure or following an explicit user request with equivalent fresh gates.

See [references/local-automation-contract.md](references/local-automation-contract.md) for local commands, process patterns, artifact fields, and verification evidence.

## Per-Run Action Limits

A clean hourly run may perform:

- at most one high-signal English technical reply; and
- at most one cautious follow-back that independently satisfies every rule below.

Do not publish a main post from an hourly follower-reply run. Main posts belong to an explicitly requested, separately gated publishing workflow.

Zero actions is the correct result when candidates are weak, stale, duplicated, risky, or unverifiable.

## Cautious Follow-Back

Follow back only after visible inspection proves that the account:

1. already follows the managed account;
2. is genuinely AI, software, research, or developer-tool relevant;
3. is non-spam and not a follower-train account;
4. is not already followed;
5. has enough visible identity and content evidence to support the decision.

If any criterion is uncertain, skip and log `no safe follow candidate`.

Never use a blind first-button `follow_back.sh` flow to make the decision. After a permitted click, verify the final `Following` state and log the account URL plus the evidence used.

## Reply Candidate Quality

Prefer recent public English discussions about:

- AI agents and coding agents
- evals, benchmarks, observability, and permissions
- persistent state, recovery, rollback, and long-running execution
- workflow infrastructure and developer tools
- production AI reliability and failure analysis

Reject:

- spam, giveaways, bot-like accounts, generic promotion, or event bait
- crypto, Web3, NFT, token, airdrop, pump, wallet, or trading content
- NSFW, political or religious fights
- follower trains, mutual-follow solicitation, and engagement bait
- self-posts, repeated handles, job applications, or unrelated marketing
- posts too old or context-poor to support a specific reply

Use [references/reply-quality-rubric.md](references/reply-quality-rubric.md) to score a candidate. Publish only when the reply is specific, useful, and natural without relying on a template.

## Public Copy Contract

Public X copy must be:

- English only, with no Chinese punctuation;
- one to three sentences for replies;
- value-first, adding a concrete observation, risk, example, caveat, implementation detail, or tradeoff;
- specific to the target post;
- free of links and hashtags unless directly necessary;
- free of generic praise, repeated boilerplate, artificial urgency, and engagement bait.

Do not reuse a prepared sentence verbatim when it does not fit the target. Drafts are starting points, not a reply farm.

## OpenHarness Attribution

Mention OpenHarness only when the discussion directly concerns agent reliability, persistent state, task contracts, evals, recovery, scheduled execution, or long-running automation.

Use this order:

1. Add technical value first.
2. Mention the project only if it materially advances the discussion.
3. Disclose the relationship naturally, such as `In our open-source OpenHarness work...`.
4. Never ask for stars or follows.

Keep public GitHub metrics separate from follower-growth claims and log stars/forks only when relevant.

## Profile Experiments

Profile bio, name, link, banner, pinned-post, or positioning changes require explicit user approval. A diagnostic may recommend an experiment, but must not apply it automatically or mix it with same-hour reply actions when attribution would be unclear.

## Measurement And Goal Claims

- Preserve baseline, current count, sample time, and freshness.
- Treat net follower change as an outcome, not proof of causation.
- Do not infer exact unfollower identities from public counts.
- Keep negative movement visible; never reset a baseline to hide it.
- Claim the daily target only after a fresh completion audit proves at least `+20` net followers.
- Stop public actions when the target is already verified.

When no public action occurred, the measurement state must remain pending or not applicable. Never manufacture an action timestamp to make a plan look complete.

## Self-Evolving Loop

Improve the operating system, not the spam rate:

1. Gate the run.
2. Read current evidence and budget.
3. Triage the smallest actionable gap.
4. Apply only a minimal safe fix.
5. Verify independently.
6. Log the result and next adjustment.
7. Exit early when blocked or when no useful action exists.

Use strategy skills for hooks, positioning, and drafts only. They never override this contract.

## Required Ledger Evidence

Every run should log:

- readiness snapshot path and hard blockers;
- artifact-health state and disk pressure when relevant;
- login/profile evidence or why it is stale;
- follower/following/post counts and sample time;
- current-hour visible and unlogged activity;
- duplicate, queue, and capacity decisions;
- pending measurement label and due time;
- exact reply text and target/reply URLs when published;
- follow-back account URL, visible evidence, and verified final state;
- skips, failures, public action count, and next adjustment;
- OpenHarness stars/forks when directly relevant.

## Closeout States

End with exactly one evidence-based state:

- `Published`: URL, exact text, and visible verification.
- `Held`: blocker, snapshot path, and next safe checkpoint.
- `Draft-only`: candidate or draft plus the reason no public action was safe.
- `Complete`: fresh evidence that the daily target passed.
- `No-op`: clean run, but no candidate met the quality contract.

Growth is the target. Trust is the moat.
