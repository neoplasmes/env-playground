# Infrastructure

- Read `../README.md` and the infrastructure sections of `../ARCHITECTURE.repo.md`.
  Use the existing moon tasks and bootstrap scripts as the execution interface.
- Terraform bootstrap/state and recovery live outside disposable cluster compute.
  The current backend is local: serialize infrastructure mutations.
- Preserve the delivery boundary: PR checks have no deployment secrets; master-only
  cron reconciles verified same-repository revisions using the trusted master chart.
  Promote immutable image digests and re-check the desired PR revision before deploy.
- Preview slots have isolated data, scoped credentials, quotas, and network policy.
  Closing/drafting a PR must not allow an older run to recreate its preview.
- Use `$preview-diagnostics` to investigate delivery before changing live state.
  Terraform MCP is for registry documentation, not a replacement for Cloud.ru's
  provider documentation or the account catalog.
- Run `moon run infra:check` and `infra:test` for relevant changes. Local static/unit
  checks do not establish that live Cloud.ru, Kubernetes, TLS, or Woodpecker works.
