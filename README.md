# NDXinfo

> 美股自动交易系统 + 纳指每日分析报告生成器
> 项目组合：一个项目，两个工具，相互联动

---

## 项目组成

| # | 模块 | 功能 | 入口 |
|---|---|---|---|
| 🅰️ | **美股自动交易系统** | 真/模拟券商，下单、风控、策略、回测 | `trader.py` · `trading/` · `webapp/` |
| 🅱️ | **NDX 每日分析报告** | 纳指 (NDX) + 12 只重点股每日技术分析 + 报告 | `nasdaq_analyzer.py` · `reports/*.html` |

**联动**：交易系统 Dashboard 顶部展示今日 NDX 大盘状态（来自 🅱️）——见 `webapp/features/NdxStatusBar.tsx`。

---

## 🅰️ 美股自动交易系统（trader）

### 包含

| 子模块 | 内容 |
|---|---|
| `trading/`    | broker / risk / strategy / executor / cache / rate limiter（**生产级**） |
| `backtest/`   | 回测引擎、组合、12 项指标、HTML 报告 |
| `gui/`        | PyQt5 桌面 app（Dashboard / Trading / Strategy 三个标签页，深/浅主题） |
| `examples/`   | 7 个独立 demo 脚本 + 一键 `run_all_demos.bat` |
| `tests/`      | 29 个单元测试 |
| `webapp/`     | **React 18 + FastAPI 网页版**（5 个页面、TradingView K 线、实时推送） |
| `.github/`    | CI: 跑测试 + 算覆盖率 + 主题哈希校验 |

### 三个启动方式

```powershell
# 1️⃣ 跑 PyQt5 桌面 app（Windows 原生窗口）
cd e:\Projects\NDXinfo
python trader.py

# 2️⃣ 跑 React 网页版（默认 mock，离线演示）
.\webapp\scripts\dev.ps1
# → 浏览器打开 http://127.0.0.1:5173

# 3️⃣ 跑 React 网页版（真引擎 + 模拟券商）
$env:NDXINFO_BACKEND='real'
$env:NDXINFO_BROKER='simulation'
.\webapp\scripts\dev.ps1

# 4️⃣ 跑 Alpaca Paper（需要免费 key）
$env:APCA_API_KEY_ID='PK...'
$env:APCA_API_SECRET_KEY='SK...'
.\webapp\scripts\start_alpaca_paper.ps1
```

### 跑所有 demo 验证

```powershell
cd e:\Projects\NDXinfo
.\examples\run_all_demos.bat
# → 跑完 9 步（broker / sim rules / backtest / config / observability / strategies / theme / capture_gui / dashboard）
```

### 网页版截图

`webapp/screenshots/` 下：

| 文件 | 内容 |
|---|---|
| `dashboard.png`         | 总览（含净值曲线 + 持仓 + NDX 大盘状态） |
| `dashboard_light.png`   | 浅色主题 |
| `trading.png`           | 交易（K 线 + 下单面板） |
| `strategy.png`          | 策略（8 策略 + 权重） |
| `logs.png`              | 实时日志 |
| `settings.png`          | 设置 |

---

## 🅱️ NDX 每日分析报告（nasdaq_analyzer）

详见 [`nasdaq_analyzer.py`](nasdaq_analyzer.py) — 这个模块是已有的，由 jianjiao jianjiao 写。

```powershell
pip install -r requirements.txt
python nasdaq_analyzer.py
# → 生成 nasdaq_report_YYYY-MM-DD.html，浏览器打开即可看
```

| 模块 | 内容 |
|---|---|
| `data_fetcher.py`       | 多数据源抽象层（yfinance + akshare） |
| `indicators.py`         | 10 大技术指标（MA / MACD / RSI / KDJ / BOLL / ATR / OBV / WR / CCI / VWAP） |
| `analysis.py`           | 趋势 + 支撑阻力 + VIX |
| `backtest.py`           | MACD+RSI+WR 组合策略回测 |
| `sentiment.py`          | 中英文金融词典情绪 |
| `sector.py`             | 11 行业 ETF 板块轮动 |
| `comparison.py`         | 与上期报告对比 |
| `report_generator.py`   | Jinja2 + ECharts 暗色报告 |
| `providers/`            | yfinance / akshare 适配器 |
| `templates/`            | 报告模板 |

---

## 联动说明

交易系统的 Dashboard 顶部渲染 NDX 状态条：

```
NDX 大盘 [⚠ mock]   ↗ +1.12%   $21,350   MA200 20,710   MA50 21,030   RSI 58.4   [温和偏多]
NDX 上涨 1.12%，MA200 上方；情绪 温和偏多                [查看今日报告 →]
```

数据通路：

```
┌───────────────────────────────┐
│ 🅱️ nasdaq_analyzer            │
│   data_fetcher.fetch_index()  │ ── 拉 ^NDX 日 K
│   indicators.calc_all()       │ ── MA50 / MA200 / RSI
│   report_generator            │ ── reports/nasdaq_report_*.html
└───────────────────────────────┘
            ▲ data path ▲
            │
            ▼ HTTP /api/market/ndx
┌───────────────────────────────┐
│ 🅰️ webapp                     │
│   backend/adapters/ndx_adapter│ ── 缓存 5 分钟
│   server.py GET /api/market/ndx
│   frontend NdxStatusBar.tsx   │ ── Dashboard 顶部
└───────────────────────────────┘
```

> 注意：当前是**轻联动**——交易页面只是显示 NDX 状态，不影响交易。
> 后续可以加深到：交易策略拿 NDX > 200MA 作为开仓条件。

---

## 目录结构

```
e:\Projects\NDXinfo\
├── trader.py              🅰️  PyQt5 桌面入口
├── trading/               🅰️  交易内核
├── backtest/              🅰️  回测引擎
├── gui/                   🅰️  PyQt5 GUI 模块
├── examples/              🅰️  7 demo + run_all
├── tests/                 🅰️  29 单元测试
├── webapp/                🅰️  React + FastAPI 网页版
│
├── nasdaq_analyzer.py     🅱️  NDX 报告主入口
├── data_fetcher.py        🅱️  数据拉取
├── indicators.py          🅱️  技术指标
├── analysis.py            🅱️  趋势分析
├── backtest.py            🅱️  报告器内回测（与 trading.backtest 不同）
├── sentiment.py           🅱️  情绪
├── sector.py              🅱️  板块
├── comparison.py          🅱️  历史对比
├── report_generator.py    🅱️  HTML 报告
├── ml_predictor.py        🅱️  ML 价格预测（实验）
├── providers/             🅱️  多数据源抽象层
├── templates/             🅱️  Jinja2 模板
├── requirements-report.txt 🅱️ 报告器依赖
│
├── config.py              🅱️ 报告器配置（与 🅰️ 的 config/default.yaml 不冲突）
├── requirements.txt       🅰️ 主依赖（PyQt5 / pandas / yfinance / akshare …）
├── config/default.yaml    🅰️ 交易配置
├── Dockerfile             🅱️ 报告器的容器镜像
├── data/, reports/        🅱️ 报告 + SQLite 历史
├── nasdaq_report_*.html   🅱️ 今天生成的报告
└── README.md              本文件
```

---

## 依赖（一次安装搞定全部）

```powershell
pip install -r requirements.txt
# 然后给交易引擎做（Python web app 用）
pip install fastapi uvicorn[standard] websockets
# 然后给 React 前端做（Node 自动装）
cd webapp/frontend ; npm install
```

---

## 测试

```powershell
cd e:\Projects\NDXinfo
pytest                 # 29 单元测试
coverage run -m pytest ; coverage report   # 覆盖率报告
```

CI 在 `.github/workflows/smoke.yml` —— push 上去自动跑。

---

## License

MIT

---

## 路线图

- [x] 模拟券商（slippage / commission / T+1 / 部分成交）
- [x] 8 个策略（含 KDJ / BOLL-width / Ensemble）
- [x] 回测 + 12 项指标
- [x] PyQt5 深/浅主题
- [x] 单元测试 + GitHub Actions CI
- [x] React + FastAPI 网页版
- [x] 真引擎 + Alpaca Paper 适配
- [x] NDX 报告器 → 交易 Dashboard 轻联动
- [ ] 中联动：策略以 NDX > MA200 为开仓前置
- [ ] 重联动：统一数据层（合并为 trading.report）
- [ ] 部署到 Vercel + Render / 或打包 .exe
