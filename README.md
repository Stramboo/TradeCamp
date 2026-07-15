# 🏕️ TradeCamp — 新手的股票交易训练营

<p align="center">
  <strong>📖 学 → 🧪 练 → 📊 看 → 🤖 模拟 → 💰 真刀真枪</strong>
</p>

<p align="center">
  从零开始学炒股的开源工具箱 —— 内置 8 章教程、AI 教练、模拟交易、每日大盘分析报告
</p>
<p align="center">
  <sub>v2.1 · 89 项测试全绿 · 六层架构重构完成</sub>
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
- **结构化评估**：**v2.1 新增** —— 四维评分系统（决策/执行/风险/归因），交易后自动给出 S~D 等级 + 亮点 + 改进点
- **LLM 增强**：可选接入 DeepSeek，AI 用自然语言点评你的每笔交易

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
# 全量测试（当前 89 passed，零失败）
pytest tests/

# 报告系统验证
python nasdaq_analyzer.py          # 10 步全部成功即为正常

# E2E 流程测试（数据 → 买入 → 卖出 → 教练评估）
pytest tests/test_e2e_smoke.py -v  # 10 项 API 级冒烟测试
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
