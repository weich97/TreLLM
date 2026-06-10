# 实验设计 04:FinAudit —— LLM 作为金融轨迹审计员的评测

> 状态:设计稿 v1(2026-06-10)。优先级:**中**(差异化生态位,可独立成文或并入 03)。
> 目标 venue:ACL/EMNLP FinNLP workshop、ICAIF、或作为 03 的一章;成熟后可冲主会 D&B。

## 1. 定位与研究问题

视角反转:不评"LLM 会不会交易",评"**LLM 能不能审计交易**"。这个生态位目前没人占,且与仓库的审计基因完全一致——TradeArena 的每条轨迹自带 ground truth(风控违规记录、执行异常、claim 越界都是结构化落盘的),这意味着审计任务的标注几乎免费。

**RQ1**:LLM 能否从轨迹 artifact 中检出已知的风控违规、执行异常、审计缺口?(检出能力)

**RQ2**:LLM 能否判断一段研究声明是否越过了证据边界(claim boundary review,仓库已有该任务的人工协议)?(判断能力)

**RQ3**:审计能力与交易能力是否相关?会交易的模型更会审计吗?(与 03 排行榜交叉)

**RQ4**:模型在"自我审计"(审自己生成的轨迹)时是否系统性放水?(自偏袒效应——这是最有记忆点的实验)

## 2. 任务设计

仓库现有素材:`skills/` 下六个审计技能(trajectory-audit / risk-gate-review / claim-boundary-review / reproduction-review / execution-calibration / plugin-author)、`examples/skill_tasks*` 任务与参考答案、`schemas/skill_task_rubric.schema.json` 评分 schema、`scripts/score_skill_task.py` 评分脚手架、Poe 模型矩阵实验记录。这些目前是小规模手工任务,本方向的工作是把它规模化、自动化。

### 任务族(每族给出自动生成方法)

**T1 违规检出**(自动生成,主任务)
取一条干净轨迹,程序化注入缺陷后让模型找:
- 删除/篡改某条风控违规记录(审计完整性破坏);
- 改写成交价使滑点与执行参数矛盾(数值一致性);
- 注入超出 `max_position_weight` 的未拦截仓位(规则违规);
- 替换 replay hash(可回放性破坏)。
每条缺陷有确定的 ground truth → precision/recall 全自动评分。**这是本方向可规模化的关键:缺陷注入器一次写好,题目无限生成。**

**T2 claim 边界审查**(半自动)
给定结果 artifact + 一段声明,判断声明等级(engineering/benchmark/scientific,仓库 claim ladder 已定义三级)是否被证据支持。现有 `skill_tasks` 人工题扩充至 ≥100 题:用模板 + 缺陷注入(把"stress 模拟"说成"校准成本"、把单 seed 说成显著)生成越界声明。

**T3 修复建议质量**(开放式,小规模)
检出后给修复建议,人工 rubric 评分(复用 `skill_task_rubric.schema.json`),50 题,双人评注一致性报告。

### 难度分层
- L1:缺陷在单条记录内可见;
- L2:需要跨记录对账(意图 vs 成交 vs 风控报告三方一致性);
- L3:需要调用计算(重算滑点方程、重算 drawdown)——区分"会读"与"会算"。

## 3. 实验设计

| 维度 | 取值 |
| --- | --- |
| 模型 | 与 03 同一组(≥8),便于 RQ3 交叉 |
| 任务量 | T1 自动生成 500 题(各缺陷类型×难度均衡);T2 100 题;T3 50 题 |
| 条件 | 标准审计;自我审计(RQ4:用该模型在 03 中生成的轨迹注入缺陷) |
| 重复 | 每题 3 samples(温度>0),报告多数投票与单次两种成绩 |

### 因变量与统计
- T1/T2:precision、recall、F1 + Wilson 区间;模型两两 McNemar 检验(同题配对),BH-FDR;
- 难度梯度:L1→L3 的成绩衰减曲线;
- RQ3:审计 F1 与交易 Sharpe 的 Spearman 相关(模型层面,n≈8,只做探索性报告);
- RQ4:自我 vs 交叉审计的 recall 差,配对置换检验——**若显著,单独可成一个发现**。

## 4. 基础设施缺口

| 项 | 工作量 | 说明 |
| --- | --- | --- |
| 轨迹缺陷注入器(核心) | 3-4 天 | 读轨迹 JSON → 注入 4 类缺陷 → 落 ground truth 标注;复用 `core/trajectory.py` 与 serialization |
| 审计任务 harness(出题→调模型→判分) | 2-3 天 | 复用 `score_skill_task.py` 骨架 |
| T2 题库扩充模板 | 2 天 | 基于 claim ladder 三级 |
| 自我审计管线(03 轨迹回灌) | 1 天 | 依赖 03 完成 |

## 5. 威胁与限制

- 注入缺陷的分布≠真实审计缺陷分布(定位为能力下界测量);
- T1 自动评分只覆盖"检出",不覆盖"解释质量"(由 T3 小规模补);
- 轨迹 JSON 较长,上下文窗口与成本需要先做单题成本测算(建议先跑 20 题 pilot 估算)。

## 6. 时间线与依赖

依赖 03 的模型直连基础设施,但任务生成器可立即动工(只依赖现有轨迹格式)。
建议节奏:7-8 月写注入器与 harness(与 03 并行),9-10 月跑全量,**FinNLP/ICAIF-workshop 先发任务定义 + pilot 结果占坑**,完整版视 RQ4 结果决定冲主会还是并入 03 修订版。

## 7. 为什么这个方向值得排队

- 标注成本趋近零(ground truth 来自模拟器,不需要人工标);
- 与 LLM-as-judge 文献直接对话,但领域 ground truth 是硬的(不是另一个 LLM 的意见);
- RQ4 自偏袒若成立,对"用 LLM 审计 LLM 交易代理"的实践有直接安全含义,与 TreLLM 的 live-readiness 路线(05)形成闭环叙事。
