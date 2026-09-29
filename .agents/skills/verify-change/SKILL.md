---
name: verify-change
description: Select and run the env-playground checks needed for a substantive code or configuration change, and report concrete validation evidence.
---

# Verify a project change

Read root AGENTS.md and inspect the task diff, including new files. Identify the
observable behavior and affected dependency paths before choosing checks.
Use README.md and the current moon task definitions as the command source of truth.

| Changed area | Starting checks |
| --- | --- |
| Next.js UI, controllers, data adapters | web:check, web:test; web:build for build/server boundaries |
| Rust API, persistence, jobs | image-api:check, image-api:test |
| Python image processing | image-processor:check, image-processor:test |
| Shared statement padding | repo-style:check, repo-style:test and affected language checks |
| Terraform, Helm, bootstrap, delivery | infra:check, infra:test |
| Cross-service upload/job/result contract | playground:smoke |
| User-visible browser flow | playground:browser-test |
| Shared Node tooling | playground:node-check; browser-test when its runner/spec changes |
| Agent tooling | playground:agents-check; browser-test when its runner/spec changes |

Invoke selected targets with moon run. Activate node/activate.sh when
using this checkout's local toolchain. Use playground:check/test/build for changes
spanning the application, rather than assuming that one package check covers callers.
Do not require browser tests for prose-only changes.

The browser scenario starts disposable services and requires installed Chromium.
HTTP smoke checks real service integration but does not test the browser.
For Next runtime diagnosis start web:dev and use Next DevTools MCP; a production
server does not expose the dev MCP endpoint.

For substantive changes request the separate code-reviewer on the actual diff.
Give it the change scope and acceptance criteria, without prescribing its verdict.
Resolve actionable findings, then rerun checks affected by the fix. Use the
architecture-reviewer when contracts, dependencies, or state ownership changed.

Return the commands actually executed, pass/fail, relevant artifacts, and unverified
areas. A missing dependency, credential, or cloud environment is a limit, not a pass.
Commit each coherent verified milestone following the root commitlint instructions.
