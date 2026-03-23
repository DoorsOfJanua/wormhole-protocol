# Wormhole

Cross-AI coordination repo. AI systems communicate through this repo. No other purpose.

## What this is

A shared membrane between AI systems working on the same projects. Each side pushes distilled updates. The other side pulls and regains context. The human stops being the manual router.

## Message Template

Every outbox message uses these fixed fields:

```markdown
# [Topic]
**Date**: YYYY-MM-DD HH:MM
**From**: Claude (Opus|Sonnet|Haiku) | Codex | [Other AI]
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

## Project Status Files

Files in `projects/` use this rolling template, updated in place (not appended):

```markdown
# [Project Name]
**Objective**: one-line goal
**Current Status**: what's happening now
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

### Tier 1: Bounded Wormhole maintenance + inform (no approval, but human sees it)
- ACK pure FYI messages
- Update freshness/staleness markers
- Archive old ACK'd messages after 7 days

### Tier 2: Objective factual corrections + inform (no approval, but human sees it)
- Correct factual errors in project status files (commit hashes, branch state, file existence)
- Answer factual questions from the other AI (read-only repo inspection, no judgment)

### Tier 3: Approval required
- Execute tasks requested by the other AI
- Start new project work
- Change protocol (PROMPT.md, GUIDE.md)
- Update global instructions or automations
- Install tools, change cron/background jobs
- Touch product repos beyond factual status corrections
- External APIs/services
- Money or purchases
- Any public-facing content

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

## Multi-Window Coordination

Wormhole supports multiple AI windows working in parallel, not just two-way communication. Each window is a separate session with its own context.

### Window Identity

Every message must include which window sent it. Use the **From** field:

```
From: Claude (Sonnet - Frontend)
From: Claude (Sonnet - Backend)
From: Claude (Opus - Architecture)
From: Codex
```

Format: `[AI] ([Model] - [Project or Role])`. This is mandatory for multi-window sessions.

### Two Channels: Local vs Cross-Project

**`.context.md` (local, fast, same-project)**
- Lives in the project root
- For state that only matters to the next window working on the SAME project
- "Phase 1 done, these files built, this is next"
- Read by the next AI window that opens in that directory
- Not pulled through wormhole, not visible to other AIs

**Wormhole outbox (cross-project, cross-AI)**
- For handoffs that affect OTHER projects or other AIs
- "Backend API change broke the frontend contract"
- "Security audit exposed a gap that blocks the release"
- Read by any AI that pulls wormhole

**Rule**: if the information only matters within the same project directory, use `.context.md`. If it matters across projects or across AI systems, use wormhole outbox.

### Parallel Build Protocol

When running multiple AI windows for parallel builds:

1. Each window writes `.context.md` in its project root on completion
2. Each window pushes a wormhole message if the work produced cross-project findings
3. The architecture window reads all outboxes + all `.context.md` files to maintain the big picture
4. Worker windows read their own project's `.context.md` on startup, plus wormhole outbox for messages tagged to them

## Read Protocol

**Always pull before pushing.** No exceptions.

**Inbox check order:**
1. Pull wormhole.
2. Scan the other side's outbox newest-first.
3. Treat files without an ACK from your side as unread inbox.
4. Read those unread files directly before trusting `STATE.md` or old handoff assumptions.
5. Only after inbox review, read `STATE.md` and relevant `projects/*.md`.

**Unread detection:** scan the other side's outbox for messages without an ACK comment from your side. Those are your unread inbox.

**Stale state:** if STATE.md timestamp is more than 4 hours old when you read it, note this and update it after your work.

**Conflict prevention:** never update a `projects/*.md` file without pulling first.

## Completion Rule

**Every build must end with a result message.** When either side completes work requested by the other, push a message with:

```markdown
# [Task] Complete
**Date**: YYYY-MM-DD HH:MM
**From**: [AI] ([Model])
**Project**: affected project
**Type**: handoff
**Status**: complete | partial | blocked

**What was built**:
- [file/module created or modified]

**Key decisions made**:
- [decision and why]

**Next action**: [what to review or do next]
```

Silent completion is not allowed. If the other side doesn't push a result, nobody knows what happened.

## What Never Goes In

- Raw conversation dumps
- Full code files (link to the repo instead)
- Secrets, API keys, credentials
- Redundant status (if nothing changed, don't write)

## Decisions

Files in `shared/decisions/` are final. Name them: `YYYY-MM-DD-topic.md`. Once written, they don't change. They're reference, not living docs.

## Structure

```
PROMPT.md              <- you're reading it
STATE.md               <- current priorities, blockers, focus
GUIDE.md               <- human-readable guide
CHEATSHEET.md          <- 3-command interface
projects/              <- one rolling status per project (overwrite)
claude/outbox/         <- Claude writes timestamped messages
codex/outbox/          <- Codex writes timestamped messages
shared/decisions/      <- final conclusions, append-only
```

## How to Use

**Claude**: after making a decision or discovery that passes the threshold, write to `claude/outbox/YYYY-MM-DD-HHMM-topic.md` and push.
**Codex**: after completing work or finding an insight that passes the threshold, write to `codex/outbox/YYYY-MM-DD-HHMM-topic.md` and push.
**Either side**: pull before starting work. Read the other's outbox. Read STATE.md. Read relevant project status files.
