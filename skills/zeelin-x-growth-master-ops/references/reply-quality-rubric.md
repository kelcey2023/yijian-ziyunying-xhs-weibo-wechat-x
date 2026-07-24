# Reply Quality Rubric

Use this reference to decide whether one public reply is worth publishing. Do not use it to justify action volume.

## Candidate Gate

Reject immediately when the target is:

- stale, deleted, restricted, or missing enough context;
- a follower train, giveaway, generic connect post, or engagement bait;
- spam, bot-like, crypto, trading, NSFW, political, or unrelated promotion;
- the managed account's own post;
- an account already targeted in the current batch or hour;
- not clearly relevant to AI, software, research, or developer tooling.

## Score

Score each category from `0` to `2`.

| Category | 0 | 1 | 2 |
|---|---|---|---|
| Relevance | unrelated | broadly technical | directly fits account expertise |
| Freshness | stale | still discussable | recent and active |
| Specificity | generic reply likely | one usable detail | clear claim to extend or challenge |
| Technical value | praise only | useful observation | concrete risk, example, tradeoff, or implementation detail |
| Conversation fit | intrusive | acceptable | naturally invites expert continuation |
| Reputation safety | questionable | low risk | credible author and clean context |

Require:

- no rejection condition;
- total score of at least `10/12`;
- technical value score `2`;
- reputation safety score `2`.

If the score is lower, skip. Do not rewrite repeatedly just to force a pass.

## Reply Shape

Use one of these structures, adapted to the target:

```text
[Address the specific claim.] [Add one implementation risk or practical implication.]
```

```text
[Agree or disagree with a precise reason.] [Give one concrete example or boundary condition.]
```

```text
[Name the hidden systems problem.] [Explain what would make the approach reliable in production.]
```

Good additions often involve:

- eval design and failure coverage;
- state, retries, recovery, and rollback;
- permissions, audit trails, and human escalation;
- latency, cost, observability, or deployment constraints;
- the gap between a demo and a trusted workflow.

## Copy Checks

Before publishing, confirm:

- English only;
- one to three sentences;
- specific to the target;
- no link or hashtag unless essential;
- no `great post`, `game changer`, or generic applause;
- no request for follows, stars, likes, replies, or reposts;
- no repeated opening from recent replies;
- no unsupported factual claim;
- no OpenHarness mention unless directly relevant and naturally disclosed.

## Examples

These are patterns to adapt, not text to paste repeatedly.

```text
The hard part is not tool invocation; it is preserving state across retries without duplicating side effects. Idempotency keys and explicit recovery checkpoints are what turn the demo into infrastructure.
```

```text
Benchmark lift matters only if it survives real workflow constraints. I would test permission errors, partial tool failures, and rollback behavior before trusting the headline score.
```

```text
Coding agents become useful when reviewability improves with capability. Small diffs, explicit assumptions, and evidence from the right tests matter more than raw lines generated.
```

## OpenHarness Pattern

Only when directly relevant:

```text
[Technical value first.] In our open-source OpenHarness work, the recurring failure mode has been [specific relevant observation], so we treat [recovery/eval/state control] as part of the task contract.
```

Never append a repository pitch to an otherwise unrelated reply.
