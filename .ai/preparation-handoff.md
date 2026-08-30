# OSHE Content Agent Adapter Handoff

Prepared: 30-08-2026
State: Prepared for controlled pull-request publication; live commit, push, PR, and merge state require GitHub readback. Dispatch remains disabled.

The content repository now has a repository-specific `AGENTS.md`, CLI adapters, and `repository-profile.json`. It deliberately does not duplicate canonical roles, skills, policies, schemas, or provider routes from `OSHEThai/oshe-platform`.

Before publication:

1. Open an `oshe-content` pull request as the primary audit record for this directly authorized work; no synthetic Issue is required under ADR-0007.
2. Canonical AI Agent OS controls and ADR-0006/ADR-0007 are merged in `oshe-platform` at `b9b86dcdcce85fc2bd2044a6f3038f1087ab7895`.
3. `canonical_ref` is pinned to that exact reviewed commit.
4. Verify every preferred role, specialist profile, skill, data class, and path against that commit.
5. Keep `dispatch_enabled: false` until provider-route and runtime enforcement gates are separately satisfied.
6. Run `python tools/run_local_ci.py --mode incremental` on the exact adapter head before opening or updating the pull request.
7. After merge, delete the head branch and remove unreferenced worktrees, local branches, caches, logs, downloads, and failed outputs while preserving evidence and valid checkpoints.
