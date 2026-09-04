#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
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

RIGHTS_METADATA = "RIGHTS-METADATA.json"
RIGHTS_REQUIRED = ("LICENSE", "DCO-1.1.txt", "NOTICE.md", RIGHTS_METADATA)
RIGHTS_IGNORED_PARTS = {".git", ".local-ci", "__pycache__", ".pytest_cache"}
RIGHTS_LICENSES = {
    "platform": {
        "OSHE_AUTHORED_ENGINEERING": {"MPL-2.0"},
        "PUBLIC_CONTRACT": {"Apache-2.0"},
        "PUBLIC_SCHEMA": {"Apache-2.0"},
        "SDK": {"Apache-2.0"},
        "INTEGRATION_EXAMPLE": {"Apache-2.0"},
        "CONFORMANCE_KIT": {"Apache-2.0"},
    },
    "content": {
        "CODE_TOOL_SCHEMA_TEST_AUTOMATION": {"Apache-2.0"},
        "OSHE_AUTHORED_PRACTICAL_CONTENT": {"CC-BY-SA-4.0"},
        "OSHE_AUTHORED_METADATA_OR_MAPPING": {"CC-BY-4.0"},
    },
}


def validate_rights_metadata(root: pathlib.Path, repo_kind: str) -> list[str]:
    """Require every repository file to have deterministic, fail-closed rights metadata."""
    errors: list[str] = []
    for relative_path in RIGHTS_REQUIRED:
        if not (root / relative_path).is_file():
            errors.append(f"missing licensing control: {relative_path}")
    metadata_path = root / RIGHTS_METADATA
    if not metadata_path.is_file():
        return errors
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return errors + [f"invalid rights metadata: {exc}"]
    if metadata.get("schema_version") != "1.0.0":
        errors.append("rights metadata must declare schema_version 1.0.0")
    if metadata.get("licensor") != "OSHEThai":
        errors.append("rights metadata licensor must be OSHEThai")
    expected_root_license = {"platform": "MPL-2.0", "content": "Apache-2.0"}[repo_kind]
    if metadata.get("root_license") != expected_root_license:
        errors.append(f"rights metadata root license must be {expected_root_license}")
    rules = metadata.get("rules")
    if not isinstance(rules, list) or not rules:
        return errors + ["rights metadata must contain ordered rules"]
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if any(part in RIGHTS_IGNORED_PARTS for part in path.relative_to(root).parts) or path.suffix == ".pyc":
            continue
        matched = next((rule for rule in rules if isinstance(rule, dict) and fnmatch.fnmatchcase(relative, rule.get("path", ""))), None)
        if matched is None:
            errors.append(f"missing rights metadata for {relative}")
            continue
        classification = matched.get("classification")
        license_id = matched.get("license")
        if classification == "THIRD_PARTY_STANDARD_TEXT":
            if not isinstance(matched.get("source"), str) or not matched["source"].strip():
                errors.append(f"third-party standard text lacks provenance: {relative}")
            continue
        allowed = RIGHTS_LICENSES[repo_kind].get(classification)
        if allowed is None or license_id not in allowed:
            errors.append(f"invalid rights classification or license for {relative}")
        if matched.get("copyright") != "OSHEThai":
            errors.append(f"OSHE-authored rights lack OSHEThai attribution: {relative}")
    for license_id in sorted({license_id for values in RIGHTS_LICENSES[repo_kind].values() for license_id in values}):
        if not (root / "LICENSES" / f"{license_id}.txt").is_file():
            errors.append(f"missing standard license text: {license_id}")
    if not (root / "LICENSE").read_bytes().strip():
        errors.append("root LICENSE is empty")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-kind", choices=("platform", "content"), required=True)
    args = parser.parse_args()

    root = pathlib.Path.cwd()
    errors: list[str] = []

    for rel in COMMON_REQUIRED + REPO_REQUIRED[args.repo_kind]:
        if not (root / rel).exists():
            errors.append(f"missing required path: {rel}")

    errors.extend(validate_rights_metadata(root, args.repo_kind))

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
