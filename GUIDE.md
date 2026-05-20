# Wormhole Guide

Wormhole is a coordination repo for AI systems working across multiple projects.

It solves one specific problem:

You make progress with Claude in one place, switch to Codex in another repo, and lose the thread. Then you copy-paste context, restate decisions, and act as the router between tools.

Wormhole removes that.

Claude and Codex keep their own project repos. Wormhole is the shared membrane between them.

## Public vs Private

This live Wormhole repo is a private working repo.

If you want a public/open-source Wormhole project, do not publish this repo directly. Create a separate sanitized public repo or export that contains only generic protocol material.

Private working content such as:
- outboxes
- project status files
- backlog/state
- personal names
- local paths
- internal examples

must stay out of the public release unless sanitized first.

## What Wormhole Is

Wormhole is not:
- a code repo for the actual products
- a note dump
- a chat room
- a replacement for your vault or project repos

Wormhole is:
- a durable handoff layer between AI systems
- a rolling cross-project state surface
- a place for decisions, blockers, handoffs, and high-signal insights

When multiple terminal agents are on the same machine, Wormhole can also run a local low-latency layer:
- gitignored runtime state in `.wormhole/`
- active task claims
- local inbox items
- preflight summaries before replying

That local layer speeds up same-machine coordination. The committed outbox still carries durable truth.

## Core Idea

Each project keeps its own real source of truth:
- project repo for code
- vault for doctrine, plans, and long memory

Wormhole only carries the minimum information needed for another AI to recover context and work correctly.

That means:
- project repos stay clean
- the vault stays strategic
- Wormhole stays sparse and operational

## Repo Structure

```text
PROMPT.md              shared protocol
STATE.md               current cross-project focus
GUIDE.md               this file
projects/              one rolling status file per project
claude/outbox/         Claude writes timestamped messages here
codex/outbox/          Codex writes timestamped messages here
shared/decisions/      final decisions, append-only
mission_control/       local bus CLI for same-machine coordination
```

## Branch Discipline

Wormhole stays on `main` by default.

That is intentional.

Per-project branches inside Wormhole create a second routing problem:
- which branch should be pulled
- which branch has unread messages
- where cross-project handoffs belong

Use `main` for routine messages, ACKs, and project status updates.

Only use a separate Wormhole branch if the human explicitly wants protocol changes reviewed before landing, such as:
- edits to `PROMPT.md`, `GUIDE.md`, or automation behavior
- structural repo reorganization
- experimental workflow changes

Keep project-specific branches in the real product repos, not here.

## When To Use Wormhole

Write to Wormhole when the other AI would work differently because of the update.

Use it for:
- decisions that affect another session or repo
- blockers
- completed handoffs
- insights with cross-project consequences

Do not use it for:
- "I read this file"
- "I started working on X"
- raw thinking
- local progress that changes nothing outside the current session

If the update would not change how the other AI works, it does not belong here.

## Message Format

Every outbox message uses the same fixed fields:

```markdown
# [Topic]
**Date**: YYYY-MM-DD HH:MM
**From**: Claude (Opus|Sonnet|Haiku) | Codex
**Project**: which project(s) this affects
**Type**: decision | blocker | insight | handoff
**Body**: 3-8 lines max. What happened, why it matters, what changed.
**Next action**: what the other side should do (or "FYI only")
```

Optional fields:

```markdown
**Workspace**: which window/session this came from
**Urgency**: low | normal | high
**Links**: repo paths, file references, URLs
**Confidence**: high | medium | low
```

## Rolling Project Status Format

Each file in `projects/` is updated in place.

```markdown
# [Project Name]
**Objective**: one-line goal
**Current Status**: what is true now
**Approval State**: proposed | awaiting_review | approved | executing | hold | blocked
**Current Blocker**: what is stuck, or none
**Last Meaningful Change**: the last thing that moved the needle
**Next Critical Move**: the most important next step
**Last Updated By**: Claude (Model) | Codex
**Last Updated At**: YYYY-MM-DD HH:MM
```

Keep each project file under 20 lines.

If it needs more, it is not a status file anymore.

## ACK Rule

For pure FYIs, do not send a reply message.

Append an ACK comment to the original message:

```html
<!-- ACK Claude (Opus) 2026-03-22 -->
```

Only create a new message if you are adding a decision, blocker, or real follow-up.

## Real Example

This is a real Codex message already used in Wormhole:

```markdown
# Wormhole protocol aligned
**Date**: 2026-03-22 15:28
**From**: Codex
**Project**: Life OS / Wormhole
**Type**: handoff
**Body**: I pulled the live Wormhole repo, read PROMPT.md and STATE.md, and reviewed the current rolling project snapshots. The protocol now matches the tightened pattern: fixed message fields, rolling status files, message-worthy threshold, and ACK comments on the original message. I also saved the same protocol and rationale into the Life OS vault so the pattern exists in durable docs, not only in the repo. This is the first live Codex outbox test.
**Next action**: FYI only. If received, append an ACK comment to this file.
**Workspace**: ~/path/to/personal-workspace
**Urgency**: normal
**Links**: ~/path/to/personal-workspace/knowledge/Cross-AI Wormhole Repo Pattern.md
**Confidence**: high

<!-- ACK Claude (Opus) 2026-03-22 -->
```

That is the pattern:
- short
- specific
- actionable
- acknowledged without noise

## Your Three Commands

You do not write messages yourself. Your AIs write them. You only need three phrases:

**"Pull wormhole"** - tell the AI to do the full inbox pass. It pulls the repo, scans unread outbox messages, tells you what changed, what matters, what needs approval, and suggests the next best task.

**"Sync wormhole only"** - tell the AI to do a quiet pull with no digest. Use this only when you truly want silence.

**"Push to wormhole"** - tell the AI to write what just happened. It creates the outbox message, updates project status if needed, commits and pushes.

**"Hand this to [Claude/Codex]"** - tell the AI to write a structured handoff. It captures the full context of what you were working on so the other side can pick it up cold.

That is your entire interface. You are the architect and dispatcher. The AIs are the readers, writers, and coordinators. You point, they move.

Terminal shortcuts for the same flow:
- `wormhole read --agent codex --project Wormhole --limit 1`
- `wormhole send --sender codex --project Wormhole --title "Handoff" --type handoff --body "What changed" --next-action "What the human should approve"`
- `wormhole daemon`
- `python mission_control/wormhole.py status`
- `python mission_control/wormhole.py health --strict`

## Same-Machine Bus

If Claude, Codex, and Gemini are all running on the same filesystem, use the local bus as the fast path:

```bash
python mission_control/wormhole.py watch
python mission_control/wormhole.py preflight --agent codex --project Wormhole --mark-read
python mission_control/wormhole.py claim --agent codex --project Wormhole --task "Implement claim routing"
python mission_control/wormhole.py emit --sender codex --project Wormhole --kind blocker --summary "Need Claude to review prompt wording"
python mission_control/wormhole.py release --agent codex --project Wormhole
python mission_control/wormhole.py status
python mission_control/wormhole.py health --strict --max-local 0 --max-durable 0
```

For self-contained durable handoffs, use:

```bash
python mission_control/wormhole.py send --sender codex --project Wormhole --title "Handoff" --type handoff --body "What changed" --next-action "What to do next"
python mission_control/wormhole.py read --agent codex --project Wormhole --limit 1
```

Rule of thumb:
- local bus = low-latency same-machine notes and claims
- outbox = durable handoff that should survive git history

## Operator Health

Wormhole is only useful if you can inspect it quickly.

Use:

```bash
python mission_control/wormhole.py status
```

to see:
- runtime health
- stale claims
- unread local bus counts
- unread durable inbox counts
- recent events

Use:

```bash
python mission_control/wormhole.py health --strict --max-local 0 --max-durable 0
```

when you want a machine-checkable verdict.

This exits nonzero in strict mode if:
- the route index is not bootstrapped
- stale claims exist and are not allowed
- unread local backlog exceeds your threshold
- unread durable backlog exceeds your threshold

Use JSON output when wiring it into scripts:

```bash
python mission_control/wormhole.py status --json
python mission_control/wormhole.py health --json
```

## Setup

1. Create a dedicated Git repo called `wormhole`.
2. Add `PROMPT.md` with the protocol.
3. Add `STATE.md` with current priorities, blockers, and pending handoffs.
4. Add `projects/` with one rolling status file per active project.
5. Add `claude/outbox/` and `codex/outbox/`.
6. Commit and push.
7. Tell both systems to pull Wormhole from `origin/main` before starting meaningful work.

## Daily Workflow

### Before work starts
- pull Wormhole
- scan unread outbox messages newest-first
- read those unread messages directly
- only then read `STATE.md`
- then read the relevant `projects/*.md`

### Worker window rule
- if this window is for a specific project, treat that project as the task boundary
- read that project's `.context.md` first when available
- only read Wormhole items for that project, plus urgent global protocol items
- do not switch to another project unless the human explicitly reroutes you

### During work
- keep working in the real project repo
- only write to Wormhole when something crosses the message threshold
- do not cross a review boundary without explicit approval

### After meaningful change
- update the relevant project status file if shared reality changed
- write a timestamped outbox message if the other AI needs to know
- push

### After a phase completes
- push a completion message
- set `Approval State` to `awaiting_review`
- stop
- wait for the human's explicit approval before starting the next phase

### When reading a pure FYI
- append an ACK comment
- do not create reply noise

## Human-in-the-Loop

the human is the architect. Both AIs are advisors and executors, but only after approval.

When you pull Wormhole and find unread messages:

1. **Always list what you found.** Never say "up to date" without showing the contents.
2. **Highlight anything actionable** that needs the human's yes/no.
3. **Suggest, don't execute.** Present options. Wait for approval.
4. **FYI messages can be ACK'd after you summarize them.** Do not let ACK replace the summary.

The auto-sync cron generates an inbox digest every 30 minutes. It notifies the human but does not spawn AIs to auto-execute. the human reviews and decides.

## Approval Gates

This is the missing discipline when work spans multiple phases.

Rules:
- a phase completion message is a request for review, not permission to continue
- after finishing a phase, set the project status to `awaiting_review` and stop
- the next phase starts only after an explicit the human approval is recorded
- if review finds issues, the project goes to `hold` or `blocked`
- no worker window may say "Phase 2 complete, starting Phase 3" unless the human already approved that exact transition

If a hold message arrives while a background task is running:
- stop at the next safe checkpoint
- report touched files and counts
- do not begin another batch item

## Project-Scoped Pulls

Wormhole has two pull modes:

- **Governance pull**: read across projects, coordinate broadly
- **Worker pull**: stay inside one claimed project

If a window was opened for DoH, Music Engine, MicroBlooming, or another specific project, it should behave as a worker pull by default.

That means:
- read local `.context.md` for that project first
- read only matching Wormhole messages and backlog items
- ignore unrelated open work

The governance window is the only window that should routinely read the whole repo as a cross-project control plane.

## Best Practices

- Keep status separate from messages.
- Update `projects/*.md` in place.
- Keep outbox messages append-only and timestamped.
- Write for the other AI's decision-making, not for your own diary.
- Prefer one clear message over five tiny ones.
- Link to files or repos instead of pasting long content.
- Never put secrets here.
- Treat phase boundaries like merge boundaries: review first, continue second.

## Failure Modes

Wormhole will rot if you let it become:
- a chat log
- a thought dump
- a second project repo
- a place for low-signal activity updates

Wormhole stays useful only if it remains:
- sparse
- high-signal
- cross-project
- decision-oriented

## What Makes It Different

Most people treat AI tools like separate windows.
That forces the human to carry continuity.

Wormhole treats them like coworkers with a shared coordination membrane.
Not shared cognition. Not one giant agent. Just a reliable way to pass state, decisions, and handoffs across sessions and repos.

That is enough to remove a surprising amount of friction.

## Minimal Rule

If this update would change how the other AI works, write it.
If not, do not.
