# Tech Spec: IPHS 400 Website Revisions (Round 2)

**Date:** 2026-09-10
**Source:** Synthesizes `docs/report_web-revision_v1_20260910.md` into actionable, ranked implementation tasks.
**Scope:** Static site only (`index.html`, `404.html`, `core/*.html`, `weeks/*.html`, `css/style.css`, `build/`, `tests/`, `README.md`). No deploy/hosting layer is in scope — the site runs via `python3 -m http.server` only.
**Baseline:** This is Round 2, following `docs/tech-spec_website-revision_v1_20260903.md` (Round 1), which has already been implemented — the `build/` templating system, skip link, `aria-current`, favicon, meta descriptions, HTML validation, pinned test dependencies, linked repo URL, and dash-entity normalization are all done and enforced by tests. This spec covers what Round 1 left open plus new defects the Round 1 work itself introduced.

Each task below is self-contained: a reader should be able to pick any one task and implement it without reading the others.

---

## How to use this document

Tasks are grouped by criticality (`high` → `medium` → `low`) and numbered `H1, H2, ...`, `M1, M2, ...`, `L1, L2, ...`. Within each tier, tasks are ordered by recommended implementation sequence, not further ranked. Each task has:

- **Description** — what changes.
- **Justification** — why it matters, referencing the source report section.
- **Steps** — concrete implementation instructions.
- **Acceptance check** — how to confirm the task is done correctly.

---

## HIGH criticality

### H1 — Fix the 5 mismatched week titles and eliminate the dual-source-of-truth that caused it

**Report ref:** §1

**Description:** Correct the 5 week pages whose `<title>`/`<h1>` text disagrees with how they're labeled on `core/schedule.html` (weeks 6, 10, 13, 14, 15), then restructure `build.py` so the schedule page's link text is generated from the same `_WEEK_TITLES` dict that already drives each week page's own title — removing the second, independently-maintained copy of those 15 strings.

**Justification:** This is a live, user-facing content bug: a student clicking "Week 6: Hooks Architecture **and Guardrails**" from the schedule lands on a page titled "Week 6: Hooks Architecture." It exists because `build/content/core/schedule.html` hardcodes 15 link-text strings that duplicate — and have drifted from — `build.py`'s `_WEEK_TITLES` dict. This is exactly the class of defect Round 1's `build/` migration was meant to eliminate (see that report's §1), except it recurred in a new spot the migration didn't cover. Fixing the content without also fixing the architecture would leave the same drift free to happen again the next time either list is edited.

**Steps:**

1. Decide the canonical title for weeks 6, 10, 13, 14, and 15. Compare both existing variants for each and pick the more descriptive/accurate one (the report's table lists both side by side):
   - Week 6: "Hooks Architecture" vs. "Hooks Architecture **and Guardrails**"
   - Week 10: "MP3 Demos and the Spec-Driven Landscape" vs. "...Spec-Driven **Development** Landscape"
   - Week 13: "Full-Cycle Capstone Work Session" vs. "...Work Session **and MP4 Presentations**"
   - Week 14: "Final Project Work Session" vs. "...Work Session **and Poster Development**"
   - Week 15: "Final Project Presentations" vs. "Final Project **Poster** Presentations"

   This requires judgment about what's actually being taught/covered that week — if in doubt, prefer the more descriptive schedule-page version, since it was likely added later to clarify content, and the terser `_WEEK_TITLES` entries look like the original draft.
2. Update `build/build.py`'s `_WEEK_TITLES` dict (around line 32) with the 5 chosen canonical strings.
3. In `build/content/core/schedule.html`, remove the hardcoded week link text and instead have `build.py` generate the schedule's week-links section from `_WEEK_TITLES` directly, so there is only one place these strings live. Concretely:
   - Add a `{{INCLUDE:schedule-weeks-N-M}}`-style mechanism, or simpler: have `_render_page` (or a new helper function) substitute a `{{WEEK_LINK:NN}}` placeholder in the schedule content with `f'<a href="../weeks/week-{NN}.html">{_WEEK_TITLES[NN]}</a>'`, reading the title straight from the dict.
   - Replace each `<li><a href="../weeks/week-NN.html">Week NN: ...</a></li>` line in `build/content/core/schedule.html` with `<li>{{WEEK_LINK:NN}}</li>`.
4. Regenerate the site: `python3 build/build.py`.
5. Verify no other content references the old titles: `grep -rn "Hooks Architecture and Guardrails\|Spec-Driven Development Landscape\|and MP4 Presentations\|and Poster Development\|Final Project Poster Presentations" . --include="*.html"` — confirm only the newly-chosen canonical form remains, in both the schedule page and the corresponding week page.
6. Add a regression test to `tests/test_integration_links.py` (or a new `TestScheduleWeekTitlesMatch` class) that, for each `weeks/week-NN.html`, reads its `<h1>` text and asserts that exact string appears as link text on `core/schedule.html`. This is the guardrail the report recommends regardless of the templating fix, since it protects against the same drift recurring through whatever mechanism generates the schedule content in the future.
7. Run `pytest tests/ -v` — all tests, including the new one, must pass. `tests/test_build_matches_committed.py` will confirm the regenerated pages match what's committed.

**Acceptance check:** For all 15 weeks, `weeks/week-NN.html`'s `<h1>` text is byte-identical to the corresponding link text on `core/schedule.html`. The new cross-check test fails if this is manually broken (spot-check by temporarily reverting one title) and passes otherwise. `python3 build/build.py && git diff --stat` shows no unexpected changes beyond the intended title fixes.

---

### H2 — Fix the stray `&ldquo;`/`&rdquo;` entities in `week-03.html` and extend the entity-encoding test to cover quotes

**Report ref:** §2

**Description:** Replace the two HTML entities in `weeks/week-03.html` (`&ldquo;user&rdquo;`) with the literal curly-quote characters (`"user"`) used everywhere else on the site, in both the committed page and its `build/content/` source. Extend the existing dash-entity test in `tests/test_unit_html_structure.py` to also catch curly-quote entities.

**Justification:** This is the same drift pattern Round 1 fixed for em/en-dashes (`&mdash;`/`&ndash;` vs. literal `—`/`–`) — fixed for dashes, but not generalized to quotes, so one instance slipped through untested. It's low-impact (both render identically), but it's a one-line fix with a one-line test addition, and leaving it unfixed means the site's stated "use literal characters" convention (documented in the existing test's own docstring) is silently violated in exactly one place.

**Steps:**

1. In `build/content/weeks/week-03.html`, find:
   ```html
   <p><strong>Ethics thread:</strong> what changes when the &ldquo;user&rdquo; of a tool is an agent: labor, deskilling, and accountability.</p>
   ```
   Replace `&ldquo;` with `"` and `&rdquo;` with `"` (literal Unicode curly quotes, matching the convention already used in `build/content/core/syllabus.html`, `build/content/core/policies.html`, and elsewhere).
2. Regenerate the site: `python3 build/build.py`. Confirm `weeks/week-03.html` picks up the change and no other file changes.
3. Open `tests/test_unit_html_structure.py`'s `TestDashEncoding` class. Rename it (or add a sibling test in the same class) to also check quote entities — extend the `hits` tuple search to include `&ldquo;`, `&rdquo;`, `&lsquo;`, `&rsquo;`, `&#8220;`, `&#8221;`, `&#8216;`, `&#8217;` alongside the existing `&mdash;`/`&ndash;` check. Consider renaming the class/test to `TestPunctuationEncoding` / `test_no_punctuation_entities` to reflect the broadened scope, and update its docstring accordingly.
4. Run `pytest tests/ -v` — confirm the updated test passes against the now-fixed content, then temporarily reintroduce `&ldquo;` in a scratch copy to confirm the test fails (sanity-check the test actually catches the pattern), then revert the scratch change.

**Acceptance check:** `grep -rn '&ldquo;\|&rdquo;\|&lsquo;\|&rsquo;' weeks/*.html core/*.html index.html 404.html` returns no results. The extended pytest check fails if any of those entities (or their numeric equivalents) are reintroduced anywhere in the site.

---

## MEDIUM criticality

### M1 — Bring `README.md`'s test-suite documentation up to date

**Report ref:** §3

**Description:** Add the 4 undocumented test files (`test_404_page.py`, `test_build_matches_committed.py`, `test_html_validity.py`, `test_requirements_pinned.py`) to the README's repository-structure tree and "Running the Tests" section, and add `html5lib` to the stated test dependencies.

**Justification:** A contributor reading the README today would not know 4 of the repo's 7 test modules exist — including `test_build_matches_committed.py`, which is the single test enforcing that the entire `build/` templating architecture (Round 1's biggest structural fix) stays in sync with the committed HTML. Undocumented tests are easy to accidentally let bit-rot or to duplicate functionality of without realizing it.

**Steps:**

1. Open `README.md`'s "Repository Structure" tree (around line 34-41). Add the 4 missing files to the `tests/` subtree so it reads:
   ```
   ├── tests/                   # pytest suite validating the site
   │   ├── conftest.py
   │   ├── test_unit_html_structure.py
   │   ├── test_integration_links.py
   │   ├── test_e2e_site.py
   │   ├── test_404_page.py
   │   ├── test_build_matches_committed.py
   │   ├── test_html_validity.py
   │   ├── test_requirements_pinned.py
   │   └── requirements.txt
   ```
2. In the "Running the Tests" section, add one bullet per missing file, matching the existing one-line style, e.g.:
   - `test_404_page.py` — `404.html`'s internal links and stylesheet reference stay root-relative, so it renders correctly if a future host auto-serves it for a nested bad path
   - `test_build_matches_committed.py` — the committed HTML never drifts from what `build/build.py` currently generates from its partials/shared/content sources
   - `test_html_validity.py` — every page parses without errors under html5lib's strict HTML5 parser (catches malformed markup the lenient BeautifulSoup/lxml parser used elsewhere would silently repair)
   - `test_requirements_pinned.py` — `tests/requirements.txt` uses exact `==` pins, not open-ended `>=` bounds
3. Update the line "The test suite (pytest + BeautifulSoup/lxml) validates..." to "The test suite (pytest + BeautifulSoup/lxml/html5lib) validates..." to reflect the `html5lib` dependency `test_html_validity.py` requires.
4. Read through the rest of the README once to confirm no other section references a stale file list or dependency set.

**Acceptance check:** Every file under `tests/` (except `__pycache__`) appears in the README's tree, and every test module has a corresponding one-line description in "Running the Tests." `grep -c 'test_' README.md` reflects all 7 test modules (plus `conftest.py` mentioned separately).

---

### M2 — Remove or clearly label the unused WordPress-theme CSS

**Report ref:** §4

**Description:** Delete the CSS rules for classes that appear nowhere in the site's actual pages (`post-preview`, `entry-meta`, `share-links`, `badge`/`badge-draft`/`badge-private`/`badge-placeholder`, `placeholder-notice`, `columns`, `wp-block-image`, `wp-block-separator`, `entry-footer`, `post-nav`, `social-nav`, `has-featured-image` and its `.featured-media` support styles, `other-blog-pages`) — or, if any are intentionally kept for a planned future feature, add a one-line comment above each retained block explaining that it's currently unused.

**Justification:** Confirmed via `grep -rl 'class="[^"]*\bCLASSNAME\b"'` across every non-`build/` `.html` file: zero matches for any of the classes listed above. This is roughly a quarter of `css/style.css`'s ~640 lines styling markup that doesn't exist anywhere in the current 22-page site — inherited from the WordPress theme the site was visually adapted from. It costs nothing at runtime, but it's a real comprehension tax: a future editor can't tell by reading the CSS alone which rules are load-bearing.

**Steps:**

1. Confirm the "unused" list is still accurate before deleting anything — re-run the check: for each class in the list below, run `grep -rl "class=\"[^\"]*\bCLASSNAME\b\"" --include="*.html" . --exclude-dir=.venv --exclude-dir=build` and confirm zero output.
   ```
   post-preview entry-meta share-links badge badge-draft badge-private badge-placeholder
   placeholder-notice columns wp-block-image wp-block-separator entry-footer post-nav
   social-nav has-featured-image other-blog-pages
   ```
2. Decide, per class group, whether to delete or keep-and-comment. Recommended default: **delete** all of them — none currently has a planned use documented anywhere in `docs/`, and `.placeholder-notice`/`.badge-*` are actively tested *for absence* (`test_no_placeholder_notice` in `tests/test_unit_html_structure.py`), suggesting they were scaffolding for a since-completed draft phase, not a forward-looking feature.
3. In `css/style.css`, remove the following rule blocks (identify each by its `/* ===== */` section comment or class selector):
   - The entire "Blog entry meta" / "Category footer + prev/next (blog)" section (`.entry-meta`, `.entry-footer`, `.post-nav`, `.share-links` and its children)
   - The `.social-nav` rules
   - The `.has-featured-image` / `.featured-media` block (including its `::after` duotone pseudo-element) — but first confirm `.no-featured-image` (the variant actually used on every page) is untouched
   - The "Blog index: live-style post previews" section (`.post-preview` and children, `.other-blog-pages`)
   - The "Badges" section (`.badge` and its 3 modifier classes)
   - The "Placeholder notice" section (`.placeholder-notice` and its `h3` child rule)
   - `.columns` (and its mobile-breakpoint override in the `@media (max-width: 768px)` block)
   - The "WP Block styles" section (`.wp-block-image`, `.wp-block-separator`)
4. After deletion, re-check the `@media` breakpoint blocks at the bottom of the file for any now-orphaned overrides referencing deleted classes (e.g., the `.columns { column-count: 1; }` and `.post-nav { flex-direction: column; ... }` overrides inside `@media (max-width: 768px)`) and remove those too.
5. Load a sample of pages (`index.html`, `core/schedule.html`, `weeks/week-01.html`) in a browser before and after the CSS edit and visually confirm no rendering change (none of the deleted rules apply to any element currently on any page, so this should be a no-op visually).
6. Run `pytest tests/ -v` — no test should be affected by a CSS-only change, but confirm regardless since `test_html_validity.py` and others parse the HTML pages, not the CSS.

**Acceptance check:** `wc -l css/style.css` shows a meaningfully smaller file (roughly 150 fewer lines). Visual diff of rendered pages (before/after screenshot or manual check) shows no change. All existing tests still pass.

---

## LOW criticality

### L1 — Add basic SEO/social metadata scaffolding (Open Graph, canonical, robots/sitemap placeholders)

**Report ref:** §5

**Description:** Add `og:title`/`og:description`/`og:type` and `twitter:card` meta tags to every page's `<head>`, reusing the per-page description string `build.py` already computes. Defer `<link rel="canonical">`, `robots.txt`, and `sitemap.xml` until the site has an actual public hosting URL to point them at.

**Justification:** The report notes this is low-stakes for a course site with no live public URL today, but the OG/Twitter tags are a five-minute addition since `build.py`'s `PAGES` list already carries a `desc` field for the meta description — the same string can be reused for `og:description` with zero new content-authoring work. Canonical URLs, `robots.txt`, and `sitemap.xml` all require knowing the eventual hosting domain, so they're correctly deferred rather than guessed at.

**Steps:**

1. In `build/partials/head.html`, add after the existing `<meta name="description">` line:
   ```html
   <meta property="og:title" content="{{TITLE}} – IPHS 400: Frontiers in AI"/>
   <meta property="og:description" content="{{DESCRIPTION}}"/>
   <meta property="og:type" content="website"/>
   <meta name="twitter:card" content="summary"/>
   ```
2. Confirm `build.py`'s `_render_page` already substitutes `{{TITLE}}` and `{{DESCRIPTION}}` into `head.html` (it does, per the existing `head.replace(...)` calls) — no changes needed to `build.py` itself, only to the partial template.
3. Regenerate the site: `python3 build/build.py`, and confirm the new tags appear on a sample of pages.
4. Do **not** add `<link rel="canonical">`, `robots.txt`, or `sitemap.xml` in this pass — leave a one-line note in this task's tracking (e.g., a follow-up TODO in `docs/`) that these are deferred until a public hosting URL exists, since a canonical tag pointing at the wrong (or a placeholder) URL is worse than no canonical tag at all.
5. Optionally, extend `tests/test_unit_html_structure.py`'s `TestMetadata` class with a check that every page has non-empty `og:title` and `og:description` content, mirroring the existing meta-description test.

**Acceptance check:** `grep -L 'property="og:description"' index.html 404.html core/*.html weeks/*.html` returns no files. No `robots.txt`, `sitemap.xml`, or canonical tag is added in this pass.

---

### L2 — Move the page `<h1>` into the `<main>` landmark (optional structural cleanup)

**Report ref:** §6

**Description:** Restructure the header so `<section class="hero"><h1>...</h1></section>` renders as the first child of `<main id="main">` rather than being nested inside `<header class="site-header">` alongside the site branding and nav.

**Justification:** Screen-reader users navigating by landmark region currently encounter the page's only heading inside the "banner" (header) landmark rather than the "main" landmark, which is a minor deviation from the common accessibility pattern. This is explicitly called out in the report as non-urgent and requiring a CSS layout change, not just a markup move (the current visual design relies on the hero sitting flush against the header's bottom edge) — treat this as an optional follow-up, not a required fix, unless a fuller accessibility audit is planned.

**Steps:**

1. In `build/partials/header.html`, remove the trailing `<section class="hero"><h1>{{TITLE}}</h1></section>` from inside `</header>`.
2. In `build/build.py`'s `_render_page`, move the hero-section rendering to immediately after `{{header}}` and before `{{breadcrumb}}`, so the generated page structure becomes: `<header>...</header><section class="hero"><h1>{{TITLE}}</h1></section><main id="main">{{breadcrumb}}<div class="page-content">...`. Note this still places the hero *outside* `<main>`, only outside `<header>` too — a further option is to move it *inside* `<main>` as the first child, which more fully satisfies the landmark-navigation goal; pick based on how much the visual layout is expected to change (moving it inside `<main>` may need `.hero`'s CSS margin/positioning reworked, since it currently assumes it's a sibling of `.header-inner` inside a `position: relative` header).
3. In `css/style.css`, adjust `.hero`'s margin/positioning rules (currently `margin: 3rem 0 0 var(--col-left)` assuming header context) so the visual result — the dashed rule + large title sitting below the nav — is unchanged after the markup move. This will likely require testing at both desktop and the `@media (max-width: 768px)` breakpoint, since `.site-header.no-featured-image .hero` has its own margin override for that variant.
4. Regenerate: `python3 build/build.py`, then visually compare every page type (home, core, week) before and after at both breakpoints to confirm no visual regression.
5. Run `pytest tests/ -v` — `test_all_pages_have_hero_with_h1` and `test_all_pages_have_site_header` in `tests/test_unit_html_structure.py` only check that `section.hero` and `header.site-header` exist somewhere on the page, not their nesting relationship, so these should still pass unmodified; confirm regardless.

**Acceptance check:** In the generated HTML, `<section class="hero">` is a sibling of `<header class="site-header">`, not a descendant. Visual rendering is unchanged from before the change (side-by-side screenshot comparison). All existing tests still pass.

---

### L3 — Align the favicon link to the same relative-path convention as the stylesheet

**Report ref:** §7

**Description:** Change `build/partials/head.html`'s hardcoded root-relative `/favicon.svg` to use the same `{{REL}}` depth-relative prefix already used for the stylesheet link one line below it — or, if root-relative is being kept intentionally, add a one-line comment explaining why.

**Justification:** Every other internal link in the page (stylesheet, nav, breadcrumbs) is depth-relative via `{{REL}}`, making the site portable to being served from a subpath. The favicon is the sole exception, hardcoded as `/favicon.svg` regardless of page depth. This works today because the site is always served from a domain root, but it's an unexplained inconsistency sitting one line above the correctly-relative stylesheet link, and would be the one broken asset if the site were ever served from a subpath.

**Steps:**

1. Decide whether subpath-hosting portability matters for this project. If the site will only ever be served from a domain root (the common case for a course site), root-relative is fine — in that case, skip to step 3 and just add the explanatory comment.
2. If portability matters, in `build/partials/head.html`, change:
   ```html
   <link rel="icon" href="/favicon.svg" type="image/svg+xml"/>
   ```
   to:
   ```html
   <link rel="icon" href="{{REL}}favicon.svg" type="image/svg+xml"/>
   ```
   This works identically to the stylesheet link on the next line, since `build.py`'s `_render_page` already substitutes `{{REL}}` with the correct `../`-depth prefix (or empty string at the root) before writing `head.html` into each page.
3. Whichever option is chosen, add a one-line comment in `build/partials/head.html` directly above the favicon line stating the deliberate choice, e.g.: `<!-- root-relative by design: matches typical domain-root hosting; see README -->` or `<!-- depth-relative, matching the stylesheet link, for subpath-hosting portability -->`.
4. Regenerate: `python3 build/build.py`. If step 2 was applied, confirm the favicon still resolves correctly on a nested page (e.g., open `weeks/week-05.html` via `python3 -m http.server` and confirm the browser tab icon loads — check the Network tab for a 200 on the favicon request, not a 404).
5. Run `pytest tests/ -v` — `test_all_pages_have_a_favicon_link` in `tests/test_unit_html_structure.py` already resolves both root-relative and page-relative hrefs correctly, so it should pass either way; confirm regardless.

**Acceptance check:** The favicon request in the browser's Network tab returns 200 (not 404) when loading a nested page (e.g., `weeks/week-05.html`) via `python3 -m http.server`. `build/partials/head.html` has an explanatory comment next to the favicon line regardless of which option was chosen.

---

## Summary table

| ID | Task | Criticality | Depends on |
|---|---|---|---|
| H1 | Fix 5 mismatched week titles; generate schedule links from `_WEEK_TITLES` | High | — |
| H2 | Fix stray quote entities in `week-03.html`; extend entity test to quotes | High | — |
| M1 | Update README's test-suite documentation | Medium | — |
| M2 | Remove unused WordPress-theme CSS (~150 lines) | Medium | — |
| L1 | Add Open Graph / Twitter Card meta tags | Low | — |
| L2 | Move `<h1>` out of the `<header>` landmark (optional) | Low | — |
| L3 | Align favicon link to the `{{REL}}` convention (or document the exception) | Low | — |

Recommended sequencing: **H1** and **H2** first (both are small, isolated content/test fixes with no dependencies on each other or anything else). Then **M1** (pure documentation, zero risk) and **M2** (CSS-only, easy to visually verify) in either order. **L1** is a quick, additive win worth doing opportunistically. **L2** and **L3** are genuinely optional — do them only if a broader accessibility/portability pass is already planned, since both touch shared layout partials and warrant a visual regression check across all page types and breakpoints.
