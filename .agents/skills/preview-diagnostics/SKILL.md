---
name: preview-diagnostics
description: Diagnose missing, stale, failing, or uncleared env-playground preview environments through GitHub revision status, Woodpecker reconcile, image build, Helm, and workload readiness.
---

# Diagnose preview delivery

Read README.md, infra/AGENTS.md, infra/ci/reconcile.py, and the relevant tests.
Establish the PR number, desired head SHA, environment/slot, and observed failure.
Use supplied evidence and authorized read-only tools; do not install GitHub MCP.

Follow the delivery chain until the first unsupported assumption:
1. Is this an eligible open, non-draft, same-repository PR?
2. Does the exact desired revision have the required successful checks?
3. Did the trusted master reconcile cron run, and was a slot available?
4. Did image building/publishing succeed for that revision?
5. Did the desired revision change before deployment, causing a legitimate skip?
6. Did Helm use the trusted chart and intended image digests?
7. Are readiness, service routing, ingress/TLS, storage, and processor connectivity healthy?
8. For closed/drafted PRs, did reconciliation remove the release/data as intended?

Prefer targeted status/log/event queries over broad dumps. Do not print tokens,
kubeconfig contents, secret resources, environment files, or sensitive plan/state.
A GitHub check status does not establish that Woodpecker delivery completed.

If credentials or the cluster are unavailable, analyze local code/tests and identify
the exact missing observation. Do not fabricate live status or request secrets in chat.

A diagnosis request does not authorize triggering reconcile, applying Terraform,
deleting a namespace/PVC, promoting a release, or altering secret/cron settings.
When a fix is authorized, first make it reviewable and run infra:check / infra:test
as relevant. Preserve authorization already given for the actual task.

Return desired versus observed state, the first failing stage, evidence, likely
cause with uncertainty, and the smallest corrective action with a verification step.
