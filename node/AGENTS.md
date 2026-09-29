# Node workspace

- Read `../ARCHITECTURE.frontend.md` before changing layer dependencies or state
  ownership. `core` is plain data and pure functions; `app` owns use cases and ports;
  `env` implements transport, validation, repositories, and caching; `main` wires them.
- Framework/browser/transport details stay outside `core` and `app` (the documented
  `AbortSignal` exception remains). UI controllers own presentation policy.
- Use oxlint and oxfmt. Do not introduce ESLint or a competing formatter.
- The application pnpm workspace is here. `tools/agent-workflow` is intentionally a
  separate tooling package with its own lockfile; install it with `--ignore-workspace`.
- For Next.js APIs, read the installed docs under
  `apps/web/node_modules/next/dist/docs/` first. Locate the relevant page with `rg`.
  Next.js's generated docs pointers complement these project architecture rules.
- Use `moon run web:check`, `web:test`, and `web:build` as appropriate. For changed
  interactions use `playground:browser-test`; for service contracts use
  `playground:smoke`. See `$verify-change` for selection.
