import pytest
from pathlib import Path
from bs4 import BeautifulSoup

SITE_ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="session")
def site_root():
    return SITE_ROOT


@pytest.fixture(scope="session")
def all_html_files(site_root):
    """All deployed HTML pages, excluding .venv and build/ sources.

    build/ holds the partials/shared/content fragments that build/build.py
    combines into the real pages below - those fragments are not standalone
    pages themselves (no DOCTYPE, header, etc.) and must not be checked as
    if they were.
    """
    excluded_dirs = {".venv", "build"}
    return sorted(
        f for f in site_root.rglob("*.html")
        if not excluded_dirs & set(f.relative_to(site_root).parts)
    )


@pytest.fixture(scope="session")
def parsed_pages(all_html_files):
    """Pre-parsed (path, html_string, soup) tuples for every HTML page."""
    pages = []
    for f in all_html_files:
        text = f.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(text, "lxml")
        pages.append((f, text, soup))
    return pages


@pytest.fixture(scope="session")
def nav_pages(all_html_files):
    """All HTML files except 404.html.

    404.html is not linked from navigation or content and is not served by
    the local dev workflow (`python3 -m http.server` has no custom-error-page
    support); it is kept root-relative and structurally valid so it works
    correctly if the site is later hosted somewhere that auto-serves a root
    404.html (e.g., GitHub Pages). It's therefore excluded from
    nav-consistency and reachability-from-index checks.
    """
    return [f for f in all_html_files if f.name != "404.html"]
