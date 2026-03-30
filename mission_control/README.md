# Wormhole Local Bus

This folder contains the same-machine coordination layer for terminal-based agents.

It does not replace the committed outbox protocol. It sits next to it.

Use the committed outbox for:
- durable cross-session handoffs
- anything that should survive git push/pull
- approvals, decisions, and completed work

Use the local bus for:
- low-latency same-machine coordination
- active task claims
- short progress notes
- preflight summaries before replying

Runtime data lives in `.wormhole/` at repo root and is gitignored.

## Commands

```bash
python mission_control/wormhole.py read --agent codex --project Wormhole --limit 1
python mission_control/wormhole.py send --sender codex --project Wormhole --title "Handoff" --type handoff --body "What changed" --next-action "What to do next"
python mission_control/wormhole.py daemon --interval 2
python mission_control/wormhole.py watch
python mission_control/wormhole.py preflight --agent codex --project Wormhole --mark-read
python mission_control/wormhole.py claim --agent codex --project Wormhole --task "Implement local bus"
python mission_control/wormhole.py emit --sender codex --project Wormhole --kind progress --summary "Need Claude to review prompt wording"
python mission_control/wormhole.py release --agent codex --project Wormhole
python mission_control/wormhole.py status
```

## Recommended Use

1. Start one watcher/daemon in a background terminal:

```bash
python mission_control/wormhole.py daemon
```

2. At the start of a session, run read (durable inbox) and preflight (local bus + outbox digest):

```bash
python mission_control/wormhole.py read --agent codex --project CharlieOS --limit 1
```

```bash
python mission_control/wormhole.py preflight --agent codex --project CharlieOS --mark-read
```

3. Claim work before you start:

```bash
python mission_control/wormhole.py claim --agent codex --project CharlieOS --task "Invoice architecture"
```

4. Emit short local notes when the other terminal agents should know something immediately:

```bash
python mission_control/wormhole.py emit \
  --sender codex \
  --project CharlieOS \
  --kind blocker \
  --summary "Need real invoice samples before locking extractor"
```

5. Release the claim when done:

```bash
python mission_control/wormhole.py release --agent codex --project CharlieOS
```

## Notes

- The first `watch` / `route` run bootstraps existing outbox files and does not replay the whole history into the local inbox.
- `preflight` still reads the durable outbox using the existing ACK rule, so the old protocol keeps working.
- This is intentionally stdlib-only Python so it is easy to carry into a sanitized public repo later.
