# IPHS 400: Frontiers in AI

**Kenyon College — Integrated Program for Humane Studies (IPHS) — Fall 2026**

Course website for IPHS 400, a hands-on study of AI software engineering (AI-SWE):
configuring, extending, and orchestrating AI coding agents through a professional
software development lifecycle. This repository contains the site's source and
its test suite; course submissions, quizzes, and grades are handled separately
on Moodle.

- **Instructor:** Jon Chun
- **Schedule:** Tu/Th, 2:40–4:00 PM · Timberlake #5 (Evans Conference Room)

## Repository Structure

```
.
├── index.html              # Home page
├── 404.html                 # Not-found page (see note below)
├── core/                    # Syllabus, schedule, assignments, policies, about
│   ├── syllabus.html
│   ├── schedule.html
│   ├── assignments.html
│   ├── policies.html
│   └── about.html
├── weeks/                   # One page per week, week-01.html … week-15.html
├── css/
│   └── style.css            # Single shared stylesheet
├── build/                   # Source of truth for the generated HTML pages
│   ├── build.py             # Regenerates every page (see below)
│   ├── partials/            # Shared header/head/footer templates
│   ├── shared/               # Prose blocks reused across multiple pages
│   └── content/              # Per-page unique content fragments
├── tests/                   # pytest suite validating the site
│   ├── conftest.py
│   ├── test_unit_html_structure.py
│   ├── test_integration_links.py
│   ├── test_e2e_site.py
│   ├── test_404_page.py
│   ├── test_build_matches_committed.py
│   ├── test_html_validity.py
│   ├── test_requirements_pinned.py
│   ├── test_readme_docs.py
│   ├── test_css_no_dead_classes.py
│   └── requirements.txt
```

The deployed site is plain static HTML/CSS with no JS framework — nothing
here runs in the browser. The committed `.html` pages are generated from the
sources under `build/` so that the shared header/nav/footer skeleton and any
prose reused across multiple pages (e.g., the course description, the
assignments table) exist in exactly one place instead of being hand-copied
into every page. **After editing anything under `build/`, regenerate the
site and commit the result:**

```bash
python3 build/build.py
```

`tests/test_build_matches_committed.py` fails if the committed pages ever
drift from what `build/build.py` currently produces, so running the test
suite (below) after a build-source edit is the way to confirm the two are
back in sync.

## Local Development

Serve the site locally with Python's built-in HTTP server:

```bash
python3 -m http.server 8080
# then open http://localhost:8080/
```

No install step is required to view the site — only the test suite has
dependencies.

`404.html` is not wired up to `python3 -m http.server` (it has no
custom-error-page support) — it's kept root-relative and structurally valid
for forward compatibility with static hosts that auto-serve a root
`404.html` (e.g., GitHub Pages), but you won't see it during local
development unless you navigate to it directly.

## Running the Tests

The test suite (pytest + BeautifulSoup/lxml/html5lib) validates structural and
content integrity of every page:

- `test_unit_html_structure.py` — every page has a DOCTYPE, title, stylesheet
  link, header, footer, and hero `<h1>`; no leftover template branding; no
  placeholder or stub content
- `test_integration_links.py` — every internal link resolves; navigation is
  identical across all pages; the schedule links to all 15 week pages and
  each link's text matches that week page's own title
- `test_e2e_site.py` — required files/directories exist; exact page count;
  every page is reachable from `index.html` (no orphaned pages)
- `test_404_page.py` — `404.html`'s internal links and stylesheet reference
  stay root-relative, so it renders correctly if a future host auto-serves
  it for a nested bad path
- `test_build_matches_committed.py` — the committed HTML never drifts from
  what `build/build.py` currently generates from its partials/shared/content
  sources
- `test_html_validity.py` — every page parses without errors under
  html5lib's strict HTML5 parser (catches malformed markup the lenient
  BeautifulSoup/lxml parser used elsewhere would silently repair)
- `test_requirements_pinned.py` — `tests/requirements.txt` uses exact `==`
  pins, not open-ended `>=` bounds
- `test_readme_docs.py` — this README's test-suite documentation stays in
  sync with the actual files under `tests/`
- `test_css_no_dead_classes.py` — every class selector in `css/style.css` is
  used by at least one page (no leftover unused theme CSS)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r tests/requirements.txt
pytest tests/ -v
```

Run a single test file or test:

```bash
pytest tests/test_unit_html_structure.py -v
pytest tests/test_integration_links.py::TestNavConsistency::test_nav_links_resolve -v
```

## Content Source and Provenance

All course content (syllabus text, schedule, assignments, policies) is
sourced from the official Fall 2026 syllabus. The page layout, navigation
pattern, and stylesheet are adapted from a prior Kenyon course site
([`programminghumanity-org`](https://github.com/jon-chun)) for visual
consistency across Jon Chun's Kenyon course sites; no course content from
that site is reused here.

## License

See [LICENSE](LICENSE).
