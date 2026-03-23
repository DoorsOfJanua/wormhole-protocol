# Wormhole Cheatsheet

You are not the router.
You point. Your AIs coordinate.

## The 3 Commands

### 1. Start or resume work
Say:
`Pull wormhole and continue.`

If you want a specific project:
`Pull wormhole, read projects/my-app.md, and continue.`

What happens:
- the AI pulls the repo
- scans unread inbox items
- tells you what changed and what matters
- highlights anything needing approval
- suggests the next best task
- then starts working without you re-explaining

### Quiet sync only
Say:
`Sync wormhole only.`

What happens:
- the AI just pulls the repo
- no inbox digest
- no suggestions unless you ask

### 2. Save shared progress
Say:
`Push this to wormhole.`

What happens:
- the AI writes a proper handoff or status update
- pushes it to Wormhole
- the other AI can now pick it up later

### 3. Switch between AIs
Say:
`Hand this to Claude via wormhole.`
or
`Hand this to Codex via wormhole.`

What happens:
- the current AI writes the transfer note
- the other AI pulls Wormhole
- you do not paste the transcript yourself

## Common Situations

### Starting a fresh session
Say:
`Pull wormhole. Read STATE.md and the relevant project status. Then [task].`

Example:
`Pull wormhole. Read projects/my-app.md. Then audit the API endpoints.`

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

### Switching windows without re-explaining
In the first window:
`Push this whole discussion to wormhole for Claude.`

In the second window:
`Pull wormhole and continue from the latest handoff.`

### Ending a session
Say:
`Push final status to wormhole.`

Use this when the other AI will need to know what changed.
If nothing meaningful changed, do not push noise.

## Fast Rule

If this would change how the other AI works, push it.
If not, don't.
