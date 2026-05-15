---
name: 经验库种子索引
description: 脱敏的通用经验库种子，首次使用时复制到 experience/ 目录启动经验闭环
type: project
created: 2026-05-14
last_updated: 2026-05-15
---

## 经验库文件

| 文件 | 描述 | 条目数 |
|------|------|--------|
| [failure-cases.md](failure-cases.md) | 翻车案例与教训 | 5 条 |
| [templates.md](templates.md) | 优质用例格式模板 | 8 类 |
| [training-data.md](training-data.md) | 业务规则 + 优质用例范例 | 规则12条 + 范例5条 |

## 版本摘要

### failure-cases.md (5条)
- 等价类拆分过细部分复现（粒度合规率86.4%）
- 反向用例分布严重不均（数据类反向仅14%）
- 前置条件引用链断裂（FLOW-044引用FLOW-043状态不连续）
- L1 废弃率过高（等价类枚举值拆成独立用例）
- HS-05 归并窗口重叠遗漏

### templates.md (8类)
- 全链路E2E端到端模板
- 完整生命周期CRUD模板
- 边界值测试模板
- 枚举完整性模板
- 状态流转模板
- 过滤规则顺序执行模板（首命中即终止的串行规则验证）
- 归并窗口聚合模板（时间窗口分组聚合+窗口边界行为）
- 弹窗取消三方式验证模板（取消按钮/×/遮罩层全覆盖）

### training-data.md (12条规则 + 5条范例)
- 12 条业务规则（BR-01~BR-12）
- 5 条优质用例范例（含选用理由）
- 3 条已确认反模式（禁止参照）

## 使用方式

首次使用 test-case-generator 时，将 `experience-seed/` 下所有 `.md` 文件复制到项目根目录的 `experience/` 目录：

```bash
cp experience-seed/*.md experience/
```

之后经验库将由 Phase 4 experience-evolver 自动增量更新。
