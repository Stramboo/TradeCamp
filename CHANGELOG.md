# Changelog

记录用户可感知的重要变化。

## Unreleased

### v2.2 — Phase 1 Simplify (2026-07-15)

- **教学化一级导航**：从 13 个入口缩减为 5 项（今日 / 学习 / 世界市场 / 模拟练习 / 我的成长）
- **新的今日首页**：回答「今天应该做什么」，展示学习阶段 + 主任务 + 唯一主按钮 + 可选探索任务
- **世界市场探索页**：展示 5 个主要市场（美国/中国/香港/日本/欧洲），含简易交易时段指示
- **模拟练习入口**：三层模式引导（引导式练习已可用，情景训练和自由模拟标记为"即将开放"）
- **我的成长页**：学习等级、XP 进度条、章节/任务统计、成就徽章
- **引导式模拟交易**：五步引导（选公司 → 了解 → 理由 → 仓位 → 下单）
- **Header 简化**：移除真实账户切换器，仅保留模拟账户余额
- **AI 推荐降级**：从一级导航移除，折叠到底部"更多工具"，保留 `/advisor` 路由兼容
- **旧路由全保留**：`/trading`、`/desk`、`/analysis`、`/strategy`、`/portfolio`、`/journal`、`/logs` 等均可直接访问

### Added
- **DeepSeek LLM 增强 AI 推荐**：接入 DeepSeek API（OpenAI 兼容），为每只股票生成专业分析师级别文字点评。通过 `DEEPSEEK_API_KEY` 环境变量或 `.env` 文件控制，无 key 时自动降级回因子拼接理由
- **`.env` 自动加载**：server.py 启动时自动从项目根目录读取 `.env`，无需手动 `$env:` 设置
- **新手实践学习系统全面增强**：
  - 沙盒交易价格连接真实行情（MockEngine/yfinance），告别 $150 硬编码
  - 13 个结构化学习任务（Quests），含 8 种检测类型（买入/卖出/盈利/日志/分散/仓位/图表/分析）
  - 沙盒数据 SQLite 持久化，刷新不丢失
  - 卖出后自动弹出复盘引导 → 快速记录交易日志
  - 学习进度仪表盘（等级/XP/章节环/任务统计/连续学习天数）
  - 10 枚成就徽章定义
- AI 教练系统：每日简报、持仓体检、段位评估、操作建议
- AI 推荐引擎：5 因子加权评分模型（趋势30%+动量25%+反转20%+量价15%+波动10%）
- 股市学习系统：8 章入门课程 + 50+ 术语词典 + 新手引导
- Web 版组合管理页面（Portfolio）
- Web 版交易日志页面（Journal）
- Web 版专用交易面板（TradingDesk）
- NDX 大盘分析页面（Analysis）：将 NASDAQ 报告数据整合到 Web 前端

### Changed
- README 重写为面向新手的介绍风格
- CI：为 Windows runner 设置 `PYTHONIOENCODING=utf-8` 防止中文编码报错
- MockEngine 新增 `fetch_history()` 方法，支持 AI 推荐在 mock 模式下获取模拟 K 线数据
- `generate_daily_recommendations_from_engine()` 兼容 MockEngine 和 EngineAdapter 两种引擎

### Fixed
- AI 推荐 `/api/advisor/recommendations` 在 mock 模式下因 AttributeError 返回 500
- `learning_content.py` QUESTS 断言数值从 13 修正为 11

---

## Previous Versions

### v2.0 — 2026-07-14

#### Added
- **美股自动交易系统**（新子系统）：
  - 模拟券商 + Alpaca 实盘券商
  - 8 个交易策略（MACD / RSI / MA Trend / Bollinger / Multi / KDJ / Boll-width / Ensemble）
  - 风控模块（仓位上限 / 止损 / 移动止损 / ATR 止损）
  - 独立回测引擎（`backtest/`）与 12 项评估指标
  - PyQt5 桌面 GUI（深/浅主题，Dashboard / Trading / Strategy）
  - React 18 + FastAPI Web 版（前后端分离，WebSocket 实时推送）
  - 交易系统与报告系统轻联动（Dashboard 显示 NDX 状态）
- GitHub Actions CI（smoke workflow）：pytest + demos + GUI 截图 + 主题切换验证

### v1.1 — 2026-07-13

#### Added
- 5 个新增技术指标：ATR / OBV / WR / CCI / VWAP（总计 10 个）
- 轻量回测引擎（`backtest.py`）：MACD+RSI+WR 组合策略
- 新闻情绪分析（`sentiment.py`）：中英文金融词典法
- 板块轮动分析（`sector.py`）：11 大行业 ETF + 4 宽基指数
- 历史报告对比（`comparison.py`）：与上期报告的关键变化
- 多数据源 Provider 架构（`providers/`）：yfinance / YahooDirectAPI / AKShare
- SQLite 存储层（`db.py`）：价格 / 指标 / 报告 / 回测 / 预测持久化
- ML 价格预测模块（`ml_predictor.py`）：Prophet + sklearn 备选
- Docker 容器化（多阶段构建）
- GitHub Actions 每日定时报告工作流
- Feature Flags 机制（`ENABLE_*` 环境变量控制各功能开关）

#### Changed
- `data_fetcher.py` 重构为 Facade，路由多 Provider
- 报告模板支持可折叠副图和新指标展示

### v1.0 — 2026-07-13

#### Added
- NASDAQ 每日分析报告程序初版
- 5 个基础技术指标：MA(5/10/20/60) / MACD / RSI / KDJ / BOLL
- 趋势分析、支撑阻力位、交易信号生成
- VIX 情绪分析、市场宽度分析
- 12 只重点美股（3 个板块）推荐系统
- NASDAQ 涨幅榜动态筛选
- Jinja2 + ECharts 5 暗色主题 HTML 报告
- 10 步主流程（`nasdaq_analyzer.py`）
- SOLO 定时任务每日自动执行
