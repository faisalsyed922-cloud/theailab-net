"""README.md's documentation of the test suite must not fall behind the
actual contents of tests/ - otherwise a contributor reading the README won't
know a given test file (or dependency) exists.
"""
from pathlib import Path

SITE_ROOT = Path(__file__).parent.parent
README = SITE_ROOT / "README.md"
TESTS_DIR = Path(__file__).parent


class TestReadmeDocumentsTestSuite:
    def test_readme_mentions_every_test_file(self):
        test_files = sorted(
            f.name for f in TESTS_DIR.glob("test_*.py")
        )
        assert test_files, "No test_*.py files found in tests/"
        readme_text = README.read_text(encoding="utf-8")
        missing = [f for f in test_files if f not in readme_text]
        assert not missing, f"README.md does not mention: {missing}"

    def test_readme_mentions_html5lib_dependency(self):
        readme_text = README.read_text(encoding="utf-8")
        assert "html5lib" in readme_text, (
            "tests/requirements.txt pins html5lib but README.md's test-suite "
            "description doesn't mention it"
        )
