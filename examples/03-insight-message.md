# Frontend bundle size doubled after i18n addition
**Date**: 2026-03-23 11:15
**From**: Claude (Sonnet - Frontend)
**Project**: My App
**Type**: insight
**Confidence**: high

While adding the translation layer, the production bundle went from 340KB to 680KB. The i18n library pulls in all locale data by default. Switching to dynamic imports (load locale on demand) should bring it back under 400KB.

**Next action**: FYI only. Will fix in the next frontend session. Flagging because it affects the performance budget Codex set up last week.
