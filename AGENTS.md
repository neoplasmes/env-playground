# Project instructions

## Communication

Общайся с пользователем на русском в образовательном стиле: объясняй назначение
изменений, незнакомые понятия и результаты проверок простыми словами. Не предполагай,
что пользователь уже знает устройство инструментов. Инструкции и комментарии в коде
пиши на английском, если пользователь не попросил иначе.

## Start here

- Read `README.md` for the current implementation and commands. Architecture is
  documented in `ARCHITECTURE.repo.md`, `ARCHITECTURE.frontend.md`, and
  `ARCHITECTURE.backend.md`; open the relevant document before changing boundaries.
- Inspect the working tree before editing. Preserve existing user changes and
  distinguish them from this task's changes.
- For substantive work, identify observable acceptance criteria, implement the
  change, run relevant checks, review the result, and report evidence and limits.
- Use the pinned toolchain and moon tasks. On this computer,
  `source node/activate.sh` activates the project-local tools
  and the existing local C-compiler shim when system `cc` is absent.
- Keep Node, Python, and Rust configuration in their language directories.
  Agent tooling lives in the separate `node/tools/agent-workflow` package.

## Skills and tools

- Use `$verify-change` to select checks for a substantive change,
  `$image-processing-change` for the upload/transform/download contract, and
  `$preview-diagnostics` for preview delivery failures.
- Use installed, version-matched documentation first. Use Context7 when library
  behavior is uncertain; verify which version its answer describes.
- Use Next DevTools MCP for a running Next.js development server. Use the
  Playwright CLI skill for exploratory browser work and `playground:browser-test`
  for the repeatable local scenario. HTTP checks alone do not establish browser
  correctness.
- Do not install GitHub MCP. Git and an existing authorized CLI/connector are
  sufficient for repository operations.
- `AGENT_WORKFLOW.md` describes setup, tools, and example requests.

## Delegation

- Use the model and reasoning effort configured in `.codex/agents/` for each role.
  For agents without a custom role, use the defaults in `.codex/config.toml`.
  Do not replace these selections with the parent chat's model or reasoning effort.
- Use a separate `code-reviewer` for substantive code/configuration changes before
  closing the task. It should inspect the diff independently and report actionable
  defects, not rephrase the implementation summary.
- Use `architecture-reviewer` for changed ownership, dependencies, or contracts;
  `platform-engineer` for infrastructure implementation/diagnosis; and `browser-qa`
  for user-facing flows. Small documentation/style changes need no delegation.
- Give a subagent a bounded task, relevant paths, acceptance criteria, and the
  permitted side effects. Do not launch every role for every task.
- Parallel writers need separate worktrees or explicitly disjoint files. Shared
  lockfiles and integration changes have one owner. The primary agent integrates
  results and owns commits; reviewers do not edit or commit.

## Logical commits and commitlint

- Regularly create a commit after each coherent, verified milestone. Do not collect
  unrelated completed changes into one final commit or create empty/WIP checkpoints.
- The user has authorized these local logical commits. Do not ask again for each
  commit. A later instruction not to commit takes precedence. Pushing, publishing,
  merging, and deploying are separate actions and require task authorization.
- Follow the executable commitlint configuration in
  `node/commitlint.config.cjs`: Conventional Commits,
  `type(scope): imperative summary`, optional scope, English summary, no trailing
  period, header at most 100 characters. Examples:
  `feat(processor): support avif conversion`,
  `fix(api): preserve job idempotency`, `chore(agents): configure project reviewers`.
- Before committing, review the staged diff and stage only this milestone's files
  or hunks. Never sweep pre-existing changes into a commit with `git add .`.
- Run the applicable checks first. The `commit-msg` hook runs commitlint; do not
  bypass it. `moon run playground:commitlint -- --last --verbose` checks the latest
  commit. Report failures and fix them before moving to the next milestone.
- Do not rewrite existing commits or amend another contributor's commit unless
  explicitly requested.

## Evidence and external actions

- Keep secrets, Terraform state/plans, kubeconfigs, browser profiles, and runtime
  artifacts out of Git. Use disposable data for local/browser checks.
- Tool installation does not authorize cloud apply/destroy, image publication, or
  deployment. Follow the actual task's authorization at those boundaries.
- Report what was actually executed. Separate local checks from live cloud/CI
  validation; unavailable credentials or services are not a successful check.
