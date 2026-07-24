# Local Automation Contract

Load this reference only when the THUQX workspace and its local X automation scripts are available.

## Workspace Defaults

```text
workspace: /Users/youke/Desktop/Codex 驾驭工程/THUQX-智能传播技能套件1.0
account: @Gsdata5566
base URL: https://x.com
CDP port: 9222
ledger: output/x-growth-YYYY-MM-DD.md
machine artifacts: output/x-growth-machine/
```

Do not assume these paths on another machine. Discover the workspace or stay in draft and audit mode.

## Mandatory Readiness

```bash
/usr/bin/python3 scripts/ops_readiness_snapshot.py --date "$(date +%F)" --workspace .
```

Read:

```text
output/x-growth-machine/ops-readiness-snapshot-latest.json
```

Required fields before a public action:

```text
decision.public_actions_allowed_now = true
decision.blockers = []
artifact_health.artifacts_ready_for_preflight = true
cdp.reachable = true
processes.active_count = 0
automations.contract_ready = true
public_window.inside_public_window = true
```

Hard blockers:

```text
outside_public_window
cdp_unreachable
active_publish_or_monitor_process
artifact_health_not_ready
automation_contract_not_ready
```

## Guarded Launcher

```bash
/usr/bin/python3 zeelin-twitter-x-auto-ops/scripts/x_active_window_launcher.py \
  --date "$(date +%F)" \
  --target-daily 20 \
  --on-track-daily 31 \
  --year-end-target 10000 \
  --append-ledger \
  --ignore-post-action-measurement
```

The launcher must acquire and release its lock. A successful process exit is not proof of a public action. Read its JSON artifact and verify:

```text
publish_requested_to_orchestrator
final_publish_ready
final_publish_blockers
public_actions_performed
```

## Read-Only Checks

Current-hour visible self activity:

```bash
/usr/bin/python3 zeelin-twitter-x-auto-ops/scripts/x_recent_self_activity.py \
  --date "$(date +%F)" \
  --current-hour-only \
  --scrolls 3 \
  --append-ledger
```

Profile conversion snapshot:

```bash
/usr/bin/python3 zeelin-twitter-x-auto-ops/scripts/x_profile_conversion_monitor.py \
  --date "$(date +%F)" \
  --label hourly_preflight \
  --samples 3 \
  --note "Fresh login and follower snapshot before guarded active-window launcher"
```

Goal completion audit:

```bash
/usr/bin/python3 zeelin-twitter-x-auto-ops/scripts/x_daily_goal_completion_audit.py \
  --date "$(date +%F)" \
  --target-daily 20 \
  --append-ledger
```

## Active Process Guard

Treat these as conflicting when they are actually executing:

```text
x_growth_machine.py
run_hourly_growth.py
run_hourly_growth.sh
cdp_comment.py
comment.sh
tweet.sh
follow_back.sh
x_daily_growth_runner.py
x_growth_heartbeat_orchestrator.py
x_active_window_launcher.py
generate_image2_asset
run_daily_editorial_batch
four_platform_materialization
post_daily_report.py
run_monitor.mjs
```

Avoid substring-only process checks. A `git diff` or editor process may contain these filenames as arguments without executing them.

## Artifact Health

```bash
/usr/bin/python3 zeelin-twitter-x-auto-ops/scripts/x_artifact_health_check.py \
  --date "$(date +%F)" \
  --append-ledger
```

When `artifacts_ready_for_preflight=false`, public actions remain blocked even if CDP is reachable.

Generated disk cleanup helpers are dry-run first. Apply cleanup only after explicit user approval, and only within the helper's narrow rebuildable-temp scope. Never broaden approval to user documents, project files, sessions, memories, plugins, configuration, databases, or cloud-sync data.

## Measurement Plan

Read without editing:

```text
output/x-growth-machine/post-action-measurement-plan-YYYY-MM-DD.json
```

Record:

```text
action_status
publish_attempted
action_observed_at
next_measurement.label
next_measurement.due_at
completed_measurements
```

For the authorized heartbeat loop, `pending_public_action` with `action_observed_at=null` is an observation warning, not evidence of a published action and not a hard blocker.

## Final Verification

After a reply:

- verify the reply on the public target or managed profile;
- capture the target and reply URLs;
- log the exact English text;
- do not count a filled composer or click as success.

After a follow-back:

- verify the account visibly followed the managed account before the action;
- verify AI or technology relevance and non-spam status;
- verify the final button or relationship state is `Following`;
- log the account URL and evidence.

If verification fails, record `unverified` and do not claim success.
