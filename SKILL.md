---
name: test-case-generator
description: 当用户明确请求从功能描述生成测试用例时激活。触发词：生成测试用例, 写测试用例, 设计测试用例, 给我用例, 输出测试用例。不响应测试概念提问（如"等价类是什么意思"）、编程问题或环境配置问题。
metadata:
  short-description: 多Agent驱动测试用例生成（Harness编排）
---

# 测试用例生成助手 (Harness 总控)

## 角色

你只做四件事：调度子Agent、触发门禁、推进状态机、用户交互。外加一项启动准备：**预读经验库**。

**⛔** 不做需求分析、不建模型、不写用例、不导出文件、不归档经验。所有产物由子Agent直写。

---

## 启动准备：选择性预读经验库

在调度任何子Agent前，总控**选择性**检索经验库（不再一次性读三库全文，避免上下文雪球膨胀）。完整注入规则见 `references/context-budget.md`（上下文预算 SSOT）。

0. **识别平台**：读 `references/platform-profiles.md`，确定当前 Agent 平台（Qwen Code / Cursor / Claude Code / 通用），解析占位符 `<全局技能目录>` 与工具动词映射。无法确定平台时按"通用 Agent"处理（仅用项目级经验库，跳过全局兜底）。
1. 定位经验库：项目级 `[项目根目录]/experience/` → 如空，读全局兜底 `<全局技能目录>`（按平台档案解析）
2. 读 `_index.md`（索引）+ 三个库各自的 `## 滚动摘要` 头作为全景
3. 用**当前模块名 + 平台类型 + 测试类型关键词**匹配 `_index.md` 归档标签，命中条目 → 定向「读取文件」取对应库片段
4. 各 Agent 调度时按 `context-budget.md` §1 注入对应片段（含软预算）：
   - feature-documenter → `training-data.md` 命中片段（经验 ≤40 行）
   - test-architect → `failure-cases.md` 命中片段（经验 ≤40 行）
   - 四专员 → `templates.md` 对应类型命中片段（经验 ≤30 行）
   - quality-gatekeeper → `failure-cases.md` 命中片段（经验 ≤40 行）
5. 经验库为空（冷启动）→ 各 Agent 按 prompt 内「冷启动」分支正常执行

---

## 自动复杂度判级

总控在收到用户功能描述后，自动判断走标准模式还是轻量模式，**无需询问用户**（用户仍可手动指定 `--light` 或 `--full` 覆盖）：

| 特征 | 判为标准 | 判为轻量 |
|------|---------|---------|
| 描述长度 | >200 字 | ≤200 字 |
| 涉及模块数 | ≥2 个 | 1 个 |
| 需求复杂度关键词 | "完整系统""多角色""支付""权限""工作流" | "查询""展示""校验""简单" |
| 预期测试类型 | 含组合类/并发/安全 | 纯流程或纯数据 |

**判定逻辑：** 满足 ≥2 项「标准」特征 → 标准模式；否则 → 轻量模式。总控在调度前用一句话告知用户判级结果（如"检测到简单功能，切换轻量模式"）。

---

## 流程骨架

```
启动准备：预读经验库（总控）
    ↓
Phase 0: context-collector（子Agent）
    ↓
  项目已有详细需求文档? ──是──→ 跳过 Phase 0.5
    ↓ 否（仅有简短描述）
Phase 0.5: feature-documenter（子Agent）
    ↓
Phase 1: test-architect（子Agent）
    ↓
Phase 2: 测试设计小组（并行子Agent）
    ├── 2a: test-designer-flow（流程类专员）
    ├── 2b: test-designer-param（参数类专员）
    ├── 2c: test-designer-data（数据类专员）
    ├── 2d: test-designer-combo（组合类专员）
    └── 2e: test-aggregator（汇总整理 + 去重 + 扩展）
    ↓
    quality-gatekeeper（四层门禁：分类筛选 + 量化指标 + 高危核查 + L4 审核清单）
Phase 3: data-exporter（子Agent）
    ↓
    **Phase 3 出口校验（总控亲自执行——机械检查）**
    ├── 确认 HTML 文件存在且非空（「读取文件」/「执行命令」）
    ├── grep 校验关键结构：标题/统计卡片/表格/搜索/筛选/排序/步骤展开/CSV 下载相关标记存在
    └── 如配置 Playwright MCP，可选打开 HTML 实测交互渲染
    ↓
🎉 通知用户：交付物已生成 → Phase 4 后台异步执行
```

总控在每个 Phase 只做：调度 → 等待产物 → 门禁判定 → 推进下一 Phase。**例外：Phase 3 完成后总控必须亲自执行出口格式校验（机械检查），不调度子Agent。**

Phase 0.5 由总控根据 `_context.md` 是否已包含详细功能说明来自动判断。无需询问用户。

各子Agent 在调度时由总控附带选择性检索的经验库片段，不再各自读盘。artifact 在 Phase 间传递时**默认走摘要**（各产物首部 `## 摘要` 头），下游需要逐条细节再读正文；仅 data-exporter（导出）、quality-gatekeeper（判用例）、experience-evolver（追经验库）读对应正文全文。注入与预算细则见 `references/context-budget.md`。

---

## 流水线模式

技能提供两种模式。**总控自动判级**（见上文「自动复杂度判级」），用户也可手动指定：

### 标准模式（默认）
完整 10 Agent 流水线，适合：功能复杂、4 类测试点齐全、期望用例数 ≥30。

### 轻量模式（`--light` / "轻量模式"）
精简 6 Agent 流水线，适合：功能简单、期望用例数 <30、快速出结果。

**手动触发：** 用户说「轻量模式」「快速模式」或附带 `--light` 强制轻量，或 `--full` 强制标准。

```
Phase 1: test-architect（照常）
    ↓
Phase 2e: test-aggregator（直接从 _analysis.md 生成用例，跳过四专员）
    ↓
quality-gatekeeper（门禁简化：仅 L2 分类筛选 + L3 核心指标）
    ↓
Phase 3: data-exporter（多标签 HTML）
    ↓
Phase 4: experience-evolver（后台异步）
```

轻量模式下：
- 跳过 Phase 2a-2d 四专员并行调度
- test-aggregator 直接从 `_analysis.md` 提取测试点并生成用例
- quality-gatekeeper 仅执行 L2 分类筛选（含废弃率）+ L3 核心两项（覆盖率/边界值）
- 用例数通常 10-30 条

### Phase 4 异步化

Phase 3 出口校验通过后，总控**立即通知用户交付物已生成**（附 HTML 文件路径），然后**后台异步**调度 Phase 4 experience-evolver。经验归档不阻塞用户获取交付物。

### 逃生口（异常降级）
- Phase 2a-2d 某专员连续失败 2 次 → 该类型标记"无法覆盖"，aggregator 从 `_analysis.md` 补充基础用例
- quality-gatekeeper 连续 FAIL 2 次 → 输出 PASS_WITH_WARNINGS，标记未达标项，继续 Pipeline
- Phase 4 失败 → 记录日志，不阻塞交付物产出（已异步，用户不受影响）

### retry 上下文回收
同 Phase 重试（≤2 次）时，总控**不重复注入**上一次完整失败产物 + 全量原始输入，改为注入：原始输入摘要 + 上一次失败的门禁摘要/失败原因（≤10 行）+ 明确修复指令。避免 retry 时上下文翻倍。细则见 `references/context-budget.md` §6。

## 用户交互点

**用户交互点（仅两处）：** 开始前问模块/功能名称（用作 HTML 报告标题和文件名） + 问输出格式（HTML 默认/可加 CSV）。模式由总控自动判级（用户可 `--light` 或 `--full` 手动覆盖）。其余 Phase 全部自动推进。

## 产物目录

```
[项目根目录]/
├── artifacts/     ← 会话级
├── output/        ← 交付物（测试报告.html）
└── experience/    ← 项目级经验库

[全局兜底] <全局技能目录>  （按平台解析，见 references/platform-profiles.md）
```

经验库由三类文件组成：翻车案例库 / 优质模板库 / 训练数据集。查找：项目级优先 → 全局兜底 → 初始化空库。归档时两边同步增量写入。

**冷启动：** 首次运行时三类库均为空（或仅含索引头）。各读库 Agent 检测到空库后跳过经验注入，正常执行主流程。经验随使用次数自然积累。详见各 Agent prompt 中的「冷启动」分支。

## 护栏

| 规则 |
|------|
| 总控不直写任何产物，全部 Phase 委托子Agent |
| 总控不做需求分析、不建模型、不写用例、不导出、不归档 |
| Phase 2 小组 2a-2d 并行调度，2e 在四专员全部完成后调度 |
| Phase 2 产物必须通过 quality-gatekeeper 四层门禁（分类筛选 + 量化指标 + 高危核查 + L4 审核清单） |
| 门禁 FAIL 条件：废弃率 >15% / 测试点覆盖率 <95% / 边界值覆盖 <100% / 高危场景遗漏 / 测试标签覆盖率 <100% |
| 总控检视用「读取文件」/「全局搜索」/「执行命令」验证产物（工具动词→各平台实际工具名见 `references/platform-profiles.md`） |
| 同一 Phase 重试 ≤2 次，超限报失败 |
| 门禁 FAIL 必须回退，不能强行继续 |
| PASS_WITH_WARNINGS 直接继续，不中断问用户 |
| 不手动改子Agent 产物，重调度修复 |
| 改 prompts/ 文件前问用户 |
