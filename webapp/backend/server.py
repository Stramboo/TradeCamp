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

# --- 加载 .env 文件（不在版本控制中） ---
_ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
if os.path.exists(_ENV_PATH):
    with open(_ENV_PATH, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _val = _line.split("=", 1)
                _key = _key.strip()
                _val = _val.strip().strip('"').strip("'")
                if _key and _key not in os.environ:
                    os.environ[_key] = _val
from dataclasses import asdict
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
from webapp.backend.userstore import UserStore  # noqa: E402
from webapp.backend.coach import generate_briefing, get_ranking  # noqa: E402
from webapp.backend.ai_advisor import generate_daily_recommendations_from_engine, recommendations_to_dict  # noqa: E402
from webapp.backend.learning_content import STAGES, LESSONS, GLOSSARY, QUESTS  # noqa: E402
from webapp.backend.explorer import MARKETS, COMPANIES, INDUSTRIES, get_market_status, get_companies  # noqa: E402
from webapp.backend.practice import calc_position, calc_stop_loss, SCENARIOS, evaluate_scenario_decisions  # noqa: E402
from webapp.backend.review_engine import create_trade_review, MISTAKE_PATTERNS  # noqa: E402
from webapp.backend.coach_chat import chat as coach_chat  # noqa: E402
from webapp.backend.daily_challenge import get_daily_challenge, CHALLENGE_POOL  # noqa: E402
from webapp.backend.xp_service import award_xp, get_level_info  # noqa: E402
from webapp.backend.review_service import auto_review_on_sell  # noqa: E402

# v2.4 Phase 2: 复盘自动触发（纯本地规则引擎，默认开）
ENABLE_REVIEW_AUTO = os.environ.get("ENABLE_REVIEW_AUTO", "true").lower() == "true"
from webapp.backend.ai_coach import TradeCoach, enhance_with_llm  # noqa: E402

# v2.3 Phase 1: 真实数据 Provider（可选）
ENABLE_REAL_DATA = os.environ.get("ENABLE_REAL_DATA", "false").lower() == "true"
if ENABLE_REAL_DATA:
    try:
        from webapp.backend.adapters.real_data_provider import get_quote, get_ohlc as get_real_ohlc
        logger.info("ENABLE_REAL_DATA=true, 真实数据 Provider 已加载")
    except ImportError as e:
        logger.warning(f"ENABLE_REAL_DATA=true 但 real_data_provider 加载失败: {e}")
        ENABLE_REAL_DATA = False
        get_quote = None
        get_real_ohlc = None
else:
    get_quote = None
    get_real_ohlc = None

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
    # 用户数据（自选/告警/组合/日志）
    userstore: UserStore = None  # type: ignore[assignment] 

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
    state.userstore = UserStore()
    state.userstore.seed_glossary()   # 幂等填充术语表

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
                    # real 模式：推送实盘状态、告警检查
                    try:
                        # 推账户和净值
                        snap = state.engine.snapshot_equity() if hasattr(state.engine, "snapshot_equity") else state.engine.account()
                        await state.bus.publish(equity_event(snap))
                        # 推 tick
                        for sym in getattr(state.engine, "prices", {}):
                            await state.bus.publish(tick_event(sym, state.engine.prices[sym]))
                    except Exception:
                        pass
                    # 告警检查：每 5 秒检查一次
                    if int(time.time()) % 5 == 0:
                        try:
                            active = state.userstore.alert_get_active()
                            for al in active:
                                price = state.engine.prices.get(al["symbol"])
                                if price is None:
                                    continue
                                triggered = False
                                if al["condition"] == "above" and price >= al["target_value"]:
                                    triggered = True
                                elif al["condition"] == "below" and price <= al["target_value"]:
                                    triggered = True
                                if triggered:
                                    state.userstore.alert_mark_triggered(al["id"])
                                    await state.bus.publish({
                                        "type": "price_alert",
                                        "data": {
                                            "symbol": al["symbol"], "condition": al["condition"],
                                            "target": al["target_value"], "current_price": price,
                                            "ts": int(time.time() * 1000),
                                        }
                                    })
                        except Exception:
                            pass
                    # heartbeat
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

# 静态文件：让前端能通过 /reports/ 访问分析报告
_reports_dir = os.path.join(_ROOT, "reports")
if os.path.isdir(_reports_dir):
    app.mount("/reports", StaticFiles(directory=_reports_dir), name="reports")

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
        "real_data": ENABLE_REAL_DATA,
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


@app.get("/api/market/batch")
def get_market_batch(symbols: str = "") -> dict:
    """批量获取价格快照（学习沙盒用）"""
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    prices = {}
    for sym in sym_list:
        if sym in state.engine.prices:
            prices[sym] = round(state.engine.prices[sym], 2)
    return {"prices": prices, "ts": int(time.time() * 1000)}


@app.get("/api/market/{symbol}")
def get_market_quote(symbol: str) -> dict:
    sym = symbol.upper()
    
    # v2.3: 真实数据模式
    if ENABLE_REAL_DATA and get_quote:
        real_quote = get_quote(sym)
        if real_quote:
            return real_quote
        # 降级到 Mock
        logger.info(f"真实数据获取失败，降级到 Mock: {sym}")
    
    # Mock 模式
    if sym not in state.engine.prices:
        raise HTTPException(404, f"unknown symbol: {sym}")
    return {"symbol": sym, "price": state.engine.prices[sym],
            "ts": int(time.time() * 1000), "source": "mock"}


@app.get("/api/market/{symbol}/ohlc")
def get_ohlc(symbol: str, interval: str = "1m", limit: int = 200) -> list[dict]:
    sym = symbol.upper()
    
    # v2.3: 真实数据模式
    if ENABLE_REAL_DATA and get_real_ohlc:
        # 转换 interval 格式
        period_map = {"1m": "1d", "5m": "5d", "15m": "1mo", "1h": "3mo", "1d": "6mo", "1wk": "1y"}
        period = period_map.get(interval, "6mo")
        real_data = get_real_ohlc(sym, period=period, interval="1d")
        if real_data:
            return real_data[-limit:] if len(real_data) > limit else real_data
        logger.info(f"真实K线获取失败，降级到 Mock: {sym}")
    
    # Mock 模式
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
    # real 模式：实际切换策略
    if state.backend_kind == "real":
        try:
            state.engine._engine.switch_strategy(req.name)
            return {"name": req.name, "applied": True}
        except Exception as e:
            logger.warning("Strategy switch failed: %s", e)
            return {"name": req.name, "applied": False, "error": str(e)}
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


# ---------- 自动操盘 API ----------

@app.get("/api/trade/status")
def get_trade_status() -> dict:
    """获取自动交易运行状态"""
    if state.backend_kind == "mock":
        return {"running": False, "mode": "mock", "strategy": "", "tick_count": 0,
                "success": 0, "errors": 0, "interval_s": 0}
    try:
        eng = state.engine._engine
        st = eng.get_status()
        hb = st.get("heartbeat", {})
        return {
            "running": eng.is_auto_running,
            "mode": "real",
            "strategy": st.get("strategy_name", ""),
            "tick_count": hb.get("tick_count", 0),
            "success": hb.get("success_count", 0),
            "errors": hb.get("error_count", 0),
            "interval_s": getattr(eng, "_auto_interval", 60),
            "account": state.engine.account(),
            "positions_count": len(state.engine.positions_list()),
            "last_error": st.get("last_error", ""),
        }
    except Exception as e:
        return {"running": False, "mode": "real", "error": str(e)}


class AutoTradeReq(BaseModel):
    action: str = Field(..., pattern="^(start|stop)$")
    interval: int = Field(default=60, ge=10, le=600)


@app.post("/api/trade/control")
async def control_auto_trade(req: AutoTradeReq) -> dict:
    """启动/停止自动交易"""
    if state.backend_kind == "mock":
        raise HTTPException(400, "mock 模式不支持自动交易，请切换到 real 模式")

    eng = state.engine._engine
    try:
        if req.action == "start":
            if eng.is_auto_running:
                return {"action": "start", "status": "already_running"}
            # 先加载历史数据 + 刷新价格（异步包装，避免阻塞 event loop）
            import concurrent.futures
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                await loop.run_in_executor(pool, eng._load_all_history)
                await loop.run_in_executor(pool, eng.market_data.refresh_prices)
            eng.start_auto(interval_seconds=req.interval)
            await state.bus.publish({
                "type": "auto_trade", "data": {
                    "action": "started", "strategy": eng.strategy.name,
                    "interval_s": req.interval, "ts": int(time.time() * 1000),
                }
            })
            return {"action": "start", "status": "started", "interval_s": req.interval}
        else:
            if not eng.is_auto_running:
                return {"action": "stop", "status": "already_stopped"}
            eng.stop_auto()
            await state.bus.publish({
                "type": "auto_trade", "data": {
                    "action": "stopped", "ts": int(time.time() * 1000),
                }
            })
            return {"action": "stop", "status": "stopped"}
    except Exception as e:
        logger.exception("auto trade control error: %s", e)
        raise HTTPException(500, str(e))


# ---------- WebSocket ----------

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    logger.info("WS client connected: %s", ws.client)
    recv_task = None
    try:
        # 客户端消息（PING、订阅）— 当前版本先回应 PONG
        async def recv_loop():
            async for msg in ws.iter_text():
                if msg.strip() == "PING":
                    try:
                        await ws.send_text(json.dumps({"type": "pong",
                                                       "ts": int(time.time()*1000)}))
                    except Exception:
                        break

        recv_task = asyncio.create_task(recv_loop())

        async for ev in state.bus.subscribe():
            try:
                await ws.send_text(json.dumps(ev, ensure_ascii=False))
            except Exception:
                break  # 客户端断开，停发
    except WebSocketDisconnect:
        logger.info("WS client disconnected")
    except Exception as e:
        logger.warning("WS error: %s", e)
    finally:
        if recv_task is not None:
            recv_task.cancel()
            try:
                await recv_task
            except asyncio.CancelledError:
                pass


# ---------- 用户个性化 API ----------

# -- AI 交易教练 --

@app.get("/api/coach/briefing")
def get_coach_briefing() -> dict:
    """生成个性化盘前简报"""
    ndx = state.ndx.get_status()
    briefing = generate_briefing(
        account=state.engine.account(),
        positions=state.engine.positions_list(),
        ndx_status={
            "change_pct": ndx.change_pct,
            "sentiment": ndx.sentiment,
            "sentiment_label": ndx.sentiment_label,
            "summary": ndx.summary,
        },
        orders=state.engine.orders_list(limit=100),
        signals=state.engine.signal_log(limit=50) if hasattr(state.engine, "signal_log") else [],
        alerts=state.userstore.alert_list(),
        journal=state.userstore.journal_list(limit=100),
    )
    return {
        "headline": briefing.headline,
        "positions": briefing.positions,
        "warnings": briefing.warnings,
        "opportunities": briefing.opportunities,
        "ranking": briefing.ranking,
        "tone": briefing.tone,
        "generated_at": briefing.generated_at,
    }


@app.get("/api/coach/ranking")
def get_coach_ranking() -> dict:
    """获取段位评估"""
    return get_ranking(
        orders=state.engine.orders_list(limit=500),
        journal=state.userstore.journal_list(limit=500),
    )


# -- AI 每日推荐 --

@app.get("/api/advisor/recommendations")
async def get_advisor_recommendations() -> dict:
    """生成 AI 推荐（mock 模式用 MockEngine 模拟数据，real 模式用 TradingEngine 数据）"""
    import concurrent.futures
    loop = asyncio.get_running_loop()

    try:
        with concurrent.futures.ThreadPoolExecutor() as pool:
            dr = await loop.run_in_executor(pool, generate_daily_recommendations_from_engine, state.engine)
        return recommendations_to_dict(dr)
    except Exception as e:
        logger.warning(f"AI 推荐生成失败: {e}")
        return {"total_stocks": 0, "market_summary": f"推荐引擎出错: {e}", "strong_buy": [], "buy": [], "hold": [], "sell": [], "strong_sell": [], "top_picks": [], "all": []}


# -- 自选列表 --

@app.get("/api/glossary")
def get_glossary(category: str = None) -> list[dict]:
    return state.userstore.glossary_list(category or None)


@app.get("/api/glossary/search")
def search_glossary(q: str) -> list[dict]:
    if not q or len(q) < 2:
        return []
    return state.userstore.glossary_search(q)


@app.get("/api/learning/stages")
def get_learning_stages() -> dict:
    """获取六阶段学习路线"""
    progress = {}
    for p in state.userstore.learning_progress_list():
        progress[p["chapter_id"]] = p["completed"]
    stages_out = []
    for stage in STAGES:
        stage_lessons = [l for l in LESSONS if l["stage_id"] == stage["id"]]
        lessons_done = sum(1 for l in stage_lessons if progress.get(l["id"], False))
        stages_out.append({
            "id": stage["id"],
            "title": stage["title"],
            "subtitle": stage["subtitle"],
            "description": stage["description"],
            "icon": stage["icon"],
            "color": stage["color"],
            "prerequisite_stage": stage.get("prerequisite_stage"),
            "lessons_total": len(stage_lessons),
            "lessons_done": lessons_done,
            "unlocked": stage.get("prerequisite_stage") is None or any(
                progress.get(l["id"], False) for l in LESSONS
                if l["stage_id"] == stage["prerequisite_stage"]
            ),
        })
    return {"stages": stages_out}


@app.get("/api/learning/chapters")
def get_learning_chapters() -> dict:
    """获取全部课时列表，附带学习进度"""
    progress = {}
    for p in state.userstore.learning_progress_list():
        progress[p["chapter_id"]] = p["completed"]
    chapters_out = []
    for i, ch in enumerate(LESSONS):
        stage = next((s for s in STAGES if s["id"] == ch["stage_id"]), None)
        chapters_out.append({
            "id": ch["id"],
            "number": ch["number"],
            "title": ch["title"],
            "summary": ch["summary"],
            "question": ch["question"],
            "analogy": ch["analogy"],
            "concept": ch["concept"],
            "category": stage["title"] if stage else "",
            "stage_id": ch["stage_id"],
            "sections": [{"heading": s["title"], "paragraphs": s["body"]} for s in ch["sections"]],
            "interactive": ch.get("interactive"),
            "pitfall": ch.get("pitfall", ""),
            "xp": ch.get("xp", 50),
            "completed": bool(progress.get(ch["id"], False)),
        })
    return {"chapters": chapters_out}


@app.get("/api/learning/progress")
def get_learning_progress() -> list[dict]:
    return state.userstore.learning_progress_list()


@app.put("/api/learning/progress")
def mark_learning_progress(req: dict) -> dict:
    chapter_id = req.get("chapter_id", "")
    if not chapter_id:
        raise HTTPException(400, "chapter_id required")
    state.userstore.update_streak()
    return state.userstore.learning_progress_mark(chapter_id)


# ---- 学习任务（Quests）----

@app.get("/api/learning/quests")
def get_learning_quests(chapter_id: str = None) -> dict:
    """获取任务列表，附带完成状态"""
    completed_map = {}
    for p in state.userstore.quest_list():
        if p.get("completed"):
            completed_map[p["quest_id"]] = True

    quests_out = []
    for q in QUESTS:
        if chapter_id and q.get("chapter_id") != chapter_id:
            continue
        quests_out.append({
            "id": q["id"],
            "chapter_id": q.get("chapter_id", ""),
            "title": q["title"],
            "type": q.get("type", ""),
            "xp": q.get("xp", 0),
            "description": q.get("description", ""),
            "completed": completed_map.get(q["id"], False),
        })
    return {"quests": quests_out}


@app.post("/api/learning/quests/check")
def check_quest(req: dict) -> dict:
    """检查并标记任务完成"""
    quest_id = req.get("quest_id", "")
    if not quest_id:
        raise HTTPException(400, "quest_id required")

    from webapp.backend.quest_checker import check_quest

    quest = next((q for q in QUESTS if q["id"] == quest_id), None)
    if not quest:
        raise HTTPException(404, "quest not found")

    context = req.get("context", {})
    completed = check_quest(quest, context)

    if completed:
        if not state.userstore.quest_is_completed(quest_id):
            state.userstore.quest_mark_completed(quest_id)
            result = award_xp(state.userstore, "quest", quest_id, quest.get("xp", 0))
            return {"completed": True, "xp_awarded": result["amount"]}
        return {"completed": True, "xp_awarded": 0}

    return {"completed": False, "xp_awarded": 0}


@app.get("/api/learning/progress/dashboard")
def get_learning_dashboard() -> dict:
    """学习进度仪表盘数据聚合"""
    progress_list = state.userstore.learning_progress_list()
    completed_chapters = sum(1 for p in progress_list if p.get("completed"))
    quest_list = state.userstore.quest_list()
    completed_quests = sum(1 for q in quest_list if q.get("completed"))
    stats = state.userstore.get_learning_stats()
    total_xp = stats.get("total_xp", 0)
    streak_days = stats.get("streak_days", 0)

    # 学习等级（统一走 xp_service）
    level_info = get_level_info(total_xp)
    current_level = level_info["level_name"]
    next_level_xp = level_info["next_level_xp"]

    # 章节详情
    chapters_detail = []
    for ch in LESSONS:
        completed = any(p.get("chapter_id") == ch["id"] and p.get("completed") for p in progress_list)
        chapter_quests = [q for q in QUESTS if q.get("chapter_id") == ch["id"]]
        ch_completed_quests = sum(1 for q in chapter_quests for qp in quest_list if qp.get("quest_id") == q["id"] and qp.get("completed"))
        stage = next((s for s in STAGES if s["id"] == ch["stage_id"]), None)
        chapters_detail.append({
            "id": ch["id"],
            "number": ch["number"],
            "title": ch["title"],
            "category": stage["title"] if stage else "",
            "stage_id": ch["stage_id"],
            "completed": completed,
            "quests_done": ch_completed_quests,
            "quests_total": len(chapter_quests),
        })

    # 阶段进度
    stages_detail = []
    for stage in STAGES:
        stage_lessons = [l for l in LESSONS if l["stage_id"] == stage["id"]]
        stage_done = sum(1 for l in stage_lessons for p in progress_list if p.get("chapter_id") == l["id"] and p.get("completed"))
        stages_detail.append({
            "id": stage["id"],
            "title": stage["title"],
            "icon": stage["icon"],
            "lessons_total": len(stage_lessons),
            "lessons_done": stage_done,
        })

    return {
        "chapters_completed": completed_chapters,
        "chapters_total": len(LESSONS),
        "quests_completed": completed_quests,
        "quests_total": len(QUESTS),
        "total_xp": total_xp,
        "level": current_level,
        "level_num": level_info["level"],
        "level_progress_pct": level_info["progress_pct"],
        "next_level_xp": next_level_xp,
        "streak_days": streak_days,
        "chapters": chapters_detail,
        "stages": stages_detail,
    }


# ---- 世界市场探索 API (Phase 3) ----

@app.get("/api/explore/markets")
def explore_markets() -> list[dict]:
    """获取所有市场的列表（含交易状态）"""
    result = []
    for m in MARKETS:
        status = get_market_status(m["id"])
        result.append({**m, "status": status})
    return result


@app.get("/api/explore/markets/{market_id}")
def explore_market_detail(market_id: str) -> dict:
    """获取单个市场详情"""
    m = next((m for m in MARKETS if m["id"] == market_id), None)
    if not m:
        raise HTTPException(404, f"Market '{market_id}' not found")
    status = get_market_status(market_id)
    market_companies = get_companies(market=market_id)
    return {**m, "status": status, "companies": market_companies, "companyCount": len(market_companies)}


@app.get("/api/explore/companies")
def explore_companies(
    market: str = None, sector: str = None,
    industry: str = None, search: str = None
) -> list[dict]:
    """搜索/过滤公司"""
    return get_companies(market=market, sector=sector, industry=industry, search=search)


@app.get("/api/explore/companies/{symbol}")
def explore_company_detail(symbol: str) -> dict:
    """获取单个公司详情"""
    c = next((c for c in COMPANIES if c["symbol"].upper() == symbol.upper()), None)
    if not c:
        raise HTTPException(404, f"Company '{symbol}' not found")
    market = next((m for m in MARKETS if m["id"] == c["market"]), None)
    return {**c, "marketInfo": market}


@app.get("/api/explore/industries")
def explore_industries() -> list[dict]:
    """获取行业分类列表"""
    return INDUSTRIES


# ---- 练习 & 情景训练 API (Phase 4+5) ----

class RiskCalcReq(BaseModel):
    account_size: float = Field(..., gt=0)
    stock_price: float = Field(..., gt=0)
    stop_loss_pct: float = Field(..., gt=0, le=50)
    max_loss_per_trade: float = Field(..., gt=0)


@app.post("/api/practice/risk-calc")
def practice_risk_calc(req: RiskCalcReq) -> dict:
    """仓位计算器：根据账户资金、股价、止损比例和最大亏损计算合理仓位"""
    return calc_position(req.account_size, req.stock_price,
                         req.stop_loss_pct, req.max_loss_per_trade)


@app.get("/api/practice/scenarios")
def practice_scenarios() -> list[dict]:
    """获取所有情景训练列表（不含详细步骤）"""
    return [
        {
            "id": s["id"], "title": s["title"],
            "description": s["description"], "difficulty": s["difficulty"],
            "xp": s["xp"], "steps_count": len(s["steps"]),
        }
        for s in SCENARIOS
    ]


@app.get("/api/practice/scenarios/{scenario_id}")
def practice_scenario_detail(scenario_id: str) -> dict:
    """获取单个情景训练的完整内容"""
    s = next((s for s in SCENARIOS if s["id"] == scenario_id), None)
    if not s:
        raise HTTPException(404, f"Scenario '{scenario_id}' not found")
    return s


class ScenarioEvalReq(BaseModel):
    decisions: list[dict] = []


@app.post("/api/practice/scenarios/{scenario_id}/evaluate")
def practice_scenario_evaluate(scenario_id: str, req: ScenarioEvalReq) -> dict:
    """评估情景训练的决策结果"""
    s = next((s for s in SCENARIOS if s["id"] == scenario_id), None)
    if not s:
        raise HTTPException(404, f"Scenario '{scenario_id}' not found")
    result = evaluate_scenario_decisions(req.decisions)
    result["scenario_title"] = s["title"]
    result["xp_earned"] = round(s["xp"] * result["score"] / 100)
    result["takeaway"] = s["takeaway"]
    return result


# ---- AI 教练增强 API (Phase 6) ----


@app.get("/api/coach/weekly-report")
def coach_weekly_report() -> dict:
    """生成每周学习/交易总结"""
    import datetime
    
    progress = state.userstore.learning_progress_list()
    quest_list = state.userstore.quest_list()
    sandbox = state.userstore.sandbox_get()
    journal_entries = state.userstore.journal_list()
    journal_count = len(journal_entries)

    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())
    completed_lessons = [p for p in progress if p.get("completed")]
    done_quests = [q for q in quest_list if q.get("completed")]

    orders = state.userstore.sandbox_orders_list()
    total_trades = len(orders)
    buy_trades = sum(1 for o in orders if o.get("side") == "BUY")
    sell_trades = sum(1 for o in orders if o.get("side") == "SELL")

    # 沙盒净值 = 现金 + 持仓市值（按成本价估算）
    sandbox_equity = sandbox.get("cash", 0) + sum(
        p.get("quantity", 0) * p.get("avg_cost", 0)
        for p in sandbox.get("positions", [])
    )

    ranking = get_ranking()

    report = {
        "week": f"{week_start} ~ {today}",
        "ranking": ranking,
        "learning": {
            "lessons_completed": len(completed_lessons),
            "lessons_total": 24,
            "quests_completed": len(done_quests),
            "quests_total": len(QUESTS),
        },
        "trading": {
            "total_trades": total_trades,
            "buy_trades": buy_trades,
            "sell_trades": sell_trades,
            "journal_entries": journal_count,
            "sandbox_equity": round(sandbox_equity, 2),
        },
        "tips": [],
    }

    if total_trades < 5:
        report["tips"].append("本周交易次数较少，多练习才能积累经验。")
    if journal_count == 0:
        report["tips"].append("本周还没写交易日志。复盘是进步的加速器！")
    if len(completed_lessons) < 4:
        report["tips"].append("学习进度可以再快一点，每天一课只需要 5-10 分钟。")
    if sell_trades > 0 and buy_trades < sell_trades:
        report["tips"].append("卖出多于买入，检查一下是止盈还是恐慌卖出。")

    return report


# ---- AI 教练对话 API (v2.3 Phase 4) ----

class ChatReq(BaseModel):
    message: str


@app.post("/api/coach/chat")
def coach_chat_api(req: ChatReq) -> dict:
    """AI 教练对话"""
    # 构建上下文
    context = {
        "glossary": GLOSSARY,
        "trades": state.userstore.sandbox_orders_list(10),
        "progress": {
            "completed_lessons": len([p for p in state.userstore.learning_progress_list() if p.get("completed")]),
            "total_lessons": 24,
            "current_stage": 1,  # TODO: 从进度计算
        },
    }
    
    response = coach_chat(req.message, context)
    
    return {
        "message": req.message,
        "response": response,
        "ts": int(time.time() * 1000),
    }


# ---- 每日挑战 API (v2.3 Phase 5) ----

@app.get("/api/challenges/daily")
def get_daily_challenge_api() -> dict:
    """获取今日挑战"""
    # TODO: 从用户数据计算等级
    user_level = 1
    challenge = get_daily_challenge(user_level)
    return challenge


@app.get("/api/challenges/pool")
def get_challenge_pool() -> list[dict]:
    """获取所有挑战模板"""
    return CHALLENGE_POOL


@app.post("/api/challenges/complete")
def complete_challenge(req: dict) -> dict:
    """标记挑战完成"""
    challenge_id = req.get("challenge_id", "")
    # TODO: 验证挑战完成条件 + 发放 XP
    return {"ok": True, "challenge_id": challenge_id, "xp_earned": 30}


# ---- 沙盒交易 API ----

@app.get("/api/sandbox/account")
def get_sandbox_account() -> dict:
    return state.userstore.sandbox_get()


class SandboxOrderReq(BaseModel):
    symbol: str
    side: str = Field(..., pattern="^(BUY|SELL)$")
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)
    order_id: str = ""


@app.post("/api/sandbox/order")
def post_sandbox_order(req: SandboxOrderReq) -> dict:
    oid = req.order_id or f"sandbox-{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
    ts = int(time.time() * 1000)
    if req.side == "BUY":
        state.userstore.sandbox_buy(req.symbol.upper(), req.quantity, req.price, oid, ts)
    else:
        state.userstore.sandbox_sell(req.symbol.upper(), req.quantity, req.price, oid, ts)

    # 更新当日交易计数
    try:
        import datetime as _dt
        state.userstore.checkin_touch(_dt.date.today().isoformat(), "trades_done", 1)
    except Exception:
        pass

    # v2.4: SELL 后自动生成复盘
    review = None
    if ENABLE_REVIEW_AUTO and req.side == "SELL":
        try:
            review = auto_review_on_sell(
                state.userstore, req.symbol.upper(), req.quantity, req.price, oid, ts
            )
        except Exception as e:
            logger.warning(f"复盘自动生成失败: {e}")

    return {"order_id": oid, "status": "filled", "ts": ts, "review": review}


@app.get("/api/sandbox/orders")
def get_sandbox_orders(limit: int = 50) -> list[dict]:
    return state.userstore.sandbox_orders_list(limit)


@app.post("/api/sandbox/reset")
def reset_sandbox() -> dict:
    state.userstore.sandbox_reset()
    return {"ok": True}


# ---- 交易复盘 API (v2.3 Phase 3) ----

@app.get("/api/reviews")
def list_reviews(limit: int = 20) -> list[dict]:
    """获取交易复盘列表"""
    return state.userstore.review_list(limit)


@app.post("/api/reviews/generate")
def generate_review(req: dict) -> dict:
    """为指定交易生成复盘报告"""
    trade = req.get("trade", {})
    context = req.get("context", {})
    
    # 添加上下文信息
    context.setdefault("recent_trades", state.userstore.sandbox_orders_list(50))
    context.setdefault("has_stop_loss", True)  # TODO: 从 trade_plan 检查
    context.setdefault("has_journal", False)   # TODO: 从 journal 检查
    
    review = create_trade_review(trade, context)
    
    # 保存到 userstore（如果支持）
    try:
        state.userstore.review_save(review)
    except AttributeError:
        pass  # userstore 还没有 review_save 方法
    
    return review


@app.get("/api/reviews/patterns")
def list_mistake_patterns() -> dict:
    """获取所有错误模式定义"""
    return MISTAKE_PATTERNS


# ---- 交易计划 ----

@app.post("/api/trade-plans")
def create_trade_plan(req: dict) -> dict:
    return state.userstore.trade_plan_create(
        symbol=req.get("symbol", ""),
        direction=req.get("direction", "long"),
        reason=req.get("reason", ""),
        entry_price=req.get("entry_price"),
        target_price=req.get("target_price"),
        stop_loss_price=req.get("stop_loss_price"),
        max_loss_pct=req.get("max_loss_pct"),
        position_pct=req.get("position_pct"),
        planned_holding=req.get("planned_holding"),
    )


@app.get("/api/trade-plans")
def list_trade_plans(limit: int = 20) -> list[dict]:
    return state.userstore.trade_plan_list(limit)


# -- AI 教练结构化反馈 --

_coach = TradeCoach()


@app.post("/api/coach/review")
def coach_review(req: dict) -> dict:
    """基于规则的交易教练评估（可选 LLM 增强）"""
    trade = req.get("trade", {})
    journal = req.get("journal")
    plan = req.get("plan")
    cash = req.get("cash", 100_000)
    enable_llm = req.get("enable_llm", True)

    report = _coach.evaluate(trade, journal=journal, plan=plan, cash=cash)

    result = {
        "overall": report.overall,
        "grade": report.grade,
        "decision": {
            "score": report.decision.score,
            "summary": report.decision.summary,
            "breakdown": report.decision.breakdown,
        },
        "execution": {
            "score": report.execution.score,
            "summary": report.execution.summary,
            "breakdown": report.execution.breakdown,
        },
        "risk": {
            "score": report.risk.score,
            "summary": report.risk.summary,
            "breakdown": report.risk.breakdown,
        },
        "attribution": {
            "score": report.attribution.score,
            "summary": report.attribution.summary,
            "breakdown": report.attribution.breakdown,
        },
        "highlights": report.highlights,
        "improvements": report.improvements,
        "llm_comment": "",
    }

    # 可选 LLM 增强
    if enable_llm:
        try:
            comment = enhance_with_llm(report, trade)
            if comment:
                result["llm_comment"] = comment
        except Exception:
            pass  # LLM 失败不阻断规则评分

    return result


# -- 自选列表 --

@app.get("/api/watchlists")
def get_watchlists() -> list[dict]:
    return state.userstore.watchlist_list()


class WatchlistCreateReq(BaseModel):
    name: str
    symbols: list[str] = []


@app.post("/api/watchlists")
def create_watchlist(req: WatchlistCreateReq) -> dict:
    return state.userstore.watchlist_create(req.name, req.symbols)


@app.put("/api/watchlists/{list_id}")
def update_watchlist(list_id: int, req: WatchlistCreateReq) -> dict:
    result = state.userstore.watchlist_update(list_id, req.name, req.symbols)
    if result is None:
        raise HTTPException(404, "watchlist not found")
    return result


@app.delete("/api/watchlists/{list_id}")
def delete_watchlist(list_id: int) -> dict:
    ok = state.userstore.watchlist_delete(list_id)
    if not ok:
        raise HTTPException(404, "watchlist not found")
    return {"deleted": True}


# -- 价格告警 --

@app.get("/api/alerts")
def get_alerts() -> list[dict]:
    return state.userstore.alert_list()


class AlertCreateReq(BaseModel):
    symbol: str
    condition: str = Field(..., pattern="^(above|below|pct_change)$")
    target_value: float
    note: str = ""


@app.post("/api/alerts")
async def create_alert(req: AlertCreateReq) -> dict:
    return state.userstore.alert_create(req.symbol, req.condition, req.target_value, req.note)


@app.put("/api/alerts/{alert_id}")
def update_alert(alert_id: int, req: AlertCreateReq) -> dict:
    result = state.userstore.alert_update(alert_id, symbol=req.symbol,
                                          condition=req.condition,
                                          target_value=req.target_value,
                                          note=req.note)
    if result is None:
        raise HTTPException(404, "alert not found")
    return result


@app.delete("/api/alerts/{alert_id}")
def delete_alert(alert_id: int) -> dict:
    ok = state.userstore.alert_delete(alert_id)
    if not ok:
        raise HTTPException(404, "alert not found")
    return {"deleted": True}


@app.post("/api/alerts/{alert_id}/ack")
def ack_alert(alert_id: int) -> dict:
    ok = state.userstore.alert_ack(alert_id)
    if not ok:
        raise HTTPException(404, "alert not found")
    return {"acknowledged": True}


# -- 投资组合 --

@app.get("/api/portfolio")
def get_portfolio() -> list[dict]:
    return state.userstore.portfolio_holdings()


class PortfolioAddReq(BaseModel):
    symbol: str
    name: str = ""
    quantity: float = Field(..., gt=0)
    avg_cost: float = Field(..., gt=0)
    entry_date: str = ""
    notes: str = ""


@app.post("/api/portfolio")
def add_portfolio_holding(req: PortfolioAddReq) -> dict:
    return state.userstore.portfolio_add_holding(
        req.symbol, req.name, req.quantity, req.avg_cost,
        req.entry_date or None, req.notes)


@app.put("/api/portfolio/{holding_id}")
def update_portfolio_holding(holding_id: int, req: PortfolioAddReq) -> dict:
    result = state.userstore.portfolio_update_holding(
        holding_id, symbol=req.symbol, name=req.name,
        quantity=req.quantity, avg_cost=req.avg_cost, notes=req.notes)
    if result is None:
        raise HTTPException(404, "holding not found")
    return result


@app.delete("/api/portfolio/{holding_id}")
def delete_portfolio_holding(holding_id: int) -> dict:
    ok = state.userstore.portfolio_delete_holding(holding_id)
    if not ok:
        raise HTTPException(404, "holding not found")
    return {"deleted": True}


@app.get("/api/portfolio/snapshots")
def get_portfolio_snapshots(limit: int = 90) -> list[dict]:
    return state.userstore.portfolio_snapshots(limit)


class SnapshotReq(BaseModel):
    total_value: float
    cash: float = 0
    holdings_json: str = "[]"


@app.post("/api/portfolio/snapshots")
def add_portfolio_snapshot(req: SnapshotReq) -> dict:
    return state.userstore.portfolio_add_snapshot(
        req.total_value, req.cash, req.holdings_json)


# -- 交易日志 --

@app.get("/api/journal")
def get_journal(symbol: str = None, limit: int = 50) -> list[dict]:
    return state.userstore.journal_list(symbol=symbol, limit=limit)


class JournalCreateReq(BaseModel):
    symbol: str = ""
    direction: str = ""
    entry_date: str = ""
    exit_date: str = ""
    entry_price: float = 0
    exit_price: float = 0
    quantity: float = 0
    pnl: float = 0
    pnl_pct: float = 0
    tags: list[str] = []
    notes: str = ""
    rating: int = 0


@app.post("/api/journal")
def create_journal(req: JournalCreateReq) -> dict:
    return state.userstore.journal_create(**req.model_dump())


@app.put("/api/journal/{journal_id}")
def update_journal(journal_id: int, req: JournalCreateReq) -> dict:
    result = state.userstore.journal_update(journal_id, **req.model_dump(exclude_none=True))
    if result is None:
        raise HTTPException(404, "journal entry not found")
    return result


@app.delete("/api/journal/{journal_id}")
def delete_journal(journal_id: int) -> dict:
    ok = state.userstore.journal_delete(journal_id)
    if not ok:
        raise HTTPException(404, "journal entry not found")
    return {"deleted": True}


@app.get("/api/journal/stats")
def get_journal_stats() -> dict:
    return state.userstore.journal_stats()


# -- 策略参数 --

@app.get("/api/strategy/{name}/params")
def get_strategy_params(name: str) -> dict:
    return state.userstore.strategy_params_get(name)


class StrategyParamsReq(BaseModel):
    params: dict


@app.put("/api/strategy/{name}/params")
def set_strategy_params(name: str, req: StrategyParamsReq) -> dict:
    return state.userstore.strategy_params_set(name, req.params)


# ---------- 直跑入口 ----------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("webapp.backend.server:app",
                host="0.0.0.0", port=8765, reload=False)
