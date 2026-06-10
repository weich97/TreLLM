# 实验设计 05:人工门控的 LLM 交易控制面(系统论文)

> 状态:设计稿 v1(2026-06-10)。优先级:**远期**(等链路端到端跑通)。
> 目标 venue:ICAIF industry/system track、ACM DEBS/Middleware(若强调系统性质)、或 arXiv 系统报告 + 主论文引用。

## 1. 定位

论文类型:系统/经验论文(systems & experience)。对象是 2026 年 6 月刚合入的整条 live-readiness 链路:

- broker adapter capability 清单(`schemas/broker_adapter_capability.schema.json`、`tools/broker_capability.py`);
- 审批 artifact 与人工门控(`schemas/broker_approval_artifact.schema.json`、审批绑定校验);
- handoff / response 对账(`schemas/broker_handoff_artifact.schema.json`、`broker_response_artifact.schema.json`、reconciliation demo);
- live readiness preflight(`tools/live_readiness.py`、485 行)与 operator runbook(`tools/operator_runbook.py`);
- 大量防御性校验(50+ 个 whitespace-guard / binding 分支即为此链路的加固记录)。

**核心主张**:LLM 交易代理要接近真实经纪接口,需要的不是更好的模型,而是一个把"意图→审批→下单→对账"全程 artifact 化、哈希化、人工门控化的控制面;我们给出第一个开源参考实现及其在故障注入下的拦截率测量。

**与 04 的叙事闭环**:04 证明 LLM 审计不可全信(若自偏袒成立),所以控制面必须人工门控——两篇互相引用。

## 2. 研究问题

**RQ1(完备性)**:控制面的 schema + 校验层能拦截多少类已知的代理-经纪接口故障?(故障注入实验)

**RQ2(成本)**:审计与门控层引入多少延迟与人工开销?在什么决策频率下人工审批成为瓶颈?

**RQ3(对账有效性)**:当经纪端返回与意图不一致(部分成交、改价、拒单、静默丢单)时,reconciliation 层的检出率与误报率?

## 3. 实验设计

### 3.1 前置条件(没有这个就不要动笔)

端到端 paper-trading 案例真实跑通:LLM 代理 → preflight → 审批 artifact(真人签发)→ paper broker(Alpaca paper 或 mock sandbox,`paper_sandbox.py` 已有)→ response 对账 → runbook 事件演练。**连续运行 ≥4 周**,产生真实的运行数据(审批次数、拦截事件、对账差异)。这是系统论文的"deployment experience"门槛。

### 3.2 故障注入矩阵(RQ1/RQ3 主实验)

故障目录(每类注入点已有对应 guard 分支,注入即测试这些 guard 的覆盖):

| 故障类 | 例 | 期望拦截层 |
| --- | --- | --- |
| 标识污染 | 空白填充的 order id / symbol / operator id | schema 校验(已有 guard) |
| 权限越界 | 代理对 capability 清单外的资产/订单类型下单 | capability 绑定校验 |
| 审批绕过 | 过期审批、审批与 handoff 字段不一致、重放旧审批 | approval binding 校验 |
| 响应异常 | broker 返回未知 client_order_id、改量成交、静默丢单 | reconciliation |
| 时钟问题 | preflight 时间戳漂移、无时区时间 | preflight guard(已有) |
| 运行手册违规 | 超出 runbook 声明的 symbol scope / 事件未走升级路径 | runbook 校验 |

方法:写一个对抗性 harness,程序化生成各类畸形 artifact(每类 ≥50 个变体,含变异模糊),报告逐层拦截率、漏网案例分析。**漏网的每个案例都是一个修复 PR,论文与代码加固互相喂养。**

### 3.3 成本测量(RQ2)

- 各校验层的延迟分布(P50/P99,纯本地,报告分位数即可,不需推断统计);
- 4 周运行期内的人工审批负载:审批次数/日、平均响应时间、超时率;
- 用决策频率做参数扫描:日频/小时频/分钟频下,人工门控的可行边界在哪——给出"什么频率以上必须降级为规则自动审批"的量化结论。

## 4. 基础设施缺口

| 项 | 工作量 | 说明 |
| --- | --- | --- |
| 端到端 paper 运行编排(把新合入的各环节串起来连续跑) | 1-2 周 | 最大缺口;各环节单测已有,缺连续运行 harness |
| 对抗性 artifact 生成器 | 3-4 天 | 与 04 的缺陷注入器共享思路 |
| 审批 UI/CLI 的最小人工流程 | 2-3 天 | 真人签发审批的操作面 |
| 运行期监控落盘(审批延迟等) | 2 天 | observability 模块扩展 |

## 5. 威胁与限制

- 单一 paper broker(Alpaca)≠ 真实经纪多样性,声明为参考实现;
- 4 周运行是单一运维者(作者本人)的经验,人工负载数据外推有限——如实报告;
- 故障目录来自已知 guard,存在"考自己出的题"的循环性;缓解:邀请 1-2 名外部贡献者盲注故障(社区任务机制现成);
- 永远不碰真实资金。论文所有措辞对照 `docs/claim_boundaries.md` 与 live readiness 文档的边界声明。

## 6. 时间线

- 2026 H2:端到端编排 + 连续运行(与 03/04 并行,运行本身不占人力);
- 2026 Q4:故障注入矩阵 + 外部盲注;
- 2027 年初:成文,投 ICAIF 2027 industry track 或先发 arXiv 系统报告供 03/04 引用。

## 7. 价值判断

单独作为研究论文新颖性偏工程,但:(a) 它是 TreLLM 整体叙事("审计→评测→门控上线")的终点,补全故事线;(b) 开源的 LLM-broker 安全接口参考实现目前是空白,工程影响力可能大于学术引用;(c) 故障注入产生的安全数据反哺 03/04。建议保持低优先级推进,不为它牺牲 01-03 的进度。
