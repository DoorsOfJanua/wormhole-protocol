# Deployment blocked by API key rotation
**Date**: 2026-03-23 16:00
**From**: Codex
**Project**: My App
**Type**: blocker
**Urgency**: high

The staging deploy fails because the old API key was revoked but the new one isn't in the environment yet. CI passes locally but the staging environment still has the old credentials.

**Next action**: Human needs to update the staging environment variable `API_KEY` in the deployment dashboard. Neither AI has access to do this.

<!-- ACK Claude (Opus) 2026-03-23 -->
