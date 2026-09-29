The main tools for repository managment and CI/CD are follows:
- prototools
- moonrepo
- woodpecker CI
- terraform

core technology stack should be installed with `proto` and recorded in .prototools;

all repository apps and packages should be managed through moonrepo `moon` commands or mcp;

default repository structure:

```
lang_name/
	apps/
		app_name/
			...
			Dockerfile
			moon.yaml
			app_name_specific_configuration_files.ext
	packages/
		package_name/
			...
			moon.yaml
	lang_name_specific_configuration_files.ext
lang_name_2/
	apps/
		...
	packages/
		...
global_monorepo_specific_configuration_files.ext
moon.yaml
```

I've decided to split everything by language, because I don't want to a fucking mess of different unrelated configs in the root of monorepo (and they will unfortunatelly appear there, when there will be more than one projects on the same language);

Language specifics:

### node (ts projects):

- package-manager: pnpm;
- oxlint for linting and oxfmt for formatting; no ESLint runner or configuration;
- oxlint loads `@stylistic/eslint-plugin` through `jsPlugins`;
- `@stylistic/padding-line-between-statements` exactly matches `~/qualification_work`: `blankLine: always`, `prev: *`, `next: [return, throw, break, continue]`;

### python:

- uv for everything;
- ruff for formatting and linting;
- the `repo-style` workspace tool checks blank lines before `return`, `raise`, `break`, and `continue`;
- ty as language server;

### rust:

- Rust replaces the previously discussed Go service;
- Cargo for dependencies, workspaces, builds, and tests, invoked through moon tasks;
- rustfmt for formatting and Clippy for linting;
- `repo-style` checks blank lines before explicit `return`, `break`, and `continue`; Rust tail expressions and opaque macro token bodies are excluded;
- the Rust toolchain is installed through proto and pinned alongside the other core tools;
- the Cargo workspace and its lockfile belong in `rust/`.

## Project scope and architecture references

This repository is an image-processing application and a reproducible infrastructure playground. It is intended for learning Kubernetes, multiple deployment environments, CI/CD, and temporary environments for pull requests. The infrastructure must support repeated creation and destruction in Cloud.ru Evolution.

The application consists of a Next.js frontend with a BFF and two backend services: Rust and Python.

| Component | Responsibility |
| --- | --- |
| Next.js frontend and BFF | Upload UI, transformation settings, job history and status, result downloads, and the server-side interface used by the frontend. |
| Rust service | File metadata, processing jobs and their lifecycle, access to source images and results, and coordination with the processing service. |
| Python service | Image transformations and reporting processing results or failures. |

The initial application flow is: upload an image, choose a transformation, submit a job, observe its status, and download the result. Resizing and format conversion are the proposed first operations. The MVP accepts non-animated PNG/JPEG/WebP up to 10 MiB and 16 megapixels, resizes within 4096 by 4096 pixels, and strips metadata.

The following documents define the internal application architecture:

- [Frontend architecture](ARCHITECTURE.frontend.md): frontend layers, commands and queries, ports, entity storage, caching, controllers, and package boundaries.
- [Backend architecture](ARCHITECTURE.backend.md): backend layers, use cases, ports, pure domain processes, adapters, composition roots, and package boundaries.

Apply the backend dependency rules to Python, Rust, and the server-side BFF. Python-specific module naming and `__init__.py` rules remain Python-specific; use explicit module exports and public interfaces appropriate to Rust and TypeScript. Next.js routing and request handlers are framework entrypoints and must preserve the documented application-layer boundaries.

The implementation uses Axum, SQLite with WAL and a persistent polling worker, FastAPI and Pillow. Source and result bytes share the job database so job creation is atomic. A single Rust replica recovers interrupted jobs at startup. Each environment admits at most 50 jobs.

## Language workspaces and repository configuration

Keep the language-based structure above. Each language owns its package-manager manifests, lockfiles, and language-wide configuration. The repository root contains configuration shared by the monorepo, architecture documents, and orchestration entrypoints.

The implemented layout follows this structure:

```text
node/
    apps/
        web/
            Dockerfile
            moon.yaml
            package.json
    packages/
    package.json
    pnpm-workspace.yaml
    pnpm-lock.yaml
python/
    apps/
        image_processor/
            Dockerfile
            moon.yaml
            pyproject.toml
    packages/
    pyproject.toml
    uv.lock
rust/
    apps/
        image_api/
            Dockerfile
            moon.yaml
            Cargo.toml
    packages/
    Cargo.toml
    Cargo.lock
infra/
    terraform/
    bootstrap/
    charts/
    ci/
    local/
    moon.yaml
.moon/
.woodpecker/
.prototools
moon.yaml
ARCHITECTURE.repo.md
ARCHITECTURE.frontend.md
ARCHITECTURE.backend.md
```

`infra/` contains infrastructure configuration shared across languages. It does not become a second home for application source code or language-specific package-manager configuration. Create shared packages when there is an actual consumer; the example does not require empty packages or placeholder applications.

## Toolchains and task execution

- Use the latest stable compatible versions when first implementing the stack, then record exact versions. Resolve version numbers from current upstream releases rather than copying old examples.
- Install core development and infrastructure tools through proto and record them in `.prototools`. Configure the necessary proto plugins where applicable. Pin deployed platform components and container base images in their deployment/build configuration as well.
- Commit language lockfiles and the Terraform provider lockfile. CI installs dependencies using the relevant locked/frozen mode. Floating `latest` tags must not determine what a rebuild or deployment runs.
- Expose development, formatting, linting, type checking, tests, builds, image builds, and deployment operations through moon tasks. Language tools run underneath those tasks.
- Local development and Woodpecker must use the same task definitions. Configure moon project dependencies and inputs so affected-project checks also include dependent packages and applications.
- Keep the pnpm workspace in `node/`, the uv workspace in `python/`, and the Cargo workspace in `rust/`; configure task working directories accordingly.

## Container builds

Every deployable application has its own optimized `Dockerfile` and image. Build tasks select the application-specific build context and Dockerfile explicitly.

- Use multiple build stages, reuse dependency caches, and copy only runtime artifacts and required runtime dependencies into the final image.
- Exclude local secrets, development environments, build caches, and unrelated files from build contexts.
- Run application processes as an unprivileged user and provide health/readiness checks suitable for Kubernetes.
- Configure build contexts so applications can consume their language workspace lockfiles and shared packages.
- Identify images by commit and deploy immutable digests. Promote the same tested artifacts between environments.
- Keep runtime environment configuration separate from the image. Any Next.js settings that are embedded during the build must be identified explicitly so they do not accidentally bind an image to one PR environment.

## Cloud infrastructure and lifecycle

The target cloud is **Cloud.ru Evolution**. Terraform manages the cloud resources needed for the playground, including virtual machines, networking, disks, and public access. Kubernetes and platform installation must also be reproducible from versioned configuration.

The user originally allocated 4,000 bonus credits and confirmed on 2026-09-29 that quotas are sufficient. Quotas are therefore not an outstanding preparation question. The current bonus balance, expiry, and cost of the selected resources still need checking before deployment.

The proposed initial topology is a small k3s cluster on virtual machines: one control-plane node and one worker, with an additional worker configurable for experiments. The earlier estimate of 2 vCPU / 4 GiB for the control plane and 4 vCPU / 8 GiB for the worker is a sizing proposal, not a verified capacity or cost guarantee. A single control-plane node is not highly available.

Separate infrastructure bootstrap from application delivery:

- Terraform, Kubernetes bootstrap, and Woodpecker installation/recovery must be runnable from the operator's computer or another control point outside the disposable cluster.
- Woodpecker runs on the playground nodes and handles application CI/CD after bootstrap. Recreating the cluster must not depend on a Woodpecker instance that was destroyed with it.
- Store Terraform state outside disposable compute, protect it as sensitive data, and serialize infrastructure mutations.
- Document which resources a normal teardown deletes and which it retains. Persistent storage, retained IPs, image registries, and backups must be included in the cost calculation.
- Treat PR data as disposable. Application data and the Woodpecker database are disposable on full teardown; local Terraform state, credentials and external GHCR images survive it.
- Keep cloud credentials, OAuth secrets, private SSH keys, state files, and sensitive plan files out of Git and build logs. Version templates containing placeholders only.

## Kubernetes environments

The proposed starting point is one cluster with separate namespaces for the platform and application environments:

| Namespace | Purpose |
| --- | --- |
| `platform` | Self-hosted Woodpecker and shared platform components. |
| `dev` | The application version built from the default branch. |
| `prod` | An explicitly promoted application release; this is an educational production environment. |
| `preview-1..3` | Three reusable isolated slots, each assigned to an open PR; public hostname is `pr-<number>`. |

Each application environment contains the Next.js/BFF, Rust, and Python components. Creating a PR environment normally creates Kubernetes resources within the existing cluster; it does not require new virtual machines.

Namespaces must be complemented by resource quotas/limits, scoped service accounts and RBAC, and enforced network policies. Give environments isolated application data and storage access; PR code must not read or modify `prod` data. A shared cluster remains a shared failure domain.

## GitHub and Woodpecker CI/CD

The repository will be hosted on **GitHub**. **Self-hosted Woodpecker** is the CI/CD system. Version its pipelines under `.woodpecker/` and invoke moon tasks from them.

The intended lifecycle is:

1. Opening or updating a PR runs the relevant format, lint, type, unit, integration, and build checks through moon.
2. Successful checks produce the images needed for that revision and publish them to an external container registry that remains available after cluster teardown. Reuse unchanged images only when they match the tested dependency graph.
3. The master-only reconcile cron builds a verified same-repository PR revision and deploys it into an available preview slot, using the trusted chart from master.
4. Helm waits for workload readiness and prints the preview URL in delivery logs. The local HTTP smoke command checks the complete processing flow; live cloud and browser tests remain deployment validation.
5. The next reconcile after closing/merging/drafting a PR uninstalls its release and deletes its PVC. The empty slot namespace and bootstrap secrets remain reusable.
6. The reconcile cron deploys a verified default-branch revision to `dev`. `moon run infra:promote` copies the same image digests to `prod`.
7. A periodic reconciliation task removes abandoned previews and restores the desired preview set after downtime, since webhook events may be missed while the cluster is destroyed.

Serialize deployments per environment and prevent an older build from overwriting a newer revision or recreating a preview after its PR closes. Limit concurrent builds and preview resource consumption to fit the playground budget. Keep deployment permissions separate from jobs executing untrusted PR code, especially fork PRs.

Images are stored in GHCR. Delivery secrets are restricted to cron events only, with the cron configured for master; PR and push workflows receive no deployment credentials. Cron settings and repository push access are trusted administration boundaries. GitHub OAuth registration and a reachable Woodpecker webhook endpoint are deployment prerequisites.

## Public addresses and DNS

As of 2026-09-29, the user has no domain/DNS setup. Hostnames must be configurable, and purchasing a domain is not a prerequisite for writing or testing the application locally.

Two deployment options are available:

- Register a domain with a registrar and use its DNS service or delegate a zone to Evolution DNS. Use names such as `ci.play.example.com`, `dev.play.example.com`, `prod.play.example.com`, and `pr-42.play.example.com`.
- For an initial experiment, use a public-IP-based DNS service such as `sslip.io`, with names such as `ci.<public-ip-with-dashes>.sslip.io` and `pr-42.<public-ip-with-dashes>.sslip.io`. The user selected this temporary scheme for the initial deployment.

Evolution DNS documentation describes hosting and delegating zones for a domain registered with a registrar; it does not establish a domain-purchase service. See [Evolution DNS delegation](https://cloud.ru/docs/evolution-dns/ug/topics/guides__delegate-zone?source-platform=Evolution).

DNS resolution alone does not provide HTTPS. For the temporary option, obtain certificates for the individual public hostnames and account for issuance limits; `sslip.io` does not provide wildcard certificates. A changed public IP changes these temporary hostnames, so bootstrap must document updating Woodpecker's public URL, GitHub OAuth callback, and webhooks. See [sslip.io / nip.io documentation](https://sslip.io/).

## Implementation status

Application code, Dockerfiles, Terraform, bootstrap scripts, Helm chart, moon tasks and Woodpecker pipelines are implemented. See README.md for verification and setup. No Cloud.ru resources have been created; account-specific catalog, cost, live Kubernetes and CI validation remain pending credentials.

## Statement padding

`repo-style` is implemented in `python/packages/repo_style`. It uses Python AST and the tree-sitter Rust grammar, not regular expressions. Padding is required only between sibling statements in one block; a control statement at the start of a block needs no blank line. Comments stay attached to the following statement. Parse errors fail the check.

`moon run playground:format` runs language formatters and adds missing padding. `moon run repo-style:fix` only inserts blank lines; same-line statements must first be split by Ruff/rustfmt. `moon run repo-style:check` and each backend check task enforce the rule. `moon run repo-style:test` covers syntax, comments, strings, labels, macros, CRLF, and idempotent fixes. Rust checks therefore also require the Python tooling workspace.
