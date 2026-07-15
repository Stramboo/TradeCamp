# TradeCamp 系统架构

## Overview

TradeCamp 是两个子系统的组合项目，共享部分模块但保持独立运行：

```
┌─────────────────────────────────────────────────────────────┐
│                       TradeCamp                              │
│                                                               │
│  ┌──────────────────────┐   ┌──────────────────────────────┐ │
│  │  🅰️ 交易系统           │   │  🅱️ 每日分析报告              │ │
│  │                      │   │                              │ │
│  │  PyQt5 Desktop  ←──┐ │   │  SOLO Schedule              │ │
│  │  React WebApp ←──┐ │ │   │  GitHub Actions (cron)      │ │
│  │                  │ │ │   │         │                    │ │
│  │  ┌───────────────▼─▼─┐ │   │  nasdaq_analyzer.py       │ │
│  │  │  trading/ engine   │ │   │       │                    │ │
│  │  │  broker / strategy │ │   │  ┌────▼─────────────┐     │ │
│  │  │  risk / executor   │ │   │  │ data_fetcher.py  │     │ │
│  │  └────────┬──────────┘ │   │  │ (Facade)         │     │ │
│  │           │             │   │  └────┬─────────────┘     │ │
│  │  ┌────────▼──────────┐ │   │       │                    │ │
│  │  │  backtest/ engine  │ │   │  ┌────▼─────────────┐     │ │
│  │  └───────────────────┘ │   │  │ providers/        │     │ │
│  │                         │   │  │ yfinance / direct │     │ │
│  │  ┌───────────────────┐ │   │  │ akshare           │     │ │
│  │  │  webapp/backend    │◄┼───┼──┤ ndx_adapter      │     │ │
│  │  │  coach / advisor   │ │   │  └────┬─────────────┘     │ │
│  │  │  learning          │ │   │       │                    │ │
│  │  └───────────────────┘ │   │  ┌────▼─────────────┐     │ │
│  └──────────────────────┘   │  │ indicators /       │     │ │
│                              │  │ analysis           │     │ │
│              ▲               │  └────┬─────────────┘     │ │
│              │ 轻联动 (HTTP)   │       │                    │ │
│              └───────────────┼───────┘                    │ │
│                              │  ┌────▼─────────────┐     │ │
│                              │  │ report_generator  │     │ │
│                              │  │ + Jinja2 模板     │     │ │
│                              │  └────┬─────────────┘     │ │
│                              │       │                    │ │
│                              │  ┌────▼─────────────┐     │ │
│                              │  │ HTML Report       │     │ │
│                              │  │ + echarts.min.js  │     │ │
│                              │  └──────────────────┘     │ │
│                              └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

- **🅰️ 交易系统**与 **🅱️ 报告系统**是两个独立的子系统
- 联动方式：交易系统的 WebApp 通过 `NdxAdapter` 调用报告系统的数据模块，在 Dashboard 顶部展示 NDX 大盘状态
- 共享模块：`indicators.py`（被两个子系统共用）、`providers/`（报告系统独占，但 NdxAdapter 桥接）

---

## Tech Stack

### 报告系统（🅱️）

| 层 | 技术 | 说明 |
|----|------|------|
| 语言 | Python 3.10+ | |
| 数据获取 | yfinance, Yahoo Direct API, AKShare | 多数据源 Provider 模式 |
| 数据处理 | pandas, numpy | 纯 pandas 技术指标计算 |
| 报告模板 | Jinja2 | 服务端渲染 HTML |
| 图表 | ECharts 5 (echarts.min.js) | 前端渲染，本地文件优先 + CDN 回退 |
| 存储 | SQLite (sqlite3 stdlib) | 价格快照、指标、报告元数据 |
| 容器 | Docker (python:3.11-slim) | 多阶段构建 |
| CI/CD | GitHub Actions (cron + gh-pages) | 定时生成 + 静态发布 |
| 调度 | SOLO Schedule | 独立定时任务兜底 |

### 交易系统（🅰️）

| 层 | 技术 | 说明 |
|----|------|------|
| 语言 | Python 3.10+ (后端), TypeScript (前端) | |
| 桌面 GUI | PyQt5 + pyqtgraph | Windows 原生窗口 |
| Web 后端 | FastAPI + uvicorn + WebSocket | REST API + 实时推送 |
| Web 前端 | React 18 + Vite 5 + Tailwind CSS 3 | SPA |
| 状态管理 | Zustand | 前端 store |
| K线图 | TradingView Lightweight Charts | Web 版图表 |
| 券商 API | alpaca-py | 实盘/模拟交易 |
| 配置 | YAML (config/default.yaml) | 通过环境变量覆盖 |
| CI | GitHub Actions (Windows runner) | pytest + demos + GUI 截图 |

---

## Directory Structure

```
TradeCamp/
│
├── 🅱️ NASDAQ 每日报告子系统
│   ├── nasdaq_analyzer.py       # 主入口：10 步流程串联所有模块
│   ├── config.py                # 集中配置（股票池、指标参数、Feature Flags）
│   ├── data_fetcher.py          # 数据获取 Facade，按 ticker 前缀路由 Provider
│   ├── providers/               # 数据提供者抽象层
│   │   ├── base.py              # DataProvider 协议
│   │   ├── yfinance_provider.py # 美股/指数数据
│   │   ├── yahoo_direct_provider.py # Yahoo Finance JSON API（绕过 yfinance 库）
│   │   └── akshare_provider.py  # 港股/A股/新闻数据
│   ├── indicators.py            # 10 大技术指标（纯 pandas）
│   ├── analysis.py              # 趋势/支撑阻力/信号/宽度/VIX 情绪
│   ├── report_generator.py      # Jinja2 渲染 → HTML 报告
│   ├── templates/               # HTML 报告模板
│   │   └── report_template.html
│   ├── backtest.py              # 报告器内轻量回测（⚠️ 与 backtest/ 不同）
│   ├── sentiment.py             # 新闻情绪分析（词典法）
│   ├── sector.py                # 板块轮动分析（11 行业 ETF）
│   ├── comparison.py            # 历史报告对比
│   ├── ml_predictor.py          # ML 价格预测（Prophet/sklearn，可选）
│   ├── db.py                    # SQLite 存储层
│   ├── echarts.min.js           # ECharts 5 库（~1MB）
│   ├── reports/                 # 历史报告归档
│   ├── data/                    # SQLite 数据库文件
│   ├── Dockerfile               # 容器镜像构建
│   └── .dockerignore
│
├── 🅰️ 交易子系统
│   ├── trader.py                # PyQt5 桌面入口（argparse CLI）
│   ├── trading/                 # 交易内核
│   │   ├── trading_engine.py    # 主引擎：券商 + 策略 + 风控 + 执行
│   │   ├── broker.py            # 券商抽象（Simulation / Alpaca）
│   │   ├── strategy.py          # 策略模式：StrategyBase + 8 个策略
│   │   ├── risk_manager.py      # 风控（仓位/止损/日上限/ATR）
│   │   ├── executor.py          # 订单执行管道
│   │   ├── market_data.py       # 行情数据管理
│   │   ├── persistence.py       # 状态持久化（engine-restart 恢复）
│   │   ├── observability.py     # 日志/指标收集
│   │   ├── config_loader.py     # YAML 配置加载
│   │   ├── config_models.py     # 配置数据模型
│   │   ├── data_cache.py        # 行情缓存（内存）
│   │   ├── rate_limiter.py      # API 限流
│   │   ├── sim_rules.py         # 模拟交易规则（滑点/手续费/T+1）
│   │   ├── hot_reload.py        # 配置热更新
│   │   └── errors.py            # 自定义异常
│   ├── backtest/                # 独立回测引擎
│   │   ├── engine.py            # BacktestEngine（逐bar + 策略 + 风控）
│   │   ├── portfolio.py         # 组合追踪
│   │   ├── metrics.py           # 12 项评估指标
│   │   ├── reporter.py          # HTML 回测报告
│   │   ├── cli.py               # 回测 CLI
│   │   └── legacy.py            # 兼容层
│   ├── gui/                     # PyQt5 桌面 GUI
│   │   ├── main_window.py       # 主窗口（3 标签 + 系统托盘）
│   │   ├── dashboard_tab.py     # 总览标签（账户/持仓/净值曲线）
│   │   ├── trading_tab.py       # 交易标签（K线/下单/订单）
│   │   ├── strategy_tab.py      # 策略标签（策略选择/参数/权重）
│   │   ├── chart_widget.py      # pyqtgraph K 线图
│   │   ├── styles.py            # 深/浅主题系统
│   │   ├── notify.py            # 系统托盘通知
│   │   ├── state_store.py       # GUI 状态管理
│   │   ├── utils.py             # GUI 工具函数
│   │   └── widgets/             # 自定义控件
│   │       ├── crosshair.py     # 十字光标
│   │       └── filter_proxy.py  # 表格过滤代理
│   ├── webapp/                  # React + FastAPI Web 版
│   │   ├── backend/
│   │   │   ├── server.py        # FastAPI 入口 + REST + WebSocket
│   │   │   ├── coach.py         # AI 教练（段位/洞察/建议/预警）
│   │   │   ├── ai_advisor.py    # AI 推荐引擎（多因子评分）
│   │   │   ├── learning_content.py # 学习内容（8 章课程 + 50+ 术语）
│   │   │   ├── userstore.py     # 用户数据 SQLite 持久化
│   │   │   └── adapters/        # 引擎适配器
│   │   │       ├── mock_engine.py    # 模拟行情引擎（离线演示）
│   │   │       ├── engine_adapter.py # 真实 TradingEngine 适配器
│   │   │       ├── event_bus.py      # 事件总线（pub/sub → WebSocket）
│   │   │       └── ndx_adapter.py    # NDX 分析数据桥接（轻联动）
│   │   ├── frontend/
│   │   │   ├── src/
│   │   │   │   ├── App.tsx           # 路由配置（14 个路由）
│   │   │   │   ├── components/       # Header / Sidebar / LearningNav
│   │   │   │   ├── features/         # 15 个业务组件
│   │   │   │   ├── routes/           # 12 个页面
│   │   │   │   ├── lib/              # API / WebSocket / utils
│   │   │   │   ├── store/            # Zustand stores
│   │   │   │   └── styles/           # Tailwind CSS
│   │   │   └── index.html
│   │   ├── scripts/              # 启动脚本（dev.ps1 / dev.sh）
│   │   └── screenshots/          # 页面截图（PNG）
│   ├── examples/                 # 8 个 demo 脚本 + 一键批处理
│   ├── tests/                    # pytest 单元测试（7 个文件）
│   └── config/default.yaml       # 交易系统 YAML 配置
│
├── .github/workflows/            # GitHub Actions
│   ├── smoke.yml                 # CI：pytest + demos + GUI 截图
│   └── daily-report.yml          # 定时 NASDAQ 报告生成 + gh-pages
│
├── README.md                     # 项目总览
├── ROADMAP.md                    # 项目路线图
├── ARCHITECTURE.md               # 本文件
├── DECISIONS.md                  # 技术决策记录
├── CHANGELOG.md                  # 变更日志
├── AGENTS.md                     # AI Agent 开发规则
├── LICENSE                       # MIT
└── .trae/documents/              # 内部设计文档
```

### 路径注意事项

- **回测已统一**（v2.1）：`nasdaq_analyzer.py` 已迁移到 `backtest/engine.py`。根目录 `backtest.py` 保留为历史参考（无调用方），`backtest/legacy.py` 提供兼容包装。所有新回测走 `from backtest.engine import BacktestEngine`。固定测试数据在 `tests/fixtures/market_data/*.csv`，一致性测试在 `tests/test_backtest_consistency.py`。
- **两个 config**：根目录的 `config.py`（报告系统配置，Python 常量）和 `config/default.yaml`（交易系统配置，YAML + 环境变量覆盖），互不冲突。
- **两个数据库**：`data/nasdaq.db`（报告系统）和 `data/userdata.db`（WebApp 用户数据），独立管理。

---

## Data Flow

### 🅱️ 报告生成数据流

```
Yahoo Finance API ─┐
Yahoo Direct API ──┼──→ providers/ ──→ data_fetcher.py (Facade)
AKShare ───────────┘                         │
                                              ▼
                                     nasdaq_analyzer.py
                                     │  │  │  │  │
                                     ▼  ▼  ▼  ▼  ▼
                          indicators  analysis  sentiment  sector  comparison
                              │           │          │        │        │
                              └───────────┴──────────┴────────┴────────┘
                                              │
                                              ▼
                                     report_data (dict)
                                              │
                                              ▼
                              report_generator.py ──→ Jinja2 模板
                                              │
                                              ▼
                                    nasdaq_report_YYYY-MM-DD.html
                                    + echarts.min.js (copy)
                                    + reports/ 归档
                                    + data/nasdaq.db 写入
```

### 🅰️ 交易系统数据流

```
券商 API (Alpaca) ─┐
Yahoo Finance ─────┼──→ market_data.py ──→ data_cache.py
本地模拟行情 ──────┘                              │
                                                  ▼
                                          trading_engine.py
                                          │   │   │   │
                                          ▼   ▼   ▼   ▼
                                    broker  strategy  risk_manager
                                      │       │           │
                                      │       ▼           │
                                      │   generate_signal │
                                      │       │           │
                                      ▼       ▼           ▼
                                    executor.py ──→ 订单执行
                                          │
                                          ▼
                              ┌──────────────────────┐
                              │  PyQt5 GUI            │  ← 桌面入口
                              │  React WebApp         │  ← 浏览器入口
                              │  (WebSocket 实时推送)  │
                              └──────────────────────┘
```

### 联动数据流（轻联动）

```
🅱️ 报告系统                              🅰️ 交易系统 WebApp
data_fetcher.py ──→ ndx_adapter.py ──→ FastAPI /api/market/ndx ──→ NdxStatusBar
                                   (缓存 300s)           (Dashboard 顶部)
```

---

## Important Design Choices

### 1. 两个子系统分离但共享

交易系统和报告系统各自有独立的入口、配置、数据流。共享模块仅限于无副作用的纯函数模块（`indicators.py`），联动通过 HTTP API 桥接而非代码耦合。

### 2. Feature Flags 体系

报告系统通过 `ENABLE_*` 环境变量控制所有可选模块。`nasdaq_analyzer.py` 主流程中每个模块用 `if ENABLE_XXX:` 包裹，单个失败不阻断主流程。

### 3. Provider 模式

数据获取采用 Facade + Provider 模式。`data_fetcher.py` 根据 ticker 前缀（`HK:`, `SH:`, 美股无前缀）路由到不同 Provider。CI 环境还可切换 `USE_DIRECT_API` 绕过 yfinance 库的限制。

### 4. 策略模式

交易策略基于 `StrategyBase` 抽象基类，所有策略实现 `generate_signal()` 方法。回测引擎和实盘引擎共用相同的策略类，确保回测结果与实盘行为一致。

### 5. 两种 UI 并存

交易系统同时提供 PyQt5 桌面端和 React Web 端，共享同一套 `trading/` 业务逻辑。Web 端通过适配器层（`engine_adapter.py`）桥接。

### 6. 模拟券商设计

模拟券商实现了真实券商的完整约束：滑点、手续费、T+1 结算、部分成交、市价单/限价单。这些规则通过 `sim_rules.py` 的规则对象配置，可在运行时切换。
