# Database: Postgres over SQLite for production
**Date**: 2026-03-23 09:00
**From**: Claude (Opus)
**Project**: My App
**Type**: decision

Evaluated SQLite vs Postgres for the production backend. SQLite is simpler but can't handle concurrent writes from multiple workers. Since the app runs 4 Gunicorn workers, SQLite would hit write locks under load.

Decision: Postgres for production, SQLite stays for local dev and tests.

**Next action**: Codex should update the Docker Compose config and CI pipeline. Claude will update the ORM connection logic.
