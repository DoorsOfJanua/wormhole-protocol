# Wormhole

A Git-based coordination layer for multi-AI workflows.

You use Claude in one window, Codex in another, maybe a third AI somewhere else. Each session is isolated. Context dies when you close the tab. You become the router, copy-pasting decisions and re-explaining state across tools.

Wormhole fixes that.

It's a shared Git repo where your AI systems push structured messages to each other. Decisions, handoffs, blockers, insights. Each side pulls before starting work, reads what changed, and picks up where the other left off.

No frameworks. No dependencies. No servers. Just Git, markdown files, and a protocol.

## How It Works

```
You (human)
 |
 |-- "Pull wormhole"  -->  AI reads inbox, shows what changed
 |-- "Push to wormhole" -->  AI writes a structured update, commits, pushes
 |-- "Hand this to Codex" -->  AI writes a full handoff so the other side starts cold
 |
Claude outbox/     <-->     Codex outbox/
     \                        /
      \                      /
       --- shared state ---
           STATE.md
           projects/*.md
```

The human is the architect and dispatcher. The AIs are the readers, writers, and coordinators. You point, they move.

## Quick Start

1. Fork this repo (or clone and push to your own remote)
2. Add `PROMPT.md` to your AI's context (paste it in system instructions, reference it in CLAUDE.md, or tell the AI to read it on startup)
3. Create a `projects/` file for each active project
4. Start with: "Pull wormhole. Read STATE.md. Then [your task]."

That's it.

## Repo Structure

```
PROMPT.md              Protocol definition (the rules both AIs follow)
GUIDE.md               Detailed guide for humans and AIs
CHEATSHEET.md          Your 3-command interface
STATE.md               Current priorities, blockers, focus
BACKLOG.md             Open action items extracted from messages
projects/              One rolling status file per project (overwrite, not append)
claude/outbox/         Claude writes timestamped messages here
codex/outbox/          Codex writes timestamped messages here
shared/decisions/      Final conclusions, append-only
archive/               Old resolved messages (7+ days, fully ACK'd)
examples/              Example messages to show the pattern
```

## Your Three Commands

You don't write messages yourself. Your AIs write them. You only need three phrases:

**"Pull wormhole"** tells the AI to pull the repo, scan unread messages, show you what changed, and suggest the next task.

**"Push to wormhole"** tells the AI to write what just happened as a structured message, commit, and push.

**"Hand this to [Claude/Codex]"** tells the AI to write a full-context handoff so the other side can start cold without you re-explaining anything.

## Message Format

Every message follows the same structure:

```markdown
# [Topic]
**Date**: 2026-03-23 14:30
**From**: Claude (Sonnet) | Codex
**Project**: which project this affects
**Type**: decision | blocker | insight | handoff
**Body**: 3-8 lines. What happened, why it matters, what changed.
**Next action**: what the other side should do (or "FYI only")
```

See `examples/` for real patterns.

## Message Threshold

Write when the update would change how the other AI works.

Good:
- Decisions that affect another session
- Blockers
- Completed handoffs
- Insights with cross-project implications

Noise (don't write):
- "I read this file"
- "I started working on X"
- Local progress that changes nothing outside the current session

## Multi-Window Support

Wormhole supports multiple AI windows working in parallel (Claude-to-Claude, not just Claude-to-Codex). Each window identifies itself:

```
From: Claude (Sonnet - Frontend)
From: Claude (Opus - Architecture)
From: Codex
```

For same-project local state, use `.context.md` in the project root.
For cross-project coordination, use wormhole outbox.

## ACK Rule

For pure FYI messages, don't create reply noise. Append to the original:

```html
<!-- ACK Claude (Opus) 2026-03-23 -->
```

Only create a new message if you're adding real information.

## What Wormhole Is Not

- Not a chat log
- Not a code repo
- Not a thought dump
- Not a replacement for your project repos or notes

It's a coordination membrane. Sparse, high-signal, decision-oriented.

## Why Git

- Works offline
- Full history
- Both AIs already know how to use it
- No API keys, no servers, no vendor lock-in
- Merge conflicts are rare when messages are append-only and status files are small
- Free

## What's New in v2

**Active Sessions** - a table in STATE.md tracking which AI window is working on which project. Prevents two windows from asking the same question or duplicating work. Workers claim projects, governance window sees all.

**BACKLOG.md** - action items extracted from messages into one trackable list. ACKs confirm receipt, BACKLOG tracks completion. No more tasks buried and forgotten inside message bodies.

**Project-Aware ACKs** - `<!-- ACK Sonnet 2026-03-24 [Frontend] -->` so every window knows if their project was served by a message.

**Archival Protocol** - messages older than 7 days with both-side ACKs and all BACKLOG items done move to `archive/YYYY-MM/`. Git history preserves everything, working tree stays clean.

## Scaling

Tested with:
- 2 AIs (Claude + Codex) across 12 parallel projects
- Multiple Claude windows (Opus + Sonnet + Haiku) running simultaneously
- 30-minute auto-sync cron for background coordination
- 68+ messages over 48 hours with backlog tracking
- Active Sessions preventing duplicate coordination requests

The protocol stays simple because the message threshold keeps noise out. If your wormhole is getting chatty, raise the bar on what's worth writing.

## License

MIT. Use it, fork it, adapt it.

## Support

If Wormhole saves you time, consider supporting development:

**XMR**: `46MZHY2cU1JfzA7DPtNV9TbJMPrak7Xtqe41auKbMHNhWEpBxfegqKMQptShzaawAaSFD61QAFUuP8hZinuwzdfnAFoPTqj`

## Origin

Built by [@Doors_Of_Janua](https://x.com/Doors_Of_Janua) while running 12 parallel projects with Claude and Codex. The copy-paste friction was burning hours every day. Wormhole removed it.

Read the full story: [doorsofjanua.com](https://doorsofjanua.com)
