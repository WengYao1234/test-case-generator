# 样例输出

本目录包含一组端到端样例：从 `input/需求描述.md` 出发，经完整流水线产出的交付物。

- `input/需求描述.md` — 一段简洁的功能描述（模拟用户输入）
- `output/用户登录_测试报告.html` — 主交付物：自包含交互式 HTML 测试报告（仪表盘 + 搜索/筛选/排序/CSV 下载）
- `output/测试设计文档.md` — 兼容输出：Markdown 测试设计文档
- `output/测试用例.csv` — 兼容输出：CSV 用例文件
- `_run-log.md` — 控制面样例：总控运行账本（会话级，实跑时位于 `artifacts/_run-log.md`，非交付物，仅供观测）

## 运行方式

将 `input/需求描述.md` 的内容粘贴到对话中（或让 context-collector 读取它），触发 skill 即可复现本样例。
