# 测试用例生成助手 — 整体介绍

## 一句话概述

一个**多 Agent 协作、Harness 编排**的测试用例自动生成技能。你提供一段功能描述，它走完 10 个子Agent 的流水线，从无到有输出**交互式 HTML 测试报告**（内置搜索/筛选/排序/CSV 下载），内置五层质量门禁和完整经验闭环。

---

## 快速开始

### 环境要求
- **Qwen Code**（v0.14+）
- **Python 3.8+**（用于 HTML/CSV/Markdown 导出脚本）

### 安装（接入 Qwen Code）

**方式一：直接引用本地路径**

在 Qwen Code 对话中输入：
```
/add-skill /path/to/test-case-generator
```

或者在你的项目 `.qwen/skills/` 目录下创建符号链接：
```bash
ln -s /path/to/test-case-generator ~/.qwen/skills/test-case-generator
```

**方式二：配置 skills 目录**

编辑 Qwen Code 的 `settings.json`，添加 skills 路径：
```json
{
  "skills": {
    "paths": ["/path/to/test-case-generator"]
  }
}
```

### 使用

1. 启动 Qwen Code，进入目标项目目录
2. 输入一段功能描述（或直接粘贴 `examples/input/需求描述.md` 的内容）
3. Skill 自动激活，总控自动判断复杂度并选择标准/轻量模式，全自动推进流水线
4. 产出在 `output/` 目录下：`[模块名]_测试报告.html`（双击浏览器打开即可）

> 💡 多标签 HTML 报告包含：仪表盘、测试策略、测试点清单、模型（Mermaid）、交互式用例表格（搜索/筛选/排序/展开）、质量门禁报告、一键 CSV 下载。

### 常见问题

**Q: 首次运行经验库为空怎么办？**
总控启动时**选择性检索**经验库（按模块/平台/测试类型关键词命中片段 + 滚动摘要，预算见 `references/context-budget.md`），避免上下文随经验库轮次膨胀；空库时各 Agent 自动降级为"跳过经验注入"模式，不影响主流程。仓库提供 `experience-seed/` 脱敏种子库（翻车案例 + 模板 + 业务规则），首次使用时可将其内容复制到 `experience/` 目录启动经验闭环。第二轮开始经验库逐步积累，自动生效。

**Q: 只想生成少量用例（轻量模式）？**
总控自动根据功能描述复杂度判级，简单功能自动走轻量模式（6 Agent，10-30 条用例）。也可在对话中手动指定 `--light` 或 `--full` 覆盖。详见下文"流水线模式"。

**Q: Mac/Linux 能用吗？**
可以。`tools/` 下的导出脚本已用 Python 重写，跨平台兼容。

---

## 核心设计理念：人主导、AI 辅助

AI 做体力活（拆解功能、建模型、写用例、格式化输出），人的专业判断贯穿全流程：

| 人负责 | AI 负责 |
|--------|---------|
| 提供功能描述和业务知识 | 膨胀为结构化功能文档 |
| 设定测试策略方向 | 识别测试点、建模型、打测试标签 |
| 复核高风险场景 | 小组分工按四步法生成用例 |
| 终审把关 | 四层门禁量化校验 + 高危核查 + L4 审核清单 |
| 沉淀经验 | 自动归档三类知识库 + 历史翻车交叉校验 |

---

## 五层质量管控体系

| 层 | 名称 | 技能内实现 |
|----|------|-----------|
| **L1** | 业务需求前置拆解 | Phase 0.5 feature-documenter：简短描述→8节结构化文档，注入历史业务规则 |
| **L2** | 分类筛选 | Phase 2 quality-gatekeeper 第一层：每条用例归入「直接保留/待修改/废弃」 |
| **L3** | 多维度量化校验 | Phase 2 quality-gatekeeper 第二+三层：9 项硬指标 + 8 类高危场景 + 翻车案例交叉校验 |
| **L4** | 三级审核 | Phase 2 quality-gatekeeper 第四层：14 项初审/复核/终审清单 |
| **L5** | 复盘沉淀形成闭环 | Phase 4 experience-evolver 写库 + 4 个 Agent 读库，闭环运转 |

---

## 架构：Harness + 10 个子Agent

```
                          ┌─────────────────┐
                          │   Harness 总控    │
                          │  调度+门禁+状态机  │
                          └────────┬────────┘
                                   │
    ┌──────────────┬───────────────┼───────────────┬──────────────┐
    │              │               │               │              │
┌───▼───┐   ┌──────▼──────┐  ┌─────▼─────┐  ┌─────▼─────┐  ┌────▼────┐
│Phase 0│   │  Phase 0.5  │  │  Phase 1  │  │  Phase 2  │  │ Phase 2 │
│context│──→│  feature    │─→│  test-    │─→│  小组(5)  │─→│quality- │
│collect│   │ documenter  │  │ architect │  │ 4专员并行 │  │gatekeep │
└───────┘   └─────────────┘  └───────────┘  │ +汇总串行 │  │(四层)   │
                                            └───────────┘  └────┬────┘
                                                                │
                                            ┌───────────┐  ┌────▼────┐
                                            │  Phase 4  │  │ Phase 3 │
                                            │experience │◄─│  data   │
                                            │ evolver   │  │exporter │
                                            └───────────┘  └─────────┘
```

**总控只做四件事：** 调度子Agent → 等待产物 → 门禁判定 → 推进状态机。所有产物由子Agent直写。

---

## 完整流水线

```
用户输入：一段功能描述
   │
Phase 0: context-collector ────→ _context.md
   │
   ├── 项目已有详细需求文档？──→ 跳过
   └── 否
Phase 0.5: feature-documenter ──→ _feature-doc.md （读 training-data.md 注入业务规则）
   │
Phase 1: test-architect ────────→ _analysis.md （读 failure-cases.md 覆盖历史盲区）
   │                                   测试点带「建议测试标签」
   │
Phase 2a-2d: 四专员并行 ────────→ _test-cases-flow/param/data/combo.md
   │                              （各读 templates.md 对齐用例风格）
Phase 2e: test-aggregator ──────→ _test-cases.md （去重+扩展+分层+优先级）
   │
Phase 2: quality-gatekeeper ────→ _verification-phase2.md + L4 审核清单
   │                              （读 failure-cases.md 交叉校验）
   │
Phase 3: data-exporter ─────────→ output/测试报告.html
   │                              （HTML 报告：仪表盘 + 交互表格 + CSV 下载）
Phase 4: experience-evolver ────→ experience/（三类库增量更新）
                                  _experience-result.md
```

**用户交互点仅两处：** 开始前问模块/功能名称 + 问输出格式。模式由总控自动判级（用户可 `--light` / `--full` 手动覆盖），其余全自动。

> 💡 **轻量模式：** 总控自动判级，简单功能走 6 Agent（10-30 条用例）；也可说「轻量模式」或 `--light` 强制。详见 SKILL.md「流水线模式」。

---

## 经验闭环

经验库不再只进不出——四个 Agent 在生产过程中主动读取：

```
   ┌──────────────────────────────────────────────┐
   │              经验库（三类文件）                │
   │                                              │
   │  failure-cases.md  ◄── Phase 4 写入          │
   │  templates.md      ◄── Phase 4 写入          │
   │  training-data.md  ◄── Phase 4 写入          │
   └──┬──────────┬──────────────┬─────────────────┘
      │          │              │
      ▼          ▼              ▼
  Phase 0.5   Phase 1        Phase 2a-2d       Phase 2 gatekeeper
  feature-    test-          四专员并行          quality-gatekeeper
  documenter  architect
      │          │              │                    │
  读training  读failure     读templates         读failure-cases
  -data.md    -cases.md       .md               .md
      │          │              │                    │
  注入业务    纳入测试点      对齐用例风格         交叉校验
  规则        清单                               「同坑不踩两次」
```

| 谁读 | 读什么 | 改善什么 |
|------|--------|---------|
| feature-documenter | `training-data.md` | 功能文档不遗漏已知业务约束 |
| test-architect | `failure-cases.md` | 测试点清单覆盖 AI 盲区 |
| 四专员 | `templates.md` | 用例句式结构贴近团队习惯 |
| quality-gatekeeper | `failure-cases.md` | 历史翻车案例交叉校验，遗漏→严重问题 |

---

## 各 Phase 详解

### Phase 0 — context-collector
收集项目上下文：模块名称、需求类型（新增/变更/回归）、技术栈、测试范围。

### Phase 0.5 — feature-documenter（条件触发）
将简短描述膨胀为结构化功能文档，输出 `_feature-doc.md`（8 节），并读取 `training-data.md` 注入历史业务规则和禁止规则。

### Phase 1 — test-architect（测试架构师）
制定测试策略 → 扫描测试点 → 六属性全面性检查 → 四分类 → 风险评估 → 建模 → **打 6 种测试标签**。读取 `failure-cases.md` 将历史漏测场景直接纳入测试点清单。

### Phase 2 — 测试设计小组（5 人）

| 专员 | 处理 | 方法 |
|------|------|------|
| **2a flow** | 流程类 | 路径分析（4 策略可选） |
| **2b param** | 参数类 | 输入-输出表逐行覆盖 |
| **2c data** | 数据类 | 等价类 + 边界值 |
| **2d combo** | 组合类 | 正交分析 + 剔除无效组合 |
| **2e aggregator** | 汇总 | 去重 + 错误推测扩展 + 非功能补充 + 分层 + 优先级 |

2a-2d 并行调度，2e 串行等待。四专员各读 `templates.md` 对齐团队用例风格。

### Phase 2 — quality-gatekeeper（四层门禁）

| 层 | 内容 | 关键指标 | 不达标后果 |
|----|------|---------|-----------|
| L2 分类筛选 | 每用例归入保留/待修改/废弃 | 废弃率 ≤15% | FAIL |
| L3 量化指标 | 9 项硬指标 | 覆盖≥95%/边界100%/标签100% | FAIL |
| L3 高危核查 | 8 类场景 + 翻车案例交叉校验 | 漏洞0%/历史翻车不再漏 | FAIL |
| L4 审核清单 | 初审4+复核5+终审5=14 项 | — | 仅输出 |

### 6 种测试标签

| 标签 | 触发条件 |
|------|---------|
| 接口测试 | API 调用、接口对接 |
| 性能测试 | 大数据量、高并发 |
| 安全测试 | 登录/权限、敏感数据 |
| 故障注入 | 依赖外部服务、网络通信 |
| 兼容性测试 | 多浏览器/设备/版本 |
| 并发测试 | 共享资源、竞态条件 |

标签由 test-architect 在测试点打标 → test-designer 继承 → gatekeeper L3.9 核查覆盖率 → data-exporter 导出到 CSV。

### Phase 3 — data-exporter
导出自包含的多标签 **HTML 测试报告**（默认主输出，6 标签页：仪表盘/测试策略/测试点/模型/交互式用例表格/质量门禁，零依赖打开即用），可选附加 CSV（UTF-8 BOM / CRLF / 含测试标签列）。

### Phase 4 — experience-evolver
从本轮产物提取经验，增量更新三类知识库：
- `failure-cases.md` — 翻车案例（漏测/AI幻觉）
- `templates.md` — 优质模板（按用例类型分类）
- `training-data.md` — 训练数据（优质用例+业务规则+禁止规则）

---

## 方法论基础

详见 `references/methodology.md`：

| 方法 | 用途 |
|------|------|
| 四步测试策略制定法 | 质量目标→风险分析→适配流程→分层 |
| 测试方法车轮图 | 六属性→测试类型→测试方法 |
| 四步测试设计法 | 建模→基础用例→数据补充→扩展 |
| 测试点四分类 | 流程/参数/数据/组合 |
| 路径覆盖四策略 | 语句/分支/最小线性无关/全覆盖 |
| 分层测试（V模型） | 单元→集成→系统→验收 |
| 风险分析 | 识别→评估→应对 |
| 覆盖度评估 | 需求/路径/方法 |

---

## 文件结构

```
test-case-generator/
├── SKILL.md                              ← Harness 总控
├── README.md                             ← 本文件
├── .archive/
│   └── _archived_test-designer.md        ← 旧版（已归档）
├── experience-seed/
│   ├── _index.md                         ← 脱敏种子库索引
│   ├── failure-cases.md                  ← 翻车案例种子
│   ├── templates.md                      ← 用例模板种子
│   └── training-data.md                  ← 业务规则+范例种子
├── prompts/
│   ├── context-collector.md              ← Phase 0
│   ├── feature-documenter.md             ← Phase 0.5（条件触发，读经验库）
│   ├── test-architect.md                 ← Phase 1（打标签，读翻车案例）
│   ├── test-designer-flow.md             ← Phase 2a 流程类专员
│   ├── test-designer-param.md            ← Phase 2b 参数类专员
│   ├── test-designer-data.md             ← Phase 2c 数据类专员
│   ├── test-designer-combo.md            ← Phase 2d 组合类专员
│   ├── test-aggregator.md                ← Phase 2e 汇总员
│   ├── quality-gatekeeper.md             ← Phase 2 四层门禁（交叉校验）
│   ├── data-exporter.md                  ← Phase 3
│   └── experience-evolver.md             ← Phase 4 三类库
├── references/
│   ├── methodology.md                    ← 测试方法工具箱
│   ├── output-templates.md               ← Markdown/CSV 模板
│   └── naming-conventions.md             ← 命名规范单一事实来源
└── tools/
    ├── export_html.py                  ← HTML 测试报告（主输出）
    ├── export_csv.py                   ← CSV 导出（可选）
    └── export_md.py                    ← Markdown 导出（兼容）
```

---

## 触发方式

在 Qwen Code 中提及以下**强意图**关键词即可激活：
- 生成测试用例、写测试用例、设计测试用例
- 给我用例、输出测试用例

> ⚠️ 注：单纯问测试概念（如"等价类是什么意思"）不会触发此 Skill。

---

## 参考与致谢

本项目在设计和实现过程中，参考了以下优秀的思想和成果：

| 参考来源 | 作者 | 参考内容 |
|---------|------|---------|
| [如何用 HARNESS 的理念设计一个 AI 驱动的 UI 自动化工程](https://testerhome.com/articles/44066) | 孙高飞 | Harness 设计模式：角色边界、状态机、产物契约、护栏规则 |
| [5 层 AI 质量管理体系](https://testerhome.com/topics/44072) | 狂师 | L1-L5 五层质量管控框架：业务拆解→分类筛选→量化指标→三级审核→复盘闭环 |
| 《测试架构师修炼之道：从测试工程师到测试架构师》 | 刘琛梅 | 测试方法论：四步法、等价类、边界值、路径分析、正交分析等 |

在此向以上作者表示衷心感谢。

### 免责声明

本项目仅供学习和研究使用。若涉及侵权内容，请联系删除。
