"""css/style.css must not contain rules for classes that no page actually
uses. The site has no JS, so every class referenced by a CSS selector should
appear as a literal class="..." token somewhere in the committed HTML - any
selector that doesn't is dead weight left over from template/theme reuse.
"""
import re
from pathlib import Path

SITE_ROOT = Path(__file__).parent.parent
CSS_FILE = SITE_ROOT / "css" / "style.css"

# Classes intentionally kept even though no page currently uses them
# (e.g. reserved for a documented future feature). Add an entry here with a
# comment explaining why, rather than letting an unused selector go unnoticed.
ALLOWED_UNUSED_CLASSES = set()

_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_CLASS_SELECTOR_RE = re.compile(r"\.(-?[A-Za-z_][A-Za-z0-9_-]*)")


def _css_class_selectors(css_text):
    css_text = _COMMENT_RE.sub("", css_text)
    classes = set()
    for block in css_text.split("{"):
        selector_part = block.rsplit("}", 1)[-1]
        classes.update(_CLASS_SELECTOR_RE.findall(selector_part))
    return classes


class TestNoDeadCSSClasses:
    def test_every_css_class_selector_is_used_by_some_page(self, parsed_pages):
        css_classes = _css_class_selectors(CSS_FILE.read_text(encoding="utf-8"))

        used_classes = set()
        for _, _, soup in parsed_pages:
            for tag in soup.find_all(class_=True):
                used_classes.update(tag.get("class", []))

        dead = sorted(css_classes - used_classes - ALLOWED_UNUSED_CLASSES)
        assert not dead, (
            f"css/style.css styles classes no page uses: {dead}. "
            f"Remove the dead rule, or add the class to ALLOWED_UNUSED_CLASSES "
            f"with a comment explaining why it's intentionally kept."
        )
