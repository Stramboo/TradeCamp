# -*- coding: utf-8 -*-
"""
ai_advisor.py — AI 推荐引擎

不是简单展示数据，而是替你分析每一只股票，给出：
  1. 综合评分 (0-100) — 越高越值得操作
  2. 操作建议 (BUY/HOLD/SELL)
  3. 一句话理由 — 像真人一样解释
  4. 因子明细 — 为什么得这个分

多因子模型（离线可用 + 可选LLM增强）：
  - 趋势因子   (30%)：均线排列、价格位置
  - 动量因子   (25%)：MACD、KDJ 交叉信号
  - 反转因子   (20%)：RSI、布林带超买超卖
  - 量价因子   (15%)：成交量变化、OBV方向
  - 波动因子   (10%)：ATR、布林带宽度
"""

from __future__ import annotations

import logging
import math
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))

if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def _safe_last(df: pd.DataFrame, col: str) -> Optional[float]:
    """安全读取最后一行的某个列值"""
    try:
        v = float(df[col].iloc[-1])
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except (KeyError, IndexError, ValueError):
        return None


def _safe_prev(df: pd.DataFrame, col: str, offset: int = 1) -> Optional[float]:
    try:
        idx = -1 - offset
        v = float(df[col].iloc[idx])
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except (KeyError, IndexError, ValueError):
        return None


# ============================================================
# 因子计算函数
# ============================================================

def factor_trend(df: pd.DataFrame) -> tuple[float, str]:
    """
    趋势因子 (0-30)：均线排列 + MA200 位置
    - 多头排列 MA5>MA20>MA60 → 高分
    - 空头排列 → 低分
    """
    ma5 = _safe_last(df, "MA5") or 0
    ma10 = _safe_last(df, "MA10") or 0
    ma20 = _safe_last(df, "MA20") or 0
    ma60 = _safe_last(df, "MA60") or 0
    close = _safe_last(df, "Close") or 0

    score = 15.0  # 基准
    reasons = []

    if ma5 and ma20 and ma5 > ma20:
        score += 5
        reasons.append("短线向上 (MA5>MA20)")
    elif ma5 and ma20:
        score -= 3
        reasons.append("短线偏弱 (MA5<MA20)")

    if ma20 and ma60 and ma20 > ma60:
        score += 5
        reasons.append("中线向上 (MA20>MA60)")
    elif ma20 and ma60:
        score -= 5
        reasons.append("中线偏弱 (MA20<MA60)")

    if close and ma60 and close > ma60:
        score += 5
    elif close and ma60:
        score -= 5
        reasons.append("价格低于MA60")

    return max(0, min(30, score)), "; ".join(reasons) if reasons else "趋势中性"


def factor_momentum(df: pd.DataFrame) -> tuple[float, str]:
    """
    动量因子 (0-25)：MACD + KDJ 信号
    """
    dif = _safe_last(df, "DIF")
    dea = _safe_last(df, "DEA")
    hist = _safe_last(df, "MACD_HIST")
    prev_hist = _safe_prev(df, "MACD_HIST")
    k = _safe_last(df, "K")
    d = _safe_last(df, "D")
    j = _safe_last(df, "J")

    score = 12.0
    reasons = []

    # MACD
    if dif is not None and dea is not None:
        if dif > dea:
            score += 6
            reasons.append("MACD 多头")
        else:
            score -= 3

        if hist is not None and prev_hist is not None and hist > prev_hist:
            score += 3
            reasons.append("MACD 柱放大")

        if hist is not None and prev_hist is not None and hist > 0 and prev_hist <= 0:
            score += 4
            reasons.append("MACD 刚金叉")

    # KDJ
    if k is not None and d is not None:
        if k > d:
            score += 3
        if j is not None:
            if j is not None and j < 20:
                score += 4
                reasons.append("KDJ 超卖区，有反弹动力")
            elif j is not None and j > 80:
                score -= 4
                reasons.append("KDJ 超买区，回调风险")

    return max(0, min(25, score)), "; ".join(reasons) if reasons else "动量中性"


def factor_reversal(df: pd.DataFrame) -> tuple[float, str]:
    """
    反转因子 (0-20)：RSI + 布林带位置
    """
    rsi = _safe_last(df, "RSI")
    close = _safe_last(df, "Close") or 0
    upper = _safe_last(df, "BOLL_UPPER") or 0
    lower = _safe_last(df, "BOLL_LOWER") or 0

    score = 10.0
    reasons = []

    if rsi is not None:
        if rsi < 30:
            score += 8
            reasons.append(f"RSI 严重超卖 ({rsi:.0f})，反弹概率高")
        elif rsi < 40:
            score += 4
            reasons.append(f"RSI 偏低 ({rsi:.0f})，有反弹空间")
        elif rsi > 70:
            score -= 6
            reasons.append(f"RSI 超买 ({rsi:.0f})，回调风险")
        elif rsi > 60:
            score -= 2

    # 布林带
    if close and upper and lower and upper > lower:
        bb_width = (upper - lower) / close
        if close <= lower * 1.02:
            score += 5
            reasons.append("价格接近布林下轨，技术支撑")
        elif close >= upper * 0.98:
            score -= 5
            reasons.append("价格接近布林上轨，技术压力")

    return max(0, min(20, score)), "; ".join(reasons) if reasons else "超买超卖中性"


def factor_volume(df: pd.DataFrame) -> tuple[float, str]:
    """
    量价因子 (0-15)：成交量趋势 + OBV
    """
    vol = _safe_last(df, "Volume") or 0
    vol_ma = 0
    try:
        vol_ma = float(df["Volume"].tail(20).mean())
    except Exception:
        pass
    obv = _safe_last(df, "OBV")
    prev_obv = _safe_prev(df, "OBV", 5)
    close = _safe_last(df, "Close") or 0
    prev_close = _safe_prev(df, "Close", 1) or close

    score = 7.5
    reasons = []

    if vol_ma > 0 and vol > vol_ma * 1.5:
        score += 3
        reasons.append("放量（显著高于20日均量）")
    elif vol_ma > 0 and vol > vol_ma * 1.2:
        score += 1.5
    elif vol_ma > 0 and vol < vol_ma * 0.5:
        score -= 2
        reasons.append("缩量")

    if obv and prev_obv and obv > prev_obv:
        score += 3
        reasons.append("OBV 上升，资金流入")

    if close and prev_close and close > prev_close:
        score += 1.5

    return max(0, min(15, score)), "; ".join(reasons) if reasons else "量价中性"


def factor_volatility(df: pd.DataFrame) -> tuple[float, str]:
    """
    波动因子 (0-10)：ATR 相对值 + 布林宽度
    """
    atr = _safe_last(df, "ATR")
    close = _safe_last(df, "Close") or 1

    score = 5.0
    reasons = []

    if atr and close:
        atr_pct = atr / close * 100
        if atr_pct > 5:
            score -= 3
            reasons.append(f"高波动率 ({atr_pct:.1f}%)，适合短线但不稳")
        elif atr_pct > 3:
            score -= 1
        elif atr_pct < 1.5:
            score += 2
            reasons.append("低波动，走势稳健")

    return max(0, min(10, score)), "; ".join(reasons) if reasons else "波动中性"


# ============================================================
# 综合评分 + 推荐
# ============================================================

@dataclass
class StockRecommendation:
    symbol: str
    name: str
    sector: str
    price: float
    change_pct: float
    score: int                      # 0-100
    action: str                     # "STRONG_BUY" | "BUY" | "HOLD" | "SELL" | "STRONG_SELL"
    action_label: str               # "强烈买入" | "买入" | "持有" | "卖出" | "强烈卖出"
    reason: str                     # 一句话理由
    factors: dict                   # {trend: {score, detail}, momentum: {...}, ...}
    rsi: float | None
    macd_signal: str                # "bull" | "bear" | "neutral"
    support: float | None           # 最近支撑位
    resistance: float | None        # 最近压力位


def _action_from_score(score: int) -> tuple[str, str]:
    if score >= 72:
        return "STRONG_BUY", "强烈买入"
    if score >= 58:
        return "BUY", "买入"
    if score >= 42:
        return "HOLD", "持有"
    if score >= 28:
        return "SELL", "卖出"
    return "STRONG_SELL", "强烈卖出"


def analyze_stock(symbol: str, name: str, sector: str, df: pd.DataFrame,
                  price: float, change_pct: float) -> StockRecommendation:
    """分析单只股票 — 多因子综合打分"""

    # 计算各因子
    trend_score, trend_detail = factor_trend(df)
    momentum_score, momentum_detail = factor_momentum(df)
    reversal_score, reversal_detail = factor_reversal(df)
    volume_score, volume_detail = factor_volume(df)
    volatility_score, volatility_detail = factor_volatility(df)

    total = trend_score + momentum_score + reversal_score + volume_score + volatility_score

    # 近期涨跌幅微调（追涨杀跌心理纠正）
    if change_pct > 5:
        total -= 3   # 追涨有风险
    elif change_pct < -5:
        total += 3   # 超跌有反弹机会

    total = max(0, min(100, round(total)))

    action, action_label = _action_from_score(total)

    # 支撑/压力
    boll_lower = _safe_last(df, "BOLL_LOWER")
    boll_upper = _safe_last(df, "BOLL_UPPER")
    ma20 = _safe_last(df, "MA20")

    # 一句话理由——选最重要的2-3个因子
    detail_parts = []
    if trend_score >= 20:
        detail_parts.append(trend_detail)
    if momentum_score >= 15:
        detail_parts.append(momentum_detail)
    if reversal_score >= 12:
        detail_parts.append(reversal_detail)
    if not detail_parts:
        detail_parts = [trend_detail, momentum_detail, reversal_detail]

    reason = " | ".join(detail_parts[:2])

    return StockRecommendation(
        symbol=symbol,
        name=name,
        sector=sector,
        price=round(price, 2),
        change_pct=round(change_pct, 2),
        score=total,
        action=action,
        action_label=action_label,
        reason=reason,
        factors={
            "trend": {"score": round(trend_score, 1), "max": 30, "detail": trend_detail},
            "momentum": {"score": round(momentum_score, 1), "max": 25, "detail": momentum_detail},
            "reversal": {"score": round(reversal_score, 1), "max": 20, "detail": reversal_detail},
            "volume": {"score": round(volume_score, 1), "max": 15, "detail": volume_detail},
            "volatility": {"score": round(volatility_score, 1), "max": 10, "detail": volatility_detail},
        },
        rsi=_safe_last(df, "RSI"),
        macd_signal="bull" if (_safe_last(df, "DIF") or 0) > (_safe_last(df, "DEA") or 0) else "bear",
        support=round(boll_lower, 2) if boll_lower else None,
        resistance=round(boll_upper, 2) if boll_upper else None,
    )


# ============================================================
# 每日推荐入口
# ============================================================

@dataclass
class DailyRecommendations:
    generated_at: str
    total_stocks: int
    strong_buy: list[StockRecommendation]
    buy: list[StockRecommendation]
    hold: list[StockRecommendation]
    sell: list[StockRecommendation]
    strong_sell: list[StockRecommendation]
    top_picks: list[StockRecommendation]    # 按评分 TOP 5
    market_summary: str
    all_stocks: list[StockRecommendation]


def _load_data_and_indicators(symbols: list[str]) -> dict[str, pd.DataFrame]:
    """拉取数据 + 计算指标"""
    try:
        from data_fetcher import DataFetcher
        from indicators import calc_all_indicators

        fetcher = DataFetcher()
        batch = fetcher.fetch_stocks_batch(symbols, period="6mo")

        result = {}
        for sym, df in batch.items():
            if df.empty or len(df) < 30:
                continue
            df = calc_all_indicators(df)
            result[sym] = df
        return result
    except Exception as e:
        logger.warning("Full data fetch failed: %s", e)
        return {}


def _get_realtime_prices(symbols: list[str]) -> dict[str, float]:
    """获取实时价格"""
    try:
        from data_fetcher import DataFetcher
        fetcher = DataFetcher()
        batch = fetcher.fetch_stocks_batch(symbols, period="5d")
        prices = {}
        for sym, df in batch.items():
            if not df.empty and "Close" in df.columns:
                prices[sym] = float(df["Close"].iloc[-1])
        return prices
    except Exception:
        return {}


def generate_daily_recommendations_from_engine(engine_adapter) -> DailyRecommendations:
    """
    从引擎已有的行情数据生成 AI 推荐（不额外拉 yfinance）
    引擎实盘模式已经在 market_data 里有缓存数据。
    也支持 MockEngine —— 直接调用其 fetch_history 方法。
    """
    import sys, os
    _ROOT2 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _ROOT2 not in sys.path:
        sys.path.insert(0, _ROOT2)

    from config import STOCK_UNIVERSE

    all_symbols = []
    sector_map = {}
    for sector, syms in STOCK_UNIVERSE.items():
        all_symbols.extend(syms)
        for s in syms:
            sector_map[s] = sector

    # 兼容 MockEngine 和 EngineAdapter
    is_mock = not hasattr(engine_adapter, '_engine')
    if is_mock:
        eng_wrapper = engine_adapter  # MockEngine itself
        prices = getattr(eng_wrapper, 'prices', {}) or {}
    else:
        eng_wrapper = engine_adapter._engine
        prices = getattr(engine_adapter, "prices", {}) or {}

    results: list[StockRecommendation] = []
    for sym in all_symbols:
        try:
            if hasattr(eng_wrapper, 'market_data') and hasattr(eng_wrapper.market_data, 'fetch_history'):
                df = eng_wrapper.market_data.fetch_history(sym, period="6mo")
            elif hasattr(eng_wrapper, 'fetch_history'):
                df = eng_wrapper.fetch_history(sym, period="6mo")
            else:
                df = None
        except Exception:
            df = None

        if df is None or df.empty or len(df) < 30:
            results.append(StockRecommendation(
                symbol=sym, name=sym, sector=sector_map.get(sym, ""),
                price=prices.get(sym, 0), change_pct=0, score=50,
                action="HOLD", action_label="持有",
                reason="数据不足，无法分析", factors={},
                rsi=None, macd_signal="neutral",
                support=None, resistance=None,
            ))
            continue

        try:
            from indicators import calc_all_indicators
            df = calc_all_indicators(df)
        except Exception:
            pass

        close = float(df["Close"].iloc[-1]) if "Close" in df.columns else prices.get(sym, 0)
        prev_c = float(df["Close"].iloc[-2]) if len(df) >= 2 and "Close" in df.columns else close
        chg_pct = (close / prev_c - 1) * 100 if prev_c else 0

        rec = analyze_stock(sym, sym, sector_map.get(sym, ""), df,
                            price=prices.get(sym, close),
                            change_pct=chg_pct)
        results.append(rec)

    strong_buy = [r for r in results if r.action == "STRONG_BUY"]
    buy = [r for r in results if r.action == "BUY"]
    hold = [r for r in results if r.action == "HOLD"]
    sell = [r for r in results if r.action == "SELL"]
    strong_sell = [r for r in results if r.action == "STRONG_SELL"]
    top_picks = sorted(results, key=lambda r: r.score, reverse=True)[:5]

    avg_score = sum(r.score for r in results) / max(len(results), 1)
    if avg_score >= 60:
        market_summary = f"市场偏强，均分 {avg_score:.0f}/100"
    elif avg_score >= 45:
        market_summary = f"市场中性震荡，均分 {avg_score:.0f}/100"
    else:
        market_summary = f"市场偏弱，均分 {avg_score:.0f}/100"

    return DailyRecommendations(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        total_stocks=len(results),
        strong_buy=strong_buy, buy=buy, hold=hold, sell=sell, strong_sell=strong_sell,
        top_picks=top_picks, market_summary=market_summary, all_stocks=results,
    )


def _rec_to_dict(r: StockRecommendation) -> dict:
    return {
        "symbol": r.symbol,
        "name": r.name,
        "sector": r.sector,
        "price": r.price,
        "change_pct": r.change_pct,
        "score": r.score,
        "action": r.action,
        "action_label": r.action_label,
        "reason": r.reason,
        "factors": r.factors,
        "rsi": r.rsi,
        "macd_signal": r.macd_signal,
        "support": r.support,
        "resistance": r.resistance,
    }


def recommendations_to_dict(dr: DailyRecommendations) -> dict:
    return {
        "generated_at": dr.generated_at,
        "total_stocks": dr.total_stocks,
        "market_summary": dr.market_summary,
        "strong_buy": [_rec_to_dict(r) for r in dr.strong_buy],
        "buy": [_rec_to_dict(r) for r in dr.buy],
        "hold": [_rec_to_dict(r) for r in dr.hold],
        "sell": [_rec_to_dict(r) for r in dr.sell],
        "strong_sell": [_rec_to_dict(r) for r in dr.strong_sell],
        "top_picks": [_rec_to_dict(r) for r in dr.top_picks],
        "all": [_rec_to_dict(r) for r in dr.all_stocks],
    }


__all__ = [
    "generate_daily_recommendations_from_engine", "recommendations_to_dict",
    "StockRecommendation", "DailyRecommendations", "analyze_stock",
]
