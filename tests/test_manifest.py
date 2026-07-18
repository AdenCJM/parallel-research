from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from parallel_research.manifest import (
    create_manifest,
    load_manifest,
    make_run_id,
    record_artifact,
    slugify,
)
from parallel_research.models import Depth


class ManifestTests(unittest.TestCase):
    def test_slugify_is_safe_and_has_fallback(self) -> None:
        self.assertEqual(slugify("Crème brûlée & AI"), "creme-brulee-ai")
        self.assertEqual(slugify("研究"), "research")
        self.assertLessEqual(len(slugify("word " * 100)), 60)

    def test_run_ids_do_not_collide_in_same_second(self) -> None:
        now = datetime(2026, 7, 18, 7, 45, 12, tzinfo=UTC)
        first = make_run_id("same topic", now)
        second = make_run_id("same topic", now)
        self.assertNotEqual(first, second)
        self.assertTrue(first.endswith("same-topic"))

    def test_manifest_round_trip_and_run_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / ".research"
            first, first_dir = create_manifest(root, "Topic one", Depth.QUICK, ["fake"])
            second, second_dir = create_manifest(root, "Topic two", Depth.QUICK, ["fake"])
            self.assertNotEqual(first_dir, second_dir)
            self.assertEqual(load_manifest(first_dir).run_id, first.run_id)
            self.assertEqual(load_manifest(second_dir).run_id, second.run_id)
            self.assertTrue((root / "index.yaml").is_file())

    def test_artifacts_must_exist_inside_selected_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / ".research"
            manifest, directory = create_manifest(root, "Topic", Depth.QUICK, ["fake"])
            artifact = directory / "structured" / "fake.md"
            artifact.write_text(
                f"---\nrun_id: {manifest.run_id}\nprovider: fake\n---\n\nstructured\n",
                encoding="utf-8",
            )
            updated = record_artifact(
                root,
                manifest.run_id,
                "structured/fake.md",
                provider="fake",
            )
            self.assertEqual(updated.providers["fake"].structured_file, "structured/fake.md")
            with self.assertRaises(ValueError):
                record_artifact(
                    root,
                    manifest.run_id,
                    "../../outside.md",
                    provider="fake",
                )


if __name__ == "__main__":
    unittest.main()
