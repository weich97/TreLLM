# 实验设计 02:记忆污染与杠杆放大 —— LLM 代理的可审计失败模式

> 状态:设计稿 v1(2026-06-10)。优先级:**高**(与 01 共享基础设施,可并行或接续)。
> 目标 venue:ICAIF 2026;备选 NeurIPS/ICLR safety & agents workshop、AAAI 2027。

## 1. 研究问题与假设

仓库已有两个独有的诊断指标(`技术白皮书 §1`,memory-aware strategy):
- `memory_pollution_ratio`:记忆窗口中缺失净值、被污染条目、被拒订单、风控违规的加权占比;
- `memory_driven_leverage_amplification`:记忆调整后目标敞口相对基础信号敞口的放大倍数。

**RQ1(剂量-反应)**:注入的记忆污染比例与代理风险行为(杠杆放大、换手、回撤)之间是否存在单调关系?

**RQ2(损失追逐)**:连续亏损记忆是否使 LLM 代理变得更激进(加仓/加杠杆),而非更保守?这是白皮书 §4.2 中 drawdown kill switch 针对的失败模式,但尚无系统测量。

**RQ3(防御有效性)**:指数衰减记忆(`memory_decay_rate`)与风控网关,各自能消解多少污染引起的行为偏移?(消融)

**RQ4(模型差异)**:不同 LLM 对相同污染的敏感度是否不同?是否存在"越大的模型越会被记忆带偏"或相反的模式?

**核心论点**:LLM 交易代理的记忆是一个未被审计的风险面;噪声记忆会系统性放大风险敞口,且该效应可被量化、可被风控层部分拦截。

## 2. 贡献声明

1. 首个对 LLM 交易代理记忆污染的受控剂量-反应研究;
2. 两个可复用的审计指标(pollution ratio / leverage amplification)的实证验证;
3. 记忆衰减 × 风控网关的防御消融,给出"哪层防御挡住了什么"的归因。

## 3. 实验设计

### 3.1 自变量

**A. 污染剂量(主操纵)**:在 memory journal 中注入受控比例的污染条目,p ∈ {0%, 10%, 25%, 50%, 75%}。
污染类型(分别注入,不混合,作为子条件):
- 虚假被拒订单记录(代理以为自己被拒了);
- 虚假风控违规记录;
- 缺失净值条目(信息缺失型);
- 损失序列注入(RQ2 专用:伪造连续 k 步亏损记忆,k ∈ {1, 3, 5})。

**B. 记忆衰减率**:`memory_decay_rate` ∈ {无衰减, 默认, 强衰减}(3 档)。

**C. 风控**:`MaxPositionRiskManager`(默认)vs `NoRiskManager`(消融)。

**D. 代理**:memory-aware 确定性策略(主实验,无 LLM 成本,可大规模跑)+ ≥3 个 LLM 代理(验证泛化,RQ4)。

### 3.2 因变量

- 主:`memory_driven_leverage_amplification`(逐步记录,取轨迹均值与 P95);
- 行为:目标权重的绝对变化、换手率、违规计数、kill switch 触发率;
- 结果:最大回撤、收益波动(注意:**结果指标只作辅助**,核心 claim 落在行为层,避免"污染让收益变差"这种依赖市场路径的弱结论);
- LLM 专属:决策 rationale 文本中风险词汇频率变化(轻量内容分析,可选)。

### 3.3 设计矩阵与规模

主实验(确定性 memory-aware 策略):
5 剂量 × 4 污染类型 × 3 衰减 × 2 风控 = 120 cell,每 cell 10 seeds = 1200 runs,全部本地零成本,单机数小时。

LLM 验证(选最敏感的 2 个污染类型 × 3 剂量 × 默认衰减 × 2 风控):
12 cell × 3 模型 × 5 seeds × 3 samples = 540 runs。预算估 $100–300。

### 3.4 统计方案

- 剂量-反应:逐 cell 配对(同 seed)对比 p=0 基线;趋势检验用斜率的置换检验(seed 内打乱剂量标签);
- 防御归因:双因子(衰减 × 风控)效应分解,报告配对 Cohen's d;
- RQ4 模型差异:模型 × 剂量交互项,seed 层 cluster bootstrap;
- 全部 p 值 BH-FDR 校正(依赖 00 号文档 P0 修复)。

## 4. 需要补的基础设施

| 项 | 工作量 | 说明 |
| --- | --- | --- |
| ✅ 污染注入器(2026-06-10 完成) | — | 实现为**读取时**污染:`PollutedResearchMemory`(`memory/pollution.py`)包装基础 store,`recent()` 返回时按剂量替换事件并打 `injected=True`;journal 本身保持干净。**读路径分离**:策略走 `recent()` 看到污染视图,风控网关读裸 `memory.events` 保持接地——"代理被骗、风控清醒"的实验设计天然成立 |
| ✅ 剂量扫描脚本(2026-06-10 完成) | — | `scripts/run_memory_pollution_sweep.py`:剂量×类型×衰减×风控全矩阵,配对 vs 剂量0 + BH-FDR + 效应量,含操纵检查表(感知污染率 vs 注入剂量) |
| ✅ LLM 链路接入(2026-06-10 完成) | — | `llm.py` 风险反馈 helper 已切到 `recent("step", N)`(带旧 store 回退),读取时污染可直达 LLM prompt,集成测试已固定该行为;只差直连 runner 即可跑 LLM 实验臂 |
| rationale 文本分析(可选) | 1 天 | 词频/简单分类即可 |

**先决检查(已完成,2026-06-10)**:
- `memory_pollution_ratio` / `memory_driven_leverage_amplification` 只在 `MemoryAwareSignalWeightedStrategy`(`agents/strategy.py:549`)中计算,写入 decision metadata,由 `metrics.py` 聚合——确定性主实验可直接用。
- **LLM 链路已经消费 memory**:`agents/llm.py` 的 `_recent_risk_feedback` / `_long_term_risk_memory` 把记忆事件注入 prompt,且已有 **placebo 和 contrarian 两种反馈消融模式**(`_placebo_recent_risk_feedback` / `_contrarian_recent_risk_feedback`)——这是现成的 prompt 级记忆操纵基础设施,RQ3 的消融可以直接复用。
- LLM 决策不经过 memory-aware overlay,因此 `leverage_amplification` 指标对 LLM 不自动计算。**解决方案**:LLM 的"放大"用配对反事实测量——同一市场路径跑两次(干净记忆 prompt vs 污染记忆 prompt),行为差即为污染效应。这比 overlay 指标更干净,且与本文档 §3.4 的配对统计方案天然契合。RQ4 增量成本从"+2 天补装"降为"无需补装,只需注入器写到 memory journal 即可流入 prompt"。

## 4.5 确定性主实验结果(2026-06-11,1140 runs,docs/results/memory_pollution/)

- **剂量-反应稳健成立**:主结局(杠杆放大系数)的 90 个配对比较中 72 个过 BH-FDR(q<0.05),效应量巨大(|d| 7–18);三种比例型污染均单调压低敞口(最大剂量下放大系数平均下移 ~0.24)。未显著的 18 个 = dose 0.1 的空剂量(lookback=5 时 round(0.1×5)=0,剂量分辨率为 1/lookback=0.2)+ loss_streak 平台段。
- **loss_streak 阶跃平台**:k=1/3/5 效应完全相同——确定性规则对亏损记忆是阶跃响应,一条伪造亏损即触发 risk-off,加长无增量。"规则型防御对渐变型攻击不分级"可作为发现写。
- **衰减防御无效(真发现)**:decay 0.6/0.85/1.0 下最大剂量效应几乎相同(0.2429–0.2440)。原因:污染均匀散布在召回窗口内,衰减加权后的污染比例≈剂量,与衰减率无关。**衰减只防时间局部化污染,防不了均匀污染**——论文中是防御消融的核心结论。
- **⚠️ 风控网关的"无效"是构造使然,不是发现**:放大系数记录在策略 decide 阶段(风控批准之前),网关按构造不可能影响该指标。RQ3 中网关的防御效果必须用**结局指标**(max_drawdown 等,58 个比较过 FDR)评估,写作时务必避免用主结局声称"网关无效",审稿人会抓。
- 结果方向(污染→降杠杆)是确定性规则的编码行为,作为 LLM 实验臂的校准基准;LLM 是否反向(追损加仓)是论文的真正问题。

## 5. 威胁与限制

- 注入的污染是合成的,真实污染(provider 幻觉、工具错误)分布未知——定位为"受控下界研究";
- 确定性 memory-aware 策略的反应是规则编码的,其剂量-反应曲线是机制验证而非发现;**论文的新颖性主张必须落在 LLM 部分**,确定性部分作为校准基准;
- 损失追逐结论依赖合成市场路径设计,需要在多种 regime(calm/high-vol)下重复。

## 5.5 LLM 实验臂启动清单(2026-06-12 状态:等预算)

基础设施全就绪,差的只有 provider 预算:
- 注入器、剂量扫描、LLM prompt 链路(`recent()` 已接通)全部在 main;
- 设计:2 个最敏感污染类型(确定性结果指向 fake_violations 与 fake_rejections)× 3 剂量 × 2 风控 × 3-5 模型 × 5 seeds × 3 samples ≈ **5-8k 次调用**;
- 配对反事实测量(同 seed 干净 vs 污染 prompt)直接复用 `--samples-per-seed` 与 checkpoint 机制;
- 启动条件:Poe 充值(多模型方便)或改用直连 key;deepseek 可先单模型 pilot(~1.5k 次调用,便宜)验证效应方向。

## 6. 时间线

与 01 共享统计修复与 API runner。独立增量约 3-4 周:
W1 注入器 + 主实验矩阵;W2 LLM 验证;W3 分析与写作;W4 内审。
若与 01 二选一投 ICAIF:01 数据更现成、风险更低;02 故事更新颖、审稿人记忆点更强。**若人力允许,01 投 ICAIF 主会,02 投 同期 workshop 或 AAAI。**

## 7. 失败保底

若剂量-反应平坦(LLM 对记忆污染不敏感):转写"LLM 交易代理对记忆噪声的鲁棒性"+ 防御层冗余分析,与 kill switch 触发数据合并,仍是一篇可发的 negative-result/audit 论文(ICAIF 接受这类工程证据)。
