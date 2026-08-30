# OSHE Content

This repository is the authoritative engineering source for versioned content packs, checklists, forms, signs, translations, legal mappings, standards mappings, and industry overlays after reviewed migration from the stakeholder workspace.

## Boundaries

- Source facts, interpretation, company policy, and system configuration remain distinguishable.
- Licensed or restricted source text is not redistributed without rights.
- Published content is immutable and versioned.
- Historical records retain the content revision used at the time.
- AI may draft content but cannot publish legal or safety-critical content.

## Agent Controls

`AGENTS.md` is the repository contract. `.ai/repository-profile.json` is a fail-closed adapter to the canonical controls in `OSHEThai/oshe-platform`; it intentionally denies automated dispatch until an exact canonical commit is pinned and compatibility is reviewed.

Run `python tools/run_local_ci.py --mode incremental` before opening or updating a pull request. It collects every applicable failure and checkpoints only unchanged passing evidence. Full CI is reserved for Milestone closure and runs locally before GitHub.
