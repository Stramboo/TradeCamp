# TradeCamp 发布检查清单

> 在发布新版本前的必要验证步骤。

---

## 🔍 代码质量

- [ ] 所有测试通过：`pytest tests/ -v`（当前：89 passed）
- [ ] 前端编译无新错误：`npx tsc --noEmit`（仅允许预存在的 4 个 errors）
- [ ] 后端启动正常：`python -m webapp.backend.server`（端口 8765）
- [ ] 前端启动正常：`.\webapp\scripts\dev.ps1`（端口 5173）

## 🧪 功能验证

- [ ] 沙盒交易完整流程：买入(含计划) → 卖出(含复盘) → AI教练评估
- [ ] 市场行情获取：`/api/market/batch?symbols=NVDA,AAPL`
- [ ] AI 推荐：`/api/advisor/recommendations`
- [ ] 自选列表 CRUD
- [ ] 学习进度：`/api/learning/progress`
- [ ] 任务系统：`/api/learning/quests`
- [ ] 成就徽章：`/api/learning/achievements`

## 🌍 环境隔离

| 模式 | 环境变量 | 说明 |
|------|---------|------|
| Demo | `NDXINFO_BACKEND=mock` | 模拟行情，开箱即用 |
| Test | `NDXINFO_BACKEND=real` | 真实数据，测试用 |
| Personal | `NDXINFO_BACKEND=real` + `DEEPSEEK_API_KEY=sk-...` | 完整功能 |

## 📦 发布步骤

1. **合并分支**：`git checkout master && git merge <feature-branch>`
2. **运行测试**：`pytest tests/ -v`
3. **更新 CHANGELOG**：记录本次发布内容
4. **更新版本号**：在 `CHANGELOG.md` 标记版本
5. **Tag 发布**：`git tag vX.Y.Z && git push --tags`
6. **CI 验证**：检查 GitHub Actions 状态

## 🔧 已知问题（不阻塞发布）

- TypeScript 预存 errors：`useNavigate`、`ws.ts:setWsStatus`、`vite.config.ts`（不影响功能）
- Windows 文件锁：test_cash_ledger/trade_plan teardown 时有 PermissionError（pytest 自动清理）
- MockEngine nanosecond 警告：`Discarding nonzero nanoseconds`（无害）

---

*最后更新：2026-07-15（Goal 1-6 完成版）*
