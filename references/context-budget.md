# 上下文预算 — Single Source of Truth

> **此文件是 Context Manager（上下文管理）的唯一权威来源。** 规定每个 Agent 注入什么上下文、用摘要还是全文、软预算多少。
> 解决问题：随 Phase/retry/经验库轮次增加，artifacts 与经验库全量传播导致 token 雪球膨胀、attention 稀释、指令漂移。
> 修改任何注入规则前，先改此文件，再同步到 `SKILL.md` 与各 prompt（见 §7 同步清单）。

---

## 1. 注入矩阵（Injection Matrix）

定义每个 Agent 由总控注入的内容、来源、读取方式、软预算。**读取方式**：`全文` = 完整注入；`摘要优先` = 先读 `## 摘要` 头，不足再「读取文件」取正文；`命中片段` = 按关键词从 `_index.md` 命中后定向取片段；`按类型切片` = 只取与本 Agent 职责相关的部分。（工具动词→各平台实际工具名见 `references/platform-profiles.md`）

| Agent | 注入经验库 | 注入 artifact | 读取方式 | 软预算 |
|-------|-----------|--------------|---------|--------|
| Phase 0 context-collector | — | 用户原始描述 | 全文 | — |
| Phase 0.5 feature-documenter | `training-data.md` 命中片段（业务规则/禁止规则） | `_context.md` | 摘要优先 | 经验 ≤40 行 |
| Phase 1 test-architect | `failure-cases.md` 命中片段（历史漏测场景） | `_feature-doc.md` / `_context.md` | 摘要优先（建模时按需读正文） | 经验 ≤40 行 |
| Phase 2a-2d 四专员 | `templates.md` 命中片段（对应类型模板） | `_analysis.md`（按类型切片）+ `_context.md`（摘要） | 按类型切片 | 经验 ≤30 行；只取本类型测试点+模型 |
| Phase 2e test-aggregator | — | 4 分部文件（摘要优先）+ `_analysis.md`（摘要） | 摘要优先；去重/自查时再读正文 | 各分部摘要 ≤8 行 |
| Phase 2 quality-gatekeeper | `failure-cases.md` 命中片段 | `_test-cases.md`（全文）+ `_analysis.md`（摘要）+ 4 分部（摘要，交叉校验用） | 用例全文必读，其余摘要优先 | 经验 ≤40 行 |
| Phase 3 data-exporter | — | `_test-cases.md`（全文）+ `_analysis.md`（全文，建模页需要）+ `_verification-phase2.md`（全文） | 全文（导出需完整数据） | — |
| Phase 4 experience-evolver | 三库现有内容（增量追加用，读正文） | `_test-cases.md` + `_verification-phase2.md`（全文）+ `_analysis.md` / `_feature-doc.md`（摘要） | 产物摘要优先，经验库读正文 | — |

> **原则：** 默认摘要优先；只有「最终消费者」（data-exporter 导出、gatekeeper 判用例、evolver 追经验库）才读对应正文全文。

> **控制面元数据例外：** `_run-log.md`（总控运行账本）**不注入任何子Agent**，仅供总控观测与人工查看，不计入注入预算。

---

## 2. 摘要头规范（Summary Memory）

每个产物文件的**正文之前**写一个 `## 摘要` 块，作为下游的轻量入口。规范：

- 标题固定为 `## 摘要`，紧跟文件主标题之后、其余章节之前
- **≤8 行**，每行一条要点，复用该 Agent「报告格式」里已有的关键数字
- 用 `---` 分隔摘要与正文

通用模板：

```markdown
# [文件主标题]

## 摘要
- 模块：[模块名] | 关键规模：[测试点数/用例数等]
- 关键约束：[1-2 条最重要的业务约束或边界]
- 类型分布/高危：[如 流程X/参数Y/数据Z 或 高危 H1/H4]
- 下游须知：[需要下游特别注意的 1-2 条，如缺口/待补项]
---

（正文……）
```

下游 Agent 的 `## 输入` 段统一加一句：

> **先读 `## 摘要`，摘要信息足够即可；需要逐条细节时再「读取文件」读对应正文章节。**

---

## 3. 选择性检索协议（Selective Retrieval — 总控启动准备）

总控在调度任何子 Agent 前，**不再一次性读三个经验库全文**，改为：

1. 读 `experience/_index.md`（索引，通常 <40 行）
2. 读三个库各自的 `## 滚动摘要` 头（见 §5），作为经验全景注入
3. 用当前**模块名 + 平台类型 + 测试类型关键词**匹配 `_index.md` 的归档标签：命中的归档条目 → 定向「读取文件」取对应库该片段，按 §1 软预算注入给对应 Agent
4. **冷启动**（三库为空或仅含索引头）→ 保持各 prompt 内「冷启动」分支：跳过经验注入，正常产出

经验库与各 Agent 的对应关系见 §1「注入经验库」列。

---

## 4. Token 预算原则（Token Budget）

- 预算以**行数/条目数**近似，LLM 自估即可，不要求精确 token
- 注入的经验片段超过软预算时：只保留与本模块标签最相关的 **Top-K** 条，其余以一行提示替代：
  > 另有 N 条历史经验未注入，需要时「读取文件」`[库文件]`
- artifact 摘要超过 8 行时由产出 Agent 自行精简，不在下游截断

---

## 5. 经验库容量压缩与滚动摘要（Context Compression）

由 Phase 4 experience-evolver 在写入前执行（详见 `prompts/experience-evolver.md`）：

| 库文件 | 容量阈值 | 压缩动作 |
|--------|---------|---------|
| `failure-cases.md` | >40 条 | 同类（同标签/同场景）旧条目归并为 1 条「模式摘要」，保留代表性 1-2 例 + 指针 |
| `templates.md` | >300 行 | 同类型旧模板归并，保留最优 1-2 例 + 指针 |
| `training-data.md` | >40 条业务规则 | 同模块旧规则归并去重，保留最新表述 |

- 每个库维护一个 `## 滚动摘要` 头（≤10 行），供 §3 注入
- **压缩只动「已归并的旧条目」，最近 3 次归档原样保留**

---

## 6. retry 上下文回收（Retry Context Recycling）

总控在同 Phase 重试（≤2 次）时：

- **不重复注入**上一次的完整失败产物 + 原始全量输入
- 改为注入：原始输入摘要 + 上一次失败的**门禁摘要/失败原因**（≤10 行）+ 明确的修复指令
- 逃生口（连续失败降级）逻辑不变，见 `SKILL.md`

---

## 7. 修改此文件后

任何对本文件的修改，必须同步检查以下文件：

| 类别 | 涉及文件 | 检查点 |
|------|---------|--------|
| 总控 | `SKILL.md` | 启动准备「选择性检索」段、retry 回收段 |
| Phase 0 | `prompts/context-collector.md` | 输出 `## 摘要` 头 |
| Phase 0.5 | `prompts/feature-documenter.md` | 输入预算行 + 输出摘要头 |
| Phase 1 | `prompts/test-architect.md` | 输入预算行 + 输出摘要头 |
| Phase 2a-2d | `prompts/test-designer-{flow,param,data,combo}.md` | 输入预算行/切片 + 输出摘要头 |
| Phase 2e | `prompts/test-aggregator.md` | 输入「先读摘要」+ 输出摘要头 |
| Phase 2 门禁 | `prompts/quality-gatekeeper.md` | 输入「先读摘要」+ 预算行 |
| Phase 3 | `prompts/data-exporter.md` | 输入「全文」标注（不走摘要） |
| Phase 4 | `prompts/experience-evolver.md` | 容量压缩 Step + 滚动摘要头 |
| 经验库 | `experience/{failure-cases,templates,training-data}.md`、`experience-seed/*` | `## 滚动摘要` 头 |
| 关联 SSOT | `references/naming-conventions.md` | artifact 文件名一致性 |
