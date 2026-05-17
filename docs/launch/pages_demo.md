# GitHub Pages Demo

TradeArena publishes the API-free showcase as a static GitHub Pages demo:

```text
https://weich97.github.io/TradeArena/showcase.html
```

The Pages workflow lives in `.github/workflows/pages.yml`. On every push to
`main`, it:

1. installs the repository with `python -m pip install -e ".[dev]"`
2. runs `python scripts/run_showcase.py`
3. uploads `outputs/examples/` as the Pages artifact
4. deploys the artifact with GitHub Pages Actions

The deployed demo contains only generated HTML, SVG, GIF, CSV, and JSON
artifacts from the API-free showcase path. It does not include raw LLM caches,
paper sources, or local credentials.

Useful entry points:

- `showcase.html`: top-level demo portal
- `audit_report.html`: replayable audit report
- `crisis_snapshot_gallery.html`: diagnostic visual gallery
- `retail_planning_report.html`: planning sandbox report

If the URL does not resolve immediately after a push, check the `Pages Demo`
workflow run in GitHub Actions. First-time Pages deployments can take a few
minutes to become visible.
