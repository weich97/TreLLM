# 实验设计 01:执行假设敏感性 —— LLM 交易代理排行榜的脆弱性

> 状态:设计稿 v1(2026-06-10)。优先级:**最高**(近期投稿主力)。
> 目标venue:ICAIF 2026(主选,截稿通常 7 月中);备选 ICLR 2027 / FinLLM workshop。

## 1. 研究问题与假设

**RQ1**:同一组交易代理(LLM 与经典基线)的排名,在不同执行假设下(理想成交 → 压力摩擦 → 校准参数 → 报价回放)会翻转多少?

**RQ2**:哪类代理对执行摩擦最敏感?假设:高换手、高集中度的 LLM 策略在摩擦加大时排名下降最快;buy-and-hold 类几乎不变。

**RQ3**:现有 LLM trading 论文普遍使用的"收盘价全额成交"假设,会高估 LLM 代理收益多少个 bps?给出系统性的偏差区间。

**核心论点(一句话)**:在理想执行下得出的 LLM 交易代理优劣结论,在现实摩擦下不可迁移;评测必须声明执行假设,否则排行榜没有外部效度。

## 2. 贡献声明(投稿用)

1. 首个系统量化执行假设对 LLM 交易代理**排名**(而非仅收益)影响的研究;
2. 一个四档执行假设阶梯(ideal / stress / calibrated / quote-replay)+ 排名稳定性度量协议;
3. 公开可复现的全部轨迹、配对统计与排名翻转分析。

## 3. 实验设计

### 3.1 自变量:执行假设(4 档阶梯)

| 档位 | 模拟器 | 仓库现状 |
| --- | --- | --- |
| E0 理想 | `SimpleOrderSimulator`(收盘价+固定滑点) | ✅ 已有 |
| E1 压力 | `RealisticOrderSimulator` 默认参数(latency=1, participation=5%, impact=0.15) | ✅ 已有,当前 benchmark 默认 |
| E2 压力扫描 | E1 参数网格:spread∈{0,5,20}bps × latency∈{0,1,3} × participation∈{1%,5%,10%} | ✅ 参数可配,需写扫描脚本 |
| E3 校准/回放 | `CalibratedOrderSimulator`(Binance 校准 profile)+ `QuoteReplayOrderSimulator` | ✅ 类已有;公开数据只覆盖 crypto,需扩 |

### 3.2 被试:代理集合(固定,所有档位同一组)

- 经典基线(确定性):buy-and-hold、风险平价、最小方差、均值回归、动量、随机配置(对照)。全部已在 `factory.py` / `agents/strategy.py` 中。
- LLM 代理:≥4 个模型(建议直连 API:Claude、GPT、Gemini、DeepSeek 各一档旗舰 + 一档轻量),复用现有 cache-backed analyst 链路。**注意:不要再走 Poe 路由**(见 03 号文档的去 Poe 化要求)。

### 3.3 场景:市场环境

- 8 个合成场景(已有:calm trend / high vol / jump tail / latency spike / liquidity collapse / spread explosion 等)——主实验;
- 2 个真实市场窗口(已有 Yahoo 数据)——外部效度检查;
- E3 档:Binance BTCUSDT 公开样本(已有 500 条对齐 fills)+ 建议新增 1-2 个公开 L2 数据源(如 Binance 现货多币种,数据可免费重新下载,脚本 `download_binance_microstructure_sample.py` 可扩展)。

### 3.4 因变量

**主指标:排名稳定性**
- 各档位下代理按 risk-adjusted return(Sharpe)排名,档位两两之间算 Kendall's tau,bootstrap CI(seed 重采样);
- 排名翻转计数:top-3 集合在 E0 → E1 的 Jaccard 相似度;
- "理想化偏差":每个代理 E0 与 E1/E3 的收益差(bps),按代理类型分组。

**机制指标(解释为什么翻转)**
- 换手率、平均参与率、部分成交率、拒单率、滑点成本占收益比;
- 回归:排名变动 ~ 换手率 + 集中度 + 平均订单参与率(跨代理,场景聚类标准误)。

### 3.5 统计方案

- 确定性基线:30 seeds(复用 `--statistical-seeds` 管线);
- LLM:10 seeds × 3 provider samples(00 号 P0 已落实:`--samples-per-seed` 可用)。注意功效约束(00 号 §六):n=5 在置换检验下结构性无法显著,n=10 只能可靠检出大效应(d≥0.8 功效约 0.6,d≥1.2 约 0.93);若 pilot 显示效应中等,把 seeds 升到 20;
- 同 seed 配对比较 + sign-flip 置换检验;所有 p 值 BH-FDR 校正;
- Kendall's tau 的 CI 用 seed 层面的 cluster bootstrap。

## 4. 需要补的基础设施

| 项 | 工作量 | 依赖 |
| --- | --- | --- |
| 执行参数网格扫描脚本(包一层现有 runner) | 1-2 天 | 无 |
| 排名稳定性分析模块(Kendall tau + 翻转表) | 1 天 | statistics.py 扩展 |
| `--samples-per-seed` 与缓存 key 扩展 | 1 天 | 00 号 P0 |
| 直连 API runner(替换 Poe 路由) | 2-3 天 | API keys、预算 |
| Binance 多币种 L2 样本扩展(可选,E3 增强) | 2 天 | 公开数据 |

## 5. 预算估计

LLM 调用:4 模型 × 10 场景 × 10 seeds × 3 samples × ~60 决策步 ≈ 7.2 万次调用,短 prompt,缓存可断点续跑。按主流 API 价格估 $300–800。确定性部分零成本。

## 6. 威胁与限制(论文 Limitations 直接素材)

- E3 档只有 crypto 公开数据,股票档位只能停留在 E2 压力扫描——明确声明,不外推;
- 合成市场的波动结构可能与真实微观结构不一致,排名翻转结论以"在受控合成场景中"为限;
- LLM 可能记忆了真实窗口的历史走势(真实市场部分仅作外部效度参考,主结论建立在合成场景上,这反而规避了污染问题);
- 模型版本漂移:全部调用锁定版本号并落盘 redacted manifest。

## 7. 时间线(以 ICAIF 7 月中截稿倒排)

| 周 | 内容 |
| --- | --- |
| W1(6月中) | 00 号文档 P0/P1 统计修复;扫描脚本;直连 API runner |
| W2 | 确定性基线全矩阵跑完(零成本,先把结论骨架立起来) |
| W3 | LLM 矩阵跑完;排名稳定性分析 |
| W4 | E3 校准档补充;机制回归;图表 |
| W5-6 | 写作、内审、claim boundary 自查(对照 `docs/claim_boundaries.md`) |

## 8. 失败保底

如果 LLM 排名在各档位下基本不翻转(负结果),论文转向:"执行摩擦对 LLM 代理与经典基线的影响是均匀的吗?"——量化偏差幅度本身仍可发 workshop;且负结果对 benchmark 论文(03)是有用证据(说明 E1 默认档是公平的)。
