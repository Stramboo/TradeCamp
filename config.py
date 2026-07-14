# -*- coding: utf-8 -*-
"""
NASDAQ 每日分析报告 - 配置模块
集中管理所有配置常量：股票池、路径、指标参数、Feature Flags
支持环境变量覆盖
"""

import os

# ============================================================
# 路径配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_DIR = BASE_DIR  # 报告直接输出到项目根目录
REPORTS_ARCHIVE_DIR = os.path.join(BASE_DIR, "reports")  # 历史报告归档目录
DATA_DIR = os.path.join(BASE_DIR, "data")  # SQLite 数据目录
DB_PATH = os.path.join(DATA_DIR, "nasdaq.db")  # SQLite 数据库路径

# ============================================================
# Feature Flags（功能开关，可通过环境变量覆盖）
# ============================================================

def _get_env_flag(key, default="true"):
    """从环境变量读取布尔开关"""
    return os.getenv(key, default).lower() == "true"

ENABLE_BACKTEST = _get_env_flag("ENABLE_BACKTEST", "true")
ENABLE_ML_PREDICT = _get_env_flag("ENABLE_ML_PREDICT", "false")
ENABLE_NEWS_SENTIMENT = _get_env_flag("ENABLE_NEWS_SENTIMENT", "true")
ENABLE_PDF_EXPORT = _get_env_flag("ENABLE_PDF_EXPORT", "false")
ENABLE_EMAIL = _get_env_flag("ENABLE_EMAIL", "false")
ENABLE_HK_A_SHARE = _get_env_flag("ENABLE_HK_A_SHARE", "false")
ENABLE_SECTOR_ETF = _get_env_flag("ENABLE_SECTOR_ETF", "true")
ENABLE_WEB = _get_env_flag("ENABLE_WEB", "false")
ENABLE_COMPARISON = _get_env_flag("ENABLE_COMPARISON", "true")

# ============================================================
# 指数与市场指标
# ============================================================
INDEX_TICKERS = {
    "ixic": "^IXIC",   # NASDAQ Composite（纳斯达克综合指数）
    "ndx": "^NDX",     # NASDAQ-100（纳斯达克100指数）
    "vix": "^VIX",     # VIX 恐慌指数
}

# Yahoo Finance 指数 fallback（CI/限流环境使用 ETF 作为代理）
# 在 CI 上 ^ 前缀指数经常返回空数据，启用 USE_ETF_PROXY 后
# YFinanceProvider 会优先使用这里的 ETF，再 fallback 回 INDEX_TICKERS
INDEX_ETF_PROXY = {
    "ixic": "QQQ",     # 纳斯达克100 ETF（走势几乎一致）
    "ndx":  "QQQ",     # 纳斯达克100 ETF
    "vix":  "VIXY",    # VIX 短期期货 ETF
}
USE_ETF_PROXY = _get_env_flag("USE_ETF_PROXY", "false")  # CI 默认关闭，由代码自动启用

# ============================================================
# 推荐股票池（按板块分组）
# ============================================================
STOCK_UNIVERSE = {
    "半导体/AI芯片": ["NVDA", "AMD", "TSM", "AVGO"],
    "大型科技股": ["AAPL", "MSFT", "GOOGL", "AMZN", "META"],
    "成长/创新股": ["TSLA", "PLTR", "COIN"],
}

# ============================================================
# 行业 ETF 配置（板块轮动分析）
# ============================================================
SECTOR_ETFS = {
    "科技": "XLK",
    "金融": "XLF",
    "能源": "XLE",
    "医疗": "XLV",
    "可选消费": "XLY",
    "必需消费": "XLP",
    "工业": "XLI",
    "材料": "XLB",
    "房地产": "XLRE",
    "公用事业": "XLU",
    "通信": "XLC",
}

BROAD_INDEX_ETFS = {
    "SPY": "标普500",
    "QQQ": "纳指100",
    "IWM": "罗素2000",
    "DIA": "道琼斯",
}

# ============================================================
# 港股/A股配置（默认关闭）
# ============================================================
HK_STOCK_UNIVERSE = {
    "互联网": ["HK:0700", "HK:3690", "HK:9988"],  # 腾讯/美团/阿里
}

A_SHARE_UNIVERSE = {
    "新能源": ["SH:300750"],  # 宁德时代
    "消费": ["SH:600519"],    # 贵州茅台
}

# ============================================================
# 数据参数
# ============================================================
HISTORY_PERIOD = "1y"       # 获取1年历史数据（满足MA60、MACD等需求）
HISTORY_INTERVAL = "1d"     # 日线
CHART_DISPLAY_DAYS = 60     # 图表显示最近60个交易日

# ============================================================
# 技术指标参数
# ============================================================
MA_PERIODS = [5, 10, 20, 60]
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
KDJ_PERIOD = 9
BOLL_PERIOD = 20
BOLL_STD = 2

# 新增指标参数
ATR_PERIOD = 14             # ATR 平均真实波幅周期
WR_PERIOD = 14              # 威廉指标周期
CCI_PERIOD = 20             # CCI 商品通道指标周期
VWAP_PERIOD = 20            # VWAP 成交量加权均价周期

# ============================================================
# 回测参数
# ============================================================
BACKTEST_INITIAL_CAPITAL = 100000  # 初始资金
BACKTEST_COMMISSION = 0.001        # 交易手续费率（0.1%）
BACKTEST_LOOKBACK = 252            # 回测区间（交易日，约1年）

# ============================================================
# ML 预测参数
# ============================================================
ML_FORECAST_HORIZON = 5   # 预测未来5个交易日

# ============================================================
# 新闻情绪分析参数
# ============================================================
NEWS_TOP_N = 10             # 每次获取新闻条数

# ============================================================
# 动态筛选配置
# ============================================================
SCREENER_TOP_N = 10         # 动态筛选 Top N 涨幅股

# ============================================================
# 请求控制
# ============================================================
REQUEST_INTERVAL = 0.5      # 请求间隔（秒），避免触发 Yahoo 速率限制
MAX_RETRIES = 3             # 最大重试次数
RETRY_BACKOFF = 2           # 指数退避基数（秒）

# ============================================================
# 邮件推送配置（通过环境变量注入）
# ============================================================
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")
