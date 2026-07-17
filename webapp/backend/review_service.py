# -*- coding: utf-8 -*-
"""
review_service.py — 复盘编排服务 (v2.4 Phase 2)

功能:
  - 从 sandbox_orders 做 FIFO 配对，计算卖出单的真实盈亏与持有天数
  - 组装 context（近期交易/止损/仓位），调用 review_engine 生成复盘
  - 落库 trade_reviews 并通过 xp_service 发放复盘 XP
"""

import logging
from datetime import datetime
from typing import Optional

from webapp.backend.review_engine import create_trade_review
from webapp.backend.xp_service import award_xp

logger = logging.getLogger(__name__)


def compute_sell_pnl(orders: list[dict], symbol: str, sell_qty: float, sell_price: float, sell_ts: int) -> dict:
    """
    FIFO 配对历史买单，计算卖出盈亏

    参数:
        orders: 全部沙盒订单（任意顺序，函数内部按 ts 排序）
        symbol: 卖出的股票代码
        sell_qty: 卖出数量
        sell_price: 卖出价格
        sell_ts: 卖出时间戳 (ms)

    返回:
        dict: {pnl, pnl_pct, holding_days, avg_cost}
    """
    # 取该 symbol 的订单，按时间正序
    sym_orders = sorted(
        [o for o in orders if o.get("symbol") == symbol],
        key=lambda o: o.get("ts", 0),
    )

    # FIFO 买单队列（排除本次卖出之后的单）
    buy_queue: list[dict] = []
    for o in sym_orders:
        if o.get("ts", 0) >= sell_ts:
            break
        if o.get("side") == "BUY":
            buy_queue.append({"qty": o["quantity"], "price": o["price"], "ts": o["ts"]})
        elif o.get("side") == "SELL":
            # 之前的卖出消耗 FIFO 队列
            remaining = o["quantity"]
            while remaining > 0 and buy_queue:
                if buy_queue[0]["qty"] <= remaining:
                    remaining -= buy_queue[0]["qty"]
                    buy_queue.pop(0)
                else:
                    buy_queue[0]["qty"] -= remaining
                    remaining = 0

    if not buy_queue:
        return {"pnl": 0, "pnl_pct": 0, "holding_days": 0, "avg_cost": 0}

    # 本次卖出按 FIFO 配对
    remaining = sell_qty
    total_cost = 0.0
    earliest_ts: Optional[int] = None
    matched_qty = 0.0

    for lot in buy_queue:
        if remaining <= 0:
            break
        take = min(lot["qty"], remaining)
        total_cost += take * lot["price"]
        matched_qty += take
        remaining -= take
        if earliest_ts is None:
            earliest_ts = lot["ts"]

    if matched_qty <= 0:
        return {"pnl": 0, "pnl_pct": 0, "holding_days": 0, "avg_cost": 0}

    avg_cost = total_cost / matched_qty
    pnl = (sell_price - avg_cost) * matched_qty
    pnl_pct = round((sell_price / avg_cost - 1) * 100, 2) if avg_cost > 0 else 0

    holding_days = 0.0
    if earliest_ts:
        holding_days = round((sell_ts - earliest_ts) / (1000 * 60 * 60 * 24), 1)

    return {
        "pnl": round(pnl, 2),
        "pnl_pct": pnl_pct,
        "holding_days": holding_days,
        "avg_cost": round(avg_cost, 4),
    }


def auto_review_on_sell(store, symbol: str, quantity: int, price: float, order_id: str, ts: int) -> Optional[dict]:
    """
    卖出后自动生成复盘报告并落库

    参数:
        store: UserStore 实例
        symbol: 股票代码
        quantity: 卖出数量
        price: 卖出价格
        order_id: 订单 ID
        ts: 时间戳 (ms)

    返回:
        dict: 复盘报告；异常时返回 None（Graceful Degradation）
    """
    try:
        # 已存在则不重复生成（幂等）
        existing = store.review_get_by_trade(order_id)
        if existing:
            return existing

        orders = store.sandbox_orders_list(500)
        pnl_info = compute_sell_pnl(orders, symbol, quantity, price, ts)

        # 组装 context
        account = store.sandbox_get()
        total_equity = account.get("cash", 0) + sum(
            p.get("quantity", 0) * p.get("avg_cost", 0)
            for p in account.get("positions", [])
        )
        position_value = quantity * price
        position_pct = round(position_value / total_equity * 100, 1) if total_equity > 0 else 0

        # 检查是否有止损计划
        has_stop_loss = False
        try:
            plans = store.trade_plan_list(20)
            has_stop_loss = any(
                p.get("symbol") == symbol and p.get("stop_loss_price")
                for p in plans
            )
        except Exception:
            pass

        trade = {
            "order_id": order_id,
            "symbol": symbol,
            "side": "SELL",
            "quantity": quantity,
            "price": price,
            "ts": ts,
            "pnl": pnl_info["pnl"],
            "pnl_pct": pnl_info["pnl_pct"],
            "holding_days": pnl_info["holding_days"],
            "position_pct": position_pct,
        }
        context = {
            "recent_trades": orders,
            "has_stop_loss": has_stop_loss,
            "has_journal": False,
        }

        review = create_trade_review(trade, context)
        store.review_save(review)

        # 更新当日打卡 + 发放 XP
        today = datetime.now().date().isoformat()
        store.checkin_touch(today, "reviews_done", 1)
        award_xp(store, "review", order_id, 15)

        logger.info(f"复盘已生成: {symbol} SELL {quantity}@{price} pnl={pnl_info['pnl']} score={review['score']}")
        return review

    except Exception as e:
        logger.warning(f"复盘自动生成失败: {e}")
        return None


__all__ = ["compute_sell_pnl", "auto_review_on_sell"]
