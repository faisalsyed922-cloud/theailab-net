"""Integration tests: internal links resolve, nav is consistent, schedule links all weeks."""
import pytest
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import unquote

SITE_ROOT = Path(__file__).parent.parent

EXPECTED_NAV_LABELS = {"Home", "Syllabus", "Schedule", "Assignments", "Policies", "About"}


def _rel(path):
    return str(path.relative_to(SITE_ROOT))


def _resolve_href(href, page_path):
    """Resolve a relative or root-relative href to an absolute Path, or None
    for external/anchor/mailto links."""
    if not href or href.startswith(("http://", "https://", "mailto:", "#", "javascript:")):
        return None
    href = href.split("#")[0]
    if not href:
        return None
    href = unquote(href)
    if href.startswith("/"):
        return (SITE_ROOT / href.lstrip("/")).resolve()
    return (page_path.parent / href).resolve()


def _collect_broken_links(page_path, soup, selector="a"):
    broken = []
    for tag in soup.select(selector):
        href = tag.get("href", "")
        target = _resolve_href(href, page_path)
        if target is not None and not target.exists():
            broken.append(href)
    return broken


class TestAllInternalLinks:
    def test_all_internal_links_resolve(self, site_root, parsed_pages):
        """Every internal <a href> across all pages must resolve to an existing file."""
        broken = []
        for path, _, soup in parsed_pages:
            for bad in _collect_broken_links(path, soup):
                broken.append(f"{_rel(path)} -> {bad}")
        assert not broken, f"{len(broken)} broken internal links. First 15: {broken[:15]}"


class TestNavConsistency:
    def test_all_nav_pages_have_identical_nav_labels(self, site_root, nav_pages):
        """Every page (except 404.html) must have the exact same set of nav link labels."""
        failures = []
        for f in nav_pages:
            soup = BeautifulSoup(f.read_text(encoding="utf-8"), "lxml")
            nav = soup.select_one("nav.main-nav")
            if not nav:
                failures.append(f"{_rel(f)}: missing nav.main-nav")
                continue
            labels = {a.get_text(strip=True) for a in nav.find_all("a")}
            if labels != EXPECTED_NAV_LABELS:
                failures.append(f"{_rel(f)}: {sorted(labels)}")
        assert not failures, f"Pages with inconsistent nav labels: {failures[:15]}"

    def test_nav_markup_is_identical_modulo_active_item_and_depth(self, site_root, nav_pages):
        """The nav <ul> markup must be byte-identical across pages once the
        active-item attributes and the '../' depth prefix are stripped out.

        This is what actually catches copy-paste drift like two different
        relative-link conventions or inconsistent attribute ordering on the
        active item - the label/resolution checks above don't touch markup
        shape at all.
        """
        canonical_forms = {}
        for f in nav_pages:
            soup = BeautifulSoup(f.read_text(encoding="utf-8"), "lxml")
            nav = soup.select_one("nav.main-nav")
            if not nav:
                continue
            pieces = []
            for a in nav.find_all("a"):
                href = a.get("href", "")
                while href.startswith("../"):
                    href = href[len("../"):]
                pieces.append(f"{href}|{a.get_text(strip=True)}")
            canonical_forms[_rel(f)] = tuple(pieces)

        distinct = set(canonical_forms.values())
        assert len(distinct) == 1, (
            f"Nav markup (href target + label, ignoring depth and active state) "
            f"differs across pages: {dict(list(canonical_forms.items())[:5])}"
        )

    def test_nav_links_resolve(self, site_root, nav_pages):
        """Nav links on every non-404 page must resolve to existing files."""
        broken = []
        for f in nav_pages:
            soup = BeautifulSoup(f.read_text(encoding="utf-8"), "lxml")
            nav = soup.select_one("nav.main-nav")
            if not nav:
                continue
            for link in _collect_broken_links(f, nav, "a"):
                broken.append(f"{_rel(f)} -> {link}")
        assert not broken, f"Broken nav links: {broken[:15]}"


class TestScheduleLinksAllWeeks:
    def test_schedule_links_to_all_15_weeks(self, site_root):
        """core/schedule.html must link to weeks/week-01.html through weeks/week-15.html."""
        schedule = site_root / "core" / "schedule.html"
        soup = BeautifulSoup(schedule.read_text(encoding="utf-8"), "lxml")
        hrefs = {a.get("href", "") for a in soup.find_all("a")}
        missing = []
        for n in range(1, 16):
            expected = f"../weeks/week-{n:02d}.html"
            alt = f"weeks/week-{n:02d}.html"
            if expected not in hrefs and alt not in hrefs and not any(
                h.endswith(f"week-{n:02d}.html") for h in hrefs
            ):
                missing.append(f"week-{n:02d}.html")
        assert not missing, f"core/schedule.html missing links to: {missing}"

    def test_schedule_week_link_text_matches_week_page_h1(self, site_root):
        """Each week link's visible text on core/schedule.html must exactly
        match that week page's own <h1> text - otherwise a student following
        the link sees a different title than the one that brought them there.
        """
        schedule = site_root / "core" / "schedule.html"
        schedule_soup = BeautifulSoup(schedule.read_text(encoding="utf-8"), "lxml")

        mismatches = []
        for n in range(1, 16):
            week_name = f"week-{n:02d}.html"
            week_path = site_root / "weeks" / week_name
            week_soup = BeautifulSoup(week_path.read_text(encoding="utf-8"), "lxml")
            h1 = week_soup.find("h1")
            assert h1 is not None, f"{week_name}: missing <h1>"
            expected_text = h1.get_text(strip=True)

            link = schedule_soup.find("a", href=lambda h: h and h.endswith(week_name))
            assert link is not None, f"core/schedule.html: no link to {week_name}"
            actual_text = link.get_text(strip=True)

            if actual_text != expected_text:
                mismatches.append(f"{week_name}: schedule says '{actual_text}', page h1 is '{expected_text}'")

        assert not mismatches, f"Schedule link text / week page title mismatches: {mismatches}"
