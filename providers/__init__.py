# -*- coding: utf-8 -*-
"""
数据提供者抽象层包（providers）

提供统一的数据获取接口，支持多数据源路由：
    - 美股：YFinanceProvider（基于 yfinance）或 YahooDirectProvider（直接调 JSON API）
    - 港股/A股：AkshareProvider（基于 akshare）

使用方式:
    from providers import DataProvider, YFinanceProvider, AkshareProvider, YahooDirectProvider

    yf_provider = YFinanceProvider()
    df = yf_provider.fetch_history("AAPL")

    ak_provider = AkshareProvider()
    df = ak_provider.fetch_history("HK:0700")
"""

from providers.base import DataProvider
from providers.yfinance_provider import YFinanceProvider
from providers.akshare_provider import AkshareProvider
from providers.yahoo_direct_provider import YahooDirectProvider

__all__ = [
    "DataProvider",
    "YFinanceProvider",
    "AkshareProvider",
    "YahooDirectProvider",
]