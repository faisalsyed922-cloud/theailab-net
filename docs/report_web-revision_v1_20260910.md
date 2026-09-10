# Website Code Review: IPHS 400 Course Site

**Date:** 2026-09-10
**Scope:** Full repository at commit `ea0a5b2` — 22 generated static HTML pages, `css/style.css`, the `build/` templating system (`build.py` + partials/shared/content fragments), and the pytest suite (8 files, 40 tests). No JS, no CI/CD, no hosting config; the site runs only via a local static file server (`python3 -m http.server`).
**Reviewer:** Claude Code (automated review)
**Baseline:** This supersedes `report_web-revision_v1_20260903.md`. That report's two headline findings — hand-duplicated header/nav/footer markup across 22 files, and a stale test-suite comment describing a defunct Netlify 404 redirect — are both resolved: a `build/` templating system now generates every page from shared partials, and `tests/conftest.py`'s `nav_pages` fixture correctly describes the current no-redirect reality. Most of that report's other findings (skip link, `aria-current`, favicon, meta descriptions, HTML validation, pinned test dependencies, linked repo URL, dash-entity normalization) are also fixed and enforced by new tests. See [What's Already Fixed](#whats-already-fixed-since-the-09-03-report) for the full list. This report focuses on what's left.

## Summary

The build system is a genuine improvement: 22 pages generated from one `build.py` script, six partial/shared fragments, and per-page content files, with `test_build_matches_committed.py` enforcing that the committed HTML never drifts from what the generator produces. Combined with `test_html_validity.py` (html5lib strict parsing) and the existing structural/link/accessibility checks, this is a well-tested static site for its size.

Two findings stand out because they're real content defects the current suite doesn't catch:

1. **Five of fifteen week-page titles don't match how those weeks are labeled on the schedule page** (§1) — a student clicking "Week 6: Hooks Architecture **and Guardrails**" from `core/schedule.html` lands on a page titled just "Week 6: Hooks Architecture." This is a data-consistency bug introduced by the same architecture that fixed the *previous* report's duplication problem: `build.py`'s `_WEEK_TITLES` dict and `build/content/core/schedule.html`'s hardcoded link text are two independent sources of truth for the same 15 strings, and they've already drifted in 5 of 15 cases.
2. **One page (`week-03.html`) uses `&ldquo;`/`&rdquo;` HTML entities** where every other page uses literal curly-quote characters (§2) — the same class of drift the 09-03 report flagged for em/en-dashes and which is now fixed *for dashes specifically*, but the fix didn't generalize to quotes.

Beyond those, the README's test-suite documentation has fallen behind the actual `tests/` directory (§3), a meaningful chunk of `css/style.css` is dead code inherited from the WordPress theme this site was adapted from (§4), and the SEO/social-metadata and accessibility gaps noted in the prior report that weren't addressed are still open (§5, §6). None of these require architectural change — they're targeted fixes, most of them small.

---

## 1. Bug: week-page titles don't match their schedule-page link text

`build/content/core/schedule.html` hardcodes the visible link text for each week as literal strings. `build.py`'s `_WEEK_TITLES` dict independently defines the `<title>` and `<h1>` text baked into each week page. These are two hand-maintained copies of the same 15 labels, and they've diverged in 5 places:

| Week | Schedule page says | Week page's own `<title>`/`<h1>` says |
|---|---|---|
| 6 | Hooks Architecture **and Guardrails** | Hooks Architecture |
| 10 | MP3 Demos and the Spec-Driven **Development** Landscape | MP3 Demos and the Spec-Driven Landscape |
| 13 | Full-Cycle Capstone Work Session **and MP4 Presentations** | Full-Cycle Capstone Work Session |
| 14 | Final Project Work Session **and Poster Development** | Final Project Work Session |
| 15 | Final Project **Poster** Presentations | Final Project Presentations |

```
core/schedule.html:53      <li><a href="../weeks/week-06.html">Week 6: Hooks Architecture and Guardrails</a></li>
weeks/week-06.html:26      <section class="hero"><h1>Week 6: Hooks Architecture</h1></section>
```

This is invisible to the current suite: `test_schedule_links_to_all_15_weeks` (`tests/test_integration_links.py`) only checks that an `href` to each `week-NN.html` exists somewhere on the schedule page — it never reads the week page's own title and compares it to the link text used to get there. `test_build_matches_committed.py` also can't catch this, because both mismatched strings are equally "correct" as far as the build script is concerned — it faithfully reproduces whatever `_WEEK_TITLES` and the hardcoded schedule content say, and nothing cross-checks the two.

**Likely root cause:** `_WEEK_TITLES` was probably edited (shortened, or the schedule text was later extended with more descriptive labels) after the schedule page's content fragment was written, and no single source of truth was ever established between them.

**Fix, in order of how much it prevents recurrence:**
- **Best:** delete the hardcoded link text in `build/content/core/schedule.html` and generate it from `build.py`'s own `_WEEK_TITLES` dict (which is already the source of truth for each week's actual page title). This makes the two permanently identical by construction.
- **Guardrail regardless:** add a pytest check that reads each `weeks/week-NN.html`'s `<h1>` text and asserts it appears verbatim as the link text pointing to that file from `core/schedule.html`. This is cheap and would have caught all 5 instances above; add it even if the "Best" fix above is also done, since it protects against the same drift recurring in whatever replaces the hardcoded list.
- **Content decision needed either way:** someone with the actual syllabus needs to decide which of the two titles is correct for weeks 6, 10, 13, 14, and 15 — this review can't determine intent, only that they disagree.

---

## 2. Bug: inconsistent quote-character encoding (one page uses HTML entities, all others use literal characters)

`weeks/week-03.html` is the only page in the site using `&ldquo;`/`&rdquo;` entities instead of literal curly-quote characters:

```html
<!-- weeks/week-03.html:34 -->
<p><strong>Ethics thread:</strong> what changes when the &ldquo;user&rdquo; of a tool is an agent...</p>
```

Every other page that uses curly quotes (`core/syllabus.html`, `core/policies.html`, `core/assignments.html`, and the `build/shared/*` fragments) uses the literal `"`/`"` characters directly in the source. Both render identically in a browser, so this is purely cosmetic — but it's the exact same category of drift the 09-03 report caught for em/en-dashes (`&mdash;`/`&ndash;` vs. literal `—`/`–`), which was fixed and is now guarded by `TestDashEncoding.test_no_mdash_or_ndash_entities` in `tests/test_unit_html_structure.py`. That test's docstring even states the site-wide convention ("literal —/– characters... not the &mdash;/&ndash; HTML entities") but the check wasn't generalized to cover quote entities, so this one slipped through.

**Fix:** replace the two entities in `weeks/week-03.html` (and its `build/content/weeks/week-03.html` source) with literal `"`/`"` characters, then re-run `python3 build/build.py`. Extend `test_no_mdash_or_ndash_entities` (or add a sibling assertion) to also flag `&ldquo;`, `&rdquo;`, `&lsquo;`, `&rsquo;`, and their numeric equivalents (`&#8220;`, `&#8221;`, etc.), so this class of drift can't reappear for any punctuation character.

---

## 3. Documentation drift: README's test-suite section is behind the actual `tests/` directory

`tests/` has grown to 8 files (`conftest.py` + 7 test modules), but `README.md`'s "Repository Structure" tree and "Running the Tests" section only mention 4 of the 7 test modules:

**Listed in the README's file tree and/or described:**
`conftest.py`, `test_unit_html_structure.py`, `test_integration_links.py`, `test_e2e_site.py`

**Present in `tests/` but absent from both the README's tree *and* its prose:**
`test_404_page.py`, `test_build_matches_committed.py`, `test_html_validity.py`, `test_requirements_pinned.py`

Two consequences:
- A contributor reading the README's file tree (`README.md:34-41`) would not know these four files exist, including `test_build_matches_committed.py` — arguably the single most important test in the suite, since it's the one that enforces the whole `build/` templating architecture actually stays in sync with what's committed (see this report's own baseline note above).
- The README's dependency description ("The test suite (pytest + BeautifulSoup/lxml) validates...", `README.md:81`) omits `html5lib`, which `tests/requirements.txt` pins and `test_html_validity.py` requires.

**Fix:** add the four missing files to the repository-structure tree, and add one bullet per file to "Running the Tests" describing what each validates (build/commit sync, HTML5 parse validity, 404-page root-relativity, pinned requirements) — following the same one-line style already used for the three documented files. Update the "pytest + BeautifulSoup/lxml" line to include `html5lib`.

---

## 4. Dead CSS: WordPress-theme classes never used anywhere in the site

`css/style.css` was adapted from a WordPress "Twenty Nineteen"-style theme (per its own header comment), and roughly a quarter of its ~640 lines style classes that don't appear in any of the 22 generated pages or their `build/` sources:

```
post-preview, entry-meta, share-links, badge (+ badge-draft/badge-private/badge-placeholder),
placeholder-notice, columns, wp-block-image, wp-block-separator, entry-footer, post-nav,
social-nav, has-featured-image, other-blog-pages
```

Confirmed via `grep -rl 'class="[^"]*\bCLASSNAME\b"'` across every `.html` file outside `build/` — zero matches for any of the above. (`.placeholder-notice` and `.badge-*` are actively tested *for absence* by `test_no_placeholder_notice`, suggesting these were scaffolding classes from an earlier draft/placeholder-content phase of the site that's now complete — but the CSS rules for them were never removed.) `.has-featured-image` in particular styles an entire full-viewport hero-image layout mode (~40 lines, including a `.featured-media` duotone-image treatment) that no page in this course-site build ever uses — every page uses `no-featured-image`.

This isn't a functional bug (unused CSS costs nothing at runtime beyond a slightly larger download), but it's a maintenance and comprehension cost: a future editor styling a real blog-style feature, a badge, or a placeholder banner might reasonably assume these rules are already wired up and tested, when in fact they're unreachable from any current page, and any editor auditing "what does this site actually look like" has to mentally filter out ~150 lines of theme leftovers to find the ~490 lines that matter.

**Fix:** delete the unused rule blocks, or — if they're intentionally kept as a "theme swatch" for future blog-style content — add a one-line comment at the top of each unused section explaining that it's speculative/unused-for-now, so the next reader doesn't have to grep the whole site to find out.

---

## 5. Missing SEO / social metadata (carried over, still unaddressed)

Unchanged from the 09-03 report: no page has Open Graph or Twitter Card tags (`og:title`, `og:description`, `twitter:card`), no `<link rel="canonical">`, and there's no `robots.txt` or `sitemap.xml` at the site root. Per-page `<meta name="description">` and a favicon — the two cheapest, highest-value items from that list — are now done and tested (`TestMetadata` in `tests/test_unit_html_structure.py`).

This remains low-stakes for a course site with no live public URL to canonicalize against, and is reasonable to keep deferring. Flagged again here only so it isn't lost — it's a five-minute addition (`og:title`/`og:description` can reuse the same per-page `desc` field `build.py` already threads through for the meta description) whenever the site does get a real hosted URL.

---

## 6. Accessibility: remaining items from the 09-03 report

The 09-03 report's two most actionable a11y items — a skip-to-content link and `aria-current="page"` on the active nav item — are fixed and covered by tests (`TestAccessibility` in `tests/test_unit_html_structure.py`). One structural item and one contrast item remain, both previously noted as non-urgent and still true:

- **`<h1>` lives inside `<header>`, not `<main>`.** `section.hero` (containing the page's only `<h1>`) is nested inside `header.site-header` alongside the site branding and `<nav>`, rather than being the first element of `<main>`. Not invalid HTML, and not flagged by `test_exactly_one_h1_per_page` (which only counts `<h1>`s, not their landmark placement), but it means screen-reader users navigating by landmark region encounter the page's heading inside the "banner" landmark rather than the "main" landmark — a minor deviation from the common pattern.
- **`--text-lt: #767676` on white measures 4.54:1 contrast** — computed directly from the CSS custom property values (`#767676` vs `#fff`), this clears WCAG AA's 4.5:1 threshold for normal text by 0.04, essentially no margin. It's used for the tagline, breadcrumbs, and page-meta text, all of which appear to be sized ≥16px today, so it currently passes — but there's no slack if this color is ever reused for smaller text, and no automated check would catch a future regression (contrast isn't covered by any test in the suite).

Neither is a regression from the prior review; both are simply still open.

---

## 7. Minor: favicon uses a different link-path convention than every other asset

Every page links its stylesheet and internal nav via the `{{REL}}` depth-relative prefix that `build.py` computes per page (`../css/style.css` from `weeks/`, `css/style.css` from the root, etc.). The favicon is the one exception — every page links it as the literal root-relative `/favicon.svg`, hardcoded in `build/partials/head.html`, regardless of depth:

```html
<!-- build/partials/head.html:4 -->
<link rel="icon" href="/favicon.svg" type="image/svg+xml"/>
```

This works correctly today because `python3 -m http.server` (and any host that serves this repo from its own domain root) treats `/` as the site root. But it's an inconsistent convention sitting right next to the `{{REL}}`-based stylesheet link one line below it, and — like `404.html`'s root-relative links (`tests/test_404_page.py`) — it would silently break if this site were ever served from a subpath (e.g., `example.com/iphs400/`) rather than a domain root, unlike every other internal link in the page, which is depth-relative and subpath-safe. Not urgent given the site's current single-domain-root deployment story, but worth aligning to `{{REL}}favicon.svg` if that assumption ever changes, or documenting the intentional exception with a one-line comment if it's staying root-relative on purpose (mirroring how `build.py` already comments *why* `404.html` is root-relative).

---

## What's Already Fixed Since the 09-03 Report

For completeness, so this report doesn't read as if the codebase stood still:

| 09-03 finding | Status |
|---|---|
| Hand-duplicated header/nav/footer across 22 files; two nav-link conventions; inconsistent `active`-attribute order | **Fixed.** `build/` templating system generates every page from shared partials; `test_nav_markup_is_identical_modulo_active_item_and_depth` guards it |
| `404.html` dead code + stale test comment describing a nonexistent Netlify redirect | **Fixed.** Comment now accurately describes the no-redirect reality; `test_404_page.py` added to verify root-relativity is preserved for a future host |
| Course GitHub URL rendered as inert text | **Fixed.** `TestRepoURLIsLinked` enforces it site-wide |
| Mixed em/en-dash character vs. entity usage | **Fixed for dashes** (`TestDashEncoding`) — see §2 above for the quote-entity gap this didn't cover |
| No favicon / no meta description | **Fixed.** `favicon.svg` added; per-page descriptions threaded through `build.py`; both enforced by `TestMetadata` |
| No skip-link / no `aria-current` | **Fixed.** Both present and tested |
| No HTML validation beyond lenient BeautifulSoup parsing | **Fixed.** `test_html_validity.py` runs html5lib strict parsing |
| `tests/requirements.txt` unpinned (`>=`) | **Fixed.** Exact `==` pins; `test_requirements_pinned.py` enforces it |
| Duplicated prose (course description, learning outcomes, assignments table, secrets-hygiene section) across pages | **Fixed.** All four now live once in `build/shared/*.html` and are pulled in via `{{INCLUDE:...}}` |

---

## Priority Summary

| # | Finding | Section | Effort |
|---|---|---|---|
| 1 | Week titles on the schedule page don't match 5 of 15 week pages' own titles | §1 | Small (fix content + add a cross-check test) |
| 2 | `week-03.html` uses `&ldquo;`/`&rdquo;` entities instead of the site's literal-character convention | §2 | Trivial (fix + extend existing dash test) |
| 3 | README's test-suite documentation omits 4 of 7 test files and the `html5lib` dependency | §3 | Trivial (doc fix) |
| 4 | ~150 lines of unused WordPress-theme CSS (blog/badge/placeholder/featured-image styles) | §4 | Small (delete or comment as speculative) |
| 5 | No OG/Twitter/canonical tags, no `robots.txt`/`sitemap.xml` | §5 | Small, low priority until a live URL exists |
| 6 | `<h1>` sits in the `header` landmark rather than `main`; `--text-lt` contrast has near-zero AA margin | §6 | Small, non-urgent |
| 7 | Favicon link is root-relative while every other internal link is depth-relative | §7 | Trivial, cosmetic-consistency only |

Items 1–3 are the ones worth doing regardless of anything else — they're real, user-visible or contributor-visible inconsistencies with essentially no downside to fixing. Items 4–7 are polish, in roughly descending priority.
