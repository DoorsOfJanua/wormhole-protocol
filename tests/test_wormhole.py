from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "mission_control" / "wormhole.py"
SPEC = importlib.util.spec_from_file_location("wormhole_local", MODULE_PATH)
wormhole = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(wormhole)


class WormholeLocalTests(unittest.TestCase):
    def test_parse_markdown_message(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            message_path = root / "claude" / "outbox" / "2026-03-29-test.md"
            message_path.parent.mkdir(parents=True, exist_ok=True)
            message_path.write_text(
                "\n".join(
                    [
                        "# Test Title",
                        "**Date**: 2026-03-29 21:00",
                        "**From**: Claude (Opus)",
                        "**Project**: Wormhole",
                        "**Type**: handoff",
                        "**Body**: Short summary",
                        "**Next action**: FYI only",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            parsed = wormhole.parse_message(message_path)
            self.assertEqual(parsed["title"], "Test Title")
            self.assertEqual(parsed["project"], "Wormhole")
            self.assertEqual(parsed["summary"], "Short summary")

    def test_parse_raw_multiline_message(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            message_path = root / "codex" / "outbox" / "2026-03-29-test.md"
            message_path.parent.mkdir(parents=True, exist_ok=True)
            message_path.write_text(
                "\n".join(
                    [
                        "Date: 2026-03-29 21:00",
                        "From: Codex",
                        "Project: Wormhole",
                        "Type: decision",
                        "Body:",
                        "Reviewed the daemon plan and narrowed scope.",
                        "",
                        "Next_action:",
                        "- Build the local bus first.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            parsed = wormhole.parse_message(message_path)
            self.assertIn("Reviewed the daemon plan", parsed["summary"])
            self.assertIn("Build the local bus first", parsed["next_action"])

    def test_emit_creates_inbox_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            event = wormhole.emit_event(
                root=root,
                sender="codex",
                recipients=["claude", "gemini"],
                project="Wormhole",
                kind="progress",
                summary="Bus live",
            )
            self.assertEqual(event["sender"], "codex")
            claude_items = list((root / ".wormhole" / "inbox" / "claude" / "new").glob("*.json"))
            gemini_items = list((root / ".wormhole" / "inbox" / "gemini" / "new").glob("*.json"))
            self.assertEqual(len(claude_items), 1)
            self.assertEqual(len(gemini_items), 1)
            payload = json.loads(claude_items[0].read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"], "Bus live")

    def test_route_bootstraps_then_routes_new_outbox_files(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            first = root / "claude" / "outbox" / "2026-03-29-old.md"
            first.parent.mkdir(parents=True, exist_ok=True)
            first.write_text(
                "# Old\n**From**: Claude\n**Project**: Wormhole\n**Type**: handoff\n**Body**: Old\n",
                encoding="utf-8",
            )
            routed = wormhole.route_outboxes(root)
            self.assertEqual(routed, [])

            second = root / "claude" / "outbox" / "2026-03-29-new.md"
            second.write_text(
                "# New\n**From**: Claude\n**Project**: Wormhole\n**Type**: handoff\n**Body**: New\n",
                encoding="utf-8",
            )
            routed = wormhole.route_outboxes(root)
            self.assertEqual(len(routed), 1)
            claude_inbox = list((root / ".wormhole" / "inbox" / "codex" / "new").glob("*.json"))
            self.assertEqual(len(claude_inbox), 1)

    def test_claim_detects_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            wormhole.ensure_runtime(root)
            path = wormhole.claim_path(root, "Wormhole")
            wormhole.write_json(
                path,
                {
                    "project": "Wormhole",
                    "owner": "claude",
                    "task": "Existing",
                    "ttl_minutes": 120,
                    "touched_at": wormhole.iso_now(),
                },
            )
            claims = wormhole.active_claims(root)
            self.assertEqual(len(claims), 1)
            self.assertEqual(claims[0]["owner"], "claude")

    def test_compose_last_form_message_includes_bootstrap(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            (root / "projects").mkdir(parents=True, exist_ok=True)
            (root / "projects" / "wormhole.md").write_text("# Wormhole\n", encoding="utf-8")
            message = wormhole.compose_last_form_message(
                root=root,
                sender="codex",
                recipients=["claude"],
                project="Wormhole",
                title="Protocol Upgrade",
                kind="handoff",
                body="Upgraded messaging.",
                next_action="Review and confirm.",
            )
            self.assertIn("**Protocol**: wormhole-last-form-v1", message)
            self.assertIn("## Wormhole Bootstrap (Self-Contained)", message)
            self.assertIn("mission_control/wormhole.py preflight", message)

    def test_write_outbox_message_uses_timestamped_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            destination = wormhole.write_outbox_message(
                root=root,
                sender="codex",
                title="My Test Title",
                content="# Hello\n",
            )
            self.assertTrue(destination.exists())
            self.assertTrue(destination.name.endswith("-my-test-title.md"))
            self.assertIn("/codex/outbox/", str(destination))


if __name__ == "__main__":
    unittest.main()
