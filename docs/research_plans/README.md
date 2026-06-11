# 研究规划文档索引

> 创建于 2026-06-10,基于 commit `f8505c8` 的仓库状态。内部规划文档(中文);若某方向进入公开协作阶段,再翻译为英文并入正式 docs。

## 文档清单

| 编号 | 文档 | 主题 | 优先级 | 目标 venue |
| --- | --- | --- | --- | --- |
| 00 | [多 seed 统计框架复盘](00_multi_seed_statistics_review.md) | 统计基础设施现状、缺口与修复顺序 | **✅ 主体已完成(2026-06-10)** | — |
| 01 | [执行假设敏感性](01_execution_sensitivity.md) | 排行榜在执行摩擦下的脆弱性 | **最高** | ICAIF 2026(7 月) |
| 02 | [记忆污染与杠杆放大](02_memory_pollution.md) | LLM 代理记忆失败模式的剂量-反应研究 | 高 | ICAIF / safety workshop |
| 03 | [TradeArena benchmark 论文](03_tradearena_benchmark_paper.md) | 正式 benchmark 论文(去 Poe 化、污染控制、外部验证) | 中期主线 | ICLR 2027(9 月) |
| 04 | [FinAudit 审计代理评测](04_financial_audit_agent_benchmark.md) | LLM 作为轨迹审计员(含自偏袒实验) | 中 | FinNLP / ICAIF workshop |
| 05 | [人工门控控制面](05_live_readiness_control_plane.md) | live-readiness 链路的系统论文 | 远期 | ICAIF 2027 industry |

## 依赖关系

```text
00 统计修复 ──┬─→ 01 执行敏感性 ──┐
              ├─→ 02 记忆污染   ──┼─→ 03 benchmark 论文(复用 01/02 结果作证据章节)
              │                  │
直连 API runner ─────────────────┘
                                      04 审计评测 ←─ 03 的轨迹(自我审计实验)
                                      05 控制面  ←─ 04 的自偏袒结论(叙事闭环)
```

## 总时间线(2026)

| 时段 | 里程碑 |
| --- | --- |
| 6 月中下旬 | ✅ 00 号 P0/P1/P2 修复(FDR、效应量、samples-per-seed、功效曲线、随机效应 meta 分析);✅ 01 确定性扫描(排名稳定性随市场压力下降,jump_tail E0→E1 tau=0.33);✅ 02 注入器+确定性主实验;✅ 03 的 C1 符号匿名化、C2 前向冻结、intent-execution gap 指标;✅ 04 缺陷注入器+出题判分。**待 API key:直连 runner、01/02 的 LLM 实验臂、03 污染探针、04 调模型环节** |
| 7 月中 | **ICAIF 2026 提交(01,02 视进度投 workshop)** |
| 7-8 月 | 03 的外部验证邀请、全矩阵;04 全量出题 |
| 9 月 | **ICLR 2027 提交(03)** |
| Q4 | 04 全量实验;05 端到端连续运行启动 |

## 共同原则

- 所有 claim 措辞对照 [claim_boundaries](../claim_boundaries.md) 的三级 claim ladder 自查;
- 所有 LLM 结果:锁定模型版本、redacted manifest、≥10 seeds、provider 采样重复、FDR 校正;
- 负结果有保底出口(各文档第"失败保底"节);
- 不为 05 牺牲 01-03 进度。
