#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


KNOWN_AGENTS = ("claude", "codex", "gemini")
OUTBOX_OWNERS = {
    "claude": "claude",
    "codex": "codex",
}
LAST_FORM_PROTOCOL = "wormhole-last-form-v1"

MARKDOWN_FIELD_RE = re.compile(r"^\*\*(?P<key>[^*]+)\*\*:\s*(?P<value>.*)$")
RAW_FIELD_RE = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9_ /().-]*):\s*(?P<value>.*)$")
TITLE_RE = re.compile(r"^#\s+(?P<title>.+?)\s*$")
ACK_RE = {
    "claude": re.compile(r"<!--\s*ACK\s+Claude\b", re.IGNORECASE),
    "codex": re.compile(r"<!--\s*ACK\s+Codex\b", re.IGNORECASE),
    "gemini": re.compile(r"<!--\s*ACK\s+Gemini\b", re.IGNORECASE),
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def runtime_root(root: Path) -> Path:
    return root / ".wormhole"


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def human_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def message_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def filename_now() -> str:
    return datetime.now().strftime("%Y-%m-%d-%H%M")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


def ensure_runtime(root: Path) -> dict[str, Path]:
    runtime = runtime_root(root)
    paths = {
        "runtime": runtime,
        "events": runtime / "events",
        "inbox": runtime / "inbox",
        "claims": runtime / "claims",
        "state": runtime / "state",
        "digests": runtime / "digests",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    for agent in KNOWN_AGENTS:
        (paths["inbox"] / agent / "new").mkdir(parents=True, exist_ok=True)
        (paths["inbox"] / agent / "read").mkdir(parents=True, exist_ok=True)
    return paths


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def normalize_key(value: str) -> str:
    key = value.strip().lower()
    key = key.replace(" ", "_")
    key = key.replace("/", "_")
    key = key.replace("-", "_")
    return key


def looks_like_field(line: str) -> bool:
    return bool(MARKDOWN_FIELD_RE.match(line) or RAW_FIELD_RE.match(line))


def extract_multiline_value(lines: list[str], start_index: int) -> tuple[str, int]:
    value_lines: list[str] = []
    index = start_index + 1
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped.startswith("<!--"):
            break
        if looks_like_field(line):
            break
        if value_lines and not stripped:
            break
        if stripped:
            value_lines.append(stripped)
        index += 1
    return " ".join(value_lines).strip(), index


def parse_message(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = path.stem
    for line in lines:
        match = TITLE_RE.match(line.strip())
        if match:
            title = match.group("title").strip()
            break

    fields: dict[str, str] = {}
    index = 0
    while index < len(lines):
        raw_line = lines[index]
        line = raw_line.strip()
        field_match = MARKDOWN_FIELD_RE.match(line)
        if field_match:
            key = normalize_key(field_match.group("key"))
            value = field_match.group("value").strip()
            if not value and key in {"body", "next_action"}:
                value, index = extract_multiline_value(lines, index)
            fields.setdefault(key, value)
            index += 1
            continue
        field_match = RAW_FIELD_RE.match(raw_line)
        if field_match:
            key = normalize_key(field_match.group("key"))
            value = field_match.group("value").strip()
            if not value and key in {"body", "next_action"}:
                value, index = extract_multiline_value(lines, index)
            fields.setdefault(key, value)
        index += 1

    sender = fields.get("from", "").strip() or infer_sender_from_path(path)
    try:
        relative_path = str(path.relative_to(repo_root()))
    except ValueError:
        relative_path = str(path)
    return {
        "id": path.stem,
        "title": title,
        "date": fields.get("date", ""),
        "sender": sender,
        "project": fields.get("project", ""),
        "type": fields.get("type", ""),
        "urgency": fields.get("urgency", ""),
        "summary": fields.get("body", ""),
        "next_action": fields.get("next_action", ""),
        "path": str(path),
        "relative_path": relative_path,
    }


def infer_sender_from_path(path: Path) -> str:
    parts = path.parts
    for owner in OUTBOX_OWNERS:
        if owner in parts:
            return owner.title()
    return "unknown"


def canonical_agent(value: str) -> str:
    lowered = value.strip().lower()
    if "claude" in lowered:
        return "claude"
    if "codex" in lowered:
        return "codex"
    if "gemini" in lowered:
        return "gemini"
    return lowered


def recipients_for_sender(sender: str, explicit: list[str] | None = None) -> list[str]:
    if explicit:
        recipients = [canonical_agent(item) for item in explicit]
        if "all" in recipients:
            sender_agent = canonical_agent(sender)
            return [agent for agent in KNOWN_AGENTS if agent != sender_agent]
        return [agent for agent in recipients if agent in KNOWN_AGENTS]
    sender_agent = canonical_agent(sender)
    return [agent for agent in KNOWN_AGENTS if agent != sender_agent]


def deliver_to_inbox(root: Path, recipient: str, event: dict[str, Any]) -> Path:
    paths = ensure_runtime(root)
    inbox_dir = paths["inbox"] / recipient / "new"
    filename = f"{event['created_at'].replace(':', '').replace('-', '')}-{event['id']}.json"
    destination = inbox_dir / filename
    write_json(destination, event)
    return destination


def emit_event(
    root: Path,
    sender: str,
    recipients: list[str],
    project: str,
    kind: str,
    summary: str,
    body: str = "",
    urgency: str = "normal",
    source: str = "session",
    workspace: str = "",
    related_path: str = "",
) -> dict[str, Any]:
    paths = ensure_runtime(root)
    event = {
        "id": uuid.uuid4().hex[:12],
        "created_at": iso_now(),
        "sender": canonical_agent(sender),
        "recipients": recipients,
        "project": project,
        "kind": kind,
        "summary": summary,
        "body": body,
        "urgency": urgency,
        "source": source,
        "workspace": workspace,
        "related_path": related_path,
    }
    append_jsonl(paths["events"] / "events.jsonl", event)
    for recipient in recipients:
        deliver_to_inbox(root, recipient, event)
    return event


def list_inbox_items(root: Path, agent: str, project: str | None = None) -> list[tuple[Path, dict[str, Any]]]:
    paths = ensure_runtime(root)
    inbox_dir = paths["inbox"] / canonical_agent(agent) / "new"
    items: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(inbox_dir.glob("*.json"), reverse=True):
        payload = load_json(path, {})
        if project and not project_matches(payload.get("project", ""), project):
            continue
        items.append((path, payload))
    return items


def mark_inbox_read(root: Path, agent: str, items: list[tuple[Path, dict[str, Any]]]) -> None:
    paths = ensure_runtime(root)
    destination_dir = paths["inbox"] / canonical_agent(agent) / "read"
    for source, _payload in items:
        source.rename(destination_dir / source.name)


def project_matches(value: str, needle: str) -> bool:
    return needle.lower() in value.lower()


def active_claims(root: Path, include_stale: bool = False) -> list[dict[str, Any]]:
    paths = ensure_runtime(root)
    claims: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)
    for path in sorted(paths["claims"].glob("*.json")):
        payload = load_json(path, {})
        touched_at = payload.get("touched_at")
        ttl_minutes = int(payload.get("ttl_minutes", 120))
        stale = False
        if touched_at:
            touched = datetime.fromisoformat(touched_at)
            stale = touched + timedelta(minutes=ttl_minutes) < now
        payload["stale"] = stale
        payload["path"] = str(path)
        if not stale or include_stale:
            claims.append(payload)
    claims.sort(key=lambda item: item.get("touched_at", ""), reverse=True)
    return claims


def claim_path(root: Path, project: str) -> Path:
    paths = ensure_runtime(root)
    return paths["claims"] / f"{slugify(project)}.json"


def read_route_index(root: Path) -> dict[str, Any]:
    paths = ensure_runtime(root)
    return load_json(paths["state"] / "routed_outbox.json", {"bootstrapped": False, "seen": {}})


def write_route_index(root: Path, payload: dict[str, Any]) -> None:
    paths = ensure_runtime(root)
    write_json(paths["state"] / "routed_outbox.json", payload)


def outbox_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for owner in OUTBOX_OWNERS:
        files.extend(sorted((root / owner / "outbox").glob("*.md")))
    return sorted(files)


def route_outboxes(root: Path) -> list[dict[str, Any]]:
    index = read_route_index(root)
    seen: dict[str, dict[str, str]] = index.get("seen", {})
    current_files = outbox_files(root)
    if not index.get("bootstrapped"):
        for path in current_files:
            relative = str(path.relative_to(root))
            seen[relative] = {"seen_at": iso_now()}
        write_route_index(root, {"bootstrapped": True, "seen": seen})
        return []

    routed: list[dict[str, Any]] = []
    for path in current_files:
        relative = str(path.relative_to(root))
        if relative in seen:
            continue
        message = parse_message(path)
        sender = canonical_agent(message.get("sender", infer_sender_from_path(path)))
        recipients = recipients_for_sender(sender)
        summary = message["summary"] or message["title"]
        event = emit_event(
            root=root,
            sender=sender,
            recipients=recipients,
            project=message.get("project", ""),
            kind=f"outbox:{message.get('type', 'message') or 'message'}",
            summary=summary,
            body=message.get("title", ""),
            urgency=message.get("urgency", "") or "normal",
            source="wormhole_outbox",
            related_path=relative,
        )
        seen[relative] = {"seen_at": iso_now()}
        routed.append(event)
    write_route_index(root, {"bootstrapped": True, "seen": seen})
    return routed


def unread_outbox_messages(root: Path, agent: str, project: str | None = None) -> list[dict[str, Any]]:
    agent_key = canonical_agent(agent)
    source_files: list[Path] = []
    if agent_key in OUTBOX_OWNERS:
        for owner in OUTBOX_OWNERS:
            if owner != agent_key:
                source_files.extend((root / owner / "outbox").glob("*.md"))
    else:
        for owner in OUTBOX_OWNERS:
            source_files.extend((root / owner / "outbox").glob("*.md"))

    messages: list[dict[str, Any]] = []
    ack_pattern = ACK_RE.get(agent_key)
    for path in sorted(source_files, reverse=True):
        text = path.read_text(encoding="utf-8")
        if ack_pattern and ack_pattern.search(text):
            continue
        message = parse_message(path)
        if project and not project_matches(message.get("project", ""), project):
            continue
        messages.append(message)
    return messages


def candidate_project_paths(root: Path, project: str) -> list[Path]:
    projects_dir = root / "projects"
    if not projects_dir.exists():
        return []
    needle = slugify(project)
    matches = sorted(projects_dir.glob("*.md"))
    ranked = sorted(
        matches,
        key=lambda path: (needle not in slugify(path.stem), len(path.stem)),
    )
    return ranked[:2]


def compose_last_form_message(
    root: Path,
    sender: str,
    recipients: list[str],
    project: str,
    title: str,
    kind: str,
    body: str,
    next_action: str,
    workspace: str = "",
    urgency: str = "normal",
    links: list[str] | None = None,
    confidence: str = "",
    status: str = "",
) -> str:
    project_paths = candidate_project_paths(root, project)
    read_targets = ["STATE.md", "BACKLOG.md"] + [str(path.relative_to(root)) for path in project_paths]
    links = links or []
    merged_links = read_targets + links
    deduped_links: list[str] = []
    for item in merged_links:
        clean = item.strip()
        if clean and clean not in deduped_links:
            deduped_links.append(clean)

    lines = [
        f"# {title}",
        f"**Date**: {message_now()}",
        f"**From**: {sender.title()}",
        f"**To**: {', '.join(recipients)}",
        f"**Project**: {project}",
        f"**Type**: {kind}",
        f"**Protocol**: {LAST_FORM_PROTOCOL}",
        f"**Body**: {body}",
        f"**Next action**: {next_action}",
    ]
    if status:
        lines.append(f"**Status**: {status}")
    if workspace:
        lines.append(f"**Workspace**: {workspace}")
    lines.append(f"**Urgency**: {urgency}")
    if deduped_links:
        lines.append(f"**Links**: {', '.join(deduped_links)}")
    if confidence:
        lines.append(f"**Confidence**: {confidence}")

    lines.extend(
        [
            "",
            "## Wormhole Bootstrap (Self-Contained)",
            "If you are reading this, run this protocol exactly:",
            f"1. Run preflight: `python mission_control/wormhole.py preflight --agent <your_agent> --project \"{project}\" --mark-read`",
            "2. Read this message fully before using STATE.md summaries.",
            "3. Read supporting context in this order:",
        ]
    )
    for target in read_targets:
        lines.append(f"   - {target}")
    lines.extend(
        [
            "4. If this message includes explicit approvals/holds, obey them before new execution.",
            "5. Reply with a durable outbox message using:",
            f"   `python mission_control/wormhole.py send --sender <your_agent> --project \"{project}\" --type handoff --title \"Reply: {title}\" --body \"<what changed>\" --next-action \"<what the human should approve next>\"`",
            "",
            "This message is designed to be enough context for cold-start recovery.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outbox_message(
    root: Path,
    sender: str,
    title: str,
    content: str,
) -> Path:
    sender_key = canonical_agent(sender)
    owner = OUTBOX_OWNERS.get(sender_key)
    if not owner:
        raise ValueError(f"Sender '{sender}' does not have a durable outbox.")
    destination_dir = root / owner / "outbox"
    destination_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{filename_now()}-{slugify(title)}.md"
    destination = destination_dir / filename
    destination.write_text(content, encoding="utf-8")
    return destination


def build_read_prompt(agent: str, message: dict[str, Any]) -> str:
    target_agent = canonical_agent(agent)
    return (
        f"WORMHOLE READ PROMPT ({target_agent})\n\n"
        "You are resuming work via Wormhole.\n"
        "1. Read this outbox file first:\n"
        f"   - {message.get('relative_path', message.get('path', ''))}\n"
        "2. Execute the \"Wormhole Bootstrap (Self-Contained)\" section inside that message exactly.\n"
        "3. Report inbox digest + action items that require human approval before execution.\n"
        "4. If a reply is needed, write it via `python mission_control/wormhole.py send ...`.\n"
    )


def recent_events(root: Path, limit: int = 10, project: str | None = None) -> list[dict[str, Any]]:
    paths = ensure_runtime(root)
    events = load_jsonl(paths["events"] / "events.jsonl")
    if project:
        events = [event for event in events if project_matches(event.get("project", ""), project)]
    return list(reversed(events[-limit:]))


def write_digest(
    root: Path,
    agent: str,
    inbox_items: list[tuple[Path, dict[str, Any]]],
    unread_messages: list[dict[str, Any]],
    claims: list[dict[str, Any]],
) -> Path:
    paths = ensure_runtime(root)
    lines = [
        f"# Wormhole Local Digest ({agent})",
        f"Generated: {human_now()}",
        "",
        f"## Local Bus ({len(inbox_items)} new)",
    ]
    if inbox_items:
        for _path, item in inbox_items:
            lines.append(
                f"- [{item.get('kind', 'event')}] from {item.get('sender', 'unknown')} "
                f"on {item.get('project', 'unknown')}: {item.get('summary', '')}"
            )
    else:
        lines.append("- none")

    lines.extend(["", f"## Durable Outbox ({len(unread_messages)} unread)"])
    if unread_messages:
        for message in unread_messages[:20]:
            lines.append(
                f"- [{message.get('type', 'message')}] {message.get('title', '')} "
                f"from {message.get('sender', '')} ({message.get('relative_path', '')})"
            )
    else:
        lines.append("- none")

    lines.extend(["", f"## Active Claims ({len(claims)})"])
    if claims:
        for claim in claims:
            lines.append(
                f"- {claim.get('project', '')}: {claim.get('owner', '')} -> {claim.get('task', '')}"
            )
    else:
        lines.append("- none")

    destination = paths["digests"] / f"{canonical_agent(agent)}.md"
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def print_preflight(
    agent: str,
    inbox_items: list[tuple[Path, dict[str, Any]]],
    unread_messages: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    digest_path: Path,
) -> None:
    print(f"LOCAL BUS ({len(inbox_items)} new)")
    if inbox_items:
        for index, (_path, item) in enumerate(inbox_items, start=1):
            print(
                f"{index}. [{item.get('kind', 'event')}] from {item.get('sender', 'unknown')} "
                f"- {item.get('project', 'unknown')}"
            )
            print(f"   Summary: {item.get('summary', '')}")
    else:
        print("0. No new local bus items.")

    print()
    print(f"DURABLE OUTBOX ({len(unread_messages)} unread for {canonical_agent(agent)})")
    if unread_messages:
        for index, message in enumerate(unread_messages[:10], start=1):
            print(
                f"{index}. [{message.get('type', 'message')}] {message.get('title', '')} "
                f"from {message.get('sender', '')}"
            )
            print(f"   Action: {message.get('next_action', '') or 'FYI only'}")
    else:
        print("0. No unread durable outbox messages.")

    print()
    print(f"ACTIVE CLAIMS ({len(claims)})")
    if claims:
        for claim in claims:
            suffix = " (stale)" if claim.get("stale") else ""
            print(f"- {claim.get('project', '')}: {claim.get('owner', '')} -> {claim.get('task', '')}{suffix}")
    else:
        print("- none")

    print()
    print(f"Digest: {digest_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local same-machine coordination tools for Wormhole.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    emit_parser = subparsers.add_parser("emit", help="Append a local bus event and fan it out to recipients.")
    emit_parser.add_argument("--sender", required=True)
    emit_parser.add_argument("--project", required=True)
    emit_parser.add_argument("--kind", required=True)
    emit_parser.add_argument("--summary", required=True)
    emit_parser.add_argument("--body", default="")
    emit_parser.add_argument("--urgency", default="normal")
    emit_parser.add_argument("--workspace", default="")
    emit_parser.add_argument("--to", nargs="*", default=[])
    emit_parser.set_defaults(func=command_emit)

    claim_parser = subparsers.add_parser("claim", help="Claim a project/task so other agents can see active ownership.")
    claim_parser.add_argument("--agent", required=True)
    claim_parser.add_argument("--project", required=True)
    claim_parser.add_argument("--task", required=True)
    claim_parser.add_argument("--workspace", default="")
    claim_parser.add_argument("--ttl-minutes", type=int, default=120)
    claim_parser.add_argument("--force", action="store_true")
    claim_parser.set_defaults(func=command_claim)

    release_parser = subparsers.add_parser("release", help="Release an active claim.")
    release_parser.add_argument("--agent", required=True)
    release_parser.add_argument("--project", required=True)
    release_parser.add_argument("--summary", default="")
    release_parser.set_defaults(func=command_release)

    preflight_parser = subparsers.add_parser("preflight", help="Show local bus items, durable outbox unread items, and active claims.")
    preflight_parser.add_argument("--agent", required=True)
    preflight_parser.add_argument("--project")
    preflight_parser.add_argument("--mark-read", action="store_true")
    preflight_parser.set_defaults(func=command_preflight)

    status_parser = subparsers.add_parser("status", help="Show active claims, recent events, and inbox counts.")
    status_parser.add_argument("--project")
    status_parser.add_argument("--recent", type=int, default=10)
    status_parser.set_defaults(func=command_status)

    route_parser = subparsers.add_parser("route", help="Route new outbox files into the local bus.")
    route_parser.set_defaults(func=command_route)

    watch_parser = subparsers.add_parser("watch", help="Poll for new outbox files and route them into the local bus.")
    watch_parser.add_argument("--interval", type=float, default=2.0)
    watch_parser.add_argument("--once", action="store_true")
    watch_parser.set_defaults(func=command_watch)

    daemon_parser = subparsers.add_parser("daemon", help="Alias for watch loop so Wormhole can run as a simple daemon.")
    daemon_parser.add_argument("--interval", type=float, default=2.0)
    daemon_parser.add_argument("--once", action="store_true")
    daemon_parser.set_defaults(func=command_daemon)

    send_parser = subparsers.add_parser("send", help="Write a durable self-contained outbox message.")
    send_parser.add_argument("--sender", required=True)
    send_parser.add_argument("--project", required=True)
    send_parser.add_argument("--title", required=True)
    send_parser.add_argument("--type", default="handoff")
    send_parser.add_argument("--body", default="No additional details provided.")
    send_parser.add_argument("--next-action", default="Review and respond via Wormhole.")
    send_parser.add_argument("--workspace", default="")
    send_parser.add_argument("--urgency", default="normal")
    send_parser.add_argument("--links", nargs="*", default=[])
    send_parser.add_argument("--confidence", default="")
    send_parser.add_argument("--status", default="")
    send_parser.add_argument("--to", nargs="*", default=[])
    send_parser.set_defaults(func=command_send)

    read_parser = subparsers.add_parser("read", help="Print unread Wormhole messages and a ready-to-use read prompt.")
    read_parser.add_argument("--agent", required=True)
    read_parser.add_argument("--project")
    read_parser.add_argument("--limit", type=int, default=1)
    read_parser.add_argument("--full", action="store_true")
    read_parser.set_defaults(func=command_read)

    return parser


def command_emit(args: argparse.Namespace) -> int:
    root = repo_root()
    recipients = recipients_for_sender(args.sender, args.to)
    event = emit_event(
        root=root,
        sender=args.sender,
        recipients=recipients,
        project=args.project,
        kind=args.kind,
        summary=args.summary,
        body=args.body,
        urgency=args.urgency,
        workspace=args.workspace,
    )
    print(json.dumps(event, indent=2, sort_keys=True))
    return 0


def command_claim(args: argparse.Namespace) -> int:
    root = repo_root()
    path = claim_path(root, args.project)
    existing = load_json(path, {})
    if existing and existing.get("owner") != canonical_agent(args.agent):
        claims = active_claims(root, include_stale=True)
        active_by_path = {claim.get("path"): claim for claim in claims}
        current = active_by_path.get(str(path), {})
        if current and not current.get("stale") and not args.force:
            print(
                f"Claim conflict: {args.project} is owned by {current.get('owner')} "
                f"for '{current.get('task')}'. Use --force to override.",
                file=sys.stderr,
            )
            return 1

    payload = {
        "project": args.project,
        "project_slug": slugify(args.project),
        "owner": canonical_agent(args.agent),
        "task": args.task,
        "workspace": args.workspace,
        "ttl_minutes": args.ttl_minutes,
        "touched_at": iso_now(),
    }
    write_json(path, payload)
    emit_event(
        root=root,
        sender=args.agent,
        recipients=recipients_for_sender(args.agent),
        project=args.project,
        kind="claim",
        summary=f"Claimed {args.project}: {args.task}",
        body=args.workspace,
        urgency="normal",
        source="claim",
        workspace=args.workspace,
        related_path=str(path.relative_to(root)),
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_release(args: argparse.Namespace) -> int:
    root = repo_root()
    path = claim_path(root, args.project)
    payload = load_json(path, {})
    if not payload:
        print(f"No claim found for {args.project}.", file=sys.stderr)
        return 1
    if payload.get("owner") != canonical_agent(args.agent):
        print(
            f"Cannot release {args.project}: owned by {payload.get('owner')}, not {canonical_agent(args.agent)}.",
            file=sys.stderr,
        )
        return 1
    path.unlink()
    emit_event(
        root=root,
        sender=args.agent,
        recipients=recipients_for_sender(args.agent),
        project=args.project,
        kind="release",
        summary=args.summary or f"Released claim on {args.project}",
        urgency="normal",
        source="claim",
    )
    print(f"Released {args.project}")
    return 0


def command_preflight(args: argparse.Namespace) -> int:
    root = repo_root()
    route_outboxes(root)
    inbox_items = list_inbox_items(root, args.agent, args.project)
    unread_messages = unread_outbox_messages(root, args.agent, args.project)
    claims = [
        claim
        for claim in active_claims(root)
        if not args.project or project_matches(claim.get("project", ""), args.project)
    ]
    digest_path = write_digest(root, args.agent, inbox_items, unread_messages, claims)
    print_preflight(args.agent, inbox_items, unread_messages, claims, digest_path)
    if args.mark_read and inbox_items:
        mark_inbox_read(root, args.agent, inbox_items)
    return 0


def command_status(args: argparse.Namespace) -> int:
    root = repo_root()
    route_outboxes(root)
    claims = [
        claim
        for claim in active_claims(root, include_stale=True)
        if not args.project or project_matches(claim.get("project", ""), args.project)
    ]
    events = recent_events(root, limit=args.recent, project=args.project)
    print(f"Status generated at {human_now()}")
    print()
    print(f"Active claims: {len(claims)}")
    for claim in claims:
        suffix = " (stale)" if claim.get("stale") else ""
        print(f"- {claim.get('project', '')}: {claim.get('owner', '')} -> {claim.get('task', '')}{suffix}")
    print()
    print(f"Recent events: {len(events)}")
    for event in events:
        print(
            f"- [{event.get('kind', 'event')}] {event.get('sender', '')} "
            f"on {event.get('project', '')}: {event.get('summary', '')}"
        )
    print()
    for agent in KNOWN_AGENTS:
        inbox_count = len(list_inbox_items(root, agent, args.project))
        print(f"{agent}: {inbox_count} new local bus items")
    return 0


def command_route(args: argparse.Namespace) -> int:
    root = repo_root()
    routed = route_outboxes(root)
    print(f"Routed {len(routed)} new outbox message(s).")
    return 0


def command_watch(args: argparse.Namespace) -> int:
    root = repo_root()
    print(f"Wormhole watch loop running from {root}")
    while True:
        routed = route_outboxes(root)
        if routed:
            print(f"{human_now()} routed {len(routed)} new outbox message(s).")
        if args.once:
            return 0
        time.sleep(args.interval)


def command_daemon(args: argparse.Namespace) -> int:
    return command_watch(args)


def command_send(args: argparse.Namespace) -> int:
    root = repo_root()
    sender = canonical_agent(args.sender)
    recipients = recipients_for_sender(sender, args.to)
    if not recipients:
        print("No valid recipients resolved for durable send.", file=sys.stderr)
        return 1
    try:
        content = compose_last_form_message(
            root=root,
            sender=sender,
            recipients=recipients,
            project=args.project,
            title=args.title.strip(),
            kind=args.type.strip() or "handoff",
            body=args.body.strip() or "No additional details provided.",
            next_action=args.next_action.strip() or "Review and respond via Wormhole.",
            workspace=args.workspace.strip(),
            urgency=args.urgency.strip() or "normal",
            links=args.links,
            confidence=args.confidence.strip(),
            status=args.status.strip(),
        )
        destination = write_outbox_message(root, sender, args.title, content)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    route_outboxes(root)
    print(f"Wrote: {destination}")
    print(f"Protocol: {LAST_FORM_PROTOCOL}")
    return 0


def command_read(args: argparse.Namespace) -> int:
    root = repo_root()
    route_outboxes(root)
    unread = unread_outbox_messages(root, args.agent, args.project)
    if not unread:
        print(f"No unread durable outbox messages for {canonical_agent(args.agent)}.")
        return 0

    limit = max(1, args.limit)
    selected = unread[:limit]
    print(f"WORMHOLE INBOX ({len(unread)} unread, showing {len(selected)})")
    print()
    for index, message in enumerate(selected, start=1):
        print(
            f"{index}. [{message.get('type', 'message')}] {message.get('title', '')} "
            f"from {message.get('sender', '')}"
        )
        print(f"   Project: {message.get('project', '')}")
        print(f"   Path: {message.get('relative_path', message.get('path', ''))}")
        action = message.get("next_action", "").strip() or "FYI only"
        print(f"   Next action: {action}")
        print()
        print(build_read_prompt(args.agent, message))
        if args.full:
            path = Path(message.get("path", ""))
            if path.exists():
                print("--- MESSAGE START ---")
                print(path.read_text(encoding="utf-8").rstrip())
                print("--- MESSAGE END ---")
                print()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
