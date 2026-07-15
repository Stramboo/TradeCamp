# TradeCamp 项目路线图

## Current Status

### 已实现功能

#### 🏗️ V2.1 架构重构（2026-07-15 完成）

| Goal | 内容 | 说明 |
|------|------|------|
| ✅ Goal 1 | 统一回测引擎 | 确定性回测 + 多标的 + 8 项一致性测试 |
| ✅ Goal 2 | 统一市场数据服务 | MarketDataService + Mock/Yahoo Provider 抽象层 |
| ✅ Goal 3 | 交易账本 | CashLedger 流水 + 持仓重建 + 资金对账 |
| ✅ Goal 4 | 交易计划与复盘 | TradePlan API + 下单前计划弹窗 + 卖出后复盘 |
| ✅ Goal 5 | AI 教练结构化反馈 | 四维评分（决策/执行/风险/归因）+ DeepSeek 增强 + CoachReview UI |
| ✅ Goal 6 | 核心 E2E 与部署 | 10 项 API E2E + 路由修复 + RELEASE.md 发布清单 |

#### 🅰️ 美股自动交易系统

| 模块 | 状态 | 说明 |
|------|------|------|
| 模拟券商 | ✅ | slippage / commission / T+1 / 部分成交 |
| Alpaca 实盘/模拟券商 | ✅ | 通过 `alpaca-py` SDK 接入 |
| 8 个交易策略 | ✅ | MACD / RSI / MA Trend / Bollinger / Multi / KDJ / Boll-width / Ensemble |
| 风控模块 | ✅ | 仓位上限 / 止损 / 移动止损 / 日交易上限 / ATR 止损 |
| 回测引擎 | ✅ | 独立 `backtest/` 模块，与交易引擎共用策略和风控 |
| 12 项回测指标 | ✅ | 年化收益 / 夏普 / 最大回撤 / 胜率 / Calmar / 等 |
| 回测 HTML 报告 | ✅ | 含净值曲线和交易明细 |
| PyQt5 桌面 GUI | ✅ | Dashboard / Trading / Strategy 三个标签，深/浅主题 |
| React + FastAPI Web 版 | ✅ | 前后端分离，WebSocket 实时推送 |
| Web 版 AI 教练 | ✅ | 段位系统、每日洞察、操作建议、风险预警 |
| Web 版 AI 推荐引擎 | ✅ | 多因子评分模型，每只股票综合评分 + 操作建议 |
| Web 版股市学习系统 | ✅ | 8 章课程 + 50+ 术语词典 + 新手引导 |
| 交易日志 | ✅ | Journal 页面，记录和回顾交易 |
| 用户数据持久化 | ✅ | SQLite（自选 / 告警 / 组合 / 日志 / 策略参数） |
| GitHub Actions CI | ✅ | push 自动跑 pytest + demos + GUI 截图 |

#### 🅱️ NASDAQ 每日分析报告

| 模块 | 状态 | 说明 |
|------|------|------|
| HTML 报告生成 | ✅ | ECharts 5 + Jinja2 暗色主题 |
| 10 大技术指标 | ✅ | MA / MACD / RSI / KDJ / BOLL / ATR / OBV / WR / CCI / VWAP |
| 趋势与信号分析 | ✅ | 支撑阻力 / 交易信号 / 投资建议 |
| 市场宽度分析 | ✅ | 涨跌比、市场情绪 |
| VIX 情绪分析 | ✅ | 恐慌指数解读 |
| 轻量策略回测 | ✅ | MACD+RSI+WR 组合策略 |
| 新闻情绪分析 | ✅ | 中英文金融词典法 |
| 板块轮动分析 | ✅ | 11 大行业 ETF + 4 宽基指数 |
| 历史报告对比 | ✅ | 与上一期报告的关键变化对比 |
| 港股/A股扩展 | ✅ | 通过 AKShare（默认关闭） |
| 多数据源 Provider | ✅ | yfinance / YahooDirectAPI / AKShare |
| SQLite 存储层 | ✅ | 价格快照 / 指标 / 报告 / 回测 / ML 预测 |
| Docker 容器化 | ✅ | 多阶段构建，python:3.11-slim |
| GitHub Actions 定时 | ✅ | 周一至周五 UTC21:00 自动生成 + gh-pages 发布 |
| SOLO 定时任务 | ✅ | 每周二至周六 北京时间 05:00 |

### 当前稳定能力

1. **每日自动报告**：两个渠道（GitHub Actions + SOLO Schedule）保证报告生成
2. **桌面交易**：PyQt5 GUI 可手动/自动交易（模拟/Alpaca）
3. **Web 交易**：React 网页版可在浏览器中进行模拟交易
4. **AI 教练**：每日简报 + 持仓体检 + 四维结构化反馈（S~D 等级）
5. **学习系统**：8 章入门课程 + 50+ 术语词典
6. **交易纪律**：下单前计划 + 卖出后复盘 + AI 教练评分

---

## Current Phase

### v2.1 架构重构已全部完成 🎉

六项 Goal 全部 merge 到 master，89 项测试全绿。核心改进：
- 回测引擎统一为 `backtest/engine.py`（确定性、多标的、一致性验证）
- 市场数据抽象层 `market_data/`（Mock/Yahoo 双 Provider）
- 交易账本 CashLedger 实现资金全程可追溯
- 交易纪律闭环：计划 → 执行 → 复盘 → AI 评分
- 10 项 API 级端到端测试覆盖全流程

### 当前主要目标

- 完善构建部署流程（Vercel + Render 部署 Web 版）

---

## Next Steps

### P0（必须）

- [x] 统一回测层：将报告系统的 `backtest.py`（根目录）迁移到使用 `backtest/engine.py` ✅ v2.1 Goal 1
- [x] 移除报告系统中与新引擎重复的代码 ✅ v2.1 Goal 1
- [x] 统一市场数据层 ✅ v2.1 Goal 2
- [x] 建立交易账本（CashLedger）✅ v2.1 Goal 3
- [x] 交易计划与复盘闭环 ✅ v2.1 Goal 4
- [x] AI 教练结构化反馈 ✅ v2.1 Goal 5
- [x] 核心 E2E 测试 ✅ v2.1 Goal 6

### P1（重要）

- [ ] **中联动**：交易系统策略以 NDX > MA200 作为开仓前置条件
- [ ] **重联动**：合并交易系统和报告系统的数据层（当前各自独立拉取数据）
- [ ] 部署到 Vercel（前端）+ Render（后端）
- [ ] 打包 Windows .exe 分发版本（PyInstaller）
- [ ] Web 前端集成 NASDAQ 每日报告展示

### P2（未来）

- [ ] 移动端适配（Web App PWA）
- [ ] 更多数据源接入（Bloomberg / FRED）
- [ ] 策略排行榜与回测对比页面
- [ ] 社区/分享功能

---

## Not Doing

以下功能**暂时不做**，避免范围失控：

- 实时交易信号推送至手机（短信/微信/Telegram）— 复杂度高，个人工具暂不需要
- 量化策略在线市场/策略商店 — 定位为个人工具
- 多用户/多账户管理 — 个人单用户场景
- 实时 Level 2 行情数据 — 需要昂贵的数据订阅
- 期权/期货/加密交易 — 专注美股现货
- 移动端原生 App（iOS/Android）— 优先 Web PWA
