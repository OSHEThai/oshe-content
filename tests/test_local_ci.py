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
LOCAL_CI_RUNNER = REPOSITORY_ROOT / "tools" / "run_local_ci.py"


class LocalCiFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self.root = Path(self._temporary_directory.name).resolve()
        self.runner_digest = hashlib.sha256(LOCAL_CI_RUNNER.read_bytes()).digest()
        self._initialize_git_fixture()

    def _initialize_git_fixture(self) -> None:
        completed = subprocess.run(
            ["git", "init", "-q"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def _write_config(self, checks: list[dict[str, object]]) -> None:
        config_path = self.root / ".ci" / "local-ci.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            json.dumps({"schema_version": "1.0.0", "checks": checks}) + "\n",
            encoding="utf-8",
        )

    def _run_runner(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [sys.executable, str(LOCAL_CI_RUNNER), *arguments],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            timeout=20,
            env=environment,
        )
        self.assertEqual(hashlib.sha256(LOCAL_CI_RUNNER.read_bytes()).digest(), self.runner_digest)
        return completed

    def test_batch_collects_all_results_without_fail_fast(self) -> None:
        self._write_config(
            [
                {
                    "id": "failing-check",
                    "command": [
                        "python",
                        "-B",
                        "-c",
                        "from pathlib import Path; Path('first-ran').write_text('ran', encoding='utf-8'); raise SystemExit(1)",
                    ],
                },
                {
                    "id": "passing-check",
                    "command": [
                        "python",
                        "-B",
                        "-c",
                        "from pathlib import Path; Path('second-ran').write_text('ran', encoding='utf-8')",
                    ],
                },
            ]
        )

        completed = self._run_runner("--mode", "incremental", "--no-checkpoint")

        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue((self.root / "first-ran").is_file())
        self.assertTrue((self.root / "second-ran").is_file())
        self.assertIn("RUN  failing-check", completed.stdout)
        self.assertIn("RUN  passing-check", completed.stdout)
        self.assertIn("Failed checks: failing-check", completed.stderr)

        outside_config = self._run_runner(
            "--mode", "incremental", "--config", "../outside-local-ci.json"
        )
        self.assertNotEqual(outside_config.returncode, 0)
        self.assertIn("CI configuration must remain inside the repository", outside_config.stderr)

    def test_unchanged_pass_is_checkpointed_and_skipped(self) -> None:
        command = [
            "python",
            "-B",
            "-c",
            (
                "from pathlib import Path; "
                "p=Path('.local-ci/run-count.txt'); "
                "p.parent.mkdir(exist_ok=True); "
                "p.write_text((p.read_text(encoding='utf-8') if p.exists() else '') + 'run\\n', encoding='utf-8')"
            ),
        ]
        self._write_config([{"id": "stable-check", "command": command}])

        first = self._run_runner("--mode", "incremental")
        count_path = self.root / ".local-ci/run-count.txt"
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertTrue((self.root / ".local-ci/checkpoints.json").is_file())
        self.assertEqual(count_path.read_text(encoding="utf-8"), "run\n")

        second = self._run_runner("--mode", "incremental")

        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("SKIP stable-check: unchanged passing checkpoint", second.stdout)
        self.assertEqual(count_path.read_text(encoding="utf-8"), "run\n")

    def test_full_ci_requires_milestone_close(self) -> None:
        self._write_config(
            [
                {
                    "id": "fixture-check",
                    "command": ["python", "-B", "-c", "pass"],
                }
            ]
        )

        missing_milestone = self._run_runner("--mode", "full")

        self.assertNotEqual(missing_milestone.returncode, 0)
        self.assertIn("Full CI is permitted only with --milestone-close", missing_milestone.stderr)

        valid_full = self._run_runner(
            "--mode", "full", "--milestone-close", "fixture-milestone"
        )

        self.assertEqual(valid_full.returncode, 0, valid_full.stderr)
        self.assertIn("Milestone closure: fixture-milestone", valid_full.stdout)


if __name__ == "__main__":
    unittest.main()
