# 命名规范 — Single Source of Truth

> **此文件是项目中所有命名约定的唯一权威来源。** 修改任何值之前，先改此文件，然后同步到各处。

---

## 1. 目录结构

| 路径 | 用途 | 说明 |
|------|------|------|
| `artifacts/` | 中间产物目录 | 会话级，所有 `_*.md` 文件存放处 |
| `output/` | 交付物目录 | 持久化，HTML/CSV/MD 最终产出 |
| `experience/` | 项目级经验库 | 项目根目录下，gitignore |
| `experience-seed/` | 脱敏种子库 | 首次使用时 `mkdir -p experience && cp experience-seed/*.md experience/` |
| `~/.qwen/skills/test-case-generator/experience/` | 全局兜底经验库 | 跨项目复用的方法论级经验 |
| `prompts/` | 子 Agent 提示词 | 10 个 prompt + 总控 SKILL.md |
| `references/` | 参考文档 | 方法论、输出模板、命名规范、上下文预算 |
| `tools/` | 导出脚本 | export_html.py、export_csv.py、export_md.py |

---

## 2. 中间产物文件名（artifacts/）

| 文件名 | 产出者 | 下游消费者 |
|--------|--------|-----------|
| `_context.md` | Phase 0 context-collector | test-architect, 四专员 |
| `_feature-doc.md` | Phase 0.5 feature-documenter | test-architect |
| `_analysis.md` | Phase 1 test-architect | 四专员, aggregator, gatekeeper |
| `_test-cases-flow.md` | Phase 2a test-designer-flow | aggregator, gatekeeper |
| `_test-cases-param.md` | Phase 2b test-designer-param | aggregator, gatekeeper |
| `_test-cases-data.md` | Phase 2c test-designer-data | aggregator, gatekeeper |
| `_test-cases-combo.md` | Phase 2d test-designer-combo | aggregator, gatekeeper |
| `_test-cases.md` | Phase 2e test-aggregator | gatekeeper, data-exporter |
| `_verification-phase2.md` | Phase 2 quality-gatekeeper | experience-evolver |
| `_export-result.md` | Phase 3 data-exporter | 总控出口校验 |
| `_experience-result.md` | Phase 4 experience-evolver | — |

---

## 3. 交付物文件名（output/）

| 格式 | 命名模式 | 示例 |
|------|---------|------|
| HTML 报告（主产物） | `{模块名}_测试报告.html` | `用户登录_测试报告.html` |
| CSV 用例（兼容） | `{模块名}_测试用例.csv` | `用户登录_测试用例.csv` |
| Markdown 设计文档（兼容） | `测试设计文档.md` | `测试设计文档.md` |

> **注意：** `{模块名}` 来自总控在开始时询问用户的名称，用作 HTML 标题和文件名前缀。建议用户用模块/功能名（如"用户登录"），而非项目名。

---

## 4. ID 命名规范

### 4.1 测试用例 ID

| 来源 | 格式 | 示例 | 说明 |
|------|------|------|------|
| 流程类专员 | `TC-FLOW-{序号3位}` | `TC-FLOW-001` | 标准模式 |
| 参数类专员 | `TC-PARAM-{序号3位}` | `TC-PARAM-001` | 标准模式 |
| 数据类专员 | `TC-DATA-{序号3位}` | `TC-DATA-001` | 标准模式 |
| 组合类专员 | `TC-COMBO-{序号3位}` | `TC-COMBO-001` | 标准模式 |
| 汇总员扩展 | `TC-EXT-{序号3位}` | `TC-EXT-001` | 错误推测/非功能扩展 |
| 轻量模式 | `TC-{序号3位}` | `TC-001` | 跳过了四专员，无类型前缀 |

**规则：**
- 序号从 001 起，3 位数字，不足补零
- 汇总员**保持专员原有 ID，不重编号**
- 轻量模式与标准模式的 ID 命名空间独立，不会冲突（因为轻量模式跳过了四专员）

### 4.2 测试点 ID

**格式：** `TP{序号2位}`，如 `TP01`、`TP02`

- 由 test-architect 在 `_analysis.md` 中分配
- 序号从 01 起，2 位数字
- 测试点 ID 不携带类型信息（类型在"类型"列单独标注）

---

## 5. 用例表格列规范

### 5.1 中间产物 Markdown 表（11 列）

| # | 列名 | 必填 | 说明 |
|---|------|------|------|
| 1 | 用例ID | ✅ | 见 §4.1 |
| 2 | 模块 | ✅ | 模块/功能名称 |
| 3 | 测试层次 | ✅ | 集成测试/系统测试/验收测试 |
| 4 | 用例标题 | ✅ | ≤30 字完整句式 |
| 5 | 前置条件 | ✅ | — |
| 6 | 测试步骤 | ✅ | 2-7 步，子项带序号 |
| 7 | 预期结果 | ✅ | 1-5 个，一一对应 |
| 8 | 优先级 | ✅ | P0/P1/P2/P3 |
| 9 | 用例类型 | ✅ | 功能/负向/边界/安全/组合/错误推测 |
| 10 | 测试标签 | — | 从测试点继承的标签，可为空 |
| 11 | 关联测试点 | ✅ | 对应 `_analysis.md` 中测试点 ID |

### 5.2 导出 CSV（9 列）

导出的 CSV 和 HTML 内嵌数据使用 9 列（去除"测试层次"和"关联测试点"，这两列为内部校验用）：

`用例ID, 模块, 用例标题, 前置条件, 测试步骤, 预期结果, 优先级, 用例类型, 测试标签`

---

## 6. 模式名称

| 正式名称 | 别名/触发词 | 说明 |
|---------|-----------|------|
| 标准模式 | （默认） | 10 Agent 全流水线 |
| 轻量模式 | `--light`、快速模式 | 6 Agent 精简流水线 |

所有 prompt 中统一使用 **"标准模式"** 和 **"轻量模式"**。

---

## 7. 关键术语

| 术语 | 含义 | 使用场景 |
|------|------|---------|
| **模块名** | 用户输入的模块/功能名称 | HTML 文件名前缀、表格"模块"列、总控交互点 |
| 测试标签 | 6 种专项测试标记 | 接口测试/性能测试/安全测试/故障注入/兼容性测试/并发测试 |
| 测试层次 | 4 层 V 模型分层 | 单元测试/集成测试/系统测试/验收测试 |
| 测试点类型 | 4 类测试点分类 | 流程类/参数类/数据类/组合类 |
| 风险等级 | 3 级风险 | 高/中/低 |
| 用例类型 | 用例的正负向属性 | 功能/负向/边界/安全/组合/错误推测 |

> **注意：** 总控问用户的是"模块名"（用于 HTML 标题），不是"项目名"。在 README 等面向用户的文档中，统一用"模块/功能名称"。

---

## 8. 经验库同步策略

| 文件 | 同步范围 | 原因 |
|------|---------|------|
| `failure-cases.md` | 项目级 + 全局双写 | 方法论级，可跨项目复用 |
| `templates.md` | 项目级 + 全局双写 | 方法论级，可跨项目复用 |
| `training-data.md` | **仅项目级** | 业务规则为项目专有，不污染全局库 |

---

## 9. Python 脚本

| 脚本 | 用途 | 调用者 |
|------|------|--------|
| `tools/export_html.py` | 生成自包含 HTML 报告 | data-exporter（默认） |
| `tools/export_csv.py` | 生成 CSV 文件 | data-exporter（可选附加） |
| `tools/export_md.py` | 生成 Markdown 设计文档 | data-exporter（兼容输出，按需） |

**Python 命令探测顺序：** `python3` → `python` → `py -3`

---

## 10. 修改此文件后

任何对此文件的修改，必须同步检查以下文件是否需要更新：

| 类别 | 涉及文件 |
|------|---------|
| 总控 | `SKILL.md` |
| 用户文档 | `README.md`, `examples/README.md` |
| Phase 0 | `prompts/context-collector.md` |
| Phase 0.5 | `prompts/feature-documenter.md` |
| Phase 1 | `prompts/test-architect.md` |
| Phase 2a-2d | `prompts/test-designer-{flow,param,data,combo}.md` |
| Phase 2e | `prompts/test-aggregator.md` |
| Phase 2 门禁 | `prompts/quality-gatekeeper.md` |
| Phase 3 | `prompts/data-exporter.md` |
| Phase 4 | `prompts/experience-evolver.md` |
| 模板 | `references/output-templates.md` |
| 种子库 | `experience-seed/_index.md` |
| 导出脚本 | `tools/export_*.py` |
