# Rust workspace

- Read `../ARCHITECTURE.backend.md` for ownership. Domain rules are pure; `app`
  orchestrates ports; SQLite, HTTP, filesystem, and configuration belong in `env`.
- Use the pinned Cargo workspace/toolchain and `--locked` through moon tasks.
- Job lifecycle changes must preserve idempotency, restart behavior, bounded
  resource use, and the BFF/processor contract. Use `$image-processing-change`.
- Run `moon run image-api:check` and relevant tests; use `playground:smoke` for
  cross-service behavior. Rust checks also need the Python statement-padding tool.
