"""Unit tests: every HTML page has valid structure and required elements."""
from pathlib import Path

SITE_ROOT = Path(__file__).parent.parent

TITLE_SUFFIX = "– IPHS 400: Frontiers in AI"  # en dash
FOOTER_TEXT = "IPHS 400: Frontiers in AI · Kenyon College"


def _rel(path):
    return str(path.relative_to(SITE_ROOT))


class TestDoctype:
    def test_all_pages_have_doctype(self, parsed_pages):
        """Every HTML page must begin with <!DOCTYPE html>."""
        failures = []
        for path, text, _ in parsed_pages:
            if not text.strip().lower().startswith("<!doctype html"):
                failures.append(_rel(path))
        assert not failures, f"Pages missing <!DOCTYPE html>: {failures[:15]}"


class TestTitle:
    def test_all_titles_end_with_course_suffix(self, parsed_pages):
        """Every <title> must end with '{TITLE_SUFFIX}'."""
        failures = []
        for path, _, soup in parsed_pages:
            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            if not title.endswith(TITLE_SUFFIX):
                failures.append(f"{_rel(path)}: '{title}'")
        assert not failures, f"Titles not ending with course suffix: {failures[:15]}"


class TestCSSLink:
    def test_all_pages_link_to_resolvable_style_css(self, parsed_pages):
        """Every page must have a <link rel='stylesheet'> to a resolvable css/style.css."""
        failures = []
        for path, _, soup in parsed_pages:
            links = [
                tag for tag in soup.find_all("link", rel="stylesheet")
                if "style.css" in tag.get("href", "")
            ]
            if not links:
                failures.append(f"{_rel(path)}: no stylesheet link")
                continue
            href = links[0]["href"]
            if href.startswith("/"):
                target = (SITE_ROOT / href.lstrip("/")).resolve()
            else:
                target = (path.parent / href).resolve()
            if not target.exists():
                failures.append(f"{_rel(path)}: href '{href}' does not resolve")
        assert not failures, f"CSS link issues: {failures[:15]}"


class TestHeaderFooterHero:
    def test_all_pages_have_site_header(self, parsed_pages):
        """Every page must contain a <header class="site-header">."""
        failures = [_rel(p) for p, _, s in parsed_pages if not s.select_one("header.site-header")]
        assert not failures, f"Pages missing header.site-header: {failures[:15]}"

    def test_all_pages_have_site_footer_with_text(self, parsed_pages):
        """Every page must contain a <footer class="site-footer"> with the course footer text."""
        failures = []
        for path, _, soup in parsed_pages:
            footer = soup.select_one("footer.site-footer")
            if not footer:
                failures.append(f"{_rel(path)}: missing footer.site-footer")
                continue
            if FOOTER_TEXT not in footer.get_text():
                failures.append(f"{_rel(path)}: footer text mismatch")
        assert not failures, f"Footer issues: {failures[:15]}"

    def test_all_pages_have_hero_with_h1(self, parsed_pages):
        """Every page must have a <section class="hero"> containing an <h1>."""
        failures = []
        for path, _, soup in parsed_pages:
            hero = soup.select_one("section.hero")
            if not hero:
                failures.append(f"{_rel(path)}: missing section.hero")
                continue
            if not hero.find("h1"):
                failures.append(f"{_rel(path)}: hero has no h1")
        assert not failures, f"Hero section issues: {failures[:15]}"

    def test_hero_is_inside_main_landmark_not_header(self, parsed_pages):
        """The page's <h1> (inside section.hero) must live in the <main>
        landmark, not inside <header>, so screen-reader users navigating by
        landmark encounter the page heading in "main", not "banner"."""
        failures = []
        for path, _, soup in parsed_pages:
            header = soup.select_one("header.site-header")
            main = soup.select_one("main#main")
            if header and header.select_one("section.hero"):
                failures.append(f"{_rel(path)}: hero is nested inside header.site-header")
            if not main or not main.select_one("section.hero"):
                failures.append(f"{_rel(path)}: hero is not nested inside main#main")
        assert not failures, f"Hero landmark issues: {failures[:15]}"


class TestNoLeftoverBranding:
    def test_no_programming_humanity_text(self, parsed_pages):
        """No page should contain leftover 'Programming Humanity' template branding."""
        failures = [
            _rel(path) for path, text, _ in parsed_pages
            if "Programming Humanity" in text
        ]
        assert not failures, f"Pages with leftover 'Programming Humanity' text: {failures[:15]}"

    def test_no_placeholder_notice(self, parsed_pages):
        """No page should contain a .placeholder-notice element."""
        failures = [
            _rel(path) for path, _, soup in parsed_pages
            if soup.select_one(".placeholder-notice")
        ]
        assert not failures, f"Pages with .placeholder-notice: {failures[:15]}"

    def test_no_stub_or_placeholder_strings(self, parsed_pages):
        """No page should contain literal 'Lorem ipsum', 'TBD', or 'TODO' text."""
        failures = []
        for path, text, _ in parsed_pages:
            hits = [s for s in ("Lorem ipsum", "TBD", "TODO") if s in text]
            if hits:
                failures.append(f"{_rel(path)}: {hits}")
        assert not failures, f"Pages with stub/placeholder strings: {failures[:15]}"


class TestAccessibility:
    def test_every_page_has_a_skip_link_to_main(self, parsed_pages):
        """Body's first element must be a skip-link pointing at #main, and
        the target must exist."""
        failures = []
        for path, _, soup in parsed_pages:
            body = soup.body
            first = body.find(True) if body else None
            if not first or first.name != "a" or "skip-link" not in first.get("class", []):
                failures.append(f"{_rel(path)}: body's first element is not a .skip-link <a>")
                continue
            if first.get("href") != "#main":
                failures.append(f"{_rel(path)}: skip-link href is '{first.get('href')}', expected '#main'")
                continue
            if not soup.select_one("main#main"):
                failures.append(f"{_rel(path)}: no element with id='main' for the skip-link to target")
        assert not failures, f"Skip-link issues: {failures[:15]}"

    def test_active_nav_item_has_aria_current(self, parsed_pages):
        """Every nav <a class="active"> must also carry aria-current="page"."""
        failures = []
        for path, _, soup in parsed_pages:
            active = soup.select_one("nav.main-nav a.active")
            if not active:
                continue  # 404.html has no active nav item by design
            if active.get("aria-current") != "page":
                failures.append(f"{_rel(path)}: active nav link missing aria-current=\"page\"")
        assert not failures, f"aria-current issues: {failures[:15]}"

    def test_exactly_one_h1_per_page(self, parsed_pages):
        """Every page must have exactly one <h1>."""
        failures = []
        for path, _, soup in parsed_pages:
            count = len(soup.find_all("h1"))
            if count != 1:
                failures.append(f"{_rel(path)}: {count} <h1> elements")
        assert not failures, f"h1 count issues: {failures[:15]}"

    def test_no_skipped_heading_levels(self, parsed_pages):
        """Heading levels (h1-h6, in document order) must never jump more
        than one level deeper than the deepest level seen so far."""
        failures = []
        for path, _, soup in parsed_pages:
            levels = [int(h.name[1]) for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])]
            max_seen = 0
            for level in levels:
                if level > max_seen + 1:
                    failures.append(f"{_rel(path)}: jumps to h{level} without a preceding h{max_seen + 1}")
                    break
                max_seen = max(max_seen, level)
        assert not failures, f"Skipped heading levels: {failures[:15]}"


class TestMetadata:
    def test_all_pages_have_a_favicon_link(self, parsed_pages):
        """Every page must have a <link rel="icon"> resolving to an existing file."""
        failures = []
        for path, _, soup in parsed_pages:
            icon = soup.find("link", rel="icon")
            if not icon or not icon.get("href"):
                failures.append(f"{_rel(path)}: no <link rel='icon'>")
                continue
            href = icon["href"]
            target = (
                (SITE_ROOT / href.lstrip("/")).resolve()
                if href.startswith("/")
                else (path.parent / href).resolve()
            )
            if not target.exists():
                failures.append(f"{_rel(path)}: favicon href '{href}' does not resolve")
        assert not failures, f"Favicon issues: {failures[:15]}"

    def test_all_pages_have_a_meta_description(self, parsed_pages):
        """Every page must have a non-empty <meta name="description"> under 160 chars."""
        failures = []
        for path, _, soup in parsed_pages:
            meta = soup.find("meta", attrs={"name": "description"})
            content = meta.get("content", "").strip() if meta else ""
            if not content:
                failures.append(f"{_rel(path)}: missing/empty meta description")
            elif len(content) > 160:
                failures.append(f"{_rel(path)}: description is {len(content)} chars (>160)")
        assert not failures, f"Meta description issues: {failures[:15]}"

    def test_favicon_uses_same_relative_depth_as_stylesheet(self, parsed_pages):
        """The favicon link must use the same relative-path convention as the
        stylesheet link (same page, same depth), not a hardcoded root-relative
        path - otherwise the two silently diverge on how portable they are to
        a subpath-hosted deployment."""
        failures = []
        for path, _, soup in parsed_pages:
            icon = soup.find("link", rel="icon")
            css_link = soup.find("link", rel="stylesheet")
            if not icon or not css_link:
                continue  # covered by other tests
            icon_href = icon.get("href", "")
            css_href = css_link.get("href", "")
            css_prefix = css_href.rsplit("css/style.css", 1)[0]
            expected_favicon_href = f"{css_prefix}favicon.svg"
            if icon_href != expected_favicon_href:
                failures.append(
                    f"{_rel(path)}: favicon href '{icon_href}' does not match "
                    f"stylesheet's relative-depth convention (expected '{expected_favicon_href}')"
                )
        assert not failures, f"Favicon path-convention issues: {failures[:15]}"

    def test_all_pages_have_open_graph_and_twitter_card_tags(self, parsed_pages):
        """Every page must have non-empty og:title, og:description, og:type,
        and twitter:card tags, so links shared in Slack/email/Moodle show a
        preview."""
        failures = []
        for path, _, soup in parsed_pages:
            og_title = soup.find("meta", attrs={"property": "og:title"})
            og_desc = soup.find("meta", attrs={"property": "og:description"})
            og_type = soup.find("meta", attrs={"property": "og:type"})
            tw_card = soup.find("meta", attrs={"name": "twitter:card"})
            for label, tag in (
                ("og:title", og_title), ("og:description", og_desc),
                ("og:type", og_type), ("twitter:card", tw_card),
            ):
                if not tag or not tag.get("content", "").strip():
                    failures.append(f"{_rel(path)}: missing/empty {label}")
        assert not failures, f"Open Graph / Twitter Card issues: {failures[:15]}"


class TestPunctuationEncoding:
    def test_no_mdash_or_ndash_entities(self, parsed_pages):
        """Dashes must use the literal —/– characters (the convention used
        site-wide in the header), not the &mdash;/&ndash; HTML entities."""
        failures = []
        for path, text, _ in parsed_pages:
            hits = [s for s in ("&mdash;", "&ndash;") if s in text]
            if hits:
                failures.append(f"{_rel(path)}: {hits}")
        assert not failures, f"Pages using dash entities instead of literal characters: {failures[:15]}"

    def test_no_quote_entities(self, parsed_pages):
        """Curly quotes must use the literal "/'/'/" characters (the
        convention used site-wide, e.g. core/syllabus.html), not the
        &ldquo;/&rdquo;/&lsquo;/&rsquo; HTML entities or their numeric
        equivalents."""
        failures = []
        quote_entities = (
            "&ldquo;", "&rdquo;", "&lsquo;", "&rsquo;",
            "&#8220;", "&#8221;", "&#8216;", "&#8217;",
        )
        for path, text, _ in parsed_pages:
            hits = [s for s in quote_entities if s in text]
            if hits:
                failures.append(f"{_rel(path)}: {hits}")
        assert not failures, f"Pages using quote entities instead of literal characters: {failures[:15]}"


class TestRepoURLIsLinked:
    def test_github_repo_url_is_a_clickable_link_wherever_it_appears(self, parsed_pages):
        """Wherever the course repo URL appears as visible text, it must be
        wrapped in a clickable <a href> to that same URL, not inert text."""
        repo_url = "https://github.com/jon-chun/theailab-net"
        failures = []
        for path, _, soup in parsed_pages:
            for el in soup.find_all(string=lambda s: s and repo_url in s):
                link = el.find_parent("a")
                if not link or link.get("href") != repo_url:
                    failures.append(f"{_rel(path)}: repo URL text not wrapped in a matching <a href>")
        assert not failures, f"Un-linked repo URL text: {failures[:15]}"


class TestContentNotEmpty:
    def test_page_content_has_minimum_text(self, parsed_pages):
        """Every page's .page-content div must have at least 20 characters of stripped text."""
        failures = []
        for path, _, soup in parsed_pages:
            content_div = soup.select_one(".page-content")
            if not content_div:
                failures.append(f"{_rel(path)}: missing .page-content")
                continue
            text = content_div.get_text(strip=True)
            if len(text) < 20:
                failures.append(f"{_rel(path)}: only {len(text)} chars")
        assert not failures, f"Pages with near-empty .page-content: {failures[:15]}"
