# Wormhole Guide

Wormhole is a coordination repo for AI systems working across multiple projects.

It solves one specific problem:

You make progress with one AI, switch to another in a different repo, and lose the thread. Then you copy-paste context, restate decisions, and act as the router between tools.

Wormhole removes that.

Your AIs keep their own project repos. Wormhole is the shared membrane between them.

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

## Core Idea

Each project keeps its own real source of truth:
- project repo for code
- vault/docs for doctrine, plans, and long memory

Wormhole only carries the minimum information needed for another AI to recover context and work correctly.

That means:
- project repos stay clean
- docs stay strategic
- Wormhole stays sparse and operational

## Repo Structure

```text
PROMPT.md              shared protocol
STATE.md               current cross-project focus
GUIDE.md               this file
CHEATSHEET.md          3-command interface
projects/              one rolling status file per project
claude/outbox/         Claude writes timestamped messages here
codex/outbox/          Codex writes timestamped messages here
shared/decisions/      final decisions, append-only
examples/              example messages showing the pattern
```

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
<!-- ACK Claude (Opus) 2026-03-23 -->
```

Only create a new message if you are adding a decision, blocker, or real follow-up.

## Your Three Commands

You do not write messages yourself. Your AIs write them. You only need three phrases:

**"Pull wormhole"** tells the AI to do the full inbox pass. It pulls the repo, scans unread outbox messages, tells you what changed, what matters, what needs approval, and suggests the next best task.

**"Push to wormhole"** tells the AI to write what just happened. It creates the outbox message, updates project status if needed, commits, and pushes.

**"Hand this to [Claude/Codex]"** tells the AI to write a structured handoff. It captures the full context so the other side can pick it up cold.

**"Sync wormhole only"** tells the AI to do a quiet pull. No digest, no suggestions. Use this only when you truly want silence.

## Setup

1. Fork this repo (or clone and push to your own remote)
2. Add `PROMPT.md` to your AI systems' context
3. Create a `projects/` file for each active project
4. Create `claude/outbox/` and `codex/outbox/` (or rename to match your AI tools)
5. Update `STATE.md` with your current priorities
6. Tell both systems to pull Wormhole before starting meaningful work

## Daily Workflow

### Before work starts
- Pull Wormhole
- Read `STATE.md`
- Read the relevant `projects/*.md`
- Check the other side's outbox

### During work
- Keep working in the real project repo
- Only write to Wormhole when something crosses the message threshold

### After meaningful change
- Update the relevant project status file if shared reality changed
- Write a timestamped outbox message if the other AI needs to know
- Push

### When reading a pure FYI
- Append an ACK comment
- Do not create reply noise

## Human-in-the-Loop

The human is the architect. All AIs are advisors and executors, but only after approval.

When pulling Wormhole and finding unread messages:

1. **Always list what you found.** Never say "up to date" without showing the contents.
2. **Highlight anything actionable** that needs the human's yes/no.
3. **Suggest, don't execute.** Present options. Wait for approval.
4. **FYI messages can be ACK'd silently**, but still mention them in your summary.

## Adapting for Your Setup

### Different AI tools
Replace `claude/outbox/` and `codex/outbox/` with whatever tools you use. The protocol works with any combination: Claude + Codex, Claude + Claude, GPT + Claude, Gemini + Codex, etc.

### Multiple windows of the same AI
Add a role tag to the From field: `Claude (Sonnet - Frontend)`. This lets you run parallel builds without confusion about which window sent what.

### Solo with one AI
Wormhole still works for cross-session continuity. Push state at the end of a session, pull at the start of the next one. Your future AI session recovers context without you re-explaining.

### Teams
Each person gets their own outbox directory. The protocol scales the same way.

## Best Practices

- Keep status separate from messages
- Update `projects/*.md` in place
- Keep outbox messages append-only and timestamped
- Write for the other AI's decision-making, not for your own diary
- Prefer one clear message over five tiny ones
- Link to files or repos instead of pasting long content
- Never put secrets here

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

Most people treat AI tools like separate windows. That forces the human to carry continuity.

Wormhole treats them like coworkers with a shared coordination membrane. Not shared cognition. Not one giant agent. Just a reliable way to pass state, decisions, and handoffs across sessions and repos.

That is enough to remove a surprising amount of friction.

## Minimal Rule

If this update would change how the other AI works, write it. If not, don't.
