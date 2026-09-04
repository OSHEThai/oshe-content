from __future__ import annotations

import json
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPOSITORY_ROOT / "tools" / "validate_repository.py"

COMMON_REQUIRED = (
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
)

CONTENT_REQUIRED = (
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
)


class ContentValidatorFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self.root = Path(self._temporary_directory.name).resolve()
        self.assertNotEqual(self.root, REPOSITORY_ROOT)
        self.validator_digest = hashlib.sha256(VALIDATOR.read_bytes()).digest()
        self._create_valid_fixture()

    def _write_text(self, relative_path: str, content: str) -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _write_json(self, relative_path: str, value: object) -> None:
        self._write_text(relative_path, json.dumps(value) + "\n")

    def _profile(self, *, pinned: bool = False) -> dict[str, object]:
        return {
            "schema_version": "1.0.0",
            "canonical_repository": "OSHEThai/oshe-platform",
            "canonical_ref": "a" * 40 if pinned else None,
            "control_status": (
                "PINNED_CANONICAL_CONTROLS_DISPATCH_DISABLED"
                if pinned
                else "UNPINNED_PREPARATION_ONLY"
            ),
            "dispatch_enabled": False,
            "authority_basis": ["ADR-0005", "ADR-0006", "ADR-0007"],
            "repository_workflow": {
                "full_ci": "MILESTONE_CLOSE_ONLY_LOCAL_THEN_GITHUB"
            },
        }

    def _write_profile(self, profile: dict[str, object]) -> None:
        self._write_json(".ai/repository-profile.json", profile)

    def _create_valid_fixture(self) -> None:
        for relative_path in COMMON_REQUIRED + CONTENT_REQUIRED:
            if relative_path == ".ai/repository-profile.json":
                self._write_profile(self._profile())
            elif relative_path == ".ci/local-ci.json":
                self._write_json(
                    relative_path,
                    {
                        "checks": [
                            {
                                "id": "fixture-check",
                                "command": ["python", "-B", "-c", "pass"],
                            }
                        ]
                    },
                )
            elif relative_path == "repo-manifest.yaml":
                self._write_text(
                    relative_path,
                    "schema_version: 1.0.0\nrepository: oshe-content\n",
                )
            elif relative_path.endswith(".json"):
                self._write_json(relative_path, {})
            else:
                self._write_text(relative_path, "fixture\n")
        self._write_text("LICENSE", "Apache-2.0 fixture text\n")
        self._write_text("DCO-1.1.txt", "DCO fixture text\n")
        self._write_text("NOTICE.md", "Notice fixture\n")
        for license_id in ("Apache-2.0", "CC-BY-4.0", "CC-BY-SA-4.0"):
            self._write_text(f"LICENSES/{license_id}.txt", "license fixture\n")
        self._write_json(
            "RIGHTS-METADATA.json",
            {
                "schema_version": "1.0.0",
                "repository": "OSHEThai/oshe-content",
                "licensor": "OSHEThai",
                "root_license": "Apache-2.0",
                "rules": [
                    {
                        "path": "LICENSE",
                        "classification": "THIRD_PARTY_STANDARD_TEXT",
                        "license": "Apache-2.0",
                        "source": "fixture",
                    },
                    {
                        "path": "LICENSES/**",
                        "classification": "THIRD_PARTY_STANDARD_TEXT",
                        "license": "SPDX_STANDARD_TEXT",
                        "source": "fixture",
                    },
                    {
                        "path": "DCO-1.1.txt",
                        "classification": "THIRD_PARTY_STANDARD_TEXT",
                        "license": "DCO-1.1",
                        "source": "fixture",
                    },
                    {
                        "path": "**",
                        "classification": "OSHE_AUTHORED_PRACTICAL_CONTENT",
                        "license": "CC-BY-SA-4.0",
                        "copyright": "OSHEThai",
                    },
                ],
            },
        )

    def _run_validator(self) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [sys.executable, str(VALIDATOR), "--repo-kind", "content"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            timeout=10,
            env=environment,
        )
        self.assertEqual(hashlib.sha256(VALIDATOR.read_bytes()).digest(), self.validator_digest)
        return completed

    def test_valid_content_repository_passes(self) -> None:
        completed = self._run_validator()

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Foundation validation passed for content.", completed.stdout)

    def test_valid_unpinned_profile_passes(self) -> None:
        self._write_profile(self._profile())

        completed = self._run_validator()

        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_valid_pinned_profile_passes(self) -> None:
        self._write_profile(self._profile(pinned=True))

        completed = self._run_validator()

        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_valid_json_syntax_passes(self) -> None:
        self._write_json("scalar.json", "fixture")
        self._write_json("array.json", ["fixture"])
        self._write_json("object.json", {"fixture": True})

        completed = self._run_validator()

        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_bootstrap_placeholders_notice_only(self) -> None:
        self._write_text("README.md", "owner: __GITHUB_ORG__\n")

        completed = self._run_validator()

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("NOTICE: bootstrap placeholders remain in:", completed.stdout)
        self.assertIn("README.md", completed.stdout)

    def test_missing_common_required_file_fails(self) -> None:
        (self.root / "README.md").unlink()

        completed = self._run_validator()

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("missing required path: README.md", completed.stderr)

    def test_missing_rights_metadata_fails_closed(self) -> None:
        (self.root / "RIGHTS-METADATA.json").unlink()

        completed = self._run_validator()

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("missing licensing control: RIGHTS-METADATA.json", completed.stderr)

    def test_missing_content_required_file_fails(self) -> None:
        (self.root / "packs/common/README.md").unlink()

        completed = self._run_validator()

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("missing required path: packs/common/README.md", completed.stderr)

    def test_malformed_json_syntax_fails(self) -> None:
        self._write_text("broken.json", '{"fixture":\n')

        completed = self._run_validator()

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("invalid JSON broken.json", completed.stderr)

    def test_missing_repository_key_in_manifest_fails(self) -> None:
        self._write_text("repo-manifest.yaml", "schema_version: 1.0.0\n")

        completed = self._run_validator()

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("repo-manifest.yaml lacks repository key", completed.stderr)

    def test_secret_patterns_detected_fails(self) -> None:
        synthetic_secret = "ghp_" + ("A" * 24)
        self._write_text("synthetic-secret.txt", synthetic_secret + "\n")

        completed = self._run_validator()
        diagnostics = completed.stdout + completed.stderr

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("synthetic-secret.txt", diagnostics)
        self.assertNotIn(synthetic_secret, diagnostics)

    def test_invalid_profile_canonical_repository_fails(self) -> None:
        profile = self._profile()
        profile["canonical_repository"] = "unapproved/repository"
        self._write_profile(profile)

        completed = self._run_validator()

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("content agent profile must resolve to OSHEThai/oshe-platform", completed.stderr)

    def test_unpinned_profile_with_non_null_canonical_ref_fails(self) -> None:
        profile = self._profile()
        profile["canonical_ref"] = "unexpected-ref"
        self._write_profile(profile)

        completed = self._run_validator()

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("un-pinned content profile must have canonical_ref null", completed.stderr)

    def test_pinned_profile_invalid_sha_format_fails(self) -> None:
        profile = self._profile(pinned=True)
        profile["canonical_ref"] = "A" * 40
        self._write_profile(profile)

        completed = self._run_validator()

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("content agent profile canonical_ref must be an exact lowercase 40-character commit SHA", completed.stderr)

    def test_invalid_profile_authority_or_workflow_fails(self) -> None:
        profile = self._profile()
        profile["authority_basis"] = ["ADR-0005"]
        self._write_profile(profile)
        authority_failure = self._run_validator()

        self.assertNotEqual(authority_failure.returncode, 0)
        self.assertIn("content agent profile authority basis must include ADR-0005 through ADR-0007", authority_failure.stderr)

        profile = self._profile()
        profile["repository_workflow"] = {"full_ci": "UNRESTRICTED"}
        self._write_profile(profile)
        workflow_failure = self._run_validator()

        self.assertNotEqual(workflow_failure.returncode, 0)
        self.assertIn("content agent profile must limit Full CI to Milestone closure, local then GitHub", workflow_failure.stderr)


if __name__ == "__main__":
    unittest.main()
