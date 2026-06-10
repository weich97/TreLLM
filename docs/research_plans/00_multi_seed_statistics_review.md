# 多 Seed 统计框架现状复盘

> 复盘日期:2026-06-10(基于 commit `f8505c8`)。
> 目的:为后续所有论文方向(01–05)确认统计基础设施的现状、亮点与缺口。

## 一、已有能力盘点

### 1. 核心统计库 `src/tradearena/evaluation/statistics.py`

纯 Python 实现,无 numpy/scipy 依赖,全部随机过程带固定 seed(可复现):

| 函数 | 功能 | 备注 |
| --- | --- | --- |
| `mean` / `sample_std` | 均值、样本标准差(n-1) | 空集返回 0.0 |
| `bootstrap_ci` | percentile bootstrap 置信区间 | 默认 2000 draws,95%,seed=1729 |
| `summarize_metric` | mean/std/CI 打包 | 输出 `{prefix}_mean/std/ci_low/ci_high` |
| `paired_bootstrap_difference` | 配对差值的 bootstrap CI + 双侧 bootstrap p 值 + sign-flip permutation p 值 | n≤16 时 permutation 精确枚举全部 2^n 符号翻转 |
| `paired_permutation_p_value` | 双侧配对符号翻转置换检验 | 同上 |

### 2. 消费链路

**合成场景模型矩阵 `scripts/run_leaderboard_model_matrix.py`**
- 默认 `DEFAULT_SEEDS = (7, 11, 17, 23, 31)`,共 5 个 seed;每个场景叠加独立 `seed_offset`(0/10/22/34/46/58),保证场景间市场路径不重叠。
- 每个 model×scenario 聚合 `summarize_metric`(return、sharpe),并对 buy-and-hold 与 random 基线做 `paired_bootstrap_difference`(输出 `bootstrap_p_value_vs_hold` / `_vs_random`)。

**真实市场矩阵 `scripts/run_real_market_leaderboard.py`**
- seed 被映射为滚动窗口偏移(`repeat_unit = "seed_mapped_to_window_offset"`),即重复单元是**时间窗口**而非市场随机性——这是正确的设计,真实数据没有"另一个随机宇宙"。
- artifact 里写入了 `statistical_tests` 与 `repeat_unit` 的 provenance 字段,审稿人可见。

**论文实验管线 `src/tradearena/experiments/paper.py`**
- 主实验 seeds 默认 `(3, 7, 11)`;CLI 通过 `--paper-seeds` 覆盖。
- 30-seed 统计稳健性表(`statistical_seeds = range(1, 31)`,CLI `--statistical-seeds`,可用 `--no-statistical` 跳过):覆盖 5 个 case(risk_aware_realistic / buy_and_hold_realistic / ideal_execution_ablation / no_risk_ablation / stress_latency),逐 metric 输出均值、95% CI,并对 buy-and-hold 基线做配对差值 CI。

## 二、亮点(论文里可以直接当卖点写)

1. **配对设计贯穿始终**:同 seed 下比较 candidate vs baseline,消除市场路径方差,这比绝大多数 LLM trading 论文的"各跑各的然后比均值"严谨。
2. **置换检验有精确模式**:n≤16 时枚举全部符号翻转,小样本下 p 值不依赖渐近近似。
3. **统计 provenance 进 artifact**:`repeat_unit`、`statistical_tests` 字段随结果落盘,可审计。
4. **零依赖、确定性**:CI 环境可复现,bootstrap 本身带 seed。

## 三、缺口(按修复优先级排序)

### P0:LLM 行的方差来源未分解
当前 LLM 模型行的重复单元是**市场 seed**:每个 seed 一次 LLM 调用(经缓存)。这把两种方差混在一起:
- 市场路径方差(seed 变了,行情不同);
- 模型随机性方差(同一行情下,provider 采样温度、路由抖动)。

论文审稿人一定会问"你的 CI 到底覆盖哪种不确定性"。**修复**:增加固定 seed 下的 repeated-sampling 维度(同一市场路径调 provider k 次,k≥3),输出双因子方差分解(seed 间 vs seed 内)。需要给缓存 key 加 `sample_index` 维度。

### P0:多重比较未校正
模型矩阵规模为 |models| × |scenarios| × 2 个基线检验,p 值数量轻松上百,无 FDR/Bonferroni 校正。**修复**:在 `statistics.py` 增加 Benjamini–Hochberg 校正函数(约 20 行纯 Python),矩阵脚本输出 `q_value` 列;论文里报告 FDR 校正后的显著性。

### P1:5-seed 的 percentile bootstrap CI 偏窄
n=5 时 percentile bootstrap 的覆盖率显著低于名义 95%。30-seed 表目前只覆盖确定性策略(成本原因 LLM 不跑 30 遍,合理)。**修复**:
- LLM 行至少升到 10 seeds(成本可控:有缓存,增量只是新 seed 的调用);
- 或者在 n<10 时报告精确置换 p 值 + 全部原始点(已支持精确枚举),弱化 bootstrap CI;
- 可选:实现 BCa bootstrap(修偏置和加速),约 60 行。

### P1:没有标准化效应量
只有原始差值,没有 Cohen's d / Cliff's delta。跨场景、跨指标比较"风险反馈的影响有多大"需要无量纲效应量。**修复**:`statistics.py` 加 `cohens_d(paired)` 与 `cliffs_delta`,矩阵和 paper 表各加一列。

### P2:没有功效分析指引
"需要多少 seed 才够"目前靠拍脑袋。**修复**:写一个基于已有 30-seed 确定性数据的 bootstrap 功效曲线脚本(给定效应量,n=5/10/20/30 时的检出率),作为论文附录,也指导 LLM 实验的预算分配。

### P2:跨场景聚合缺层级结构
当前各场景独立检验。如果论文要下"模型 X 总体上不如经典基线"的结论,应把 scenario 当随机效应做层级/混合模型,或至少报告跨场景的 meta 分析(逐场景效应量 + 随机效应合并)。纯 Python 可实现简化版(DerSimonian–Laird)。

### P3:工程细节
- `bootstrap_ci` 的分位数索引用 int 截断,边界处略保守,可改为线性插值;
- 统计摘要尚未自动渲染进 benchmark card 页(`build_benchmark_page.py` 是否消费 `*_ci_*` 列需要确认)。

## 四、给各论文方向的统计基线要求

| 方向 | 最低统计要求 |
| --- | --- |
| 01 执行敏感性 | 确定性策略 30 seeds;LLM 10 seeds × 3 samples;排名稳定性用 Kendall's tau + bootstrap CI |
| 02 记忆污染 | 污染剂量-反应曲线,每剂量 ≥10 seeds;趋势检验(Jonckheere 或回归斜率置换) |
| 03 benchmark 论文 | 上述 P0/P1 全部修复;FDR 校正;方差分解表进正文 |
| 04 审计 agent | 分类指标(precision/recall)+ Wilson 区间;模型间 McNemar 检验 |
| 05 系统论文 | 不依赖统计推断,延迟/吞吐报告分位数即可 |

## 五、建议动手顺序

1. ✅ `statistics.py` 加 BH-FDR、配对 Cohen's d、Cliff's delta(2026-06-10 完成,含单测;另加了 `variance_components` 方差分解)。
2. ✅ 缓存 key 支持 `sample_index`(=0 保持旧 key 格式兼容现有缓存),`run_leaderboard_model_matrix.py` 加 `--samples-per-seed`,baseline 行不重复;聚合配对前先在 (scenario, seed) 内对 samples 取均值;`samples>1` 时输出 `*_variance_decomposition.csv`(seed 间 vs seed 内方差)。**真实市场脚本的 samples 支持尚未做**(其重复单元是时间窗口,优先级低)。
3. ✅ 功效曲线脚本 `scripts/run_power_analysis.py`(合成效应量模式 + 从 metrics CSV 的经验模式),输出 CSV/Markdown。
4. ✅ 两个矩阵脚本聚合表均输出 `q_value_*`、`cohens_d_*`、`cliffs_delta_*` 列;`statistical_tests` provenance 已更新。benchmark card 页对新列的渲染仍未接(P3 保留)。

## 六、功效分析的硬发现(2026-06-10)

**n=5 时精确符号翻转置换检验在 α=0.05 下功效恒为 0**:5 对样本只有 2^5=32 种符号组合,双侧最小 p 值 = 2/32 = 0.0625 > 0.05,无论效应多大都不可能显著。最小可显著的重复数是 **n=6**(p_min = 2/64 ≈ 0.031)。

合成功效曲线(α=0.05,400 draws):

| Cohen's d | n=10 | n=20 | n=30 |
| ---: | ---: | ---: | ---: |
| 0.5 | ~0.27 | ~0.67 | ~0.82 |
| 0.8 | ~0.59 | ~0.92 | ~0.99 |
| 1.2 | ~0.93 | ~0.99 | ~1.00 |

含义:
- 当前 `DEFAULT_SEEDS = (7, 11, 17, 23, 31)`(5 个)在置换检验路径下**结构性无法出显著结果**——改默认值需要重跑已发布矩阵行(有成本),建议在 01 号实验启动时一并升级到 ≥10 seeds,并在 benchmark 协议 v0.3 中写死;
- 想检出中等效应(d≈0.5)且功效 ≥0.8,需要 **~30 seeds**;d≈0.8 需要 **~20 seeds**;
- 该结论已固化为测试 `tests/test_power_analysis.py::test_five_pairs_cannot_reject_at_alpha_005`。

这五步完成后,01–03 三个方向的统计地基已齐;剩余缺口为 P2 的跨场景层级聚合与 P3 的 benchmark card 渲染。
