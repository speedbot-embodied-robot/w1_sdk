"""Regression cases for mistakes VitePress may silently accept."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from verify_snippets import verify


class SnippetChecks(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "examples" / "sample.py"
        self.source.parent.mkdir()
        self.source.write_text("# region core\nprint(1)\n# endregion core\n")
        for lang in ("zh", "en"):
            page = self.root / "docs" / lang / "sample.md"
            page.parent.mkdir(parents=True)
            page.write_text("<<< ../../examples/sample.py#core{python}\n")

    def test_shared_source(self):
        verify(self.root)

    def test_missing_file(self):
        self.source.unlink()
        with self.assertRaisesRegex(ValueError, "missing or external"):
            verify(self.root)

    def test_missing_region(self):
        self.source.write_text("print(1)\n")
        with self.assertRaisesRegex(ValueError, "missing or malformed region"):
            verify(self.root)

    def test_empty_region(self):
        self.source.write_text("# region core\n\n# endregion core\n")
        with self.assertRaisesRegex(ValueError, "empty code"):
            verify(self.root)

    def test_translation_drift(self):
        page = self.root / "docs/en/sample.md"
        page.write_text("<<< ../../examples/sample.py{python}\n")
        with self.assertRaisesRegex(ValueError, "different source"):
            verify(self.root)

    def test_empty_file(self):
        self.source.write_text("")
        for page in (self.root / "docs").rglob("*.md"):
            page.write_text("<<< ../../examples/sample.py{python}\n")
        with self.assertRaisesRegex(ValueError, "empty code"):
            verify(self.root)

    def test_no_space_still_checks_source(self):
        (self.root / "docs/zh/sample.md").write_text("<<<../../examples/missing.py\n")
        with self.assertRaisesRegex(ValueError, "missing or external"):
            verify(self.root)

    def test_mismatched_region_comment_types(self):
        self.source.write_text("// region core\nprint(1)\n# endregion core\n")
        with self.assertRaisesRegex(ValueError, "missing or malformed region"):
            verify(self.root)

    def test_empty_import_path(self):
        (self.root / "docs/zh/sample.md").write_text("<<< \n")
        with self.assertRaisesRegex(ValueError, "empty source path"):
            verify(self.root)


if __name__ == "__main__":
    unittest.main()
