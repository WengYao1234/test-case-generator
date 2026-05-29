# 设计：test-case-generator 跨 Agent 平台支持

> 状态：已通过用户设计评审（待 spec 文件评审）
> 日期：2026-05-29
> 方案：A（单一事实源 + 平台档案）

---

## 1. 背景与目标

`test-case-generator` 是一个 **纯 prompt 驱动**的多 Agent 测试用例生成技能（markdown，无平台运行时代码）。当前与 Qwen Code 强耦合，目标是让它同时支持 **Qwen Code / Cursor / Claude Code / 通用 Agent**。

经探查，qwen 耦合点仅三类，且全部集中可控：

1. **prompt 中写死的 qwen 工具名**：`read_file` / `write_file` / `run_shell_command` / `grep_search`
2. **硬编码的全局兜底经验库路径**：`~/.qwen/skills/test-case-generator/experience/`
3. **README 安装/触发文档**：全部按 "Qwen Code" 编写

`SKILL.md` 格式本身已兼容各平台的 Agent Skills 机制（本仓库当前即作为 Cursor skill 加载），无需改造。

## 2. 设计原则

- **单一事实源（SSOT）**：平台差异集中到一张表，新增平台只改一处。
- **零重复**：不生成 per-platform 产物副本（不走构建流水线），避免 11 个 prompt × N 平台的漂移。
- **中立优先**：prompt 用平台中立的自然语言动词，agent 天然可映射；硬编码工具名才是 qwen 残留。

## 3. 组件设计

### 3.1 平台档案 SSOT — 新增 `references/platform-profiles.md`

权威表，定义每个平台的差异维度：

| 平台 | 全局技能根目录 | 安装目录 | 工具动词约定 | 触发方式 |
|------|---------------|---------|-------------|---------|
| Qwen Code | `~/.qwen/skills/` | `~/.qwen/skills/test-case-generator/` | read_file / write_file / run_shell_command / grep_search | 强意图关键词激活 |
| Cursor | `~/.cursor/skills/`（按版本探测） | `<root>/test-case-generator/` | Read / Write / Shell / Grep | 强意图关键词激活 |
| Claude Code | `~/.claude/skills/` | `<root>/test-case-generator/` | Read / Write / Bash / Grep | 强意图关键词激活 |
| 通用 | `<AGENT_HOME>/skills/` | 同上 | 自然语言动词（读取/写入/执行命令/搜索） | 取决于宿主 |

定义占位符约定：

- `<全局技能目录>` = 「当前平台全局技能根目录」+ `test-case-generator/experience/`
- 总控在「启动准备」第 0 步先读本表确定当前平台并解析占位符。

> 注：Cursor / Claude 的全局技能目录因版本而异（本机 Cursor 实为 `~/.cursor/skills-cursor/`）。档案表标注"按版本探测"，由 `install.py` 实际探测，不在 prompt 写死。

### 3.2 Prompt 工具名中立化

将所有写死的 qwen 工具名替换为平台中立动词，首次出现处指向档案表：

| 原 qwen 工具名 | 中立动词 |
|---------------|---------|
| `read_file` | 读取文件 |
| `write_file` | 写入文件 |
| `run_shell_command` | 执行命令 |
| `grep_search` | 全局搜索 |

涉及文件与位置：

- `SKILL.md` L24、L73、L158
- `references/context-budget.md` L11、L53、L63、L74
- `prompts/quality-gatekeeper.md` L24
- `prompts/test-aggregator.md` L21
- `prompts/feature-documenter.md` L27
- `prompts/test-architect.md` L33
- `prompts/experience-evolver.md` L166

### 3.3 全局路径去硬编码

`~/.qwen/skills/test-case-generator/experience/` → 占位符 `<全局技能目录>`（解析规则见档案表）。

涉及文件与位置：

- `SKILL.md` L22、L142
- `prompts/experience-evolver.md` L20
- `references/naming-conventions.md` L15、§8

总控「启动准备」新增第 0 步：读 `platform-profiles.md` → 识别当前平台 → 解析 `<全局技能目录>`。

### 3.4 多平台安装脚本 — 新增 `tools/install.py`

用法：`python tools/install.py [--agent cursor|qwen|claude] [--root <自定义skills目录>]`

行为：

1. 确定目标平台：`--agent` 显式指定；否则探测 `~/.cursor` / `~/.qwen` / `~/.claude` 存在性。
2. 解析该平台 skills 根目录（`--root` 可覆盖；否则按档案表 + 探测，找不到则报错并提示手动指定）。
3. 软链接（失败回退为复制）本技能目录到 `<root>/test-case-generator/`。
4. `mkdir experience/` 并从 `experience-seed/*.md` 播种（已存在则跳过，不覆盖）。
5. 打印该平台触发说明与产物目录位置。
6. 跨平台：用 `pathlib`，Windows 软链接失败自动回退复制；Python 命令探测沿用 `python3 → python → py -3` 约定。

### 3.5 README 多平台化

「环境要求 / 安装 / 触发方式」三节改为按平台分小节（Qwen / Cursor / Claude / 通用）。其余内容（设计理念、架构、流水线、经验闭环等）不变。新增一句指向 `tools/install.py` 一键安装。

### 3.6 naming-conventions.md 维护

- §1 目录表：全局路径行换成 `<全局技能目录>` 占位符 + "按平台档案解析"备注。
- §9/§10 修改清单：加入 `references/platform-profiles.md` 与 `tools/install.py`。

## 4. 数据流 / 控制流变化

唯一的运行时流程变化：总控「启动准备」在「定位经验库」之前，先读 `platform-profiles.md` 解析当前平台与 `<全局技能目录>`。其余 Phase 流程、产物契约、门禁逻辑 **完全不变**。

## 5. 不做什么（YAGNI）

- 不生成 per-platform 产物副本 / 构建流水线（方案 B 已否决）。
- 不在总控 prompt 里塞复杂的平台自动探测逻辑（探测放在 `install.py`，prompt 只读档案表）。
- 不改动任何测试方法论、Phase 流程、门禁指标、导出脚本逻辑。

## 6. 验收标准

1. `grep -r "read_file\|write_file\|run_shell_command\|grep_search"` 在 prompt/SKILL/context-budget 中无残留（档案表内作为"对应工具名"举例除外）。
2. `grep -r "~/.qwen"` 仅出现在 `platform-profiles.md`（作为 qwen 平台条目）。
3. `references/platform-profiles.md` 存在且包含 4 个平台条目。
4. `tools/install.py` 存在，`--agent cursor|qwen|claude` 三个分支可运行，自动探测分支可运行。
5. README 含 4 个平台的安装小节。
6. 现有 qwen 用户行为不回归：qwen 工具名仍能从中立动词正确映射（中立动词对 qwen agent 无歧义）。
