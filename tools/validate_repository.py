#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

PLACEHOLDERS = tuple(
    "__" + name + "__"
    for name in (
        "GITHUB_ORG",
        "PRIMARY_GITHUB_OWNER",
        "RECOVERY_GITHUB_OWNER",
        "SECURITY_CONTACT_EMAIL",
    )
)

COMMON_REQUIRED = [
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "QWEN.md",
    ".github/CODEOWNERS",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/bug.yml",
    ".github/ISSUE_TEMPLATE/change.yml",
    ".github/workflows/foundation.yml",
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "README.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "repo-manifest.yaml",
    ".ci/local-ci.json",
    "tools/run_local_ci.py",
]

REPO_REQUIRED = {
    "platform": [
        "apps/README.md",
        "modules/README.md",
        "packages/README.md",
        "contracts/README.md",
        "schemas/README.md",
        "database/README.md",
        "tests/README.md",
        "deploy/README.md",
        "docs/adr/README.md",
        "docs/rfc/README.md",
        ".ai/README.md",
    ],
    "content": [
        ".ai/README.md",
        ".ai/preparation-handoff.md",
        ".ai/repository-profile.json",
        "packs/README.md",
        "packs/common/README.md",
        "packs/capability/README.md",
        "packs/industry/README.md",
        "packs/jurisdiction/thailand/README.md",
        "packs/standards/README.md",
        "forms/README.md",
        "checklists/README.md",
        "signage/README.md",
        "translations/README.md",
        "schemas/pack.schema.json",
        "tests/README.md",
    ],
}

SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(password|secret|token)\s*[:=]\s*[\"'][^\"']{8,}[\"']"),
]

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-kind", choices=("platform", "content"), required=True)
    args = parser.parse_args()

    root = pathlib.Path.cwd()
    errors: list[str] = []

    for rel in COMMON_REQUIRED + REPO_REQUIRED[args.repo_kind]:
        if not (root / rel).exists():
            errors.append(f"missing required path: {rel}")

    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"possible secret in {path.relative_to(root)}")

        if path.suffix == ".json":
            try:
                json.loads(text)
            except json.JSONDecodeError as exc:
                errors.append(f"invalid JSON {path.relative_to(root)}: {exc}")

    manifest = root / "repo-manifest.yaml"
    if manifest.exists() and "repository:" not in manifest.read_text(encoding="utf-8"):
        errors.append("repo-manifest.yaml lacks repository key")

    if args.repo_kind == "content":
        profile_path = root / ".ai" / "repository-profile.json"
        if profile_path.is_file():
            try:
                profile = json.loads(profile_path.read_text(encoding="utf-8"))
                if profile.get("canonical_repository") != "OSHEThai/oshe-platform":
                    errors.append("content agent profile must resolve to OSHEThai/oshe-platform")
                if profile.get("control_status") == "UNPINNED_PREPARATION_ONLY":
                    if profile.get("canonical_ref") is not None:
                        errors.append("un-pinned content profile must have canonical_ref null")
                    if profile.get("dispatch_enabled") is not False:
                        errors.append("un-pinned content profile must deny dispatch")
                else:
                    canonical_ref = profile.get("canonical_ref")
                    if not isinstance(canonical_ref, str) or re.fullmatch(r"[0-9a-f]{40}", canonical_ref) is None:
                        errors.append("content agent profile canonical_ref must be an exact lowercase 40-character commit SHA")
                    if profile.get("dispatch_enabled") is not False:
                        errors.append("content agent profile dispatch must remain disabled until runtime gates pass")
                if set(profile.get("authority_basis") or []) != {"ADR-0005", "ADR-0006", "ADR-0007"}:
                    errors.append("content agent profile authority basis must include ADR-0005 through ADR-0007")
                workflow = profile.get("repository_workflow") or {}
                if workflow.get("full_ci") != "MILESTONE_CLOSE_ONLY_LOCAL_THEN_GITHUB":
                    errors.append("content agent profile must limit Full CI to Milestone closure, local then GitHub")
            except json.JSONDecodeError as exc:
                errors.append(f"invalid content agent profile JSON: {exc}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    unresolved = []
    for path in root.rglob("*"):
        if path.is_file() and ".git" not in path.parts:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if any(value in text for value in PLACEHOLDERS):
                unresolved.append(str(path.relative_to(root)))

    if unresolved:
        print("NOTICE: bootstrap placeholders remain in:")
        for item in unresolved:
            print(f"  - {item}")
        print("They must be replaced before pushing to GitHub.")

    print(f"Foundation validation passed for {args.repo_kind}.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
