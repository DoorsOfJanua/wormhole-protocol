# Wormhole

## Scope
Git-based coordination layer for Claude/Codex workflows. This repo is the protocol and the operational memory for shared projects.

## Shared Coordination
- Read `STATE.md` before any edit. This repo is the coordination layer, so stale state is itself a bug.
- If another agent already owns the overlapping protocol or project change, coordinate before editing.
- After substantial work or any push, update the relevant handoff surface so `STATE.md`, `BACKLOG.md`, and the outbox remain trustworthy.

## Read First
- `CLAUDE.md`
- `GUIDE.md`
- `PROMPT.md`
- `STATE.md`
- `BACKLOG.md`

## Guardrails
- Preserve the simple three-command interface. Do not add cleverness that makes the protocol harder to audit.
- Keep `GUIDE.md`, `PROMPT.md`, `README.md`, and any changed workflow examples consistent when the protocol changes.
- Respect `OPEN_SOURCE_BOUNDARY.md` when changing docs, examples, or published artifacts.
- If you touch ACK, archival, handoff, or project-state behavior, update docs and tests together.
