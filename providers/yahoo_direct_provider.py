# -*- coding: utf-8 -*-
"""
Yahoo Finance 直接 HTTP Provider

绕过 yfinance Python 库，直接调用 Yahoo Finance 的 JSON API:
    https://query1.finance.yahoo.com/v8/finance/chart/{ticker}

适用场景：
    - GitHub Actions 等 CI 环境（yfinance 在这些 IP 段经常失败）
    - Yahoo Finance 主动限制 yfinance 时

优势：
    - 不需要 cookie / crumb 验证
    - 不依赖 yfinance 版本
    - 在 CI 环境成功率远高于 yfinance

接口与 YFinanceProvider 完全兼容。
"""

import time
import logging
import urllib.request
import urllib.parse
import json

import pandas as pd

from providers.base import DataProvider

logger = logging.getLogger(__name__)


# Yahoo Finance v8 API 端点
# query1 在大多数网络环境下都通；query2 是备用
_API_ENDPOINTS = [
    "https://query1.finance.yahoo.com/v8/finance/chart/",
    "https://query2.finance.yahoo.com/v8/finance/chart/",
]

# 模拟常见浏览器的 User-Agent，避免被 Yahoo 拒绝
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class YahooDirectProvider(DataProvider):
    """
    直接调用 Yahoo Finance v8 JSON API 的数据提供者

    不依赖 yfinance 库，绕过其在 CI 上的限制问题。
    """

    def __init__(self):
        super().__init__()

    # ============================================================
    # 接口方法实现
    # ============================================================

    def fetch_history(self, ticker, period="1y"):
        """获取单个 ticker 的历史 OHLCV 数据"""
        range_ = self._period_to_range(period)
        raw = self._fetch_chart(ticker, range_=range_, interval="1d")
        return self._parse_chart_response(raw, ticker)

    def fetch_batch(self, tickers, period="1y"):
        """批量获取，串行调用 fetch_history（简单可靠）"""
        stocks = {}
        for ticker in tickers:
            try:
                df = self.fetch_history(ticker, period)
                stocks[ticker] = df
            except Exception as e:
                logger.warning(f"获取 {ticker} 失败: {e}")
                stocks[ticker] = pd.DataFrame()
        success = sum(1 for v in stocks.values() if not v.empty)
        logger.info(f"批量下载 {len(tickers)} 只标的完成，成功 {success} 只")
        return stocks

    def fetch_info(self, ticker):
        """获取股票基本信息（轻量版，不支持完整 info）"""
        raw = self._fetch_chart(ticker, range_="5d", interval="1d")
        try:
            meta = raw["chart"]["result"][0]["meta"]
            return {
                "name": meta.get("longName") or meta.get("shortName") or ticker,
                "sector": "N/A",  # JSON API 不提供 sector
                "market_cap": None,
            }
        except Exception:
            return {"name": ticker, "sector": "N/A", "market_cap": None}

    def screen_gainers(self, top_n=10):
        """
        涨幅榜：JSON API 没有 screen 接口，
        用 fallback 方案：下载一组热门股票 5d 数据并排序。
        """
        fallback_tickers = [
            "NVDA", "TSLA", "AMD", "META", "AMZN", "AAPL", "MSFT",
            "GOOGL", "NFLX", "AVGO", "COST", "PEP", "ADBE", "INTC",
            "CMCSA", "CSCO", "TMUS", "QCOM", "TXN", "AMGN",
            "PLTR", "COIN", "PYPL", "SHOP", "SQ", "ROKU",
            "SNOW", "CRWD", "ZS", "DDOG", "NET", "PANW",
        ]

        stocks = self.fetch_batch(fallback_tickers, period="5d")
        gainers = []
        for ticker, df in stocks.items():
            if df.empty or len(df) < 2:
                continue
            try:
                last_close = float(df["Close"].iloc[-1])
                prev_close = float(df["Close"].iloc[-2])
                if prev_close == 0:
                    continue
                change_pct = round((last_close - prev_close) / prev_close * 100, 2)
                gainers.append({
                    "ticker": ticker,
                    "name": ticker,
                    "price": round(last_close, 2),
                    "change_pct": change_pct,
                    "volume": int(df["Volume"].iloc[-1]),
                    "market_cap": None,
                })
            except Exception:
                continue

        gainers.sort(key=lambda x: x["change_pct"], reverse=True)
        return gainers[:top_n]

    # ============================================================
    # 内部辅助方法
    # ============================================================

    def _period_to_range(self, period):
        """把 yfinance 风格的 period 转换为 Yahoo v8 API 的 range"""
        mapping = {
            "1d": "1d", "5d": "5d", "1mo": "1mo", "3mo": "3mo",
            "6mo": "6mo", "1y": "1y", "2y": "2y", "5y": "5y",
            "10y": "10y", "ytd": "ytd", "max": "max",
        }
        return mapping.get(period, "1y")

    def _fetch_chart(self, ticker, range_="1y", interval="1d"):
        """调用 Yahoo v8 chart API"""
        def _do():
            url = f"{_API_ENDPOINTS[0]}{urllib.parse.quote(ticker)}?range={range_}&interval={interval}"
            req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            # 检查错误
            err = data.get("chart", {}).get("error")
            if err:
                raise RuntimeError(f"Yahoo API 错误: {err}")
            return data

        result = self._retry(_do)
        if result is None:
            # 尝试备用端点 query2
            def _do_query2():
                url = f"{_API_ENDPOINTS[1]}{urllib.parse.quote(ticker)}?range={range_}&interval={interval}"
                req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                err = data.get("chart", {}).get("error")
                if err:
                    raise RuntimeError(f"Yahoo API 错误: {err}")
                return data
            result = self._retry(_do_query2)
        return result

    def _parse_chart_response(self, data, ticker):
        """
        把 Yahoo v8 chart API 响应解析为 DataFrame

        返回包含 Open/High/Low/Close/Volume 的 DataFrame
        """
        if not data or "chart" not in data or not data["chart"].get("result"):
            logger.warning(f"解析 {ticker} 响应失败")
            return pd.DataFrame()

        result = data["chart"]["result"][0]
        timestamps = result.get("timestamp", [])
        indicators = result.get("indicators", {})
        quote = indicators.get("quote", [{}])[0]
        adjclose = indicators.get("adjclose", [{}])[0]

        if not timestamps:
            logger.warning(f"解析 {ticker}: 无时间戳")
            return pd.DataFrame()

        # adjclose 优先（已调整除权除息），fallback 到 close
        closes = adjclose.get("adjclose") or quote.get("close") or []

        df = pd.DataFrame({
            "Open":   quote.get("open",   [None] * len(timestamps)),
            "High":   quote.get("high",   [None] * len(timestamps)),
            "Low":    quote.get("low",    [None] * len(timestamps)),
            "Close":  closes,
            "Volume": quote.get("volume", [0]    * len(timestamps)),
        }, index=pd.to_datetime(timestamps, unit="s", utc=True).tz_convert(None))

        # 去除全空行
        df = df.dropna(subset=["Close"]).reset_index()
        df.columns = ["Date", "Open", "High", "Low", "Close", "Volume"]

        logger.info(f"获取 {ticker} 数据成功: {len(df)} 条记录")
        return df