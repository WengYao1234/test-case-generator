# 平台档案 — Single Source of Truth

> **此文件是本技能"跨 Agent 平台差异"的唯一权威来源。**
> 本技能是纯 prompt 驱动的 Agent Skill，`SKILL.md` 格式本身兼容各主流 Agent。
> 平台之间只有三类差异：**工具动词命名 / 全局技能目录 / 安装与触发方式**。全部集中在本表。
> 新增一个平台 = 只在本表加一行 + 在 `tools/install.py` 加一个分支。

---

## 1. 平台差异表

| 平台 | 全局技能根目录 | 安装目录 | 工具动词对应 | 触发方式 |
|------|---------------|---------|-------------|---------|
| **Qwen Code** | `~/.qwen/skills/` | `~/.qwen/skills/test-case-generator/` | read_file / write_file / run_shell_command / grep_search | 强意图关键词激活 |
| **Cursor** | `~/.cursor/skills/`（按版本探测，亦可能为 `~/.cursor/skills-cursor/`） | `<root>/test-case-generator/` | Read / Write / Shell / Grep | 强意图关键词激活 |
| **Claude Code** | `~/.claude/skills/` | `<root>/test-case-generator/` | Read / Write / Bash / Grep | 强意图关键词激活 |
| **通用 Agent** | `<AGENT_HOME>/skills/` | `<root>/test-case-generator/` | 自然语言动词（读取文件 / 写入文件 / 执行命令 / 全局搜索） | 取决于宿主 Agent |

> Cursor / Claude 的全局技能目录因客户端版本而异，**不在 prompt 里写死**，由 `tools/install.py` 实际探测（`--root` 可手动覆盖）。

---

## 2. 工具动词约定（Tool Verb Convention）

各 prompt、`SKILL.md`、`references/context-budget.md` 一律使用 **平台中立动词**，不写死任何单一平台的工具名。各 Agent 按本表把中立动词映射到自己平台的实际工具：

| 中立动词 | Qwen Code | Cursor | Claude Code | 含义 |
|---------|-----------|--------|-------------|------|
| **读取文件** | `read_file` | `Read` | `Read` | 读取文件内容 |
| **写入文件** | `write_file` | `Write` | `Write` | 写入/创建文件 |
| **执行命令** | `run_shell_command` | `Shell` | `Bash` | 运行 shell 命令 |
| **全局搜索** | `grep_search` | `Grep` | `Grep` | 按正则/关键词搜索代码 |

> 在任何 prompt 中读到「读取文件 / 写入文件 / 执行命令 / 全局搜索」时，使用当前平台对应的工具即可。

---

## 3. 占位符约定（Path Placeholders）

| 占位符 | 含义 | 解析方式 |
|--------|------|---------|
| `<全局技能目录>` | 全局兜底经验库根 | =「本表第 1 节当前平台的全局技能根目录」+ `test-case-generator/experience/`。例：Qwen Code → `~/.qwen/skills/test-case-generator/experience/` |
| `<root>` | 当前平台 skills 安装根 | 见本表第 1 节「全局技能根目录」列 |

总控在「启动准备」最开始先读本表，确定当前平台并解析 `<全局技能目录>`，再进入经验库定位。无法确定平台时，默认按"通用 Agent"处理：仅用项目级 `experience/`，跳过全局兜底。

---

## 4. 新增平台清单

要支持一个新平台，依次：

1. 本表第 1 节加一行（全局技能根目录 / 安装目录 / 触发方式）。
2. 本表第 2 节工具动词表加一列（该平台四个工具的实际名称）。
3. `tools/install.py` 的 `PLATFORMS` 映射加一个条目。
4. `README.md` 安装小节加一段。

无需改动任何 prompt 主体——这正是中立动词 + 占位符设计的价值。
