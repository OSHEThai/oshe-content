# OSHE Content AI Adapter

This repository does not duplicate the canonical AI Agent OS. Canonical roles, specialist profiles, skills, schemas, policies, runbooks, and provider routes live in `OSHEThai/oshe-platform/.ai/` under ADR-0005, ADR-0006, and ADR-0007.

`repository-profile.json` declares the content-specific role, profile, skill, path, and data boundaries, including the ADR-0006 github-manager profile. Its `canonical_ref` is pinned to reviewed `oshe-platform` commit `b9b86dcdcce85fc2bd2044a6f3038f1087ab7895`. Automated dispatch still fails closed until the provider-route, credential, session, and runtime enforcement gates pass.

Runtime state, transcripts, credentials, licensed source dumps, customer data, medical data, and security-case data must never be committed.

Repository-local execution follows ADR-0007: run one non-fail-fast local incremental CI batch, reuse only unchanged passing checkpoints, run GitHub CI after the local pass, reserve Full CI for Milestone closure, and clean unreferenced branches, worktrees, caches, logs, downloads, and failed outputs after the task.

See `preparation-handoff.md` for the controlled publication and canonical-ref pinning steps.
