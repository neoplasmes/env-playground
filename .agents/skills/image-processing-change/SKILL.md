---
name: image-processing-change
description: Change the env-playground image upload, transformation, job, or download behavior consistently across Next.js BFF, Rust API, and Python processor.
---

# Change image-processing behavior

Start with the requested behavior and acceptance criteria. Read README.md and the
relevant ARCHITECTURE.frontend.md / ARCHITECTURE.backend.md sections. Trace the real
implementation; do not treat architectural sketches as completed behavior.

Map the affected contract through:
- node/apps/web/app/api/jobs and src/core, app, env, ui.
- rust/apps/image_api/src/core, app, env, api.
- python/apps/image_processor/src/image_processor and its tests.

For a new option or format, account for input/output validation, DTO parsing,
domain representation, transformation, error mapping, UI controls, and the result
response. Change only the parts the requested feature actually needs.

For job behavior, preserve idempotency-key semantics, transitions, retries/recovery,
polling, and result availability. Inspect persisted state when changing a field;
decide whether an existing local database needs compatibility or an explicit migration.

Read current limit constants and tests instead of copying limits into this skill.
Relevant image properties include pixel/file limits, aspect ratio, alpha handling,
EXIF orientation, metadata removal, corrupt content, and animation. Choose assertions
that distinguish the new behavior from a plausible incorrect implementation.

Keep pure validation in core, orchestration/ports in app, concrete processing and
storage in env, and UI policy in controllers. Framework performance advice does not
override the project's ownership rules.

Use verify-change for package checks and the real cross-service smoke. For changed
user-facing behavior run the browser scenario; verify the downloaded image's format
and dimensions. Request architecture review when the service contract or ownership
changes. Report compatibility implications and actual test evidence.
