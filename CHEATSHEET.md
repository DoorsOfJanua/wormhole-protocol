# Wormhole Cheatsheet

You are not the router.
You point. Claude and Codex coordinate.

## The 3 Commands

### 1. Start or resume work
Say:
`Pull wormhole and continue.`

Terminal equivalent:
`wormhole read --agent codex --project Wormhole --limit 1`

If you want a specific project:
`Pull wormhole, read projects/dmt.md, and continue.`

What happens:
- the AI pulls `origin/main`
- if the window is project-specific, it stays scoped to that project
- scans unread outbox items first
- reads those unread messages before trusting `STATE.md`
- tells you what changed and what matters
- highlights anything needing approval
- suggests the next best task
- then starts working without you re-explaining

Important:
- if the last message says a phase is complete, the AI must stop at `awaiting_review`
- it may not start the next phase unless you explicitly approve it

### Quiet sync only
Say:
`Sync wormhole only.`

What happens:
- the AI just pulls `origin/main`
- no inbox digest
- no suggestions unless you ask

### 2. Save shared progress
Say:
`Push this to wormhole.`

Terminal equivalent:
`wormhole send --sender codex --project Wormhole --title "Update" --type handoff --body "What changed" --next-action "What the human should approve next"`

What happens:
- the AI writes a proper handoff or status update
- pushes it to `main`
- the other AI can now pick it up later

### 3. Switch between Claude and Codex
Say:
`Hand this to Claude via wormhole.`
or
`Hand this to Codex via wormhole.`

What happens:
- the current AI writes the transfer note
- the other AI pulls Wormhole
- you do not paste the transcript yourself

## Common Situations

### Starting a fresh Claude or Codex session
Say:
`Pull wormhole. Read STATE.md and the relevant project status. Then [task].`

Example:
`Pull wormhole. Read unread outbox first, then projects/microblooming.md. Then audit the iOS client against the proxy plan.`

For a project window, better:
`Pull wormhole for Doors of Harmony only, then continue.`

### Working on DMT right now
Say:
`Pull wormhole. Read projects/dmt.md. Then [task].`

Example:
`Pull wormhole. Read projects/dmt.md. Then prepare the next release move.`

### You want the other AI to check code
Say:
`Hand this to Codex via wormhole and ask for a repo audit.`
or
`Hand this to Claude via wormhole and ask for a strategy review.`

### You made a decision or found a blocker
Say:
`Push this blocker to wormhole.`
or
`Push this decision to wormhole.`

### You are switching windows and do not want to explain again
In the first window:
`Push this whole discussion to wormhole for Claude.`

In the second window:
`Pull wormhole and continue from the latest handoff.`

### Ending a session
Say:
`Push final status to wormhole.`

Use this when the other AI will need to know what changed.
If nothing meaningful changed, do not push noise.

### Stopping drift
Say:
`Push hold to wormhole for [project].`

What happens:
- the AI writes a high-urgency stop/hold message
- the worker for that project must stop at the next safe checkpoint
- no new phase or batch starts until you re-approve

## Same-Machine Bus

Start the watcher:
`python mission_control/wormhole.py watch`

Daemon alias:
`wormhole daemon`

Preflight before replying:
`python mission_control/wormhole.py preflight --agent codex --project Wormhole --mark-read`

Claim a task:
`python mission_control/wormhole.py claim --agent codex --project Wormhole --task "Implement local bus"`

Send a short local note:
`python mission_control/wormhole.py emit --sender codex --project Wormhole --kind progress --summary "Need Claude to read the new CLI docs"`

Release a task:
`python mission_control/wormhole.py release --agent codex --project Wormhole`

## Fast Rule

If this would change how the other AI works, push it.
If not, do not.

If a phase just finished, do not say `continue`.
Say one of:
- `Review this first.`
- `Approve Phase 3.`
- `Hold this project.`

Wormhole itself stays on `main` unless you explicitly ask for a protocol branch.

If a window was opened for one project, Wormhole should keep it on that project until you say otherwise.
