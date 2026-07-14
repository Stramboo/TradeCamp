# -*- coding: utf-8 -*-
r"""
server.py — FastAPI 主入口（默认 mock 模式；NDXINFO_BACKEND=real 切到真实 TradingEngine）

启动 (mock):
    cd E:\Projects\NDXinfo
    python -m uvicorn webapp.backend.server:app --port 8765

启动 (real TradingEngine):
    $env:NDXINFO_BACKEND='real'
    $env:NDXINFO_BROKER='simulation'        # or 'alpaca'/'paper' 等
    $env:NDXINFO_STRATEGY='multi'           # or 'kdj','ensemble' ...
    python -m uvicorn webapp.backend.server:app --port 8765

访问:
    http://localhost:8765/api/account
    http://localhost:8765/docs             (Swagger UI)
    ws://localhost:8765/ws                 (WebSocket 实时推送)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import sys
import time
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 让 webapp.* imports 在无 setup.py 时也能找到
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from webapp.backend.adapters.mock_engine import MockEngine, SYMBOLS  # noqa: E402
from webapp.backend.adapters.event_bus import (  # noqa: E402
    EventBus, tick_event, order_event, equity_event, signal_event, log_event,
)
from webapp.backend.adapters.ndx_adapter import NdxAdapter  # noqa: E402

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("webapp.backend")

# ---------- 应用状态 ----------

class AppState:
    """全局状态：bus 永远存在；engine 根据模式换 MockEngine 或 EngineAdapter"""
    bus: EventBus
    backend_kind: str = "mock"        # 'mock' | 'real'
    last_signal_at: float = 0.0
    signal_cooldown: float = 4.0
    # 'mock' 时是 MockEngine；'real' 时是 EngineAdapter（同样实现 account/positions/...）
    engine: Any = None
    # NDX 联动（轻量分析）
    ndx: NdxAdapter = None  # type: ignore[assignment] 

state = AppState()


def _init_engine(bus: EventBus):
    """按环境变量初始化引擎"""
    mode = os.environ.get("NDXINFO_BACKEND", "mock").lower()
    if mode == "real":
        try:
            from webapp.backend.adapters.engine_adapter import EngineAdapter
            broker   = os.environ.get("NDXINFO_BROKER", "simulation")
            strategy = os.environ.get("NDXINFO_STRATEGY", "multi")
            initial  = float(os.environ.get("NDXINFO_CASH", "100000"))
            state.engine = EngineAdapter(
                broker_type=broker,
                strategy_name=strategy,
                initial_cash=initial,
                bus=bus,
            )
            state.backend_kind = "real"
            logger.info(f"backend = real | broker={broker} strategy={strategy} cash={initial:,.0f}")
            return
        except Exception as e:
            logger.warning("EngineAdapter init failed (%s); falling back to mock", e)
    # default
    from webapp.backend.adapters.mock_engine import MockEngine
    state.engine = MockEngine()
    state.backend_kind = "mock"
    logger.info("backend = mock (offline, deterministic)")


# ---------- FastAPI lifespan ----------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """startup: 初始化引擎 + 启动后台 step 协程；shutdown: 取消"""
    state.bus = EventBus()
    state.bus.bind_loop(asyncio.get_running_loop())
    _init_engine(state.bus)
    state.ndx = NdxAdapter(cache_ttl_seconds=300)

    # 每 1 秒推进一次 tick（mock 模式才自驱；real 模式让 TradingEngine 自己 _auto_tick）
    async def ticker():
        last_signal = 0.0
        while True:
            try:
                if state.backend_kind == "mock":
                    # 推进一步 MockEngine
                    ticks = state.engine.step()
                    snap = state.engine.snapshot_equity()
                    for t in ticks:
                        await state.bus.publish(tick_event(t.symbol, t.price))
                    await state.bus.publish(equity_event(snap))
                    # 每 4s 随机发信号
                    now = time.time()
                    if now - last_signal > state.signal_cooldown:
                        sig = state.engine.maybe_emit_signal()
                        if sig is not None:
                            await state.bus.publish(signal_event(sig.to_dict()))
                            last_signal = now
                    # 推送日志（70% 概率发）
                    if random.random() < 0.7:
                        msgs = [
                            ("INFO", "tick processed", {"symbols": len(ticks),
                                                         "equity": round(snap["equity"], 2)}),
                            ("INFO", "ws heartbeat", {"clients": len(state.bus._subscribers)}),
                            ("INFO", "order matched", {"ticker": "NVDA"}) if random.random() < 0.2
                              else ("INFO", "scan loop", {}),
                        ]
                        lvl, m, ctx = random.choice(msgs)
                        await state.bus.publish(log_event(lvl, m, **ctx))
                else:
                    # real 模式：什么都不做；engine 自己的 _auto_tick / 回调会推数据
                    # 仍然每 5 秒发一条 ws heartbeat 方便前端显示 "已连接"
                    await state.bus.publish(log_event(
                        "INFO", "ws heartbeat",
                        clients=len(state.bus._subscribers),
                        backend="real",
                    ))
            except Exception as e:
                logger.exception("ticker error: %s", e)
            await asyncio.sleep(1.0)

    task = asyncio.create_task(ticker())
    logger.info(f"WebApp backend started (mode={state.backend_kind}). "
                f"open http://localhost:8765/docs")
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="trader WebApp backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],                    # 开发用；生产应限定
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- 健康检查 ----------

@app.get("/api/health")
def health() -> dict:
    st = state.engine.start_time
    if callable(st):
        st = st()
    return {
        "status": "ok",
        "backend": state.backend_kind,
        "ts": int(time.time() * 1000),
        "uptime_s": int(time.time() - st),
    }


# ---------- 账户 / 持仓 / 订单 ----------

@app.get("/api/account")
def get_account() -> dict:
    return state.engine.account()


@app.get("/api/positions")
def get_positions() -> list[dict]:
    return state.engine.positions_list()


@app.get("/api/orders")
def get_orders(limit: int = 50) -> list[dict]:
    return state.engine.orders_list(limit=limit)


# ---------- 行情 / K 线 ----------

@app.get("/api/market/symbols")
def get_symbols() -> list[str]:
    return list(state.engine.prices.keys())


@app.get("/api/market/ndx")
def get_ndx_status() -> dict:
    """今日 NDX 大盘状态（轻联动给 webapp）
    数据来自 nasdaq_analyzer/DataFetcher + indicators；
    失败时 fallback 一份 mock，绝不让前端 504。"""
    if state.ndx is None:
        raise HTTPException(503, "ndx adapter not initialized")
    return asdict(state.ndx.get_status())


@app.get("/api/analysis/full")
def get_full_analysis() -> dict:
    """完整分析数据（NDX + 关键股票 + 板块轮动 + 市场情绪）
    给前端"分析"页面使用；失败时自动降级到 mock。"""
    if state.ndx is None:
        raise HTTPException(503, "ndx adapter not initialized")
    result = state.ndx.get_full_analysis()
    return {
        "ndx": asdict(result.ndx),
        "stocks": [asdict(s) for s in result.stocks],
        "sectors": [asdict(s) for s in result.sectors],
        "market_breadth": result.market_breadth,
        "sentiment_data": result.sentiment_data,
        "source": result.source,
        "ts": result.ts,
        "ndx_analysis_report_path": result.ndx_analysis_report_path,
    }


@app.get("/api/market/{symbol}")
def get_market_quote(symbol: str) -> dict:
    sym = symbol.upper()
    if sym not in state.engine.prices:
        raise HTTPException(404, f"unknown symbol: {sym}")
    return {"symbol": sym, "price": state.engine.prices[sym],
            "ts": int(time.time() * 1000)}


@app.get("/api/market/{symbol}/ohlc")
def get_ohlc(symbol: str, interval: str = "1m", limit: int = 200) -> list[dict]:
    sym = symbol.upper()
    if sym not in state.engine.prices:
        raise HTTPException(404, f"unknown symbol: {sym}")
    return state.engine.ohlc(sym, interval=interval, limit=limit)


# ---------- 下单（mock 直接撮合）----------

class PlaceOrderReq(BaseModel):
    symbol: str
    side: str = Field(..., pattern="^(BUY|SELL)$")
    quantity: int = Field(..., gt=0)
    order_type: str = "MARKET"
    limit_price: Optional[float] = None


@app.post("/api/orders")
async def post_order(req: PlaceOrderReq) -> dict:
    raw = state.engine.place_order(
        symbol=req.symbol.upper(),
        side=req.side,
        quantity=req.quantity,
        order_type=req.order_type,
        limit_price=req.limit_price,
    )
    data = raw if isinstance(raw, dict) else raw.to_dict()
    await state.bus.publish(order_event(data))
    return data


@app.post("/api/orders/{order_id}/cancel")
def cancel_order(order_id: str) -> dict:
    # Mock: 全部直接成交，不能撤
    return {"order_id": order_id, "cancelled": False,
            "note": "MockEngine 不支持撤单"}


# ---------- 策略 / 风控 ----------

@app.get("/api/strategy")
def get_strategy() -> dict:
    return {
        "name": "multi",
        "weights": {"macd": 0.30, "rsi": 0.25, "ma": 0.25, "boll": 0.20},
        "available": ["multi", "macd", "rsi", "ma_trend", "bollinger",
                      "kdj", "boll_width", "ensemble"],
    }


class StrategyReq(BaseModel):
    name: str


@app.put("/api/strategy")
def put_strategy(req: StrategyReq) -> dict:
    # Mock：不实际切换，只回显
    return {"name": req.name, "applied": True}


@app.get("/api/limits")
def get_limits() -> dict:
    return {
        "max_position_pct": 0.25, "stop_loss_pct": -8.0,
        "trailing_stop_pct": -5.0, "max_daily_trades": 20,
        "use_atr_stop": False,
    }


# ---------- 信号 / 日志 ----------

@app.get("/api/signals")
def get_signals(limit: int = 50) -> list[dict]:
    return state.engine.signal_log(limit=limit)


@app.get("/api/logs")
def get_logs(limit: int = 200) -> list[dict]:
    """最近日志（先返回 mock 一批）"""
    if not hasattr(state, "_mock_log_buffer"):
        state._mock_log_buffer = []
    return state._mock_log_buffer[-limit:]


# ---------- Equity curve ----------

@app.get("/api/equity-history")
def get_equity_history(limit: int = 300) -> list[dict]:
    return state.engine.equity_history[-limit:]


# ---------- WebSocket ----------

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    logger.info("WS client connected: %s", ws.client)
    try:
        # 客户端消息（PING、订阅）— 当前版本先回应 PONG
        async def recv_loop():
            async for msg in ws.iter_text():
                if msg.strip() == "PING":
                    await ws.send_text(json.dumps({"type": "pong",
                                                   "ts": int(time.time()*1000)}))

        recv_task = asyncio.create_task(recv_loop())

        async for ev in state.bus.subscribe():
            await ws.send_text(json.dumps(ev, ensure_ascii=False))
    except WebSocketDisconnect:
        logger.info("WS client disconnected")
    except Exception as e:
        logger.exception("WS error: %s", e)
    finally:
        try:
            recv_task.cancel()
        except Exception:
            pass


# ---------- 直跑入口 ----------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("webapp.backend.server:app",
                host="0.0.0.0", port=8765, reload=False)
