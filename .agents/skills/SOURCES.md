# Skill sources

Vendored on 2026-09-29. Upstream license files are retained where provided.

| Skill | Source path | Revision | License |
| --- | --- | --- | --- |
| `vercel-react-best-practices` | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills/tree/063bee94c3f4df8453406c830b0a7df0f2860278/skills/react-best-practices) | `063bee94c3f4df8453406c830b0a7df0f2860278` | MIT (declared in upstream README; no LICENSE file in this revision) |
| `terraform-style-guide` | [hashicorp/agent-skills](https://github.com/hashicorp/agent-skills/tree/f706481af9b8fedb66de909f6243ad29601afa0c/plugins/terraform/skills/terraform-style-guide) | `f706481af9b8fedb66de909f6243ad29601afa0c` | MPL-2.0 |
| `playwright-cli` | [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli/tree/b85c7a736bb473bf55b584e54a09ffa698d6d871/skills/playwright-cli) | `b85c7a736bb473bf55b584e54a09ffa698d6d871` | Apache-2.0 |

## Local adaptation

- Vendored text uses LF line endings and has trailing whitespace removed; license wording is preserved.

- The Playwright entrypoint uses the pinned project wrapper and ignored output directory; global/latest installation instructions are replaced by project setup. Upstream examples remain reference material.
- Vercel and HashiCorp skills are reference guidance. Root and language AGENTS.md retain architecture and toolchain decisions.
- The three other skills are authored for this repository.

Update deliberately: inspect the upstream diff, preserve its license, reapply the local adaptation, update this revision record, and exercise the affected workflow.
