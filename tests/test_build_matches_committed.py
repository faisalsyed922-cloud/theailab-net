"""The site's committed HTML pages are generated from build/build.py sources
(partials + shared fragments + per-page content). This test is the "done"
contract for that refactor: it fails if the committed pages drift from what
the build script currently produces, which is what actually prevents the
copy-paste drift the site previously had (inconsistent nav conventions,
attribute ordering, duplicated prose) from recurring silently.
"""
import importlib.util
from pathlib import Path

SITE_ROOT = Path(__file__).parent.parent
BUILD_SCRIPT = SITE_ROOT / "build" / "build.py"


def _load_build_module():
    spec = importlib.util.spec_from_file_location("site_build", BUILD_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestBuildIsUpToDate:
    def test_generated_pages_match_committed_pages(self, tmp_path):
        assert BUILD_SCRIPT.exists(), "build/build.py is missing"
        build = _load_build_module()
        build.build(output_root=tmp_path)

        mismatches = []
        for page in build.PAGES:
            generated = (tmp_path / page["path"]).read_text(encoding="utf-8")
            committed = (SITE_ROOT / page["path"]).read_text(encoding="utf-8")
            if generated != committed:
                mismatches.append(page["path"])
        assert not mismatches, (
            f"Committed HTML is out of sync with build/build.py output for: "
            f"{mismatches}. Run `python3 build/build.py` and commit the result."
        )

    def test_build_covers_every_html_page(self, all_html_files):
        build = _load_build_module()
        built_paths = {p["path"] for p in build.PAGES}
        actual_paths = {str(f.relative_to(SITE_ROOT)) for f in all_html_files}
        assert built_paths == actual_paths, (
            f"build/build.py's PAGES list doesn't match the site's HTML files. "
            f"Missing from PAGES: {actual_paths - built_paths}. "
            f"Extra in PAGES: {built_paths - actual_paths}."
        )
