# 🏕️ TradeCamp — 新手的股票交易训练营

<p align="center">
  <strong>📖 学 → 🧪 练 → 📊 看 → 🤖 模拟 → 💰 真刀真枪</strong>
</p>

<p align="center">
  从零开始学炒股的开源工具箱 —— 内置 8 章教程、AI 教练、模拟交易、每日大盘分析报告
</p>

<p align="center">
  <a href="#-快速开始">快速开始</a> ·
  <a href="#-学习路线">学习路线</a> ·
  <a href="#-项目导航">项目导航</a> ·
  <a href="#-贡献">贡献</a> ·
  <a href="CONTRIBUTING.md">贡献指南</a>
</p>

---

## 为什么会有 TradeCamp？

每个新手学炒股都会遇到同样的问题：

> "我想学炒股，但不知道从哪里开始。看书太抽象，直接拿真钱练太冒险，看别人操作又看不懂。"

TradeCamp 就是答案。它把学炒股变成了一场**训练营体验**：

- **不用真金白银**——内置模拟券商，滑点、手续费、T+1 全都模拟，零风险练习
- **不用啃书**——8 章入门课程 + 50+ 术语词典，从 K 线到风控，循序渐进
- **有 AI 教练**——每天自动分析你的操作，给段位评估和改进建议
- **能看真实市场**——每天自动生成 NASDAQ 大盘分析报告，用真实数据学技术分析

---

## 🗺️ 学习路线

TradeCamp 引导你走过完整的四阶段学习路径：

```
第 1 阶段         第 2 阶段          第 3 阶段          第 4 阶段
📖 理论学习      🧪 回测验证       🤖 模拟实盘        💰 真实交易

 学 K 线          用历史数据         模拟券商           连接 Alpaca
 学指标          验证策略思路       零风险下单          Paper Trading
 学课程          看回测报告          AI 教练点评         真·真金白银
 背术语          理解胜率回撤       看懂大盘报告        策略上线
```

| 阶段 | 你在做什么 | 用 TradeCamp 的什么 |
|------|-----------|-------------------|
| 📖 理论 | 学习 K 线、MACD、RSI 等基础概念 | Web 版 → 学习 + 术语词典 |
| 🧪 回测 | 用历史数据验证"如果我按 MACD 金叉买会怎样" | 回测引擎 → 12 项指标报告 |
| 🤖 模拟 | 用模拟券商零风险练手，AI 教练每天给反馈 | Web 版 → 交易 + AI 教练 |
| 💰 实盘 | 申请 Alpaca 账号，用虚拟资金练，再上真资金 | 交易引擎 → Alpaca Paper/Real |

---

## 📦 里面有什么

### 🎓 学习系统（Web 浏览器打开即用）

12 个页面，从学到练一站式：

| 页面 | 干什么用 |
|------|---------|
| 📖 学习 | 8 章股市入门课程：K 线基础 → 技术指标 → 交易心理 |
| 📚 术语 | 50+ 专业术语词典，随时查 |
| 🤖 AI 教练 | 段位评估、每日简报、持仓体检、操作建议 |
| 📊 Dashboard | 账户总览、净值曲线、持仓一览 |
| 📈 交易 | K 线图 + 下单面板 |
| 🧠 交易桌面 | AI 多因子推荐引擎 |
| 🔬 分析 | NASDAQ 大盘完整技术分析 |
| ⚙️ 策略 | 8 种交易策略可选 + 风控参数 |
| 💼 组合 | 持仓管理与分析 |
| 📝 日志 | 记录每笔交易，复盘成长 |
| 📡 实时日志 | WebSocket 实时推送 |
| 🎛️ 设置 | 主题切换 / 券商切换 |

### 📊 每日大盘报告（自动生成）

每天一份专业级 HTML 报告，涵盖：
- **10 大技术指标**：MA / MACD / RSI / KDJ / BOLL / ATR / OBV / WR / CCI / VWAP
- **趋势分析**：支撑阻力位、交易信号、投资建议
- **市场宽度**：涨跌比、市场情绪
- **VIX 恐慌指数**：市场恐慌程度
- **板块轮动**：11 大行业 ETF 资金流向
- **新闻情绪**：中英文金融词典情感分析

### 🧠 AI 教练

不用请老师，AI 教练自动帮你：
- **段位评估**：根据你的交易记录给你评段（青铜 → 王者）
- **每日简报**：今天市场发生了什么，对你意味着什么
- **持仓体检**：你手上股票有没有问题？
- **风险预警**：仓位太重？止损太远？教练提醒你

### 🏦 模拟券商

内置专业级模拟券商，完整模拟真实交易环境：
- 滑点、手续费、T+1 结算
- 市价单 / 限价单
- 部分成交

---

## 🚀 快速开始

### 第一步：装依赖

```powershell
# Python（核心）
pip install -r requirements.txt

# Web 版额外需要
pip install fastapi uvicorn[standard] websockets
```

### 第二步：打开浏览器，开始学

```powershell
# Web 版（推荐新手从这里开始）
.\webapp\scripts\dev.ps1
# → 浏览器打开 http://127.0.0.1:5173
```

打开后直接点「学习」开始第一章，或点「术语」查你不懂的概念。

### 第三步：生成一份大盘报告看看

```powershell
python nasdaq_analyzer.py
# → 自动拉取 NASDAQ 数据 → 分析 → 生成 HTML 报告
# → 浏览器打开就能看到专业的图表和分析
```

### 进阶：想试试桌面版？

```powershell
python trader.py
# → PyQt5 原生 Windows 窗口，高性能 K 线图
```

---

## 📸 界面预览

| Dashboard | 交易面板 | 学习系统 |
|:---:|:---:|:---:|
| 账户 + 持仓 + 净值 | K 线 + 下单 | 8 章课程 |

| 策略配置 | AI 教练 | 大盘分析 |
|:---:|:---:|:---:|
| 8 策略 + 权重 | 段位 + 建议 | NDX 技术指标 |

完整截图见 `webapp/screenshots/`。

---

## 📁 项目导航

> 如果你是开发者、想贡献代码，请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)

| 你想做什么 | 去哪里 |
|-----------|--------|
| 了解项目架构 | [ARCHITECTURE.md](ARCHITECTURE.md) |
| 看路线图和未来计划 | [ROADMAP.md](ROADMAP.md) |
| 理解技术选型原因 | [DECISIONS.md](DECISIONS.md) |
| 看版本更新记录 | [CHANGELOG.md](CHANGELOG.md) |
| AI 辅助开发规则 | [AGENTS.md](AGENTS.md) |
| 报告 Bug | [Issue → Bug Report](https://github.com/orgs/TradeCamp/issues/new?template=bug_report.yml) |
| 提功能建议 | [Issue → Feature Request](https://github.com/orgs/TradeCamp/issues/new?template=feature_request.yml) |
| 贡献课程/术语 | [Issue → 教学内容](https://github.com/orgs/TradeCamp/issues/new?template=learning.yml) |
| 行为准则 | [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) |
| 安全策略 | [SECURITY.md](SECURITY.md) |

---

## 🧪 测试

```powershell
# 报告系统验证
python nasdaq_analyzer.py          # 10 步全部成功即为正常

# 交易系统单元测试
pytest tests/                      # 7 个测试文件全部通过

# 一键跑所有 Demo
.\examples\run_all_demos.bat
```

CI 自动跑在 `.github/workflows/smoke.yml`。

---

## 🫶 贡献

TradeCamp 的目标是让更多人学会投资。**你不一定要会写代码才能贡献：**

| 你的技能 | 你可以 |
|---------|--------|
| 📝 懂中文 | 修正错别字、润色课程文案 |
| 📖 有交易经验 | 写新的课程章节、补充实战案例 |
| 🌍 会翻译 | 中英互译课程和术语 |
| 🎨 会设计 | 改进网页 UI、设计 Logo |
| 🐍 会 Python | 新增指标、券商适配器、策略 |
| ⚛️ 会 React | 改进 Web 前端功能和体验 |

详细指南：**[CONTRIBUTING.md](CONTRIBUTING.md)**

---

## 📄 许可证

[MIT](LICENSE) © TradeCamp 贡献者

---

## ⭐ 支持项目

如果这个项目对你有帮助，请点个 Star ⭐ 让更多新手看到！

有学习问题？提 Issue 选 `question` 标签，我们帮你。

# TradeCamp 项目路线图

## Current Status

### 已实现功能

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
2. **桌面交易**：PyQt5 GUI 可手动/自动交易（模拟/Aplaca）
3. **Web 交易**：React 网页版可在浏览器中进行模拟交易
4. **AI 教练**：每日简报 + 持仓体检 + 段位系统
5. **学习系统**：8 章入门课程 + 50+ 术语词典

---

## Current Phase

### 正在解决的问题

- **CI 稳定性**：yfinance 在 GitHub Actions 环境中的网络兼容性问题（已通过 YahooDirectAPI + ETF Proxy 缓解）
- **代码一致性**：报告系统的旧回测 (`backtest.py`) 与新回测引擎 (`backtest/engine.py`) 并存，需要统一

### 当前主要目标

- 完善构建部署流程（Vercel + Render 部署 Web 版）

---

## Next Steps

### P0（必须）

- [ ] 统一回测层：将报告系统的 `backtest.py`（根目录）迁移到使用 `backtest/engine.py`
- [ ] 移除报告系统中与新引擎重复的代码

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

- **两个 backtest.py**：根目录的 `backtest.py` 是报告系统嵌入式回测（旧），`backtest/engine.py` 是独立回测引擎（新），二者不冲突但也不使用对方代码。
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

# Changelog

记录用户可感知的重要变化。

## Unreleased

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

# TradeCamp 技术决策记录

记录项目中重要的技术和产品决策。格式：编号 - 决策名称。

---

## D001 - 纯 pandas 实现技术指标

**Date:** 2026-07-13

**Background:**
需要计算 MA/MACD/RSI/KDJ/BOLL 等常见技术指标。常见的 Python 量化库如 TA-Lib 需要 C 编译，在 Windows 上安装困难；`pandas-ta` 功能强大但引入额外依赖。

**Decision:**
选用纯 pandas + numpy 实现所有 10 个技术指标。指标计算内联在 `indicators.py` 中，使用 `calc_all_indicators(df)` 统一入口。

**Reason:**
- 零外部依赖，Windows/macOS/Linux/GitHub Actions 均可直接运行
- pandas 是已引入的核心依赖
- 10 个指标均在 ~200 行代码内完成，维护成本可接受
- 对于每日分析场景，不需要 TA-Lib 级别的性能优化

**Rejected Alternatives:**
- TA-Lib：需要 C 编译，Windows 环境体验差，GitHub Actions 需额外安装步骤
- pandas-ta：额外依赖，功能远超当前需求

**Impact:**
所有指标计算在本地完成，无外部库依赖风险。

---

## D002 - ECharts 本地优先 + CDN 回退

**Date:** 2026-07-13

**Background:**
HTML 报告需要图表渲染。ECharts 5 官方 CDN（jsdelivr）在中国大陆偶尔不可用，且 GitHub Actions CI 环境可能无法访问 CDN。

**Decision:**
将 `echarts.min.js`（~1MB）下载到项目根目录，HTML 模板优先加载本地文件，CDN 作为回退。`report_generator.py` 在生成报告时自动将 `echarts.min.js` 复制到报告输出目录。

**Reason:**
- 本地文件确保离线环境和网络受限环境下图表正常渲染
- CDN 回退机制增加容错
- ~1MB 文件体积对 Git 仓库和 GitHub Actions 均可接受

**Impact:**
项目根目录需包含 `echarts.min.js` 文件。

---

## D003 - Feature Flags 控制可选模块

**Date:** 2026-07-13

**Background:**
报告系统扩展了多个可选模块（回测、情绪分析、板块轮动、ML 预测等），不同环境（本地/CI/Docker）可能需要不同的功能组合。部分模块有重型依赖（Prophet/scikit-learn），不应强制安装。

**Decision:**
在 `config.py` 中定义 `ENABLE_*` Feature Flags，通过环境变量覆盖。主流程 `nasdaq_analyzer.py` 中所有添加功能用 `if ENABLE_XXX:` 包裹，单个模块失败用 try/except 捕获后记录日志并继续。

**Reason:**
- 核心报告流程不受影响，新增模块可独立启停
- 降低依赖复杂度（不装 ML 依赖也能正常生成报告）
- Docker 镜像、GitHub Actions 可按需开关

**Impact:**
所有新增功能模块必须遵循 Feature Flags + Graceful Degradation 模式。

---

## D004 - SQLite 选择（非 MySQL/PostgreSQL）

**Date:** 2026-07-13

**Background:**
需要持久化每日价格快照、指标快照、报告元数据，以支持历史对比和指标历史查询。

**Decision:**
使用 Python 标准库 `sqlite3`，数据库文件放在 `data/nasdaq.db`。

**Reason:**
- Python 标准库自带，零安装零配置
- 文件型数据库，个人单用户场景够用
- 不需要独立数据库服务进程
- 与 Docker 容器部署天然兼容（单文件挂载即可）

**Rejected Alternatives:**
- MySQL/PostgreSQL：需要额外的数据库服务，对个人工具是过度工程
- DuckDB：虽然性能更好但额外依赖，SQLite 已满足需求

**Impact:**
所有数据存储在本地 SQLite 文件中。

---

## D005 - 两个 backtest 模块并存

**Date:** 2026-07-14

**Background:**
v1.1 在根目录创建了 `backtest.py`（嵌入式回测，直接操作 pandas DataFrame 的简易引擎）。v2.0 的 `trading/` 子系统需要更专业的回测，因此在 `backtest/` 目录下创建了新引擎（基于 StrategyBase + RiskManager + Portfolio 的专业引擎）。

**Decision:**
保持两个模块并存，用不同的命名空间区分：
- `backtest.py`（根目录）：报告器内轻量回测，MACD+RSI+WR 固定策略
- `backtest/engine.py`：独立回测引擎，可与任何交易策略搭配使用

**Reason:**
- 报告系统的回测与交易系统的回测需求不同（报告侧重展示，交易侧重精度）
- 两个模块不互相依赖，风险隔离
- 未来 P0 计划统一，但当前阶段不急于迁移

**Impact:**
- 存在代码重复和两个回测结果不一致的风险
- ROADMAP P0 已计划统一

---

## D006 - PyQt5 + React 双前端

**Date:** 2026-07-14

**Background:**
交易系统需要用户界面。PyQt5 提供原生 Windows 桌面体验（高性能 K 线图、系统托盘），React + FastAPI 则适合跨平台浏览器访问。

**Decision:**
同时支持 PyQt5 桌面 GUI 和 React WebApp 两种前端，共用 `trading/` 业务逻辑。

**Reason:**
- PyQt5 桌面端提供更好的性能（本地渲染 K 线图）和系统集成（托盘通知）
- React Web 端提供跨平台能力和远程访问
- 两种方式各有场景，不互斥

**Impact:**
- 需要维护两套前端代码
- Web 端通过适配器层（`engine_adapter.py`）桥接真实的 `TradingEngine`

---

## D007 - Yahoo Direct API 绕道方案

**Date:** 2026-07-14

**Background:**
yfinance 在 GitHub Actions CI 环境频繁失败（IP 限制 / Cloudflare 挑战 / 返回空数据）。需要更可靠的 CI 数据获取方案。

**Decision:**
新增 `YahooDirectProvider`，直接调用 `query1.finance.yahoo.com/v8/finance/chart` JSON API，彻底绕过 yfinance 库。同时引入 `USE_ETF_PROXY` 开关用 QQQ/VIXY 替代 ^IXIC/^VIX。

**Reason:**
- Direct API 不需要经过 yfinance 的网络层，成功率显著提高
- ETF 代理（QQQ）走势与纳指几乎一致，数据质量可接受
- 两个方案都是环境变量控制的可选开关，不影响本地使用

**Impact:**
- CI 环境需要使用 `USE_DIRECT_API=true` + `USE_ETF_PROXY=true`
- Direct API 返回数据格式需转换为与 yfinance 一致（已在 `yahoo_direct_provider.py` 中处理）

---

## D008 - WebApp 默认 mock 模式

**Date:** 2026-07-14

**Background:**
WebApp 需要展示功能齐全的界面。真引擎依赖外部行情数据，启动慢、不稳定。

**Decision:**
WebApp 默认使用 MockEngine（模拟行情 + 模拟账户），通过环境变量 `NDXINFO_BACKEND=real` 切换到真正的 TradingEngine。

**Reason:**
- Mock 模式确保页面始终可演示，不受网络/API 状态影响
- 开发时不需要等待真实行情加载，热更新体验好
- 真实的交易引擎作为可选切换

**Impact:**
WebApp 后端需要适配器层同时支持 MockEngine 和 EngineAdapter。

---

## D009 - 中英文金融词典情绪分析

**Date:** 2026-07-13

**Background:**
需要评估市场新闻的情绪倾向。传统的 NLP 方案（FinBERT）需要 GPU 推理，HuggingFace 模型体积大（>400MB），对个人工具不友好。

**Decision:**
使用词典法（lexicon-based），中英文金融情感词典在代码中硬编码。正面词 +1 分，负面词 -1 分，按词频归一化。

**Reason:**
- 零依赖，零模型下载
- 对财经新闻场景，词典法准确度足够
- 代码体积小（约 200 行）

**Rejected Alternatives:**
- FinBERT：需 transformers 库 + 模型下载，太重
- TextBlob/VADER：仅英文，不支持中文

**Impact:**
情绪精度有限但日常可用。支持中英文双语新闻。

---

## D010 - GitHub Actions gh-pages 发布

**Date:** 2026-07-14

**Background:**
每日生成的 HTML 报告需要能在浏览器中直接查看。直接放在仓库中无法通过 GitHub 直接打开 HTML 文件。

**Decision:**
使用 `peaceiris/actions-gh-pages` Action 将报告推送到 `gh-pages` 分支，通过 GitHub Pages 提供静态托管。使用 `keep_files: true` 保留历史报告。

**Reason:**
- 免费、零运维
- 历史报告自然归档
- 浏览器直接访问 URL

**Impact:**
报告可通过 `https://<user>.github.io/<repo>/nasdaq_report_YYYY-MM-DD.html` 访问。

---

## D011 - AI 教练规则驱动（可选 LLM）

**Date:** 2026-07-14

**Background:**
需要为交易者提供个性化建议和段位评估。纯 AI（LLM）方案成本高、延迟大。

**Decision:**
规则驱动作为主方案：段位计算、持仓体检、风险预警均基于硬编码规则 + 技术指标。预留 LLM 增强接口（`call_llm()` 函数）。

**Reason:**
- 离线可用，无 API 费用
- 规则可解释、可调试
- 延迟 < 10ms vs LLM 的 > 1s
- LLM 作为可选的增强层，不影响核心功能

**Impact:**
所有教练功能在没有 LLM 的环境中也能正常工作。

---

## D012 - 多因子 AI 推荐引擎

**Date:** 2026-07-14

**Background:**
需要为每只被监控的股票给出操作建议（BUY/HOLD/SELL），不能只是展示数据。

**Decision:**
5 因子加权评分模型：
- 趋势因子 30%（均线排列、价格位置）
- 动量因子 25%（MACD、KDJ 信号）
- 反转因子 20%（RSI、布林带超买超卖）
- 量价因子 15%（成交量变化、OBV 方向）
- 波动因子 10%（ATR、布林带宽度）

**Reason:**
- 每个因子基于已有技术指标，零额外数据需求
- 加权设计可调整，不需要训练数据
- 评分可解释（每个因子有独立得分和理由）

**Impact:**
推荐引擎与交易策略使用相同的技术指标输入，但评分逻辑独立。

---

## 不确定项

以下决策的原因或时间**需要项目所有者确认**：

1. **D005（两个 backtest 并存）**— P0 的统一计划是否已经开始？是否考虑过直接删除根目录的 `backtest.py`？
2. **D007（Yahoo Direct API）**— Yahoo 是否可能更改 `query1.finance.yahoo.com` 的 API 格式？
3. **数据库路径**— `data/userdata.db` 和 `data/nasdaq.db` 是否应该合并为一个数据库？

