"""HTML validation: every page must parse cleanly under html5lib's strict
parser. BeautifulSoup+lxml (used elsewhere in this suite) is lenient and
silently repairs malformed markup, so it can't catch structural errors the
way a spec-conformant parser can.
"""
from pathlib import Path
import html5lib

SITE_ROOT = Path(__file__).parent.parent


class TestHTML5Validity:
    def test_all_pages_parse_without_errors(self, all_html_files):
        parser = html5lib.HTMLParser(strict=False)
        failures = []
        for path in all_html_files:
            text = path.read_text(encoding="utf-8", errors="replace")
            parser.parse(text)
            if parser.errors:
                messages = [f"{pos}: {code} {data}" for pos, code, data in parser.errors]
                failures.append(f"{path.relative_to(SITE_ROOT)}: {messages[:5]}")
        assert not failures, f"HTML5 parse errors: {failures[:15]}"
