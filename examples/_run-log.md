# 运行账本 — 用户登录

> 样例：标准模式完整流水线的控制面账本（会话级，实跑时位于 `artifacts/_run-log.md`）。含一次门禁 FAIL→retry 演示。

| 时间 | Phase | Agent | 状态 | 产物 | retry | 备注 |
|------|-------|-------|------|------|-------|------|
| 16:01 | 0 | context-collector | DONE | _context.md | 0 | 模块=用户登录 |
| 16:02 | 0.5 | feature-documenter | DONE | _feature-doc.md | 0 | 8节 |
| 16:03 | 1 | test-architect | DONE | _analysis.md | 0 | 测试点42 |
| 16:05 | 2a-2d | 四专员(并行) | DONE×4 | _test-cases-{flow,param,data,combo}.md | 0 | |
| 16:07 | 2e | test-aggregator | DONE | _test-cases.md | 0 | 用例58 |
| 16:08 | 2 gate | quality-gatekeeper | FAIL→retry1 | _verification-phase2.md | 1 | 废弃率18% |
| 16:09 | 2e | test-aggregator | DONE | _test-cases.md | 1 | 去重后用例51 |
| 16:10 | 2 gate | quality-gatekeeper | PASS | _verification-phase2.md | 1 | 废弃率12% |
| 16:11 | 3 | data-exporter | DONE | output/用户登录_测试报告.html | 0 | |
| 16:11 | 3 出口 | 总控(机械校验) | PASS | — | 0 | HTML非空/结构齐 |
| 16:12 | 4 | experience-evolver | DONE | _experience-result.md | 0 | 翻车+2 模板+3 |
