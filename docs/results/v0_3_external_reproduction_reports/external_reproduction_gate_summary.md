# TreLLM v0.3 External Reproduction Gate

This artifact tracks whether independent reproduction reports satisfy the v0.3 ICLR protocol.
It is intentionally conservative: project-maintainer reports, failed command logs, private-data runs, and missing environment labels do not count as independent evidence.

- Protocol: `trellm-v0.3-iclr-protocol`
- Reports scanned: `0`
- Accepted reports: `0 / 3`
- Covered environment classes: `0 / 3`
- External reproduction ready: `False`
- Blocking reasons: `insufficient_independent_report_count;missing_required_environment_class`
- Claim boundary: This gate validates external reproduction reports against the v0.3 protocol. It does not count project-maintainer, failed, private-data, or wrong-environment reports as independent evidence.
- Open-gap policy: The external_reproduction_reports gap remains open until three independent accepted reports cover windows_or_macos, linux, and colab_or_binder.

## Environment Coverage

| Environment class | Accepted reports | Status |
| --- | ---: | --- |
| windows_or_macos | 0 | missing |
| linux | 0 | missing |
| colab_or_binder | 0 | missing |

## Report Requirements

A report counts only when it is schema-valid, uses `protocol_id=trellm-v0.3-iclr-protocol`, marks `report_author_type=independent`, sets `independent_reviewer=true`, records one required environment class, and contains no failed required commands or missing artifacts.
