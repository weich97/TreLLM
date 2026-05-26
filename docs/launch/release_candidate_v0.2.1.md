# v0.2.1 Release Candidate Manifest

This is a local release-candidate manifest. Tagging and PyPI publication are separate maintainer actions and require CI plus trusted-publishing credentials.

## Candidate State

- Target release: `v0.2.1`
- Current package version: `0.2.0`
- Commit: `88ce4e4f389ce77d784975b2e65fc6b4135d23ae`
- Working tree dirty entries when generated: `30`

## Pre-Release Commands

- `python -m compileall src scripts examples tests -q`
- `python -m ruff check src scripts examples tests`
- `python -m mypy`
- `python -m pytest tests -q`
- `python scripts/check_release_readiness.py`
- `python scripts/scan_public_artifacts.py outputs docs/results examples/benchmark_submissions`

## Artifact Hashes

- `README.md`: present sha256:8eeb44866edb1931f8f2b6bc605bd312ccae35a95ddcd00ef5166d2687a858d3
- `pyproject.toml`: present sha256:9fa232384a804156243d65eadb8347ce164f0da31d0b7db3a5d09b8ab1f5f5c4
- `benchmarks/v0.2/spec.json`: present sha256:8e688190ff17bc0fca691bcd600bc56bb13d1215d2b5d6a8ac611ae70e17b156
- `docs/results/benchmark_v0_2.md`: present sha256:0b4b63ed7353009964adf6c3093093f5f7144b8ae11b85d651238221a6221ab8
- `docs/results/execution_replay_calibration_loop.json`: present sha256:f813ec35bf31c5d62cb8adef9385d1e9eba0a52bc352728d1e571b55baf477e2
- `docs/results/execution_calibration_stability.json`: present sha256:bfd6b635f2bb517912a0b6547e77fda7db562b71a33c4f59a1786d55e4681951
- `docs/results/market_rules_fixture.json`: present sha256:1ee31e7de199849a7868d6ba90b3e74c3a6364279e0868f0a57023ba4a3dff06
- `docs/results/external_validation_bundle.md`: present sha256:736789f490b19cb67f1d17070b3a51cb25a936e14db18a8d81c7d55e9cf667ca
- `docs/results/poe_skill_task_matrix.md`: present sha256:af72aa4f11204b5ded802ffa4491aa6713907f55190c1bbb982fe7dc4655f741
- `docs/results/skill_task_matrix.md`: present sha256:e4259cf0845c778a2efb8aae4d7d8732584ee972530bfab9d00566fcca01b54a
- `docs/results/community_registry.md`: present sha256:130bd0974cdc2d7094c3bacd5a46445f882983087b9fb3010809a077151f9c4e
- `docs/public_artifact_privacy.md`: present sha256:1a52c3f5c6666655d7b60a4d9ee2ab3de0e190c545835ec2a6a8d4e1a370e86a
- `docs/launch/release_notes_v0.2.1.md`: present sha256:a0f54d789fa8e6959873112e8c5f129a521f31d4ed30c1cd9587a00cdc90115c

## Release Notes Draft

- Public artifact redaction is now enforced by default for trajectory JSON and public result scans.
- Provider audit matrix results compare frontier models as financial-audit agents rather than stock pickers.
- Execution evidence now includes a replay loop across OHLCV stress, quote replay, and fill replay.
- External validation bundle generation turns reproduction manifests into issue-ready reports.
- OpenTelemetry-style local trace export maps trajectories into portable audit spans.
