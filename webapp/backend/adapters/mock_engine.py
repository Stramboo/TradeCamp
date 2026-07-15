# -*- coding: utf-8 -*-
"""
mock_engine.py — 离线 Mock 交易引擎（演示用 / CI 用）

设计目的：
- 不依赖 yfinance、Alpaca、网络。
- 持续推送随机 tick + 偶尔的假信号 + 假订单事件 + 假净值曲线。
- 接口与真实 TradingEngine **保持兼容**：同样暴露 account/positions/orders
  + tick 回调 + 信号回调。这样未来切换到真引擎时，前端不动一行代码。

数据来源：
- 6 只"股": NVDA, AAPL, MSFT, GOOGL, AMZN, TSLA
- 初始价随机但合理（NVDA 480, AAPL 175, MSFT 420, …）
- 每一秒推进一次随机游走（±0.5%）
- 每 5~8 秒随机触发一条 BUY/SELL 信号，偶尔下单
"""

from __future__ import annotations

import asyncio
import logging
import math
import random
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Awaitable, Callable, Optional

logger = logging.getLogger(__name__)

SYMBOLS = ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
BASE_PRICES = {
    "NVDA": 480.00, "AAPL": 175.00, "MSFT": 420.00,
    "GOOGL": 142.00, "AMZN": 178.00, "TSLA": 248.00,
}


@dataclass
class Tick:
    symbol: str
    price: float
    ts: float                  # epoch ms

    def to_dict(self):
        return {"symbol": self.symbol, "price": round(self.price, 2),
                "ts": int(self.ts)}


@dataclass
class Position:
    symbol: str
    quantity: int
    avg_cost: float
    last_price: float = 0.0

    @property
    def market_value(self) -> float:
        p = self.last_price or self.avg_cost
        return round(p * self.quantity, 2)

    @property
    def unrealized_pnl(self) -> float:
        p = self.last_price or self.avg_cost
        return round((p - self.avg_cost) * self.quantity, 2)

    @property
    def unrealized_pnl_pct(self) -> float:
        p = self.last_price or self.avg_cost
        if self.avg_cost == 0:
            return 0.0
        return round((p / self.avg_cost - 1.0) * 100.0, 4)

    def to_dict(self):
        return {
            "symbol": self.symbol, "quantity": self.quantity,
            "avg_cost": round(self.avg_cost, 4),
            "last_price": round(self.last_price or self.avg_cost, 2),
            "market_value": self.market_value,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_pct": self.unrealized_pnl_pct,
        }


@dataclass
class Order:
    order_id: str
    symbol: str
    side: str                 # "BUY" / "SELL"
    quantity: int
    price: float
    status: str               # "filled" / "rejected" / "pending"
    ts: float
    note: str = ""
    rejection_code: int = 0

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "avg_fill_price": round(self.price, 4),
            "commission": 0.0,
            "status": self.status,
            "note": self.note,
            "rejection_code": self.rejection_code,
            "ts": int(self.ts),
        }


@dataclass
class Signal:
    symbol: str
    action: str                # "BUY" / "SELL" / "HOLD"
    strength: float
    reason: str
    ts: float

    def to_dict(self):
        return {
            "symbol": self.symbol, "action": self.action,
            "strength": round(self.strength, 2),
            "reason": self.reason, "ts": int(self.ts),
        }


class MockEngine:
    """Mock 交易引擎；尽量保持 TradingEngine 接口一致"""

    INITIAL_CASH = 100000.0

    def __init__(self):
        self.cash: float = self.INITIAL_CASH
        self.initial_cash: float = self.INITIAL_CASH

        # 价格状态
        self.prices: dict[str, float] = dict(BASE_PRICES)
        self.history: dict[str, list[dict]] = {
            sym: [] for sym in SYMBOLS
        }
        self.start_time = time.time()

        # 持仓
        self.positions: dict[str, Position] = {}

        # 订单
        self.orders: list[Order] = []

        # 信号记录
        self.signals: list[Signal] = []

        # 净值历史 (用于画 EquityCurve)
        self.equity_history: list[dict] = []

        # 模拟启动时先建一个仓位，制造"看起来不那么空"的 Dashboard
        self._seed_initial_position()

    # ---------- 历史 / OHLC ----------

    def ohlc(self, symbol: str, interval: str = "1m", limit: int = 120) -> list[dict]:
        """返回 K 线数据（生成式）"""
        if symbol not in self.prices:
            return []
        history = self.history.setdefault(symbol, [])
        # 缺数据就生成一段
        if not history:
            self._seed_history(symbol, limit=limit)
        out = history[-limit:]
        # 转换为 ohlc/candlestick 友好格式
        return [
            {"t": int(c["ts"]), "o": c["open"], "h": c["high"],
             "l": c["low"], "c": c["close"], "v": c["volume"]}
            for c in out
        ]

    def fetch_history(self, symbol: str, period: str = "6mo", interval: str = "1d") -> "pd.DataFrame":
        """返回历史数据 DataFrame（兼容 AI 推荐引擎调用）"""
        import pandas as pd
        from datetime import datetime, timedelta
        if symbol not in self.prices:
            return pd.DataFrame()
        # 生成足够多的日线数据（~180 天）
        n_days = 180
        history = self.history.setdefault(symbol, [])
        need = n_days - len(history)
        if need > 0:
            self._seed_history(symbol, limit=max(need, 200))
        history = self.history[symbol]
        # 取最近 n_days 条
        data = history[-n_days:]
        df = pd.DataFrame(data)
        if df.empty:
            return df
        df = df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
        df["Date"] = pd.to_datetime(df["ts"], unit="s")
        df = df.set_index("Date")
        df = df[["Open", "High", "Low", "Close", "Volume"]]
        return df

    def _seed_history(self, symbol: str, limit: int = 200) -> None:
        """生成 limit 根 1 分钟 K 线"""
        base = self.prices[symbol]
        now = time.time()
        price = base * 0.95                  # 比"当前价"略低一点点制造上行趋势
        bar_seconds = 60
        start = now - limit * bar_seconds
        for i in range(limit):
            ts = start + i * bar_seconds
            # 缓慢上行 + 噪声
            noise = random.uniform(-0.005, 0.005)
            price *= (1.0 + noise + 0.0004)   # 偏向上行
            o = price * (1 + random.uniform(-0.002, 0.002))
            c = price * (1 + random.uniform(-0.002, 0.002))
            h = max(o, c) * (1 + random.uniform(0, 0.003))
            l = min(o, c) * (1 - random.uniform(0, 0.003))
            v = random.uniform(200_000, 600_000)
            self.history[symbol].append({
                "ts": ts, "open": round(o, 2), "high": round(h, 2),
                "low": round(l, 2), "close": round(c, 2),
                "volume": int(v),
            })
            price = c
        # 回到接近 base
        self.prices[symbol] = round(price * (1 + random.uniform(-0.005, 0.005)), 2)

    # ---------- 模拟 tick 推进 ----------

    def step(self) -> list[Tick]:
        """推进一步：所有股票随机游走 ±0.5%"""
        ticks = []
        ts = time.time() * 1000
        for sym in SYMBOLS:
            move = random.uniform(-0.005, 0.005)
            self.prices[sym] = round(self.prices[sym] * (1 + move), 2)
            ticks.append(Tick(symbol=sym, price=self.prices[sym], ts=ts))
            # 同步最后一个持仓价
            if sym in self.positions:
                self.positions[sym].last_price = self.prices[sym]
        return ticks

    # ---------- 账户 ----------

    def account(self) -> dict:
        equity = self.cash + sum(pos.market_value for pos in self.positions.values())
        return {
            "cash": round(self.cash, 2),
            "equity": round(equity, 2),
            "settled_cash": round(self.cash, 2),
            "market_value": round(sum(pos.market_value for pos in self.positions.values()), 2),
            "total_return_pct": round((equity / self.initial_cash - 1.0) * 100.0, 4),
            "daily_pnl": round(
                sum(pos.unrealized_pnl for pos in self.positions.values()), 2),
            "positions": len(self.positions),
        }

    def snapshot_equity(self) -> dict:
        snapshot = self.account()
        self.equity_history.append({
            "ts": int(time.time() * 1000),
            "equity": snapshot["equity"],
            "cash": snapshot["cash"],
            "market_value": snapshot["market_value"],
            "daily_pnl": snapshot["daily_pnl"],
        })
        # 限制长度
        if len(self.equity_history) > 600:
            self.equity_history = self.equity_history[-600:]
        return self.equity_history[-1]

    # ---------- 持仓 / 订单 ----------

    def positions_list(self) -> list[dict]:
        return [pos.to_dict() for pos in self.positions.values()]

    def orders_list(self, limit: int = 50) -> list[dict]:
        return [o.to_dict() for o in self.orders[-limit:][::-1]]

    # ---------- 下单（mock 直接成交）----------

    def place_order(self, symbol: str, side: str, quantity: int,
                    order_type: str = "MARKET",
                    limit_price: Optional[float] = None) -> Order:
        ts = time.time() * 1000
        price = self.prices.get(symbol, 100.0)
        if limit_price is not None:
            price = limit_price
        order = Order(
            order_id=str(uuid.uuid4())[:8],
            symbol=symbol,
            side=side.upper(),
            quantity=int(quantity),
            price=price,
            status="pending",
            ts=ts,
        )

        # 校验：资金 / T+1
        if side.upper() == "BUY":
            cost = price * quantity
            if cost > self.cash + 0.001:
                order.status = "rejected"
                order.note = f"资金不足: 需要 ${cost:,.2f}, 可用 ${self.cash:,.2f}"
                order.rejection_code = 10
                self.orders.append(order)
                return order
            self.cash -= cost
            pos = self.positions.get(symbol)
            if pos is None:
                pos = Position(symbol=symbol, quantity=quantity, avg_cost=price,
                               last_price=price)
                self.positions[symbol] = pos
            else:
                new_total_cost = pos.avg_cost * pos.quantity + price * quantity
                new_qty = pos.quantity + quantity
                pos.avg_cost = new_total_cost / new_qty
                pos.quantity = new_qty
                pos.last_price = price
        else:  # SELL
            pos = self.positions.get(symbol)
            if pos is None or pos.quantity < quantity:
                order.status = "rejected"
                order.note = f"持仓不足: 持有 {pos.quantity if pos else 0}, 卖出 {quantity}"
                order.rejection_code = 11
                self.orders.append(order)
                return order
            proceeds = price * quantity
            self.cash += proceeds
            pos.quantity -= quantity
            if pos.quantity == 0:
                del self.positions[symbol]
            else:
                pos.last_price = price

        order.status = "filled"
        order.price = price
        self.orders.append(order)
        # 限制订单历史长度
        if len(self.orders) > 500:
            self.orders = self.orders[-500:]
        return order

    # ---------- 自动信号（每 5~8 秒随机发一条；30% 概率下单）----------

    def maybe_emit_signal(self) -> Optional[Signal]:
        if random.random() < 0.4:    # 60% 的 step 不出信号
            return None
        symbol = random.choice(SYMBOLS)
        action = random.choice(["BUY", "SELL"])
        strength = round(random.uniform(0.55, 0.95), 2)
        reasons = {
            "BUY":  ["MACD 金叉", "KDJ 金叉 K=20 D=40",
                     "RSI 超卖回升(28)", "均线多头 MA5 上穿 MA20",
                     "BOLL 下轨支撑"],
            "SELL": ["MACD 死叉", "KDJ 死叉", "RSI 超买(74)",
                     "BOLL 上轨突破", "均线空头"],
        }
        reason = random.choice(reasons[action])
        sig = Signal(symbol=symbol, action=action, strength=strength,
                     reason=reason, ts=time.time() * 1000)
        self.signals.append(sig)
        if len(self.signals) > 200:
            self.signals = self.signals[-200:]
        # 30% 跟随下单
        if random.random() < 0.3:
            qty = random.choice([10, 50, 100])
            self.place_order(symbol, action, qty)
        return sig

    def signal_log(self, limit: int = 50) -> list[dict]:
        return [s.to_dict() for s in self.signals[-limit:][::-1]]

    # ---------- 种子 ----------

    def _seed_initial_position(self) -> None:
        """模拟"已有一笔仓位"的初始状态"""
        sym = "NVDA"
        qty = 100
        cost = self.prices[sym] * 0.97     # 比当前低一点点, 制造浮盈
        pos = Position(symbol=sym, quantity=qty, avg_cost=round(cost, 2),
                       last_price=self.prices[sym])
        self.positions[sym] = pos
        # 初始撮合订单
        self.orders.append(Order(
            order_id="seed01", symbol=sym, side="BUY", quantity=qty,
            price=cost, status="filled", ts=int(self.start_time * 1000),
            note="种子持仓 (启动时)",
        ))
        # 历史净值点
        for i in range(60):
            ts = int((self.start_time - 60 + i) * 1000)
            self.equity_history.append({
                "ts": ts,
                "equity": round(
                    self.INITIAL_CASH - cost * qty + self.prices[sym] * qty
                    + (i / 60) * 500, 2),
                "cash": round(self.INITIAL_CASH - cost * qty, 2),
                "market_value": round(self.prices[sym] * qty, 2),
                "daily_pnl": round((i / 60) * 500, 2),
            })


__all__ = ["MockEngine", "Tick", "Position", "Order", "Signal", "SYMBOLS"]
