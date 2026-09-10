"""tests/requirements.txt should pin exact versions (==), not open-ended
lower bounds (>=), so a clean install is reproducible and doesn't silently
pick up a future breaking major-version bump.
"""
from pathlib import Path

REQUIREMENTS = Path(__file__).parent / "requirements.txt"


class TestRequirementsArePinned:
    def test_every_requirement_uses_exact_pin(self):
        lines = [
            line.strip() for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        assert lines, "tests/requirements.txt has no requirement lines"
        failures = [line for line in lines if "==" not in line]
        assert not failures, f"Requirements not pinned with '==': {failures}"
