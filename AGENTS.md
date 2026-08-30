# OSHE Content Agent Contract

## Mission

Develop controlled OSHE content packs, checklists, forms, signage, translations, legal and standards mappings, and industry overlays while preserving source provenance, jurisdiction, version, licensing, record integrity, accessibility, localization, and human publication authority.

## Canonical Authority

The 12 canonical roles, specialist profiles, skills, contracts, policies, and provider routes are owned by `OSHEThai/oshe-platform` under ADR-0005. This repository contains only a repository-specific adapter at `.ai/repository-profile.json`; it must not silently fork the canonical registries.

Automated dispatch is denied while `canonical_ref` is unpinned or the selected provider route is not explicitly approved.

## Required Workflow

1. Read the issue or mission, this contract, and `.ai/repository-profile.json`.
2. Resolve a canonical role, optional specialist profile, skill bundle, exact pinned control ref, provider route, data class, tool profile, and write lease.
3. Confirm authoritative sources, jurisdiction, effective date, license or quotation limits, and target language.
4. State assumptions and unknown facts before changing files.
5. Change only leased repository paths and preserve source-to-claim traceability.
6. Run all applicable local checks as one non-fail-fast incremental batch and fix the complete failure set together.
7. Reuse a passing checkpoint only when command, toolchain, repository input, and base commit remain unchanged.
8. Open or update the pull request only after local CI passes; run Full CI only for Milestone closure, locally first and then on GitHub.
9. Validate schemas, identifiers, links, terminology, and rendered layout where applicable.
10. Produce a structured result, clean unreferenced worktrees, branches, caches, logs, downloads, and failed outputs, and stop for protected publication, legal, safety, privacy, or release decisions.

## Non-Negotiable Rules

- Never publish legal, regulatory, standards, medical, or safety-critical content without the required qualified human and Sole Human Owner approval.
- Never present AI interpretation as authoritative source text or legal compliance.
- Never redistribute licensed or restricted source content without rights.
- Never invent citations, effective dates, jurisdictions, translations, approvals, or missing facts; mark unknown facts explicitly.
- Keep source facts, interpretation, company policy, and executable configuration distinguishable.
- Preserve immutable published versions and the exact revision linked to historical records.
- Produce separate English and Thai files when the governed deliverable requires both languages.
- Read back DOCX/XLSX content and render every layout-sensitive final page before visual-QA claims.
- Never access production secrets, customer data, medical data, or security-case data from a general agent workspace.
- Never use hidden subagents, unregistered sessions, or out-of-scope paths. Protected GitHub writes, merges, releases, and administration require the canonical ADR-0006 github-manager profile and an exact passing operation gate; non-GitHub production deployment remains separately authorized.
- Issue-scoped work links its Issue. Directly authorized work outside the prepared Issue set still requires a pull request, which becomes its primary audit record under canonical ADR-0007.
- Delete merged head branches and safely delete closed-unmerged or abandoned branches after proving that no active work or recovery/evidence reference needs them.

## Standard Commands

- Foundation validation: `python tools/validate_repository.py --repo-kind content`
- Local incremental CI: `python tools/run_local_ci.py --mode incremental`
- Milestone-close Full CI only: `python tools/run_local_ci.py --mode full --milestone-close "<milestone>"`
- Unresolved marker scan: `rg -n "TODO|TBC|PLACEHOLDER" .`
- Content-specific validators and renderers must be supplied by the applicable content package; do not report missing checks as passing.

## Preferred Canonical Roles and Skills

Content work normally uses the Documentation and Configuration Agent or Research and Legal Content Agent, with Test and Quality, Security Privacy and Product Safety, Independent Review and Challenge, Release and Evidence, or Implementation and Customer Success Planning roles as required by risk. The repository profile lists the expected specialist profiles and skills.

## Required Output

Include base and result commit or read-only state, changed paths, authoritative sources, commands, validation and rendered evidence class, assumptions, risks, unresolved findings, reviewer disposition, and Sole Human Owner decisions needed.
