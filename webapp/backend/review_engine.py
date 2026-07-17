# -*- coding: utf-8 -*-
"""
review_engine.py — 交易复盘自动化引擎 (v2.3 Phase 3)

功能:
  - 监听沙盒卖出事件，自动生成复盘报告
  - 错误模式识别（追涨杀跌/恐慌卖出/过度交易等）
  - 自然语言总结生成
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================
# 错误模式定义
# ============================================================

MISTAKE_PATTERNS = {
    "chase_high": {
        "name": "追涨杀跌",
        "description": "买入时价格高于近期高点，且短期内亏损卖出",
        "suggestion": "避免在价格大幅上涨后追高买入。等待回调或确认趋势后再入场。",
    },
    "panic_sell": {
        "name": "恐慌卖出",
        "description": "持有不足 2 天且亏损 > 3% 时卖出",
        "suggestion": "短期波动是正常的。给交易更多时间，不要因为小幅亏损就恐慌离场。",
    },
    "overtrade": {
        "name": "过度交易",
        "description": "单日交易次数过多",
        "suggestion": "减少交易频率。每次交易前问自己：这个决策是基于分析还是情绪？",
    },
    "no_stop_loss": {
        "name": "无止损交易",
        "description": "买入时未设置止损价格",
        "suggestion": "每笔交易前都应该设定止损位。这是保护本金的第一道防线。",
    },
    "heavy_position": {
        "name": "重仓单票",
        "description": "单只股票仓位超过 40%",
        "suggestion": "分散投资可以降低风险。建议单只股票仓位不超过 20-30%。",
    },
    "no_review": {
        "name": "不复盘",
        "description": "卖出后 24 小时内未写交易日志",
        "suggestion": "复盘是进步的关键。每笔交易后花 5 分钟记录：为什么买？为什么卖？学到了什么？",
    },
}


def detect_mistakes(trade: dict, context: dict) -> list[dict]:
    """
    检测交易中的错误模式

    参数:
        trade: 交易记录 {symbol, side, quantity, price, ts, pnl?, holding_days?}
        context: 上下文 {recent_trades, account_size, has_stop_loss, has_journal}

    返回:
        list[dict]: 检测到的错误模式列表
    """
    mistakes = []

    # 恐慌卖出检测
    if trade.get("side") == "SELL":
        holding_days = trade.get("holding_days", 999)
        pnl_pct = trade.get("pnl_pct", 0)
        if holding_days <= 2 and pnl_pct < -3:
            mistakes.append({
                "pattern": "panic_sell",
                "confidence": 0.8,
                "detail": f"持有仅 {holding_days} 天，亏损 {pnl_pct:.1f}% 时卖出",
            })

    # 重仓单票检测
    position_pct = trade.get("position_pct", 0)
    if position_pct > 40:
        mistakes.append({
            "pattern": "heavy_position",
            "confidence": 0.9,
            "detail": f"单票仓位 {position_pct:.1f}%，超过建议的 30% 上限",
        })

    # 无止损检测
    if not context.get("has_stop_loss", True):
        mistakes.append({
            "pattern": "no_stop_loss",
            "confidence": 0.7,
            "detail": "交易计划中未设置止损价格",
        })

    # 过度交易检测
    recent_trades = context.get("recent_trades", [])
    today = datetime.now().date()
    today_trades = [t for t in recent_trades if datetime.fromtimestamp(t["ts"]/1000).date() == today]
    if len(today_trades) >= 5:
        mistakes.append({
            "pattern": "overtrade",
            "confidence": 0.75,
            "detail": f"今日已交易 {len(today_trades)} 笔，可能存在过度交易",
        })

    return mistakes


def generate_review_summary(trade: dict, mistakes: list[dict], score: float) -> str:
    """
    生成自然语言复盘总结

    参数:
        trade: 交易记录
        mistakes: 检测到的错误模式
        score: 综合评分 (0-100)

    返回:
        str: 复盘总结文本
    """
    symbol = trade.get("symbol", "未知")
    side = "买入" if trade.get("side") == "BUY" else "卖出"
    pnl = trade.get("pnl", 0)
    pnl_pct = trade.get("pnl_pct", 0)

    # 开头：交易结果
    if pnl > 0:
        result_text = f"这笔 {symbol} 的{side}交易盈利了 ${abs(pnl):.2f}（+{pnl_pct:.1f}%），做得不错！"
    elif pnl < 0:
        result_text = f"这笔 {symbol} 的{side}交易亏损了 ${abs(pnl):.2f}（{pnl_pct:.1f}%）。"
    else:
        result_text = f"这笔 {symbol} 的{side}交易基本持平。"

    # 中间：错误模式
    if mistakes:
        mistake_texts = []
        for m in mistakes:
            pattern = MISTAKE_PATTERNS.get(m["pattern"], {})
            mistake_texts.append(f"• {pattern.get('name', m['pattern'])}：{m.get('detail', '')}")
        mistakes_section = "\n".join(mistake_texts)
        mistakes_intro = "\n\n需要改进的地方：\n" + mistakes_section
    else:
        mistakes_intro = "\n\n这笔交易执行得很好，没有明显的错误模式。"

    # 结尾：建议
    if score >= 80:
        advice = "\n\n继续保持！你的交易纪律很好。"
    elif score >= 60:
        advice = "\n\n整体不错，但还有提升空间。注意上面提到的问题。"
    else:
        advice = "\n\n这笔交易有一些需要改进的地方。建议回顾相关课程内容，特别是风险管理和交易计划部分。"

    return result_text + mistakes_intro + advice


def calculate_review_score(trade: dict, mistakes: list[dict]) -> float:
    """
    计算复盘综合评分

    参数:
        trade: 交易记录
        mistakes: 错误模式列表

    返回:
        float: 0-100 的评分
    """
    base_score = 70  # 基础分

    # 盈亏影响
    pnl_pct = trade.get("pnl_pct", 0)
    if pnl_pct > 5:
        base_score += 15
    elif pnl_pct > 0:
        base_score += 10
    elif pnl_pct > -3:
        base_score += 0
    elif pnl_pct > -5:
        base_score -= 10
    else:
        base_score -= 20

    # 错误模式扣分
    for m in mistakes:
        confidence = m.get("confidence", 0.5)
        base_score -= int(10 * confidence)

    # 持有时间加分（长期持有通常更好）
    holding_days = trade.get("holding_days", 0)
    if holding_days >= 5:
        base_score += 5
    elif holding_days >= 10:
        base_score += 10

    return max(0, min(100, base_score))


def create_trade_review(trade: dict, context: dict) -> dict:
    """
    创建完整的交易复盘报告

    参数:
        trade: 交易记录
        context: 上下文信息

    返回:
        dict: 复盘报告
    """
    mistakes = detect_mistakes(trade, context)
    score = calculate_review_score(trade, mistakes)
    summary = generate_review_summary(trade, mistakes, score)

    return {
        "trade_id": trade.get("order_id", ""),
        "symbol": trade.get("symbol", ""),
        "side": trade.get("side", ""),
        "quantity": trade.get("quantity", 0),
        "price": trade.get("price", 0),
        "pnl": trade.get("pnl", 0),
        "pnl_pct": trade.get("pnl_pct", 0),
        "holding_days": trade.get("holding_days", 0),
        "score": round(score, 1),
        "mistakes": mistakes,
        "summary": summary,
        "created_at": int(datetime.now().timestamp() * 1000),
    }


__all__ = [
    "MISTAKE_PATTERNS",
    "detect_mistakes",
    "generate_review_summary",
    "calculate_review_score",
    "create_trade_review",
]
