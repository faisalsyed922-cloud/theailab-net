"""404.html is not served by the local dev workflow, but must stay correct-by-
construction for hosts (e.g. GitHub Pages) that auto-serve a root 404.html
while keeping the originally-requested (possibly nested) URL in the address
bar. Page-relative paths would resolve against the wrong directory in that
case, so every internal link/asset must be root-relative.
"""
from pathlib import Path
from bs4 import BeautifulSoup

SITE_ROOT = Path(__file__).parent.parent


class TestNotFoundPageIsRootRelative:
    def test_stylesheet_link_is_root_relative(self):
        soup = BeautifulSoup((SITE_ROOT / "404.html").read_text(encoding="utf-8"), "lxml")
        link = soup.find("link", rel="stylesheet")
        assert link is not None, "404.html has no stylesheet link"
        assert link["href"].startswith("/"), f"stylesheet href not root-relative: {link['href']}"

    def test_all_internal_hrefs_are_root_relative(self):
        soup = BeautifulSoup((SITE_ROOT / "404.html").read_text(encoding="utf-8"), "lxml")
        failures = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith(("http://", "https://", "mailto:", "#", "javascript:")):
                continue
            if not href.startswith("/"):
                failures.append(href)
        assert not failures, f"404.html has page-relative internal links: {failures}"
