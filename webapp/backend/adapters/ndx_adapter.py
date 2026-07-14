# -*- coding: utf-8 -*-
"""
ndx_adapter.py — 把 nasdaq_analyzer / data_fetcher 包成"今日 NDX 分析"接口

提供两个层级的接口：
1. get_status()       — 轻量 NDX 状态（已有，给 dashboard NdxStatusBar 用）
2. get_full_analysis() — 完整分析（NDX + 关键股票 + 板块轮动 + 情绪，给"分析"页面用）

策略：
- 优先用项目里的 DataFetcher + indicators + analysis + sentiment + sector
- 失败/没有依赖时，退化到 mock 数据，绝不让 webapp 504
- 全量数据缓存 TTL = 300s
"""

from __future__ import annotations

import logging
import math
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ======================================================================
# 数据类
# ======================================================================

@dataclass
class NdxStatus:
    """今日 NDX 状态（给前端 dashboard 用）"""
    symbol: str = "NDX"
    last_close: float = 0.0
    change_pct: float = 0.0
    ma50: float = 0.0
    ma200: float = 0.0
    above_ma200: bool = False
    rsi14: float = 50.0
    sentiment: str = "neutral"
    sentiment_label: str = "中性"
    summary: str = ""
    source: str = "live"
    ts: int = 0
    ndx_analysis_report_path: str = ""


@dataclass
class StockAnalysis:
    """单只股票分析快照"""
    symbol: str = ""
    name: str = ""
    sector: str = ""
    close: float = 0.0
    change_pct: float = 0.0
    ma5: float = 0.0
    ma20: float = 0.0
    ma60: float = 0.0
    rsi14: float = 50.0
    macd_signal: str = "neutral"  # "bull" | "bear" | "neutral"
    trend: str = "震荡"
    recommendation: str = "观望"


@dataclass
class SectorAnalysis:
    """板块 ETF 分析"""
    name: str = ""
    etf: str = ""
    close: float = 0.0
    change_pct: float = 0.0
    ma20: float = 0.0
    rsi14: float = 50.0
    rank: int = 0


@dataclass
class FullAnalysis:
    """完整分析数据（给前端"分析"页面用）"""
    ndx: NdxStatus = field(default_factory=NdxStatus)
    stocks: list[StockAnalysis] = field(default_factory=list)
    sectors: list[SectorAnalysis] = field(default_factory=list)
    market_breadth: dict = field(default_factory=dict)
    sentiment_data: dict = field(default_factory=dict)
    source: str = "mock"
    ts: int = 0
    ndx_analysis_report_path: str = ""


# ======================================================================
# 工具函数
# ======================================================================

def _import_root():
    """让 import 'data_fetcher' 'indicators' 'analysis' 等能找到"""
    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.dirname(os.path.dirname(os.path.dirname(_here)))
    if _root not in sys.path:
        sys.path.insert(0, _root)


def _find_latest_report() -> str:
    """在 reports/ 下找最新的 nasdaq_report_*.html"""
    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.dirname(os.path.dirname(os.path.dirname(_here)))
    reports_dir = os.path.join(_root, "reports")
    if not os.path.isdir(reports_dir):
        return ""
    files = [f for f in os.listdir(reports_dir)
             if f.startswith("nasdaq_report_") and f.endswith(".html")]
    if not files:
        return ""
    files.sort(reverse=True)
    return f"reports/{files[0]}"


def _safe_float(v: Any) -> Optional[float]:
    """安全转 float，NaN/Inf 返回 None"""
    if v is None:
        return None
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, 2)
    except (ValueError, TypeError):
        return None


def _classify_sentiment(change_pct: float, above_ma200: bool, rsi: float) -> tuple[str, str]:
    if change_pct >= 0.7 and above_ma200 and rsi < 70:
        return "bull", "强势上涨"
    if change_pct >= 0.2 and above_ma200:
        return "bull", "温和偏多"
    if change_pct <= -0.7 and (not above_ma200) and rsi > 30:
        return "bear", "弱势下跌"
    if change_pct <= -0.2:
        return "bear", "偏空"
    if rsi > 70:
        return "bear", "RSI 超买"
    if rsi < 30:
        return "bull", "RSI 超卖"
    return "neutral", "中性震荡"


def _summary(sentiment_label: str, change_pct: float, above_ma200: bool) -> str:
    ma_clause = "MA200 上方" if above_ma200 else "MA200 下方"
    direction = "上涨" if change_pct >= 0 else "下跌"
    return f"NDX {direction} {abs(change_pct):.2f}%，{ma_clause}；情绪 {sentiment_label}"


def _macd_signal(macd_val: Optional[float], macd_signal_val: Optional[float]) -> str:
    """判断 MACD 信号"""
    if macd_val is None or macd_signal_val is None:
        return "neutral"
    if macd_val > macd_signal_val:
        return "bull"
    return "bear"


def _trend_label(score: float) -> str:
    if score >= 4:
        return "强势上涨"
    if score >= 3:
        return "上涨"
    if score >= 2:
        return "下跌"
    if score > 0:
        return "弱势下跌"
    return "震荡"


def _recommendation(change_pct: float, rsi: float, trend: str, macd_sig: str) -> str:
    """综合推荐"""
    if trend in ("强势上涨", "上涨") and macd_sig == "bull" and rsi < 70:
        return "持有/加仓"
    if trend in ("强势上涨", "上涨") and rsi >= 70:
        return "超买，谨慎"
    if trend in ("下跌", "弱势下跌") and macd_sig == "bear" and rsi > 30:
        return "减仓/观望"
    if trend in ("下跌", "弱势下跌") and rsi <= 30:
        return "超卖，关注反弹"
    return "观望"


# ======================================================================
# Mock 数据（离线兜底）
# ======================================================================

def _mock_status() -> NdxStatus:
    last = 21_350.0
    chg = 1.12
    ma200 = last * 0.97
    return NdxStatus(
        last_close=last, change_pct=chg,
        ma50=last * 0.985, ma200=ma200, above_ma200=True,
        rsi14=58.4, sentiment="bull", sentiment_label="温和偏多",
        summary="NDX 上涨 1.12%，MA200 上方；情绪 温和偏多 (mock)",
        source="mock", ts=int(time.time() * 1000),
        ndx_analysis_report_path=_find_latest_report(),
    )


def _mock_full_analysis() -> FullAnalysis:
    """完整的 mock 分析数据"""
    import random
    rng = random.Random(42)  # 确定性随机

    stocks = []
    stock_data = [
        ("AAPL", "苹果", "大型科技股"), ("MSFT", "微软", "大型科技股"),
        ("GOOGL", "谷歌", "大型科技股"), ("AMZN", "亚马逊", "大型科技股"),
        ("META", "Meta", "大型科技股"), ("NVDA", "英伟达", "半导体/AI芯片"),
        ("AMD", "AMD", "半导体/AI芯片"), ("TSM", "台积电", "半导体/AI芯片"),
        ("AVGO", "博通", "半导体/AI芯片"), ("TSLA", "特斯拉", "成长/创新股"),
        ("PLTR", "Palantir", "成长/创新股"), ("COIN", "Coinbase", "成长/创新股"),
    ]
    for sym, name, sector in stock_data:
        close = rng.uniform(100, 500)
        chg = rng.uniform(-2.5, 3.5)
        stocks.append(StockAnalysis(
            symbol=sym, name=name, sector=sector,
            close=round(close, 2), change_pct=round(chg, 2),
            ma5=round(close * (1 + rng.uniform(-0.02, 0.02)), 2),
            ma20=round(close * (1 + rng.uniform(-0.04, 0.04)), 2),
            ma60=round(close * (1 + rng.uniform(-0.08, 0.08)), 2),
            rsi14=round(rng.uniform(30, 70), 1),
            macd_signal=rng.choice(["bull", "bear", "neutral"]),
            trend=rng.choice(["上涨", "震荡", "下跌"]),
            recommendation=rng.choice(["持有/加仓", "观望", "减仓/观望"]),
        ))

    sectors = []
    sector_data = [
        ("科技", "XLK"), ("金融", "XLF"), ("能源", "XLE"),
        ("医疗", "XLV"), ("可选消费", "XLY"), ("必需消费", "XLP"),
        ("工业", "XLI"), ("材料", "XLB"), ("房地产", "XLRE"),
        ("公用事业", "XLU"), ("通信", "XLC"),
    ]
    for i, (name, etf) in enumerate(sector_data):
        close = rng.uniform(50, 200)
        chg = rng.uniform(-1.5, 2.0)
        sectors.append(SectorAnalysis(
            name=name, etf=etf,
            close=round(close, 2), change_pct=round(chg, 2),
            ma20=round(close * (1 + rng.uniform(-0.03, 0.03)), 2),
            rsi14=round(rng.uniform(35, 65), 1),
            rank=i + 1,
        ))
    # 按涨幅排序
    sectors.sort(key=lambda s: s.change_pct, reverse=True)
    for i, s in enumerate(sectors):
        s.rank = i + 1

    return FullAnalysis(
        ndx=_mock_status(),
        stocks=stocks,
        sectors=sectors,
        market_breadth={
            "advancing": 65, "declining": 35, "total": 100,
            "adv_volume": 2_500_000_000, "dec_volume": 1_200_000_000,
            "new_highs": 42, "new_lows": 8,
            "breadth_ratio": 1.86,
        },
        sentiment_data={
            "vix": 18.5, "vix_change": -0.8,
            "fear_greed_index": 62, "fear_greed_label": "贪婪",
            "put_call_ratio": 0.85,
            "summary": "市场情绪偏乐观，VIX 处于低位，恐慌贪婪指数显示贪婪",
        },
        source="mock",
        ts=int(time.time() * 1000),
        ndx_analysis_report_path=_find_latest_report(),
    )


# ======================================================================
# NdxAdapter（增强版）
# ======================================================================

class NdxAdapter:
    """NDX 分析适配器——两种接口，自动降级到 mock"""

    def __init__(self, cache_ttl_seconds: int = 300):
        self._status_cache: Optional[NdxStatus] = None
        self._analysis_cache: Optional[FullAnalysis] = None
        self._cached_at: float = 0.0
        self.ttl = cache_ttl_seconds

    # ---- 轻量接口（已有） ----

    def get_status(self, force: bool = False) -> NdxStatus:
        if not force and self._status_cache and (time.time() - self._cached_at) < self.ttl:
            return self._status_cache
        st = self._fetch_live_status() or _mock_status()
        if not st.ndx_analysis_report_path:
            st.ndx_analysis_report_path = _find_latest_report()
        st.ts = int(time.time() * 1000)
        self._status_cache = st
        return st

    # ---- 全量分析接口（新增） ----

    def get_full_analysis(self, force: bool = False) -> FullAnalysis:
        """获取完整分析数据（NDX + 股票 + 板块 + 情绪）"""
        if not force and self._analysis_cache and (time.time() - self._cached_at) < self.ttl:
            return self._analysis_cache
        result = self._fetch_full_analysis() or _mock_full_analysis()
        if not result.ndx_analysis_report_path:
            result.ndx_analysis_report_path = _find_latest_report()
        result.ts = int(time.time() * 1000)
        self._analysis_cache = result
        self._cached_at = time.time()
        return result

    # ---- 实时数据获取 ----

    def _fetch_live_status(self) -> Optional[NdxStatus]:
        try:
            _import_root()
            from data_fetcher import DataFetcher
            from indicators import calc_all_indicators
        except Exception as e:
            logger.warning("NDX live fetch skipped (deps): %s", e)
            return None

        try:
            fetcher = DataFetcher()
            df = fetcher.fetch_index_history({"ticker": "^NDX", "name": "NDX"})
            if df is None or len(df) == 0:
                return None
            df = calc_all_indicators(df)
            last_row = df.iloc[-1]
            last_close = float(last_row["Close"])
            prev_close = float(df.iloc[-2]["Close"]) if len(df) >= 2 else last_close
            change_pct = (last_close / prev_close - 1.0) * 100.0
            ma50 = _safe_float(last_row.get("MA50")) or 0.0
            ma200 = _safe_float(last_row.get("MA200")) or 0.0
            rsi14 = _safe_float(last_row.get("RSI14")) or 50.0
            above_ma200 = ma200 > 0 and last_close > ma200
            sent, sent_label = _classify_sentiment(change_pct, above_ma200, rsi14)
            return NdxStatus(
                symbol="NDX", last_close=last_close, change_pct=change_pct,
                ma50=ma50, ma200=ma200, above_ma200=above_ma200,
                rsi14=rsi14, sentiment=sent, sentiment_label=sent_label,
                summary=_summary(sent_label, change_pct, above_ma200),
                source="live",
            )
        except Exception as e:
            logger.warning("NDX live fetch failed: %s", e)
            return None

    def _fetch_full_analysis(self) -> Optional[FullAnalysis]:
        """尝试用项目原生的分析模块获取全量数据"""
        try:
            _import_root()
            from data_fetcher import DataFetcher
            from indicators import calc_all_indicators
            from config import STOCK_UNIVERSE, SECTOR_ETFS
        except Exception as e:
            logger.warning("Full analysis deps missing: %s", e)
            return None

        try:
            fetcher = DataFetcher()

            # 1. NDX 状态
            ndx_df = fetcher.fetch_index_history({"ticker": "^NDX", "name": "NDX"})
            ndx_status = None
            if ndx_df is not None and len(ndx_df) >= 2:
                ndx_df = calc_all_indicators(ndx_df)
                last_row = ndx_df.iloc[-1]
                last_close = float(last_row["Close"])
                prev_close = float(ndx_df.iloc[-2]["Close"])
                change_pct = (last_close / prev_close - 1.0) * 100.0
                ma50 = _safe_float(last_row.get("MA50")) or 0.0
                ma200 = _safe_float(last_row.get("MA200")) or 0.0
                rsi14 = _safe_float(last_row.get("RSI14")) or 50.0
                above_ma200 = ma200 > 0 and last_close > ma200
                sent, sent_label = _classify_sentiment(change_pct, above_ma200, rsi14)
                ndx_status = NdxStatus(
                    symbol="NDX", last_close=last_close, change_pct=change_pct,
                    ma50=ma50, ma200=ma200, above_ma200=above_ma200,
                    rsi14=rsi14, sentiment=sent, sentiment_label=sent_label,
                    summary=_summary(sent_label, change_pct, above_ma200),
                    source="live",
                )
            else:
                ndx_status = _mock_status()

            # 2. 关键股票分析
            stocks = []
            for sector_name, symbols in STOCK_UNIVERSE.items():
                for sym in symbols:
                    try:
                        info = fetcher.fetch_stock_info(sym) or {}
                        name = info.get("name", sym)
                    except Exception:
                        name = sym
                    try:
                        df = fetcher.fetch_stock_history({"ticker": sym, "name": sym})
                        if df is not None and len(df) >= 2:
                            df = calc_all_indicators(df)
                            last = df.iloc[-1]
                            prev = df.iloc[-2]
                            close_v = float(last["Close"])
                            prev_c = float(prev["Close"])
                            chg_pct = (close_v / prev_c - 1.0) * 100.0
                            ma5_v = _safe_float(last.get("MA5")) or 0.0
                            ma20_v = _safe_float(last.get("MA20")) or 0.0
                            ma60_v = _safe_float(last.get("MA60")) or 0.0
                            rsi_v = _safe_float(last.get("RSI14")) or 50.0
                            macd_dif = _safe_float(last.get("MACD_DIF"))
                            macd_dea = _safe_float(last.get("MACD_DEA"))
                            macd_sig = _macd_signal(macd_dif, macd_dea)
                            # 趋势判断
                            if ma5_v and ma20_v and ma60_v:
                                if ma5_v > ma20_v > ma60_v:
                                    trend = "强势上涨"
                                elif ma5_v > ma20_v:
                                    trend = "上涨"
                                elif ma5_v < ma20_v < ma60_v:
                                    trend = "弱势下跌"
                                elif ma5_v < ma20_v:
                                    trend = "下跌"
                                else:
                                    trend = "震荡"
                            else:
                                trend = "震荡"
                            rec = _recommendation(chg_pct, rsi_v, trend, macd_sig)
                            stocks.append(StockAnalysis(
                                symbol=sym, name=name, sector=sector_name,
                                close=round(close_v, 2), change_pct=round(chg_pct, 2),
                                ma5=round(ma5_v, 2), ma20=round(ma20_v, 2),
                                ma60=round(ma60_v, 2), rsi14=round(rsi_v, 1),
                                macd_signal=macd_sig, trend=trend, recommendation=rec,
                            ))
                        else:
                            stocks.append(StockAnalysis(
                                symbol=sym, name=name, sector=sector_name))
                    except Exception as e:
                        logger.debug("Stock %s fetch failed: %s", sym, e)
                        stocks.append(StockAnalysis(
                            symbol=sym, name=name, sector=sector_name))

            # 3. 板块轮动分析
            sectors = []
            for name, etf in SECTOR_ETFS.items():
                try:
                    df = fetcher.fetch_etf_history({"ticker": etf, "name": name})
                    if df is not None and len(df) >= 2:
                        df = calc_all_indicators(df)
                        last = df.iloc[-1]
                        prev = df.iloc[-2]
                        close_v = float(last["Close"])
                        prev_c = float(prev["Close"])
                        chg_pct = (close_v / prev_c - 1.0) * 100.0
                        ma20_v = _safe_float(last.get("MA20")) or 0.0
                        rsi_v = _safe_float(last.get("RSI14")) or 50.0
                        sectors.append(SectorAnalysis(
                            name=name, etf=etf,
                            close=round(close_v, 2), change_pct=round(chg_pct, 2),
                            ma20=round(ma20_v, 2), rsi14=round(rsi_v, 1),
                            rank=0,
                        ))
                    else:
                        sectors.append(SectorAnalysis(name=name, etf=etf))
                except Exception as e:
                    logger.debug("Sector %s fetch failed: %s", etf, e)
                    sectors.append(SectorAnalysis(name=name, etf=etf))
            # 排名
            if sectors and all(s.change_pct != 0 for s in sectors):
                sectors.sort(key=lambda s: s.change_pct, reverse=True)
                for i, s in enumerate(sectors):
                    s.rank = i + 1

            # 4. 市场宽度 & 情绪（尝试用 analysis 模块）
            breadth = {"advancing": 0, "declining": 0, "total": 0,
                       "adv_volume": 0, "dec_volume": 0,
                       "new_highs": 0, "new_lows": 0, "breadth_ratio": 1.0}
            sentiment = {"vix": 0, "vix_change": 0, "fear_greed_index": 50,
                         "fear_greed_label": "中性", "put_call_ratio": 1.0,
                         "summary": ""}
            try:
                from analysis import analyze_market_breadth, vix_sentiment
                breadth_result = analyze_market_breadth(stocks)
                if breadth_result:
                    breadth.update(breadth_result)
                sentiment_result = vix_sentiment(fetcher)
                if sentiment_result:
                    sentiment.update(sentiment_result)
            except Exception as e:
                logger.debug("Market breadth/sentiment skipped: %s", e)

            return FullAnalysis(
                ndx=ndx_status, stocks=stocks, sectors=sectors,
                market_breadth=breadth, sentiment_data=sentiment,
                source="live",
            )
        except Exception as e:
            logger.warning("Full analysis fetch failed: %s", e)
            return None


__all__ = ["NdxAdapter", "NdxStatus", "StockAnalysis", "SectorAnalysis", "FullAnalysis"]
