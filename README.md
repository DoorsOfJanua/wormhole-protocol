# Wormhole

Wormhole is a Git-based coordination layer for multi-AI work.

It exists for one reason:

When you switch between Claude, Codex, multiple windows, multiple accounts, and multiple repos, the models are not the bottleneck. You are. You become the router, the clipboard, and the continuity layer.

Wormhole removes that coordination loss.

## What It Does

Wormhole gives you:
- durable outbox handoffs between AI systems
- rolling project state surfaces
- a same-machine local bus for low-latency coordination
- operator-facing health checks so the system can be trusted during real work

It is not:
- a chat log
- a second brain
- a replacement for your project repos
- a replacement for your vault

It is the membrane between them.

## Core Layers

### 1. Durable handoff layer

- `claude/outbox/`
- `codex/outbox/`
- `STATE.md`
- `projects/*.md`
- ACK comments

Use this layer for:
- decisions
- blockers
- approvals
- completed handoffs
- anything that must survive time, sync, and session resets

### 2. Same-machine local bus

- `.wormhole/` runtime directory
- `mission_control/wormhole.py`

Use this layer for:
- active claims
- local inbox events
- preflight summaries
- fast coordination between agents sharing one filesystem

## New In This Update

This update adds a stronger operator layer:

- improved `status` output with health, stale claims, and unread counts
- new `health` command with strict exit codes
- machine-readable JSON status/health output
- multi-account operating protocol documentation
- VNext shipping plan for public release and relaunch

This matters because a coordination system only becomes real when you can inspect it quickly and trust its state.

## Commands

### Read and continue

```bash
python mission_control/wormhole.py read --agent codex --project Wormhole --limit 1
```

### Write a durable handoff

```bash
python mission_control/wormhole.py send \
  --sender codex \
  --project Wormhole \
  --title "Handoff" \
  --type handoff \
  --body "What changed" \
  --next-action "What to do next"
```

### Fast same-machine preflight

```bash
python mission_control/wormhole.py preflight --agent codex --project Wormhole --mark-read
```

### Operator status

```bash
python mission_control/wormhole.py status
python mission_control/wormhole.py status --json
```

### Health check

```bash
python mission_control/wormhole.py health
python mission_control/wormhole.py health --strict
python mission_control/wormhole.py health --strict --max-local 0 --max-durable 0
```

## The Multi-Account Pattern

The clean split is:

- Plus account = control tower
- Pro account = execution engine
- Obsidian = durable memory
- Wormhole = coordination membrane

Account memory is temporary. Project files, Obsidian, and Wormhole are the durable layers.

See:
- `docs/2026-04-05-multi-account-operating-protocol.md`
- `docs/2026-04-05-wormhole-vnext-shipping-plan.md`

## Repo Map

```text
README.md              repo overview
PROMPT.md              machine protocol
GUIDE.md               human + machine workflow guide
CHEATSHEET.md          short command layer
STATE.md               rolling global state
BACKLOG.md             extracted action queue
projects/              rolling status per project
claude/outbox/         Claude durable messages
codex/outbox/          Codex durable messages
mission_control/       local bus tooling
docs/                  deeper operating notes and plans
```

## Important Boundary

This live repo is an operational repo, not a public-safe template by default.

Private content such as:
- real outbox traffic
- project status files
- backlog and state
- local paths
- personal names

must be sanitized before public release.

If you want a public version, export a sanitized template or use a dedicated template repo.

## Why This Exists

Wormhole was built during real multi-project work, not as a protocol toy.

The goal is simple:

Stop making the human manually restate context between models.

That is the bottleneck.
