# Website Code Review: IPHS 400 Course Site

**Date:** 2026-09-03
**Scope:** Full repository as it stands after removal of Netlify/GitHub Actions tooling — 22 static HTML pages, `css/style.css`, and the pytest test suite. The site is now intended to run only as plain static files served by any dumb file server (e.g. `python3 -m http.server`).
**Reviewer:** Claude Code (automated review)

## Summary

This is a well-organized, dependency-free static site (22 hand-written HTML pages, one shared stylesheet, no JS, no build step) with a genuinely useful pytest suite that catches structural regressions (broken links, missing nav items, missing footers, placeholder text, orphaned pages). That test suite is the project's strongest asset and above what most sites this size have.

Two categories of finding stand out now that the site has no hosting/deploy layer of its own:

1. **`404.html` is now dead code.** It was previously wired up via a Netlify redirect rule; with that removed, nothing in the repository or the local dev workflow (`python3 -m http.server`) will ever serve it on a bad URL — visitors just get the server's own generic "File not found" page. It still exists, is still tested, and its own internal comment in `tests/conftest.py` describes a serving mechanism that no longer exists anywhere in this repo (§2.1).
2. **Every page hand-duplicates ~25 lines of identical header/nav/footer markup** with no include mechanism, and that duplication has already produced small, visible inconsistencies — two different relative-link conventions for nav hrefs, and inconsistent attribute ordering on the `active` class (§1).

Beyond those, there's a complete absence of SEO/social metadata (§3), no accessibility testing to complement the strong structural suite (§4), and a modest amount of duplicated prose across pages that the no-templating architecture makes easy to let drift (§6). None of this is hard to fix — most items below are small, targeted changes.

Findings are ordered roughly by severity within each section.

---

## 1. Architecture: no templating layer, header/nav/footer hand-duplicated 22×

The README states this is intentional ("single shared stylesheet, no build step"), and that's a reasonable choice for a 22-page course site. But the identical ~25-line header/nav/footer block is copy-pasted into all 22 files rather than shared via any include mechanism, and it has already drifted:

### 1.1 Two different relative-link conventions for nav hrefs

`core/syllabus.html` and `core/schedule.html` (and all 15 `weeks/*.html` pages) link to sibling core pages via `../core/xxx.html`:

```html
<!-- core/syllabus.html:16-20 -->
<li><a href="../index.html">Home</a></li>
<li><a class="active" href="../core/syllabus.html">Syllabus</a></li>
<li><a href="../core/schedule.html">Schedule</a></li>
```

But `core/about.html`, `core/assignments.html`, and `core/policies.html` link to the same sibling pages with plain relative paths:

```html
<!-- core/about.html:15-20 -->
<li><a href="../index.html">Home</a></li>
<li><a href="syllabus.html">Syllabus</a></li>
<li><a href="schedule.html">Schedule</a></li>
```

Both resolve correctly today (which is why the link-checker tests pass), but they are two different conventions doing the same job, and the `../core/` form is doing unnecessary work (going up a directory just to come back down into the same one). This split is itself evidence that the nav block is maintained by hand-copying rather than from one source — the next edit to the nav (e.g., adding a 7th link) has to be made correctly in two different link styles across 22 files, or a page silently falls out of sync.

**Fix:** pick one convention (plain relative paths are simpler and shorter within `core/`) and normalize all pages. Better: generate the nav from a single template.

### 1.2 Inconsistent attribute order on the `active` class

`index.html`, `core/about.html`, `core/assignments.html`, `core/policies.html` write `href="..." class="active"`; `core/schedule.html`, `core/syllabus.html`, and all `weeks/*.html` write `class="active" href="..."`. Cosmetically harmless, but it's a second, independent signal of hand-copy drift in the same block.

### 1.3 Mixed em-dash encoding

Most prose uses a literal `—` character, but `weeks/*.html` (and a couple of other pages) also use the `&mdash;`/`&ndash;` HTML entities in the same sentences (e.g., `weeks/week-01.html`: literal `—` in the nav separator, `&mdash;` in the body copy). Both render identically, so this is cosmetic, but it's one more small tell of copy-paste-and-edit authoring rather than a single content source, and worth normalizing to one convention (prefer the literal character, since it's already used site-wide in the header and is easier to search/replace).

### 1.4 Recommendation

For a 22-page site that's explicitly expected to be edited weekly during the semester (per the syllabus's own "AI tooling changes on a timescale of weeks" note, and the schedule page being the "authoritative" living document), hand-duplicated boilerplate is a real maintenance risk: a nav change, a footer copyright year, or a new "Resources" link requires 22 correct edits. Options, roughly in order of how much they preserve the current "no build step" simplicity:

- **Lightest:** a tiny build script (even a 20-line Python/Node script) that injects a shared `_header.html`/`_footer.html` partial into each page at commit-time, keeping the deployed output as plain static HTML.
- **Standard:** adopt a static site generator with includes/layouts (11ty, Jekyll, Astro in static mode) — bigger lift, but is exactly the tool for "one shared skeleton, many content pages," and would eliminate 1.1/1.2/1.3 entirely.
- **Status quo + guardrail:** if the team wants to keep zero build tooling, add a pytest check (extending `test_unit_html_structure.py`) that asserts the nav `<ul>` markup is byte-identical (modulo the `active` class and `../` prefix depth) across all pages, so drift like 1.1 fails the test suite instead of shipping silently.

---

## 2. Bugs

### 2.1 `404.html` is now unreachable dead code, and a test comment describes a mechanism that no longer exists

`404.html` was previously served via a Netlify redirect rule (`netlify.toml`'s `[[redirects]] from = "/*" to = "/404.html" status = 404`). That file has been deleted as part of removing the Netlify/GitHub Actions tooling, and nothing else in the repository maps an unmatched URL to `404.html`:

- Running the site with `python3 -m http.server` (the README's documented local-dev command) serves that server's own generic "File not found" HTTP response for any missing path — it has no concept of a custom error page and will never render `404.html`.
- `404.html` is not linked from any page (intentionally — see `tests/conftest.py`), so a visitor can only ever see it by typing `/404.html` directly into the address bar.

The page and its dedicated exclusion logic in the test suite (`nav_pages` fixture) are harmless to keep, but the comment describing *why* is now stale and misleading:

```python
# tests/conftest.py:33-41
@pytest.fixture(scope="session")
def nav_pages(all_html_files):
    """All HTML files except 404.html.

    404.html is a server-served fallback page, intentionally not linked from
    navigation or content, so it's excluded from nav-consistency and
    reachability-from-index checks.
    """
```

There is currently no "server" serving it as a fallback anywhere in this repo. This isn't a functional bug (the exclusion logic still does the right thing), but it will actively mislead the next person reading the test suite into thinking a 404-routing mechanism exists.

**Fix:** either (a) update the comment to say plainly that `404.html` is unused by the local static-file workflow and is kept only in case the site is later deployed behind a host that supports custom error pages (documenting which hosts do — GitHub Pages and most static hosts auto-serve a root-level `404.html`; a plain `http.server` does not), or (b) remove `404.html` entirely if it's not expected to be deployed anywhere in the near term. Given the project's stated goal of "no deploy pipeline, no external hosting config," (a) is the safer choice — the file costs nothing to keep and documents an easy migration path if the site is ever hosted.

### 2.2 Course-facing GitHub URL is plain text, not a link

`core/syllabus.html:39` and `core/about.html:60` render the repository URL as inert `<code>` text:

```html
<td><code>https://github.com/jon-chun/theailab-net</code> (materials) and Moodle (quizzes, grades, submissions)</td>
```

Students have to select and copy/paste it manually. Minor, but easy to fix — wrap it in `<a href="https://github.com/jon-chun/theailab-net">`.

---

## 3. Missing SEO / social / discoverability metadata

None of the 22 pages have any of the following, confirmed by grep across the whole repo:

- `<meta name="description">` — every page currently falls back to no snippet in search results and no summary when shared.
- Open Graph / Twitter Card tags (`og:title`, `og:description`, `og:type`, `twitter:card`) — links shared in Slack/Discord/email/social will show no preview.
- `<link rel="canonical">`.
- `favicon.ico` / `<link rel="icon">` — browsers will request `/favicon.ico` on every page load and silently 404.
- `robots.txt` and `sitemap.xml` at the site root.

For a course site this is low-stakes (it's not competing for search ranking, and there's currently no live URL to canonicalize against or point a sitemap at), but a per-page `<meta name="description">` and a favicon are cheap, high-value additions — the favicon in particular is a visible polish gap (browser tabs currently show a generic blank/default icon), and a description meaningfully improves how the link looks when pasted into Moodle, email, or a syllabus aggregator, whenever the site does end up hosted somewhere.

**Fix:** add a per-page description (can be templated from existing content, e.g., the hero `<h1>` text + "IPHS 400: Frontiers in AI") and a favicon; `robots.txt`/`sitemap.xml` and OG/canonical tags are worth deferring until there's an actual public URL to point them at.

---

## 4. Accessibility

The markup is basic and mostly harmless (no images means no alt-text problems, and the color palette has reasonable contrast), but a few standard patterns are missing:

- **No skip-to-content link.** Every page repeats the same ~6-item nav before the main content; keyboard and screen-reader users have no way to jump past it. Standard fix: a visually-hidden `<a href="#main" class="skip-link">Skip to content</a>` as the first element in `<body>`, plus `id="main"` on the `<main>` element (all pages already have `<main class="content-wrapper">`, so this is a small addition).
- **No `aria-current="page"`.** The current-page nav item is marked only with `class="active"` (a purely visual signal). Screen readers get no indication of which nav item represents the current page. Fix: add `aria-current="page"` alongside `class="active"` wherever it appears.
- **Header/hero structure is unconventional.** `<section class="hero">` (containing the page's only `<h1>`) is nested *inside* `<header class="site-header">`, alongside the site branding and `<nav>`. This isn't invalid HTML, but it does mean the page's `<h1>` is inside the same `<header>` landmark as the sitewide nav rather than at the start of `<main>`, which can be a little unexpected for assistive-tech users navigating by landmark. Not urgent, but worth a look if there's ever an accessibility audit.
- **`--text-lt: #767676`** on white background (used for taglines, breadcrumbs, meta text) is roughly a 4.5:1 contrast ratio — right at the WCAG AA threshold for normal-size text. It passes, but has no margin; worth confirming intended sizes stay ≥ the AA thresholds if this color is reused for smaller text later.

None of these are caught by the current test suite, which validates structure/content but not accessibility (see §5).

---

## 5. Test suite: strong on structure, has some gaps and one now-stale assumption

`tests/` is genuinely good — `test_unit_html_structure.py`, `test_integration_links.py`, and `test_e2e_site.py` together catch broken links, missing nav items, orphaned pages, placeholder text, and a hardcoded exact-page-count check that will force a deliberate update whenever a page is added or removed.

Gaps and issues, in rough priority order:

1. **Stale comment describing a 404-serving mechanism that no longer exists** (`tests/conftest.py:33-41` — see §2.1). Not a test failure, but a documentation-drift risk inside the test suite itself.
2. **No nav-markup-identity check**, so the `../core/` vs. plain-relative split (§1.1), the `active`-attribute-order split (§1.2), and the mixed em-dash entity/character usage (§1.3) all pass silently — `test_nav_links_resolve` only checks that links *resolve*, not that the markup is byte-consistent across pages.
3. **No HTML validation.** The suite parses with BeautifulSoup/lxml (which is lenient) but never runs an actual validator (e.g., the W3C validator API, or `html5lib` in strict mode) to catch malformed markup.
4. **No accessibility checks** (e.g., `axe-core` via a headless browser, or even simple heuristics like "every page has exactly one `<h1>`," "no skipped heading levels," "nav links have discernible text").
5. **No check for `<meta name="description">` or favicon presence**, so §3's gaps would ship silently even if added inconsistently later.
6. **`tests/requirements.txt` uses open-ended lower bounds** (`pytest>=7`, `beautifulsoup4>=4`, `lxml>=4`) with no upper bound or lockfile. Fine for a small low-risk project, but means a future `pip install -r tests/requirements.txt` can start failing from an unrelated upstream major-version bump with no local repro until someone re-runs the install. With CI removed, this is now purely a local-reproducibility concern (no automated gate will catch it either way), so it's slightly lower priority than before, but still worth pinning exact versions for anyone who clones the repo cold.

---

## 6. Content duplication (maintenance risk, not a bug)

Several large blocks of prose are duplicated verbatim across pages rather than written once:

- The "Course Description" paragraph and the full 9-item "Course Goals and Learning Outcomes" list are identical, word-for-word, in both `core/about.html` and `core/syllabus.html`.
- The "Summary of Assignments and Weights" table (9 rows) is duplicated identically in `core/syllabus.html` and `core/assignments.html`.
- The "Secrets Hygiene and Agent Safety" section is duplicated identically in `core/syllabus.html` and `core/policies.html`.

This is a natural consequence of the no-templating architecture (§1) rather than a distinct problem, but it compounds the maintenance risk: a mid-semester change to, say, the MP3 due date or a learning outcome now has to be made correctly in two (or three) separate files, and nothing in the test suite checks that these duplicated blocks stay in sync. If a shared-template solution (§1.4) is adopted, this becomes a natural place to factor out shared partials/includes (e.g., `_assignments-table.html`, `_secrets-hygiene.html`) rather than free text duplication.

---

## 7. Now-static hosting posture: no remaining assumptions to check, but nothing hosting-specific either

With `netlify.toml` and `.github/workflows/` removed, the repository now has zero opinions about how (or whether) it's ever deployed beyond a local dev server — which matches the stated goal. Two small, low-effort things worth keeping in mind if that changes later:

- If the site is ever pushed to a static host (GitHub Pages, a plain S3 bucket + CDN, etc.), most of them look for a root-level `404.html` by convention (GitHub Pages does) or need an explicit error-document config (S3/CloudFront do) — worth revisiting §2.1's fix once a host is chosen.
- There are currently no security response headers at all (previously set via `netlify.toml`: `X-Frame-Options`, `X-Content-Type-Options`). A plain static file server typically won't set these either. Low risk for a no-JS, no-form, no-cookie informational site, but cheap to add back at whatever layer eventually serves the site in production (a host's header config, or a `_headers`-style file if the chosen host supports one).

Neither of these is actionable *today* given the "local test server only" scope — they're flagged here so they aren't forgotten if the site's hosting story changes again.

---

## Priority Summary

| # | Finding | Section | Effort |
|---|---|---|---|
| 1 | Stale test-suite comment claims a 404-serving mechanism that no longer exists | 2.1 / 5.1 | Trivial (doc fix) |
| 2 | Two inconsistent nav-link conventions across core pages | 1.1 | Small (normalize 22 files, ideally via template) |
| 3 | No favicon / meta description on any page | 3 | Small |
| 4 | No skip-link, no `aria-current` on active nav item | 4 | Small |
| 5 | No templating layer — root cause of #2 and the content duplication in §6 | 1, 6 | Medium–Large, but highest long-term payoff |
| 6 | Test suite has no accessibility, HTML-validity, or nav-identity checks | 5 | Medium |
| 7 | GitHub repo URL rendered as inert text, not a link | 2.2 | Trivial |
| 8 | Mixed em-dash character/entity usage | 1.3 | Trivial |
| 9 | `tests/requirements.txt` has no upper-bound pins | 5.6 | Trivial |

Items 1–4 are worth doing regardless of hosting plans; item 5 is the one structural change that would prevent most of the others (and the content-duplication risk in §6) from recurring; items 6–9 are good, low-effort follow-ups.
