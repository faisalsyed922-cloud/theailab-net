# Tech Spec: IPHS 400 Website Revisions

**Date:** 2026-09-03
**Source:** Synthesizes `docs/report_web-revision_v1_20260903.md` into actionable, ranked implementation tasks.
**Scope:** Static site only (`index.html`, `404.html`, `core/*.html`, `weeks/*.html`, `css/style.css`, `tests/`). No deploy/hosting layer is in scope — the site runs via `python3 -m http.server` only.

Each task below is self-contained: a reader should be able to pick any one task and implement it without reading the others, though task **H1** is the prerequisite that makes several other tasks cheaper (noted inline where relevant).

---

## How to use this document

Tasks are grouped by criticality (`high` → `medium` → `low`) and numbered `H1, H2, ...`, `M1, M2, ...`, `L1, L2, ...`. Within each tier, tasks are ordered by recommended implementation sequence, not further ranked. Each task has:

- **Description** — what changes.
- **Justification** — why it matters, referencing the source report section.
- **Steps** — concrete implementation instructions.
- **Acceptance check** — how to confirm the task is done correctly.

---

## HIGH criticality

### H1 — Replace hand-duplicated boilerplate and prose with a template/include build step

**Report refs:** §1 (1.1–1.4), §6

**Description:** Introduce a small, dependency-light build script that generates all 22 HTML pages from (a) one shared page skeleton/partials for the header/nav/footer/breadcrumb chrome, and (b) per-page content fragments. Shared prose blocks that are currently duplicated verbatim across pages (course description, learning outcomes, assignments table, secrets-hygiene section) become single source-of-truth fragments included wherever they appear. The build step runs locally before committing; the *output* remains plain static HTML with zero client-side dependencies, so `python3 -m http.server` continues to work exactly as today.

**Justification:** This is the root cause of nearly every other structural finding in the report: the two different nav-link conventions (§1.1), the inconsistent `active`-attribute ordering (§1.2), the mixed em-dash encoding (§1.3), and — most importantly — the duplicated prose blocks in §6 (course description/outcomes in both `about.html` and `syllabus.html`; the assignments table in both `syllabus.html` and `assignments.html`; the secrets-hygiene section in both `syllabus.html` and `policies.html`). The syllabus itself states the schedule is a "living document" edited weekly; every week that duplication survives is another chance for two copies of the same fact (a due date, a policy line) to silently diverge in front of students. Fixing this once prevents the others from recurring and removes the maintenance burden of 22-file edits for a single content change.

**Steps:**

1. Create a `build/` directory (or `scripts/` — pick one, be consistent) at the repo root, kept out of the deployed page set but tracked in git.
2. Extract the shared chrome into partials, e.g.:
   - `build/partials/head.html` — the `<head>` block up to (not including) `<title>`, since the title is per-page.
   - `build/partials/header.html` — the `<header class="site-header">…</header>` block, parameterized on: (a) the relative path prefix to the site root (`""` for `index.html`/`404.html`, `"../"` for everything in `core/` and `weeks/`), and (b) which nav label gets `class="active"`.
   - `build/partials/footer.html` — the `<footer class="site-footer">` block (currently identical on every page — no parameters needed).
   - `build/partials/breadcrumb.html` — parameterized on the breadcrumb trail (e.g., `Home » Syllabus` vs. `Home » Schedule » Week 7: …`), used by every page except `index.html` and `404.html`.
3. Extract genuinely duplicated prose into shared content fragments, e.g.:
   - `build/shared/course-description.html` (used by `about.html` and `syllabus.html`)
   - `build/shared/learning-outcomes.html` (used by `about.html` and `syllabus.html`)
   - `build/shared/assignments-table.html` (used by `syllabus.html` and `assignments.html`)
   - `build/shared/secrets-hygiene.html` (used by `syllabus.html` and `policies.html`)
4. Move each page's remaining unique content into a per-page fragment under `build/content/<same relative path>` (e.g., `build/content/core/syllabus.html` holds just the syllabus-specific sections, with `{{INCLUDE:course-description}}`-style markers where a shared fragment should be spliced in).
5. Create a small metadata table the build script reads — one entry per output page — with: output path, `<title>` text (minus the fixed `– IPHS 400: Frontiers in AI` suffix, which the build script appends), active nav label, and breadcrumb trail. A plain Python `dict`/list literal or a small JSON/YAML file both work; pick whichever is easiest to keep in sync by hand for a 22-entry table.
6. Write `build/build.py` (pure standard library — no new dependency): for each metadata entry, render `head.html` + `header.html` (with the correct relative prefix and active label) + `breadcrumb.html` (if applicable) + the page's content fragment (with shared fragments spliced in) + `footer.html`, and write the result to the real output path (e.g., `core/syllabus.html`), overwriting the current hand-written file. Use simple string `.replace()` templating (e.g. `{{CONTENT}}`, `{{ACTIVE:Home}}`, `{{REL}}`) — no need for a templating library.
7. Run the build script once and diff every generated page against the current committed version with `git diff --word-diff`. Confirm the *only* differences are the drift already identified in the report (nav convention, attribute order, em-dash encoding) — no visible page content should change. This is the regression check that nothing was lost in extraction.
8. Update `README.md`'s "Local Development" section to note the new step: `python3 build/build.py` before serving (or before committing — pick one and document it clearly), so the checked-in HTML stays in sync with the source fragments.
9. Add a `pytest` check (see task **M4**) that fails if the committed HTML output doesn't match what `build/build.py` would currently produce — this is what actually prevents future drift, since there's no CI to enforce it automatically. The simplest version: build into a temp directory and byte-compare against the committed files.
10. Commit the new `build/` sources alongside the regenerated page files in one changeset so the diff is reviewable.

**Acceptance check:** `python3 build/build.py` followed by `git diff` shows either no changes (idempotent) or only the intentional normalization changes from step 7. All existing tests in `tests/` still pass unmodified. Editing one shared fragment (e.g., the assignments table) and re-running the build updates both consuming pages identically.

---

### H2 — Resolve `404.html`'s dead-code status and correct the stale test comment

**Report refs:** §2.1, §5.1

**Description:** Decide explicitly whether `404.html` is (a) kept as forward-looking dead code for a future hosting layer that supports custom error pages, or (b) removed since it currently serves no function. Recommended: **keep it**, but (1) correct the misleading comment in `tests/conftest.py` that describes a serving mechanism which no longer exists in this repo, and (2) make its internal links root-relative so it is correct-by-construction if the site is later hosted somewhere that *does* auto-serve a root `404.html` (e.g., GitHub Pages) from a nested bad path.

**Justification:** The file was wired up via the now-deleted `netlify.toml` redirect rule; nothing in the current repo (including the documented `python3 -m http.server` workflow) will ever render it. Worse, `tests/conftest.py`'s `nav_pages` fixture carries a docstring asserting `404.html` "is a server-served fallback page" — this actively misleads the next person reading the test suite into believing a 404-routing mechanism exists today. Left unaddressed, this is exactly the kind of stale comment that causes a future contributor to waste time hunting for a mechanism that isn't there, or to assume 404 behavior is tested when it isn't.

**Steps:**

1. Confirm the decision to keep `404.html` (recommended — it costs nothing to keep and several common static hosts, including GitHub Pages, auto-serve a root-level `404.html` by convention, so keeping it correctly formed now saves rework later).
2. In `404.html`, change the stylesheet link and every nav/body link from page-relative to root-relative paths (add a leading `/`):
   - `<link href="css/style.css" ...>` → `<link href="/css/style.css" ...>`
   - `<a href="index.html">` → `<a href="/index.html">`
   - `<a href="core/syllabus.html">` → `<a href="/core/syllabus.html">`, and similarly for the other four nav links.
   - The "← Home" link in the body → `<a href="/index.html">`.
   - Reasoning: a host that serves `404.html` in place of a missing nested path (e.g., `/weeks/week-99.html`) keeps the *original* URL in the browser's address bar, so page-relative paths resolve against the wrong directory. Root-relative paths resolve correctly regardless of how deep the missing path was.
3. In `tests/conftest.py`, replace the `nav_pages` fixture's docstring with an accurate statement, e.g.: *"All HTML files except `404.html`. `404.html` is not linked from navigation or content and is not served by the local dev workflow (`python3 -m http.server` has no custom-error-page support); it is kept root-relative and structurally valid so it works correctly if the site is later hosted somewhere that auto-serves a root `404.html` (e.g., GitHub Pages). It's therefore excluded from nav-consistency and reachability-from-index checks."*
4. Add a short note to `README.md` (e.g., under "Repository Structure" or a new one-line callout) stating that `404.html` is present for forward compatibility with static hosts that support custom error pages, and is not active during local development.
5. Add a regression test (fold into task **M4**, or add standalone now) asserting every `href`/`link` in `404.html` starts with `/` — this is what would have caught the original root-relative bug and prevents it from regressing if someone edits the file by hand later.

**Acceptance check:** `grep -o 'href="[^"]*"' 404.html` shows every internal path starts with `/`. `tests/conftest.py`'s docstring makes no claim about an active serving mechanism. A new test fails if any `404.html` internal link lacks a leading `/`.

---

## MEDIUM criticality

### M1 — Normalize nav link conventions and `active`-attribute ordering (interim fix if H1 is deferred)

**Report refs:** §1.1, §1.2

**Description:** Pick one relative-link convention for nav hrefs inside `core/*.html` and `weeks/*.html`, and one attribute order for the `active` class, then apply both consistently across all 22 pages.

**Justification:** These are two independent, already-observed symptoms of copy-paste drift (§1.1: `../core/x.html` vs. plain `x.html`; §1.2: `href="..." class="active"` vs. `class="active" href="..."`). Both currently "work" (the link-checker tests pass either way), but they make the next hand-edit error-prone and are exactly the kind of inconsistency that compounds over a semester of weekly edits. If task **H1** is implemented, this normalization happens automatically as part of generating the shared nav partial and this task can be skipped. If H1 is deferred or descoped, do this directly as a stopgap.

**Steps:**

1. Pick the convention: use plain relative paths within a directory (e.g., `syllabus.html` from another file inside `core/`) and `../` only to go *up* a directory (e.g., `../index.html` from `core/` or `weeks/`, `../core/x.html` from `weeks/`). This matches what `core/about.html`, `core/assignments.html`, and `core/policies.html` already do and is shorter/simpler than the `../core/` self-referential form.
2. In `core/syllabus.html` and `core/schedule.html`, change nav hrefs from `../core/schedule.html`, `../core/assignments.html`, etc. to `schedule.html`, `assignments.html`, etc. (leave `../index.html` as-is — that genuinely goes up a directory).
3. Pick the attribute order: `href="..." class="active"` (matches `index.html`, `core/about.html`, `core/assignments.html`, `core/policies.html` — the majority).
4. In `core/schedule.html`, `core/syllabus.html`, and all 15 `weeks/*.html` files, reorder `class="active" href="..."` to `href="..." class="active"` on the one nav `<a>` per page that carries the class.
5. Run the full test suite (`pytest tests/ -v`) — all nav-related tests should still pass unchanged, since they check label sets and link resolution, not markup byte-order.

**Acceptance check:** `grep -rn '\.\./core/' core/*.html` returns no results. `grep -rln 'class="active" href=' index.html core/*.html weeks/*.html` returns no results (all instances are `href="..." class="active"`).

---

### M2 — Add a favicon and per-page `<meta name="description">`

**Report refs:** §3

**Description:** Add a `<link rel="icon">` favicon and a tailored `<meta name="description">` tag to the `<head>` of all 22 pages.

**Justification:** Every page currently triggers a silent, wasted `favicon.ico` request and shows a generic/blank browser-tab icon; and with no description tag, any link pasted into Moodle, email, or a syllabus aggregator shows no summary snippet. Both are cheap, purely additive fixes with no downside, and meaningfully improve the site's day-to-day polish for students who have it open in a tab for 15 weeks.

**Steps:**

1. Produce a simple favicon (an `.svg` or small `.ico`/`.png` is fine — e.g., a monogram or a simple icon consistent with the `--primary: #0073a8` brand color already used sitewide). Save it as `favicon.svg` (or `.ico`) at the repo root.
2. Add `<link rel="icon" href="/favicon.svg" type="image/svg+xml">` (adjust `type`/filename for whichever format is chosen) to every page's `<head>`. Note the root-relative `/` path works the same way here as in task H2 — it resolves correctly regardless of page depth (`core/`, `weeks/`, or root).
3. Write one `<meta name="description" content="...">` per page. Keep each under ~155 characters. A simple, mechanical approach that avoids 22 bespoke sentences: `"{hero h1 text} — IPHS 400: Frontiers in AI, Kenyon College."` for week/core pages, and a slightly fuller one-sentence course summary for `index.html`.
4. Insert the meta tag immediately after the `<meta name="viewport">` line on every page, so its position is consistent (helps any future automated check).
5. If task **H1** (templating) is done first, add both tags to the shared `head.html` partial (with the description parameterized per page in the metadata table) instead of hand-editing 22 files.

**Acceptance check:** `grep -L 'rel="icon"' index.html 404.html core/*.html weeks/*.html` and the equivalent for `name="description"` both return no files (i.e., every page has both).

---

### M3 — Baseline accessibility improvements

**Report refs:** §4

**Description:** Add a skip-to-content link, mark the active nav item with `aria-current="page"` in addition to the existing `class="active"`, and note (for a future pass, not required now) the unconventional hero-inside-header landmark structure.

**Justification:** Every page repeats the same six-item nav before the main content, with no way for keyboard or screen-reader users to skip past it, and the visually-only `class="active"` signal is invisible to assistive technology. Both are standard, well-understood fixes with no visual-design impact for sighted mouse users, appropriate for a university course site where accessibility accommodations are already referenced in `core/policies.html`.

**Steps:**

1. Add a visually-hidden skip link as the very first element inside `<body>` on every page:
   ```html
   <a href="#main" class="skip-link">Skip to content</a>
   ```
2. Add `id="main"` to the existing `<main class="content-wrapper">` element on every page (it's already present as an element, just needs the id).
3. In `css/style.css`, add a `.skip-link` rule that hides the link off-screen by default and reveals it on keyboard focus, e.g.:
   ```css
   .skip-link {
     position: absolute;
     left: -9999px;
     top: 0;
     background: var(--bg);
     color: var(--accent);
     padding: 0.75rem 1.25rem;
     z-index: 10;
   }
   .skip-link:focus {
     left: 1rem;
     top: 1rem;
   }
   ```
4. On every page's nav, add `aria-current="page"` on the same `<a>` that already carries `class="active"` (e.g., `<a href="schedule.html" class="active" aria-current="page">Schedule</a>`).
5. Treat the hero-inside-`<header>` landmark restructuring as an optional follow-up, not part of this task — it would require a small CSS layout change beyond a pure markup fix and is lower-value than the skip-link/`aria-current` additions. Revisit only if a fuller accessibility audit is planned.
6. If task **H1** is done first, apply steps 1–2 and 4 to the shared `header.html`/page-skeleton partial instead of 22 individual files.

**Acceptance check:** Tab from the page load on any page — the skip link should become visible on first Tab press and jump focus to `<main>` when activated. `grep -c 'aria-current="page"' <file>` returns exactly 1 for every page that has an active nav item.

---

### M4 — Expand the pytest suite: nav-markup identity, HTML validation, accessibility heuristics, and metadata presence

**Report refs:** §5 (5.2–5.5)

**Description:** Add new test modules/cases to `tests/` that would have caught the issues in this report automatically, so future drift fails the test suite instead of shipping silently.

**Justification:** The existing suite (`test_unit_html_structure.py`, `test_integration_links.py`, `test_e2e_site.py`) is strong on structure and link integrity but has no coverage for nav-markup consistency, HTML validity, accessibility basics, or the metadata added in M2/M3. Since there is no CI gate anymore, the test suite run locally before a commit is the *only* automated safety net available — making it comprehensive is now more valuable, not less.

**Steps:**

1. **Nav-markup identity check** (extend `tests/test_integration_links.py` or add `tests/test_nav_identity.py`): normalize each page's `nav.main-nav` markup by stripping the `active`/`aria-current` attributes and the `../` depth prefix from every href, then assert the normalized markup is byte-identical across all non-404 pages. This directly catches the §1.1/§1.2 drift class if it ever recurs.
2. **HTML validation** (add `tests/test_html_validity.py`): parse every page with `html5lib` in place of/alongside `lxml` (add `html5lib` to `tests/requirements.txt`) and assert no parse errors are reported (`html5lib` exposes a `parseErrors` list on strict parsing). This is a fully offline check — no network dependency on the W3C validator API.
3. **Accessibility heuristics** (add `tests/test_accessibility.py`): assert (a) every page has exactly one `<h1>`, (b) heading levels never skip (no `<h4>` without a preceding `<h3>` in the same content block), (c) every page has a `.skip-link` (once M3 lands), and (d) the active nav link on every non-index page carries `aria-current="page"` (once M3 lands).
4. **Metadata presence check** (extend `tests/test_unit_html_structure.py`): assert every page has a `<link rel="icon">` and a `<meta name="description">` with non-empty `content` under ~160 characters (once M2 lands).
5. **Build-drift check** (if task **H1** landed): add `tests/test_build_matches_committed.py` that runs `build/build.py` into a temp directory and asserts byte-for-byte equality against the committed page files, using the same `all_html_files` fixture pattern already in `tests/conftest.py`.
6. Run `pytest tests/ -v` after each addition to confirm it passes against the current (post-H1/M1/M2/M3) site and would fail if the corresponding regression were reintroduced (spot-check by temporarily reintroducing one issue, e.g. reverting one nav link to the old convention, and confirming the new test catches it).

**Acceptance check:** `pytest tests/ -v` passes with the new test modules included, and each new test can be shown to fail when the defect it targets is manually reintroduced.

---

## LOW criticality

### L1 — Convert the plain-text GitHub repository URL into a clickable link

**Report refs:** §2.2

**Description:** Wrap the repository URL in `core/syllabus.html` and `core/about.html` in an `<a href>` instead of rendering it as inert `<code>` text.

**Justification:** Students currently have to manually select and copy the URL rather than clicking it — a small but easy-to-fix friction point on a page (the syllabus) students will reference often.

**Steps:**

1. In `core/syllabus.html`, find:
   ```html
   <tr><th>Course Site</th><td><code>https://github.com/jon-chun/theailab-net</code> (materials) and Moodle (quizzes, grades, submissions)</td></tr>
   ```
   Replace with:
   ```html
   <tr><th>Course Site</th><td><a href="https://github.com/jon-chun/theailab-net"><code>https://github.com/jon-chun/theailab-net</code></a> (materials) and Moodle (quizzes, grades, submissions)</td></tr>
   ```
2. In `core/about.html`, find:
   ```html
   <li>Materials: <code>https://github.com/jon-chun/theailab-net</code></li>
   ```
   Replace with:
   ```html
   <li>Materials: <a href="https://github.com/jon-chun/theailab-net"><code>https://github.com/jon-chun/theailab-net</code></a></li>
   ```
3. If task **H1** is done first and this URL lives in a shared fragment, make the edit once there instead.

**Acceptance check:** Both links are clickable in a browser and open the correct GitHub URL; `pytest tests/ -v` still passes (external links are skipped by the link-checker, per `_resolve_href`'s `http://`/`https://` exclusion).

---

### L2 — Normalize em-dash encoding (literal character vs. `&mdash;`/`&ndash;` entities)

**Report refs:** §1.3

**Description:** Standardize on the literal `—`/`–` characters (already used site-wide in the header/nav) instead of the mixed use of `&mdash;`/`&ndash;` HTML entities found in `weeks/*.html` and a few other pages.

**Justification:** Purely cosmetic (both render identically), but it's a low-cost consistency fix and removes one more small signal of copy-paste-and-edit authoring, making future find-and-replace edits across pages more reliable (a search for `—` currently misses entity-encoded instances and vice versa).

**Steps:**

1. Search for entity usage: `grep -rn '&mdash;\|&ndash;' weeks/*.html core/*.html index.html 404.html`.
2. Replace `&mdash;` with `—` and `&ndash;` with `–` in each matched file (a simple find-and-replace; no semantic change).
3. Re-open a couple of affected pages in a browser to confirm rendering is unchanged (it will be — these are the same Unicode characters either way).
4. If task **H1** lands first, do this normalization once in the source content fragments rather than across 22 output files.

**Acceptance check:** `grep -rln '&mdash;\|&ndash;' weeks/*.html core/*.html index.html 404.html` returns no files.

---

### L3 — Pin exact versions in `tests/requirements.txt`

**Report refs:** §5.6

**Description:** Replace the open-ended lower-bound version specifiers (`pytest>=7`, `beautifulsoup4>=4`, `lxml>=4`) with exact pins matching a known-good, currently-tested combination.

**Justification:** With no CI to catch an unrelated upstream major-version bump, a future contributor's `pip install -r tests/requirements.txt` could silently pull in a breaking new major version of `pytest`/`beautifulsoup4`/`lxml` with no local repro path until they dig into a confusing failure. Pinning trades a small amount of update friction for reproducibility — appropriate for a small, infrequently-touched test suite.

**Steps:**

1. In the existing `.venv` (or a fresh one), run `pip install -r tests/requirements.txt` followed by `pip freeze | grep -iE 'pytest|beautifulsoup4|lxml|html5lib'` to capture the currently-working versions (include `html5lib` if task M4 added it).
2. Replace `tests/requirements.txt` with exact `==` pins for each, e.g.:
   ```
   pytest==<captured version>
   beautifulsoup4==<captured version>
   lxml==<captured version>
   ```
3. Re-run `pytest tests/ -v` from a clean virtualenv to confirm the pinned versions install and all tests pass.
4. Note in a one-line comment at the top of the file that these are intentionally pinned (not floor-bounded) for reproducibility, and should be bumped deliberately rather than left open-ended.

**Acceptance check:** `pip install -r tests/requirements.txt` in a fresh virtualenv installs the exact pinned versions with no resolver warnings, and `pytest tests/ -v` passes.

---

## Summary table

| ID | Task | Criticality | Depends on |
|---|---|---|---|
| H1 | Template/include build step; de-duplicate shared prose | High | — |
| H2 | Resolve `404.html` dead-code status; fix stale test comment | High | — |
| M1 | Normalize nav link convention + attribute order | Medium | Skip if H1 done |
| M2 | Favicon + per-page meta description | Medium | Easier after H1 |
| M3 | Skip link, `aria-current`, landmark note | Medium | Easier after H1 |
| M4 | Test suite: nav identity, HTML validity, a11y, metadata checks | Medium | Partly depends on M1–M3 landing first |
| L1 | Linkify GitHub repo URL | Low | Easier after H1 |
| L2 | Normalize em-dash encoding | Low | Easier after H1 |
| L3 | Pin test dependency versions | Low | — |

Recommended sequencing: **H2** first (small, isolated, no dependencies), then **H1** (unlocks cheaper versions of M1–M3, L1, L2), then M2/M3 together (both are per-page `<head>`/nav additions), then M4 to lock in all the above with tests, then the remaining low-effort L-tasks.
