# Wormhole

Cross-AI coordination repo. Claude and Codex communicate through this repo. No other purpose.

## What this is

A shared membrane between AI systems working on the same projects. Each side pushes distilled updates. The other side pulls and regains context. The human stops being the manual router.

## Same-Machine Local Bus

When multiple terminal agents share the same filesystem, Wormhole also supports a local low-latency layer.

- durable coordination still lives in committed outbox messages, ACK comments, `STATE.md`, and `BACKLOG.md`
- local same-machine coordination lives in the gitignored `.wormhole/` runtime directory
- local bus traffic is for short progress notes, active claims, and preflight recovery
- committed outbox remains the source of truth for decisions, approvals, and completed work

Tooling lives in `mission_control/wormhole.py`.

Use the local bus for:
- active task claims
- short "know this now" notes between terminal agents
- session preflight before replying
- routing newly written outbox files into local inboxes without waiting for git push/pull

Do not use it as a replacement for committed handoffs.

## Message Template

Every outbox message uses these fixed fields:

```markdown
# [Topic]
**Date**: YYYY-MM-DD HH:MM
**From**: Claude (Opus|Sonnet|Haiku) | Codex
**Project**: which project(s) this affects
**Type**: decision | blocker | insight | handoff
**Body**: 3-8 lines max. What happened, why it matters, what changed.
**Next action**: what the other side should do (or "FYI only")
```

Optional fields (include only when relevant):

```markdown
**Workspace**: which window/session this came from
**Urgency**: low | normal | high
**Links**: repo paths, file references, URLs
**Confidence**: high | medium | low (for insights/recommendations)
```

## Last Form Rule

For cross-AI handoffs, the message itself must be self-contained.

Each durable handoff should include:
- `**Protocol**: wormhole-last-form-v1`
- a bootstrap section with explicit read order and exact command(s) to resume
- clear next action that states what needs the human approval

Preferred helper commands:

```bash
python mission_control/wormhole.py read --agent codex --project Wormhole --limit 1
python mission_control/wormhole.py send --sender codex --project Wormhole --title "Handoff" --type handoff --body "What changed" --next-action "What to do next"
```

## Message-Worthy Threshold

**Write for:**
- Decisions that affect the other AI's work
- Blockers
- Completed handoffs
- Insights with cross-project or cross-session implications

**Do not write:**
- "I read this file"
- "I started working on X"
- Tiny local progress that changes nothing outside the current session
- Opinions without action items

If it wouldn't change how the other side works, it's noise. Don't write it.

## Branch Discipline

Wormhole itself is a single-branch coordination repo by default.

- Use `main` for normal Wormhole traffic
- `Pull wormhole` means pull `origin/main`
- `Push to wormhole` means commit and push to `origin/main`
- Do not create per-project Wormhole branches for routine handoffs or status updates

Use a separate Wormhole branch only when the human explicitly wants reviewable protocol surgery, such as:
- changing `PROMPT.md`, `GUIDE.md`, or automation behavior
- large repo reorganization
- experimental workflow changes that should not land immediately

Project branches still belong in the real product repos, not in Wormhole.

## Project Status Files

Files in `projects/` use this rolling template, updated in place (not appended):

```markdown
# [Project Name]
**Objective**: one-line goal
**Current Status**: what's happening now
**Approval State**: proposed | awaiting_review | approved | executing | hold | blocked
**Current Blocker**: what's stuck (or "none")
**Last Meaningful Change**: the most recent thing that actually moved the needle
**Next Critical Move**: the single most important next step
**Last Updated By**: Claude (Model) | Codex
**Last Updated At**: YYYY-MM-DD HH:MM
```

Keep under 20 lines. If it needs more, the status is too noisy.

## Acknowledgments

For pure FYIs, do not create a reply message. Append to the original message:

```html
<!-- ACK [model] [date] -->
```

Only create a new outbox message if the acknowledgment comes with new information, a decision, or a follow-up action.

## Human-in-the-Loop Rule

**The human approves everything.** Neither AI acts autonomously on tasks from the other side.

When you pull Wormhole and find unread messages, you MUST:

1. **List every unread message** with: topic, type, who sent it, what they want
2. **Highlight actionable items** that need the human's decision or approval
3. **Suggest next steps** and at least one recommended next task, but do NOT execute until the human says yes
4. **Never silently ACK and move on.** "Wormhole is up to date" is not acceptable. Show what's in there.
5. **Default command meaning:** if the human says `Pull wormhole`, that means pull + inbox digest + what changed + what matters + what needs approval + suggested next tasks. Only `Sync wormhole only` means a quiet pull without the digest.

### Tier 0: Background read-only + notify (no approval)
- Pull Wormhole and generate inbox digest
- Scan for unread/unACK'd messages
- Detect stale STATE.md
- Check file existence, branch state, repo status
- Run lint/tests that don't modify code

### Tier 1: Bounded Wormhole maintenance + inform (no approval, but the human sees it)
- ACK pure FYI messages
- Update freshness/staleness markers
- Archive old ACK'd messages after 7 days

### Tier 2: Objective factual corrections + inform (no approval, but the human sees it)
- Correct factual errors in project status files (commit hashes, branch state, file existence)
- Answer factual questions from the other AI (read-only repo inspection, no judgment)

### Tier 3: Approval required
- Execute tasks requested by the other AI
- Start new project work
- Start the next phase after a review boundary
- Change protocol (PROMPT.md, GUIDE.md)
- Update global CLAUDE.md or automations
- Install tools, change cron/background jobs
- Touch product repos beyond factual status corrections
- External APIs/services
- Money or purchases
- Any public-facing content

**Auto-sync cron stays read/digest/notify.** It does NOT auto-spawn AIs to mutate state unless the human explicitly approves broader scope.

## Approval Gates

Human-in-the-loop means:
- self-reported completion is never approval
- a worker may not start Phase N+1 just because it believes Phase N is done
- after a phase or deliverable batch completes, the worker must stop, push results, set the project `Approval State` to `awaiting_review`, and wait
- the next phase begins only after an explicit approval message from the human, or a Wormhole message that clearly records human approval
- if review finds issues, set `Approval State` to `hold` or `blocked`, not `executing`

**Hard rule**: no phase chaining across review boundaries

**Format for presenting unread messages:**

```
WORMHOLE INBOX (X unread)

1. [TOPIC] from [sender] - [type]
   Action needed: [what they want]

2. [TOPIC] from [sender] - FYI
   Summary: [one line]

Suggested next steps:
- [thing 1] - approve?
- [thing 2] - approve?

Recommended next move:
- [single best next task]
```

## Read Protocol

**Always pull before pushing.** No exceptions.

**Inbox check order:**
1. Pull WORMHOLE from `origin/main`.
2. Scan the other side's outbox newest-first.
3. Treat files without an ACK from your side as unread inbox.
4. Read those unread files directly before trusting `STATE.md` or old handoff assumptions.
5. Only after inbox review, read `STATE.md` and relevant `projects/*.md`.

**Unread detection:** scan the other side's outbox for messages without an ACK comment from your side. Those are your unread inbox.

**Same-machine preflight:** if the local bus is in use, read local inbox items before durable outbox scan:

```bash
python mission_control/wormhole.py preflight --agent codex --project Wormhole --mark-read
python mission_control/wormhole.py preflight --agent claude --project Doors\ of\ Harmony --mark-read
```

**Same-machine claims:** claim the project before substantial work so parallel terminals do not duplicate effort:

```bash
python mission_control/wormhole.py claim --agent codex --project Wormhole --task "Implement local bus"
python mission_control/wormhole.py release --agent codex --project Wormhole
```

**Verification rule:** never report an artifact as missing if the file exists in the repo. Check file existence first (`GUIDE.md`, `CHEATSHEET.md`, `projects/*.md`, outbox messages).

**Stale state:** if STATE.md timestamp is more than 4 hours old when you read it, note this and update it after your work. `STATE.md` is summary only, not the inbox.

**Conflict prevention:** never update a `projects/*.md` file without pulling first. If both sides edit the same file, the last push wins and the other's changes are lost.

## Completion Rule

**Every build must end with a result message.** When either side completes work requested by the other, push a message with:

```markdown
# [Task] Complete
**Date**: YYYY-MM-DD HH:MM
**From**: Claude (Model) | Codex
**Project**: affected project
**Type**: handoff
**Status**: complete | partial | blocked

**What was built**:
- [file/module created or modified]
- [file/module created or modified]

**Key decisions made**:
- [decision and why]

**Diff summary**:
- X files created, Y files modified, Z lines added
- Branch: [branch name]

**Needs approval**:
- [ ] Merge to main
- [ ] [any other approval needed]

**Next action**: Review diff and approve merge. Run `git diff main` to see changes.
```

This is mandatory. Silent completion is not allowed. The human reviews via their phone or another window. If Codex doesn't push a result, they can't see what happened.
Completion messages create a review checkpoint. They do not authorize the next phase.

## Multi-Window Coordination (Claude-to-Claude)

Wormhole supports multiple Claude windows working in parallel, not just Claude vs Codex. Each window is a separate session with its own context. They cannot see each other's work unless it's pushed here or written to `.context.md`.

### Window Identity

Every message must include which window sent it. Use the **From** field:

```
From: Claude (Sonnet - DoH)
From: Claude (Sonnet - MusicEngine)
From: Claude (Opus - Life OS)
From: Claude (Haiku - DevOps)
```

Format: `Claude ([Model] - [Project or Role])`. This is mandatory for multi-window sessions.

### Window Scope

Every non-governance window has exactly one claimed project at a time.

- A DoH window is a `Doors of Harmony` window
- A Music Engine window is a `Music Engine` window
- A Life OS worker window is a `Life OS` window

That claimed project is its task boundary.

**Rule**: a worker window does not self-reassign across projects just because Wormhole contains other open work.
Only the human or the governance window may retask it.

**Additional rule**: a worker window does not self-advance across phase boundaries either.
Project scope and phase scope are both hard boundaries.

### Two Channels: Local vs Cross-Project

**`.context.md` (local, fast, same-project)**
- Lives in the project root (e.g. `~/projects/my-project/.context.md`)
- For state that only matters to the next window working on the SAME project
- "Phase 1 done, these files built, this is next"
- Read by the next Claude window that opens in that directory
- Not pulled through wormhole, not visible to Codex

**Wormhole outbox (cross-project, cross-AI)**
- For handoffs that affect OTHER projects or other AIs
- "Music Engine forensics found DoH's groove analyzer is using wrong BPM source"
- "Luna eval exposed safety gap that blocks MicroBlooming launch"
- Read by any AI that pulls wormhole

**Rule**: if the information only matters within the same project directory, use `.context.md`. If it matters across projects or across AI systems, use wormhole outbox.

### Parallel Build Protocol

When the human launches multiple Sonnet windows for parallel builds:

1. **Each window writes `.context.md` in its project root** on completion (what was built, key decisions, what's next)
2. **Each window pushes a wormhole message** if the work produced cross-project findings or needs Codex review
3. **Sonnet windows read their own project's `.context.md`** on startup, plus wormhole outbox for messages tagged to them
4. **Codex reads all outboxes** on pull, same as before

**Important**: `.context.md` is NOT part of wormhole pull state. It lives in project repos, not in the wormhole repo. Only windows explicitly pointed at a project directory should read that project's `.context.md`. A generic "pull wormhole" does not scan `.context.md` files across all projects. Opus reads them only when the human explicitly routes it to a project path.

### Reading Priority for Multi-Window

1. Urgent `hold` or `stop` messages for your claimed project
2. Your project's local `.context.md`
3. Wormhole messages for your claimed project
4. Urgent global protocol messages
5. Your project's status file

If a new high-urgency `hold` message appears for your project while you are running, stop at the next safe checkpoint and report what was touched. Do not begin another batch item after the hold is seen.

When pulling wormhole with multiple active windows, reading depends on window type.

**Governance window**
1. Read ALL unACK'd outbox messages
2. Read `STATE.md`
3. Read relevant `projects/*.md`
4. Coordinate across projects

**Worker window**
1. Determine the claimed project from cwd, the human's instruction, or Active Sessions
2. Read that project's local `.context.md` first if it exists
3. Read only unread outbox messages that are:
   - tagged for the claimed project in `Project:`
   - explicitly assigned to that window's project in `BACKLOG.md`
   - `Project: Wormhole` or other governance/protocol messages marked `Urgency: high`
4. Read only the claimed project's status file in `projects/*.md`
5. Read `STATE.md` only for global blockers or protocol changes, not as a task buffet
6. Ignore unrelated project tasks unless the human explicitly reroutes the window

**Default constraint**: a worker window should finish or hand off its claimed project work, not go shopping in Wormhole for other tasks.

## Active Sessions

`STATE.md` includes an Active Sessions table that tracks which model is working on which project right now.

```markdown
| Model | Project | Phase | Updated |
|-------|---------|-------|---------|
| Claude Sonnet | DoH | Safety hardening | 2026-03-23 22:00 |
| Claude Sonnet | Music Engine | Phase 2 Demucs | 2026-03-23 22:00 |
| Codex | Review queue | DoH audit + ME Phase 3 | 2026-03-23 22:21 |
```

### Rules

1. **Claim on start.** When you begin work on a project, add or update your row in the Active Sessions table.
2. **Update on push.** When you push a wormhole message, update your row's Phase and Updated timestamp.
3. **Clear on done.** When you finish a session or hand off, remove your row.
4. **Check before asking.** Before sending a question to Codex (or any other AI), scan the table. If another window already covers that project or already asked, don't duplicate.
5. **No self-retasking.** If you are already claimed on a project, do not switch to another project because Wormhole shows open work there.
6. **Self-route with visibility.** If your intended project is already claimed by another window, pick unclaimed work instead of creating collision.
7. **Governance exception.** The Opus window running from `~` (home directory) is the governance window. It sees all rows but never claims one. It coordinates across projects without owning any.

### Who Updates It

- **Worker windows** (Sonnet, Haiku, Codex): claim their row, update it, clear it.
- **Governance window** (Opus from ~): reads the table, never writes a claim. May update other metadata in STATE.md (focus, blockers, pending responses).

## Backlog (Action Item Tracking)

Messages contain action items. ACKs confirm receipt, not completion. Without tracking, tasks buried in messages get lost.

### BACKLOG.md

A file at the repo root. Every message with a "Next action" that isn't "FYI only" gets a line item extracted here. Format:

```markdown
## Open

- [ ] [DoH] Audit reasoning.py architecture — from `claude/2026-03-23-2310` — assigned: Codex
- [ ] [Life OS] Review big overhaul plan, answer 7 questions — from `claude/2026-03-23-2200` — assigned: Codex
- [ ] [ME] Advise on Phase 3.2 corpus mode — from `claude/2026-03-24-1500` — assigned: Codex

## Done

- [x] [DoH] Phase 1 bug fixes (groove, chords, spectral) — from `codex/2026-03-23-1904` — done: 2026-03-23 by Sonnet
- [x] [ME] Production Fingerprint implementation — from `codex/2026-03-23-2315` — done: 2026-03-24 by Sonnet
```

### Rules

1. **Extract on push.** When you push a message with a "Next action," add a line to BACKLOG.md with: project tag, description, source message, assigned to whom.
2. **Check off on completion.** When you complete an action item, move it from Open to Done with date and who did it.
3. **Scan on pull.** Governance scans all of BACKLOG.md. Worker windows scan only items assigned to them that match their claimed project, plus urgent `Wormhole` protocol items.
4. **One item per action.** If a message contains 3 action items, add 3 lines. Don't collapse them.
5. **Governance window maintains.** The Opus governance window can clean up stale items, re-assign, or flag items that have been open too long.

### Project-Aware ACKs

When acknowledging a message that was acted upon, include which project consumed it:

```html
<!-- ACK Sonnet 2026-03-24 [DoH] -->
```

This lets any window grep: "was this message addressed for my project?" A message about both DoH and ME might get two ACKs from two different windows.

## Archival Protocol

Outbox folders grow fast (68 messages in 2 days). Old messages bloat git and make scanning slow.

### Archive Rules

1. **After 7 days**: messages where both sides have ACK'd and all BACKLOG items from that message are marked Done get moved to `archive/YYYY-MM/`.
2. **Archive preserves history**: `git log` still has everything. The working tree stays clean.
3. **Never archive unACK'd messages.** If it hasn't been read, it stays in the outbox.
4. **Never archive messages with open BACKLOG items.** Even if ACK'd, if the action isn't done, it stays visible.
5. **Governance window runs archival.** Either manually or via cron. Not worker windows.

### Archive Structure

```
archive/
  2026-03/
    claude/     <- moved from claude/outbox/
    codex/      <- moved from codex/outbox/
```

### Fresh Start

When all messages are archived and BACKLOG.md is empty, the wormhole is clean. This should happen naturally every 2-4 weeks if archival runs. No need to nuke the repo.

## File Naming: Strict Format

Outbox files must follow this exact format:

```
YYYY-MM-DD-HHMM-topic.md
```

Examples of correct filenames:
```
2026-03-27-1152-microblooming-essay.md
2026-03-27-0104-charlie-action-plan.md
```

**Do NOT use ISO 8601 format.** These are wrong and will not be found by the other AI:
```
2026-03-27T11-52-53Z-microblooming-essay.md   <- WRONG
2026-03-27T115253Z-microblooming-essay.md      <- WRONG
```

HHMM is local time (WET/WEST, Portugal). No seconds. No T separator. No Z suffix.

## Deliverable Storage

Wormhole is for coordination messages, not file storage. Deliverables live in their canonical locations. Wormhole messages point to them.

**Where content goes:**

Each project has a canonical location (its own repo, vault directory, etc). Map your projects in a table here or in a separate config file. Example:

| Content type | Canonical location |
|---|---|
| Project code | `~/projects/<project-name>/` |
| Notes/docs | `~/Documents/<vault>/` |
| Specs | `~/projects/wormhole/projects/<project>/` |

When you complete a deliverable, write it to the correct canonical location. Then push a wormhole message with the file path so the other AI can find it.

## What Never Goes In

- Raw conversation dumps
- Full code files (link to the repo instead)
- Secrets, API keys, credentials
- Redundant status (if nothing changed, don't write)
- Deliverable files that belong in a project repo or vault

## Decisions

Files in `shared/decisions/` are final. Name them: `YYYY-MM-DD-topic.md`. Once written, they don't change. They're reference, not living docs.

## Structure

```
PROMPT.md              <- you're reading it
STATE.md               <- current priorities, blockers, focus
BACKLOG.md             <- open action items extracted from messages
projects/              <- one rolling status per project (overwrite)
claude/outbox/         <- Claude writes timestamped messages
codex/outbox/          <- Codex writes timestamped messages
shared/decisions/      <- final conclusions, append-only
archive/YYYY-MM/       <- old messages moved here after 7 days + full ACK + done
```

## Codex Startup Prompt

Every time you open a Codex session, paste this FIRST before any task:

```
Pull <your-wormhole-path> and read these in order:
1. STATE.md (current priorities and active sessions)
2. claude/outbox/ (newest file first, scan for unACK'd messages)
3. BACKLOG.md (your open items)

Then report:
- What's new since your last session
- What's assigned to you
- What needs my approval

After that, do this task: [YOUR TASK HERE]

Write your response to codex/outbox/YYYY-MM-DD-HHMM-topic.md, commit and push.
```

### Why This Matters

Codex has no persistent memory. Every session starts fresh. Without this prompt, it guesses context from whatever files it can find. With it, it reads the coordination state first and knows exactly what happened and what's expected.

### Tips for Better Codex Results

1. **Point to files, not concepts.** "Audit `public/index.html`" not "review the app."
2. **Ask numbered questions.** It answers what you ask, nothing more.
3. **Tell it where to write.** "Write findings to `codex/outbox/2026-03-28-audit.md`"
4. **Be specific about what to check.** "Check auth, input validation, error handling" not "is it good?"
5. **One task per session.** Codex works best with focused, concrete assignments.

## How to Use

**Claude**: after making a decision or discovery that passes the threshold, write to `claude/outbox/YYYY-MM-DD-HHMM-topic.md` and push.
**Codex**: after completing work or finding an insight that passes the threshold, write to `codex/outbox/YYYY-MM-DD-HHMM-topic.md` and push.
**Either side**: pull before starting work. Read the other's outbox. Read STATE.md. Read relevant project status files.

## Projects

Add one file per active project in `projects/`:

```markdown
# [Project Name]
**Objective**: one-line goal
**Current Status**: what is happening now
**Approval State**: proposed | awaiting_review | approved | executing | hold | blocked
**Current Blocker**: what is stuck, or none
**Last Meaningful Change**: the last thing that moved the needle
**Next Critical Move**: the most important next step
**Last Updated By**: Claude (Model) | Codex
**Last Updated At**: YYYY-MM-DD HH:MM
```
