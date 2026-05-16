from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_local_images_exist_and_stay_lightweight():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    paths = set(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", readme))
    paths.update(re.findall(r'<img[^>]+src="([^"]+)"', readme))

    local_paths = sorted(
        path
        for path in paths
        if not path.startswith(("http://", "https://", "#"))
        and not path.startswith("data:")
    )

    assert local_paths
    for relative in local_paths:
        target = ROOT / relative
        assert target.exists(), f"README image is missing: {relative}"
        assert target.stat().st_size > 0, f"README image is empty: {relative}"
        if target.suffix.lower() == ".gif":
            assert target.stat().st_size < 1_500_000, f"README GIF is too large: {relative}"
