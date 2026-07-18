from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from parallel_research.models import Citation, Depth, ResearchResult, RunStatus, Usage
from parallel_research.orchestrator import fetch, resume_run, validate_run
from parallel_research.providers.base import BaseProvider, ProgressCallback


class FakeProvider(BaseProvider):
    name = "fake"

    @property
    def available(self) -> bool:
        return True

    async def research(
        self,
        topic: str,
        depth: Depth,
        progress: ProgressCallback | None = None,
    ) -> ResearchResult:
        return ResearchResult(
            provider=self.name,
            model="fake-grounded-1",
            content=f"Evidence for {topic} [1].",
            duration_seconds=0.01,
            citations=[Citation("https://example.com/source", "Primary source", self.name)],
            usage=Usage(input_tokens=10, output_tokens=20, total_tokens=30),
            request_id="request-1",
        )


class ResumableProvider(FakeProvider):
    name = "resumable"

    async def research(
        self,
        topic: str,
        depth: Depth,
        progress: ProgressCallback | None = None,
    ) -> ResearchResult:
        if progress:
            await progress(
                {
                    "status": RunStatus.RUNNING,
                    "request_id": "background-1",
                    "model": "fake-deep",
                }
            )
        return ResearchResult(
            provider=self.name,
            model="fake-deep",
            content="",
            duration_seconds=0.01,
            status=RunStatus.RESUMABLE,
            request_id="background-1",
            error="Still running",
        )

    async def resume(
        self,
        request_id: str,
        depth: Depth,
        progress: ProgressCallback | None = None,
    ) -> ResearchResult:
        return ResearchResult(
            provider=self.name,
            model="fake-deep",
            content="Completed grounded research.",
            duration_seconds=0.01,
            request_id=request_id,
            citations=[Citation("https://example.org/evidence", provider=self.name)],
        )


class OrchestratorTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_writes_valid_isolated_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / ".research"
            manifest, directory = await fetch(
                "A test topic",
                Depth.QUICK,
                ["fake"],
                output,
                project_dir=Path(temporary),
                provider_registry={"fake": FakeProvider},
            )
            self.assertEqual(manifest.status, RunStatus.SUCCEEDED)
            self.assertTrue((directory / "raw" / "fake.md").is_file())
            self.assertEqual(validate_run(directory), [])
            self.assertEqual(
                manifest.providers["fake"].citations[0]["url"],
                "https://example.com/source",
            )

    async def test_background_run_can_be_resumed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / ".research"
            manifest, _ = await fetch(
                "A deep topic",
                Depth.DEEP,
                ["resumable"],
                output,
                project_dir=Path(temporary),
                provider_registry={"resumable": ResumableProvider},
            )
            self.assertEqual(manifest.status, RunStatus.RESUMABLE)
            resumed, directory = await resume_run(
                output,
                manifest.run_id,
                project_dir=Path(temporary),
                provider_registry={"resumable": ResumableProvider},
            )
            self.assertEqual(resumed.status, RunStatus.SUCCEEDED)
            self.assertIn(
                "Completed grounded research", (directory / "raw/resumable.md").read_text()
            )

    async def test_validation_reports_scalar_frontmatter_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / ".research"
            manifest, directory = await fetch(
                "A test topic",
                Depth.QUICK,
                ["fake"],
                output,
                project_dir=Path(temporary),
                provider_registry={"fake": FakeProvider},
            )
            raw_relative = manifest.providers["fake"].raw_file
            self.assertIsNotNone(raw_relative)
            assert raw_relative is not None
            raw_file = directory / raw_relative
            raw_file.write_text("---\nscalar\n---\n\ncontent", encoding="utf-8")
            self.assertEqual(validate_run(directory), ["fake: frontmatter must be a mapping"])


if __name__ == "__main__":
    unittest.main()
