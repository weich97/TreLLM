# v0.2.1 Release Candidate Manifest

This is a local release-candidate manifest. Tagging and PyPI publication are separate maintainer actions and require CI plus trusted-publishing credentials.

## Candidate State

- Target release: `v0.2.1`
- Current package version: `0.2.0`
- Commit: `2dbe871b1b71d12f5ae040c8d34509f52b076610`
- Working tree dirty entries when generated: `4`

## Pre-Release Commands

- `python -m compileall src scripts examples tests -q`
- `python -m ruff check src scripts examples tests`
- `python -m mypy`
- `python -m pytest tests -q`
- `python scripts/check_release_readiness.py`
- `python scripts/scan_public_artifacts.py outputs docs/results examples/benchmark_submissions`

## Artifact Hashes

- `README.md`: present sha256:16eb7a232b1ef35cbb10c2699b0d08226379e0dde76b9630c44496f728d6e4d8
- `pyproject.toml`: present sha256:731c9d6a87972559da33f90571255fe2b0a156c3780b2f9ff01f14dd21bd7ae5
- `benchmarks/v0.2/spec.json`: present sha256:a8cde14d8da398642074c4f4910cda297a60a11636217359e589d43b312922e4
- `docs/results/benchmark_v0_2.md`: present sha256:19d848c2406adb536546f73b48175cab076b5c9b002ee40919e0ad9657a03cd2
- `docs/results/execution_replay_calibration_loop.json`: present sha256:f813ec35bf31c5d62cb8adef9385d1e9eba0a52bc352728d1e571b55baf477e2
- `docs/results/execution_calibration_stability.json`: present sha256:bfd6b635f2bb517912a0b6547e77fda7db562b71a33c4f59a1786d55e4681951
- `docs/results/market_rules_fixture.json`: present sha256:1ee31e7de199849a7868d6ba90b3e74c3a6364279e0868f0a57023ba4a3dff06
- `docs/results/external_validation_bundle.md`: present sha256:736789f490b19cb67f1d17070b3a51cb25a936e14db18a8d81c7d55e9cf667ca
- `docs/results/poe_skill_task_matrix.md`: present sha256:76ac29751e75d3c68f1325b750c608ba447ab3a2ed0c5a97ae0d64071e95a3d7
- `docs/results/poe_skill_challenge_matrix.md`: present sha256:e788429807baa5323df70613646794dd37e4f552a3e24a65900e62039ef3afec
- `docs/results/poe_skill_challenge_followup_matrix.md`: present sha256:ffd81bc9b63553d0b88a69ce83b81e35ef7fab1f308346faa7b6039e4bc1283a
- `docs/results/poe_skill_challenge_followup_claude_adversarial.md`: present sha256:445d87adb7647fd19920dc7c2d926d456c3fbff60ec93792d8257f4e6f97201a
- `docs/results/skill_task_matrix.md`: present sha256:c936b965c9a18a0ec43850802a7dd8bfffd3401925011d0dcb16c7b33a31f843
- `docs/results/community_registry.md`: present sha256:ef7f353b1d5c0613e00d32fb78582ac0acb28e6f197e802fc03126307cfd4899
- `docs/public_artifact_privacy.md`: present sha256:6a58cc596a96b9262cf413deed8fd158f1583010b9cd61b1fff340d82b2b4a9b
- `docs/launch/release_notes_v0.2.1.md`: present sha256:e5b02df674adf1a8a35b284d674e0df10fa48082a68abb39b41bb354976d6375

## Release Notes Draft

- Public artifact redaction is now enforced by default for trajectory JSON and public result scans.
- Provider audit matrix results compare frontier models as financial-audit agents rather than stock pickers.
- Execution evidence now includes a replay loop across OHLCV stress, quote replay, and fill replay.
- External validation bundle generation turns reproduction manifests into issue-ready reports.
- OpenTelemetry-style local trace export maps trajectories into portable audit spans.
