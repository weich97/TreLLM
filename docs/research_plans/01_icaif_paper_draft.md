# ICAIF 2026 投稿草稿骨架(01 号:执行假设敏感性)

> 状态:骨架 v1(2026-06-11)。结果占位符待 LLM 全量矩阵落地后填入。
> 目标:ICAIF 2026 主会(ACM 模板,8-9 页);语言:英文。本文件是结构与文案底稿,定稿转 LaTeX。

## Title(候选)

1. *Execution Assumptions Reorder LLM Trading-Agent Leaderboards*
2. *The Fragile Leaderboard: How Execution Frictions Change Conclusions About LLM Trading Agents*
3. *From Ideal Fills to Stressed Markets: Execution Sensitivity of LLM Trading-Agent Evaluation*

推荐 2(有记忆点)或 1(最直白)。

## Abstract(模板,~180 词)

> Most evaluations of LLM trading agents assume idealized execution: orders fill
> completely at the close price. We study how conclusions change when this
> assumption is relaxed along a documented execution-assumption ladder - ideal
> fills, a default stress simulator (latency, participation caps, spread,
> impact), single-axis stress levels, and a harsh corner. Across [N_scenarios]
> synthetic market regimes, [N_models] provider-routed LLM agents and seven
> classical baselines run in identical (scenario, level, seed) cells.
> We find: (1) ranking stability degrades as market stress rises - Kendall
> tau between ideal and stressed leaderboards falls from [tau_calm] in calm
> regimes to [tau_jump] under jump-tail risk, reordering even deterministic
> baselines; (2) [LLM fragility headline: LLM agents lose [X] more return to
> frictions than a buy-and-hold anchor on the same market paths (paired DiD,
> q<0.05) / or the symmetric negative result]; (3) [mechanism: the loss
> concentrates in (partial fills | latency | spread-crossing), predicted by
> turnover and participation]. Evaluations that omit execution assumptions
> can invert agent rankings; we release the full protocol, trajectories, and
> statistics for replication.

## 1. Introduction

要点(每点一段):
1. LLM trading agent 论文激增,但评测几乎都隐含"收盘价全额成交"——该假设从未被系统检验。
2. 执行摩擦不是误差项而是排序变量:我们用四档执行假设阶梯证明排行榜会重排。
3. 贡献清单:
   - 首个系统量化执行假设对 LLM 交易代理**排名**(非仅收益)影响的受控研究;
   - 执行假设阶梯 + 排名稳定性协议(Kendall tau-b、top-k Jaccard、摩擦脆弱性 DiD);
   - [N_models] 个 LLM 代理与 7 个经典基线在同 cell 下的全量对比,全部轨迹可回放、统计带 FDR 校正;
   - 开源协议与产物。
4. 主发现预告(填结果)。

## 2. Related Work

- LLM trading agents(TradingAgents、FinRobot、FinGPT 系——指出其评测的执行假设);
- 回测偏差与执行建模文献(Kyle 1985;Almgren-Chriss 2001;Bouchaud et al. 2009——本文阶梯的理论锚);
- agent benchmark 的脆弱性/可复现性研究(benchmark fragility 一线);
- 与 TreLLM/TradeArena 技术报告(arXiv:2605.28850)的关系:该报告给系统,本文给科学问题。

## 3. Execution-Assumption Ladder(方法核心)

- E0 ideal:close 价全额成交 + 固定滑点(文献默认);
- E1 default stress:latency 1 bar、participation 5%、线性 impact 0.15、部分成交与拒单;
- E2 单轴:spread 20bps / latency 3 / participation 1%(各自隔离一个摩擦轴);
- E2 harsh corner:三轴同压 + impact 0.3。
- 方程与默认参数表(从 technical_report.md §2 转写);明确声明:stress 假设而非校准成本预测(claim boundary)。

## 4. Experimental Setup

- 代理:7 个确定性基线(buy-and-hold、signal-weighted、momentum、mean-reversion、risk-parity、min-variance、random 对照)+ [N_models] 个 provider-routed LLM(gpt-5.5、gemini-3.1-pro、claude-opus-4.7、glm-5 via Poe;**limitation 节声明 provider routing**);
- 场景:calm / high-vol / jump-tail 合成 regime(LLM 无法记忆合成路径——天然污染控制);
- 重复:确定性 10 seeds(120 periods);LLM 10 seeds(12 决策步,每步一次调用);同 seed = 同市场路径,跨档位与跨代理可配对;
- 风控:统一 MaxPosition 预算(意图与执行的分离记录);
- 统计:配对符号翻转置换检验(n≤16 精确)、BH-FDR、配对 Cohen's d;排名稳定性 Kendall tau-b + top-3 Jaccard;脆弱性 DiD 定义(公式);
- 附录引用功效曲线(n=5 结构性无功效 → 本研究用 10 seeds 的依据)。

## 5. Results(占位)

- 5.1 排名稳定性:tau 矩阵热图(确定性部分已有:calm 0.81 / high_vol 0.52-0.90 / jump_tail 0.33);LLM 加入后的对应表 [TBD];
- 5.2 摩擦脆弱性 DiD 主表:每 LLM × {E1, harsh} vs buy-and-hold 锚,mean DiD、CI、q、d [TBD];
- 5.3 机制:fill rate、滑点成本、换手的档位梯度;回归(排名变动 ~ 换手 + 参与率)[TBD];
- 5.4 理想化偏差量化:E0 相对 E1/harsh 高估的收益 bps,按代理类型分组 [TBD]。

## 6. Limitations

- Poe 路由:模型版本不可锁定,LLM 行是"provider-routed policy"而非模型本体能力——明确措辞;
- 合成市场:微观结构与真实市场不同,结论限定为"受控合成 regime 内";
- 12 决策步的 LLM 轨迹较短(成本约束);samples-per-seed 扩展为后续工作 [若 samples=3 来得及则删除此条];
- E3(报价回放/校准档)只有 crypto 公开数据,未进入主矩阵。

## 7. Reproducibility

- 命令清单:sweep → analyze 两条命令;commit hash;redacted manifests;seeds;CI。

## 投稿核对清单

- [x] CFP 已确认(2026-06-11 查证):**截稿 2026-08-02**,ACM 双栏 ≤8 页含图表参考文献,双盲,CMT 提交(cmt3.research.microsoft.com/ICAIF2026);会议 2026-11-14/17 米兰
- [ ] ACM 模板 LaTeX 工程
- [ ] 结果填入 + 图表(tau 热图、DiD 森林图、机制梯度图)
- [ ] claim boundary 自查(对照 docs/claim_boundaries.md)
- [ ] 匿名要求确认(ICAIF 双盲;仓库链接需匿名化处理)
- [ ] LLM usage 披露声明
