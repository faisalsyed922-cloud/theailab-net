# Website Code Review: IPHS 400 Course Site

**Date:** 2026-09-01
**Scope:** Full repository — 22 static HTML pages, `css/style.css`, Netlify config, GitHub Actions deploy workflow, and the pytest test suite.
**Reviewer:** Claude Code (automated review)

## Summary

This is a well-organized, dependency-free static site (22 hand-written HTML pages, one shared stylesheet, no JS, no build step) with a genuinely useful pytest suite that catches structural regressions (broken links, missing nav items, missing footers, placeholder text, orphaned pages). That test suite is the project's strongest asset and above what most sites this size have.

The main gap is architectural, not cosmetic: every page hand-duplicates ~25 lines of identical header/nav/footer markup, and that duplication has already produced small, visible inconsistencies (see §1.1–1.2). There's also a real, reproducible bug in how the 404 page will render on nested paths (§2.1), a complete absence of SEO/social metadata (§3), and no accessibility or HTML-validity testing to complement the strong structural test suite (§5). None of this is hard to fix — most items below are small, targeted changes — but several are worth fixing before the site goes live for students.

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

**Fix:** pick one convention (plain relative paths are simpler and shorter) and normalize all pages. Better: generate the nav from a single template.

### 1.2 Inconsistent attribute order on the `active` class

`index.html`, `core/about.html`, `core/assignments.html`, `core/policies.html` write `href="..." class="active"`; `core/schedule.html`, `core/syllabus.html`, and all `weeks/*.html` write `class="active" href="..."`. Cosmetically harmless, but it's a second, independent signal of hand-copy drift in the same block.

### 1.3 Recommendation

For a 22-page site that's explicitly expected to be edited weekly during the semester (per the syllabus's own "AI tooling changes on a timescale of weeks" note, and the schedule page being the "authoritative" living document), hand-duplicated boilerplate is a real maintenance risk: a nav change, a footer copyright year, or a new "Resources" link requires 22 correct edits. Options, roughly in order of how much they preserve the current "no build step" simplicity:

- **Lightest:** a tiny build script (even a 20-line Python/Node script) that injects a shared `_header.html`/`_footer.html` partial into each page at commit- or CI-time, keeping the deployed output as plain static HTML.
- **Standard:** adopt a static site generator with includes/layouts (11ty, Jekyll, Astro in static mode) — bigger lift, but is exactly the tool for "one shared skeleton, many content pages," and would eliminate 1.1/1.2 entirely.
- **Status quo + guardrail:** if the team wants to keep zero build tooling, add a pytest check (extending `test_unit_html_structure.py`) that asserts the nav `<ul>` markup is byte-identical (modulo the `active` class and `../` prefix depth) across all pages, so drift like 1.1 fails CI instead of shipping silently.

---

## 2. Bugs

### 2.1 `404.html` uses root-relative-looking but actually page-relative paths — will break its own styling and links on nested 404s

`netlify.toml` routes any unmatched path to `404.html` while **keeping the original URL** and a `404` status:

```toml
[[redirects]]
  from = "/*"
  to = "/404.html"
  status = 404
```

But `404.html` itself links to its assets with page-relative paths, as if it always lived at the site root:

```html
<!-- 404.html:8, 13, 15-20 -->
<link href="css/style.css" rel="stylesheet"/>
...
<li><a href="index.html" class="active">Home</a></li>
<li><a href="core/syllabus.html">Syllabus</a></li>
```

Netlify serves the *content* of `404.html` but the browser's URL bar (and thus the base for relative-URL resolution) stays at whatever the visitor actually requested. So:

- A bad top-level path like `/foo` → relative paths resolve against `/`, so this happens to work.
- A bad path one level deep, e.g. `/weeks/week-99.html` or `/core/typo.html` → `css/style.css` resolves to `/weeks/css/style.css` (404, page renders unstyled), and `index.html`/`core/syllabus.html` resolve to `/weeks/index.html` / `/weeks/core/syllabus.html` (both 404) — every link and the stylesheet on the error page is broken.
- Any deeper bad path breaks even worse.

Given that most real-world 404s are exactly this kind (a mistyped or stale link one directory deep — e.g., a student bookmarking `weeks/week-16.html`, or an old link to a renamed page), this is the common case, not an edge case.

**Fix:** use root-relative paths (leading `/`) in `404.html`:

```html
<link href="/css/style.css" rel="stylesheet"/>
...
<li><a href="/index.html" class="active">Home</a></li>
<li><a href="/core/syllabus.html">Syllabus</a></li>
```

This is a one-file, ~7-line fix. Consider adding a regression test for it (see §5).

### 2.2 Course-facing GitHub URL is plain text, not a link

`core/syllabus.html:39` and `core/about.html:60` render the repository URL as inert `<code>` text:

```html
<td><code>https://github.com/jon-chun/theailab-net</code> (materials) and Moodle (quizzes, grades, submissions)</td>
```

Students have to select and copy/paste it manually. Minor, but easy to fix — wrap it in `<a href="https://github.com/jon-chun/theailab-net">`.

### 2.3 README "Live site" URL is a placeholder

`README.md:13` — `**Live site:** _add Netlify URL here once deployed_`. Not a code bug, but flag it so it isn't forgotten once the Netlify site exists (nothing currently checks for this placeholder the way the HTML test suite checks for `TODO`/`TBD`).

---

## 3. Missing SEO / social / discoverability metadata

None of the 22 pages have any of the following, confirmed by grep across the whole repo:

- `<meta name="description">` — every page currently falls back to no snippet in search results and no summary when shared.
- Open Graph / Twitter Card tags (`og:title`, `og:description`, `og:type`, `twitter:card`) — links shared in Slack/Discord/email/social will show no preview.
- `<link rel="canonical">`.
- `favicon.ico` / `<link rel="icon">` — browsers will request `/favicon.ico` on every page load and silently 404.
- `robots.txt` and `sitemap.xml` at the site root.

For a course site this is low-stakes (it's not competing for search ranking), but a per-page `<meta name="description">` and a favicon are cheap, high-value additions — the favicon in particular is a visible polish gap (browser tabs currently show a generic blank/default icon), and a description meaningfully improves how the link looks when pasted into Moodle, email, or a syllabus aggregator.

**Fix:** add a per-page description (can be templated from existing content, e.g., the hero `<h1>` text + "IPHS 400: Frontiers in AI") and a favicon; a `robots.txt` allowing all and a generated `sitemap.xml` are optional nice-to-haves.

---

## 4. Accessibility

The markup is basic and mostly harmless (no images means no alt-text problems, and the color palette has reasonable contrast), but a few standard patterns are missing:

- **No skip-to-content link.** Every page repeats the same ~6-item nav before the main content; keyboard and screen-reader users have no way to jump past it. Standard fix: a visually-hidden `<a href="#main" class="skip-link">Skip to content</a>` as the first element in `<body>`, plus `id="main"` on the `<main>` element (all pages already have `<main class="content-wrapper">`, so this is a small addition).
- **No `aria-current="page"`.** The current-page nav item is marked only with `class="active"` (a purely visual signal). Screen readers get no indication of which nav item represents the current page. Fix: add `aria-current="page"` alongside `class="active"` wherever it appears.
- **Header/hero structure is unconventional.** `<section class="hero">` (containing the page's only `<h1>`) is nested *inside* `<header class="site-header">`, alongside the site branding and `<nav>`. This isn't invalid HTML, but it does mean the page's `<h1>` is inside the same `<header>` landmark as the sitewide nav rather than at the start of `<main>`, which can be a little unexpected for assistive-tech users navigating by landmark. Not urgent, but worth a look if there's ever an accessibility audit.
- **`--text-lt: #767676`** on white background (used for taglines, breadcrumbs, meta text) is roughly a 4.5:1 contrast ratio — right at the WCAG AA threshold for normal-size text. It passes, but has no margin; worth confirming intended sizes stay ≥ the AA thresholds if this color is reused for smaller text later.

None of these are caught by the current test suite, which validates structure/content but not accessibility (see §5).

---

## 5. Test suite: strong on structure, has no coverage for the issues above

`tests/` is genuinely good — `test_unit_html_structure.py`, `test_integration_links.py`, and `test_e2e_site.py` together catch broken links, missing nav items, orphaned pages, placeholder text, and a hardcoded exact-page-count check that will force a deliberate update whenever a page is added or removed. Wired into CI (`.github/workflows/deploy-netlify.yml`) as a required gate before deploy — good practice.

Gaps, in rough priority order:

1. **No regression test for the 404.html path bug (§2.1).** Nothing checks that `404.html`'s internal asset/link paths are root-relative rather than page-relative. This is exactly the kind of subtle, non-visually-obvious bug a targeted test would have caught and would prevent from recurring.
2. **No nav-markup-identity check**, so the `../core/` vs. plain-relative split (§1.1) and the `active`-attribute-order split (§1.2) pass silently — `test_nav_links_resolve` only checks that links *resolve*, not that the markup is byte-consistent across pages.
3. **No HTML validation.** The suite parses with BeautifulSoup/lxml (which is lenient) but never runs an actual validator (e.g., the W3C validator API, or `html5lib` in strict mode) to catch malformed markup.
4. **No accessibility checks** (e.g., `axe-core` via a headless browser, or even simple heuristics like "every page has exactly one `<h1>`," "no skipped heading levels," "nav links have discernible text").
5. **No check for `<meta name="description">` or favicon presence**, so §3's gaps would ship silently even if added inconsistently later.
6. **`tests/requirements.txt` uses open-ended lower bounds** (`pytest>=7`, `beautifulsoup4>=4`, `lxml>=4`) with no upper bound or lockfile. Fine for a small low-risk project, but means CI can start failing from an unrelated upstream major-version bump with no local repro until someone runs `pip install -U`. Consider pinning exact versions (or a `constraints.txt`) for reproducibility, especially since CI has no caching/lockfile step either.

---

## 6. Deployment / CI configuration

`.github/workflows/deploy-netlify.yml` and `netlify.toml` are reasonable for a static site and already do several things right: a `test` job gates `deploy`, `concurrency` prevents overlapping production deploys, and `permissions: contents: read` is scoped down at the workflow level. A few smaller notes:

- **Third-party action pinned to a floating major-version tag, not a SHA.** `nwtgck/actions-netlify@v3` (and the official `actions/checkout@v4`, `actions/setup-python@v5`) are pinned to mutable tags. For the official `actions/*` this is low-risk; for the third-party `nwtgck/actions-netlify` action — which runs with access to `NETLIFY_AUTH_TOKEN` — pinning to a commit SHA (`nwtgck/actions-netlify@<sha> # v3.x.x`) is the stronger supply-chain-security practice, since a compromised or force-pushed tag would otherwise run arbitrary code with your deploy token. Worth doing given the guidance already baked into this course's own syllabus about secrets hygiene (`core/syllabus.html`, "Secrets Hygiene and Agent Safety").
- **Security headers cover two of several common ones.** `netlify.toml` sets `X-Frame-Options: DENY` and `X-Content-Type-Options: nosniff`, but not `Referrer-Policy`, `Permissions-Policy`, or `Strict-Transport-Security`. For a static informational site with no forms, no cookies, and no third-party scripts, the risk this closes is small, but they're one-line additions with no downside:
  ```toml
  Referrer-Policy = "strict-origin-when-cross-origin"
  Permissions-Policy = "geolocation=(), camera=(), microphone=()"
  Strict-Transport-Security = "max-age=63072000; includeSubDomains; preload"
  ```
- **Verify there isn't a second deploy path.** The workflow deploys via the Netlify API (`nwtgck/actions-netlify`) using `NETLIFY_SITE_ID`/`NETLIFY_AUTH_TOKEN`. If that Netlify site *also* has native Git-based continuous deployment enabled in the Netlify dashboard, every push to `main` would trigger two independent deploys. Worth a quick check in the Netlify site settings (Site configuration → Build & deploy) to confirm Git CD is disabled there, since the repo has clearly standardized on the GitHub Actions path.

---

## 7. Content duplication (maintenance risk, not a bug)

Several large blocks of prose are duplicated verbatim across pages rather than written once:

- "Course Description" and the full 9-item "Course Goals and Learning Outcomes" list are identical, word-for-word, in both `core/about.html` and `core/syllabus.html`.
- The "Summary of Assignments and Weights" table (9 rows) is duplicated identically in `core/syllabus.html` and `core/assignments.html`.
- The "Secrets Hygiene and Agent Safety" section is duplicated identically in `core/syllabus.html` and `core/policies.html`.

This is a natural consequence of the no-templating architecture (§1) rather than a distinct problem, but it compounds the maintenance risk: a mid-semester change to, say, the MP3 due date or a learning outcome now has to be made correctly in two (or three) separate files, and nothing in the test suite checks that these duplicated blocks stay in sync. If a shared-template solution (§1.3) is adopted, this becomes a natural place to factor out shared partials/includes (e.g., `_assignments-table.html`, `_secrets-hygiene.html`) rather than free text duplication.

---

## Priority Summary

| # | Finding | Section | Effort |
|---|---|---|---|
| 1 | `404.html` breaks its own CSS/links on any nested bad path | 2.1 | Trivial (1 file, ~7 lines) |
| 2 | Two inconsistent nav-link conventions across core pages | 1.1 | Small (normalize 22 files, ideally via template) |
| 3 | No favicon / meta description on any page | 3 | Small |
| 4 | No skip-link, no `aria-current` on active nav item | 4 | Small |
| 5 | Third-party deploy action pinned to a tag, not a SHA | 6 | Trivial |
| 6 | No templating layer — root cause of #2 and the content duplication in §7 | 1, 7 | Medium–Large, but highest long-term payoff |
| 7 | Test suite has no accessibility, HTML-validity, or nav-identity checks | 5 | Medium |
| 8 | Missing `Referrer-Policy`/`Permissions-Policy`/HSTS headers | 6 | Trivial |
| 9 | GitHub repo URL rendered as inert text, not a link | 2.2 | Trivial |
| 10 | `tests/requirements.txt` has no upper-bound pins | 5.6 | Trivial |

Items 1–5 are worth doing before the site is treated as "live" for students; items 6–10 are good follow-ups, with #6 being the one structural change that would prevent most of the others from recurring.
