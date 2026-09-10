#!/usr/bin/env python3
"""Regenerates every page in the site from build/partials, build/shared, and
build/content.

Run this locally before committing whenever you edit anything under build/:

    python3 build/build.py

The output is plain static HTML with no client-side dependencies - this
script only runs locally as a source-of-truth step, never in the browser.
`tests/test_build_matches_committed.py` fails if the committed pages drift
from what this script currently produces.
"""
import re
from pathlib import Path

SITE_ROOT = Path(__file__).parent.parent
BUILD_DIR = Path(__file__).parent
PARTIALS = BUILD_DIR / "partials"
SHARED = BUILD_DIR / "shared"
CONTENT = BUILD_DIR / "content"

NAV_ITEMS = [
    ("Home", "index.html"),
    ("Syllabus", "core/syllabus.html"),
    ("Schedule", "core/schedule.html"),
    ("Assignments", "core/assignments.html"),
    ("Policies", "core/policies.html"),
    ("About", "core/about.html"),
]

_WEEK_TITLES = {
    1: "Week 1: Course Introduction",
    2: "Week 2: Shell Fundamentals and Dotfiles",
    3: "Week 3: Anatomy of an AI Coding Agent",
    4: "Week 4: CLAUDE.md and Slash Commands",
    5: "Week 5: Agent Skills, Subagents, and MCP",
    6: "Week 6: Hooks Architecture and Guardrails",
    7: "Week 7: Multi-Agent Orchestration Fundamentals",
    8: "Week 8: Comparative Agent Harnesses",
    9: "Week 9: Harness Integration and Debugging",
    10: "Week 10: MP3 Demos and the Spec-Driven Development Landscape",
    11: "Week 11: GitHub as the AI-SDLC Hub",
    12: "Week 12: Observability, Cost, and Security",
    13: "Week 13: Full-Cycle Capstone Work Session and MP4 Presentations",
    14: "Week 14: Final Project Work Session and Poster Development",
    15: "Week 15: Final Project Poster Presentations",
}

# path: relative to site root, where this page is written
# title: used for <title>, the hero <h1>, and (if applicable) the breadcrumb
# active: the nav label that gets class="active", or None (404.html has none)
# crumb: None (no breadcrumb div), "core" (Home » Title), or "week"
#        (Home » Schedule » Title)
PAGES = [
    {
        "path": "index.html", "title": "Home", "active": "Home", "crumb": None,
        "desc": "Course site for IPHS 400: Frontiers in AI, a hands-on Kenyon "
                "College course in AI software engineering and agentic coding harnesses.",
    },
    {
        "path": "404.html", "title": "404 – Not Found", "active": None, "crumb": None,
        "desc": "Page not found — IPHS 400: Frontiers in AI course site.",
    },
    {
        "path": "core/syllabus.html", "title": "Syllabus", "active": "Syllabus", "crumb": "core",
        "desc": "Full syllabus for IPHS 400: Frontiers in AI, including course "
                "description, learning outcomes, readings, and grading policies.",
    },
    {
        "path": "core/schedule.html", "title": "Schedule", "active": "Schedule", "crumb": "core",
        "desc": "Week-by-week schedule for IPHS 400: Frontiers in AI, linking "
                "every session from Week 1 through Week 15.",
    },
    {
        "path": "core/assignments.html", "title": "Assignments", "active": "Assignments", "crumb": "core",
        "desc": "Assignment descriptions and grading weights for the four IPHS "
                "400 mini-projects and the Final Project.",
    },
    {
        "path": "core/policies.html", "title": "Policies", "active": "Policies", "crumb": "core",
        "desc": "Generative AI use policy, late-work, attendance, and other "
                "course policies for IPHS 400: Frontiers in AI.",
    },
    {
        "path": "core/about.html", "title": "About", "active": "About", "crumb": "core",
        "desc": "About IPHS 400: Frontiers in AI — instructor, course site, "
                "and course description.",
    },
]
for _n, _title in _WEEK_TITLES.items():
    PAGES.append({
        "path": f"weeks/week-{_n:02d}.html",
        "title": _title,
        "active": "Schedule",
        "crumb": "week",
        "desc": f"{_title} — IPHS 400: Frontiers in AI.",
    })

_INCLUDE_RE = re.compile(r"\{\{INCLUDE:([a-zA-Z0-9_-]+)\}\}")
_WEEK_LINK_RE = re.compile(r"\{\{WEEK_LINK:(\d{2})\}\}")


def _render_includes(text):
    def _sub(match):
        return (SHARED / f"{match.group(1)}.html").read_text(encoding="utf-8")

    prev = None
    while prev != text:
        prev = text
        text = _INCLUDE_RE.sub(_sub, text)
    return text


def _render_week_links(text):
    """Substitute {{WEEK_LINK:NN}} with an <a> to that week page, using
    _WEEK_TITLES as the single source of truth for its link text - so the
    schedule page can never disagree with the week page's own title."""
    def _sub(match):
        n = int(match.group(1))
        return f'<a href="../weeks/week-{n:02d}.html">{_WEEK_TITLES[n]}</a>'

    return _WEEK_LINK_RE.sub(_sub, text)


def _render_nav(rel, active):
    items = []
    for label, href in NAV_ITEMS:
        attrs = ' class="active" aria-current="page"' if label == active else ""
        items.append(f'<li><a href="{rel}{href}"{attrs}>{label}</a></li>')
    return "\n".join(items)


def _render_breadcrumb(page, rel):
    if page["crumb"] is None:
        return ""
    if page["crumb"] == "core":
        trail = f'<a href="{rel}index.html">Home</a> » <span>{page["title"]}</span>'
    else:  # "week"
        trail = (
            f'<a href="{rel}index.html">Home</a> » '
            f'<a href="{rel}core/schedule.html">Schedule</a> » '
            f'<span>{page["title"]}</span>'
        )
    return f'<div class="breadcrumbs">{trail}</div>\n'


def _render_page(page):
    if page["path"] == "404.html":
        # 404.html is never served relative to its own location (see
        # tests/test_404_page.py) - it must stay root-relative so it works
        # correctly on hosts that serve it in place of any nested bad path.
        rel = "/"
    else:
        depth = len(Path(page["path"]).parts) - 1
        rel = "../" * depth

    head = (PARTIALS / "head.html").read_text(encoding="utf-8")
    head = head.replace("{{REL}}", rel).replace("{{TITLE}}", page["title"])
    head = head.replace("{{DESCRIPTION}}", page["desc"])

    header = (PARTIALS / "header.html").read_text(encoding="utf-8")
    header = header.replace("{{REL}}", rel)
    header = header.replace("{{NAV}}", _render_nav(rel, page["active"]))

    footer = (PARTIALS / "footer.html").read_text(encoding="utf-8")

    content = (CONTENT / page["path"]).read_text(encoding="utf-8")
    content = _render_includes(content)
    content = _render_week_links(content)

    breadcrumb = _render_breadcrumb(page, rel)
    hero = f'<section class="hero"><h1>{page["title"]}</h1></section>'

    return f"""<!DOCTYPE html>

<html lang="en">
<head>
{head}
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
{header}

<main class="content-wrapper" id="main">
{hero}
{breadcrumb}<div class="page-content">
{content}
</div>
</main>
{footer}
</body>
</html>
"""


def build(output_root=SITE_ROOT):
    output_root = Path(output_root)
    for page in PAGES:
        out_path = output_root / page["path"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(_render_page(page), encoding="utf-8")
    return len(PAGES)


if __name__ == "__main__":
    count = build()
    print(f"Built {count} pages.")
