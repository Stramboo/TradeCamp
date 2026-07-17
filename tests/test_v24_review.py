# -*- coding: utf-8 -*-
"""test_v24_review.py — v2.4 Phase 2 复盘闭环测试"""

import os
import tempfile
import pytest

from webapp.backend.userstore import UserStore
from webapp.backend.review_service import compute_sell_pnl, auto_review_on_sell


@pytest.fixture
def store():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.unlink(path)
    s = UserStore(db_path=path)
    yield s
    try:
        os.unlink(path)
    except OSError:
        pass


def _buy(store, symbol, qty, price, ts):
    oid = f"buy-{symbol}-{ts}"
    store.sandbox_buy(symbol, qty, price, oid, ts)
    return oid


def _sell(store, symbol, qty, price, ts):
    oid = f"sell-{symbol}-{ts}"
    store.sandbox_sell(symbol, qty, price, oid, ts)
    return oid


DAY = 1000 * 60 * 60 * 24


class TestComputeSellPnl:
    def test_single_buy_single_sell_profit(self, store):
        _buy(store, "NVDA", 10, 400, 1000)
        orders = store.sandbox_orders_list()
        result = compute_sell_pnl(orders, "NVDA", 10, 440, 1000 + 5 * DAY)
        assert result["pnl"] == 400.0
        assert result["pnl_pct"] == 10.0
        assert result["holding_days"] == 5.0

    def test_single_buy_single_sell_loss(self, store):
        _buy(store, "AAPL", 10, 180, 1000)
        orders = store.sandbox_orders_list()
        result = compute_sell_pnl(orders, "AAPL", 10, 170, 1000 + DAY)
        assert result["pnl"] == -100.0
        assert result["pnl_pct"] == pytest.approx(-5.56, abs=0.01)

    def test_multiple_buys_fifo(self, store):
        """多笔买入按 FIFO 配对"""
        _buy(store, "TSLA", 10, 200, 1000)
        _buy(store, "TSLA", 10, 220, 1000 + DAY)
        orders = store.sandbox_orders_list()
        # 卖出 15 股：10 股 @200 + 5 股 @220，平均成本 = (2000+1100)/15 = 206.67
        result = compute_sell_pnl(orders, "TSLA", 15, 250, 1000 + 2 * DAY)
        assert result["avg_cost"] == pytest.approx(206.6667, abs=0.01)
        assert result["pnl"] == pytest.approx((250 - 206.6667) * 15, abs=0.1)

    def test_partial_sell_then_sell_again(self, store):
        """部分卖出后再次卖出，FIFO 队列正确消耗"""
        _buy(store, "MSFT", 20, 400, 1000)
        _sell(store, "MSFT", 10, 420, 1000 + DAY)
        orders = store.sandbox_orders_list()
        # 再卖 10 股，仍配对 @400
        result = compute_sell_pnl(orders, "MSFT", 10, 440, 1000 + 2 * DAY)
        assert result["avg_cost"] == 400.0
        assert result["pnl"] == 400.0

    def test_no_buy_history(self, store):
        result = compute_sell_pnl([], "NVDA", 10, 500, 1000)
        assert result["pnl"] == 0
        assert result["holding_days"] == 0


class TestAutoReview:
    def test_review_generated_on_sell(self, store):
        _buy(store, "NVDA", 10, 400, 1000)
        sell_oid = _sell(store, "NVDA", 10, 440, 1000 + 5 * DAY)
        review = auto_review_on_sell(store, "NVDA", 10, 440, sell_oid, 1000 + 5 * DAY)
        assert review is not None
        assert review["symbol"] == "NVDA"
        assert review["pnl"] == 400.0
        assert review["score"] > 0

    def test_review_persisted(self, store):
        _buy(store, "AAPL", 10, 180, 1000)
        sell_oid = _sell(store, "AAPL", 10, 190, 1000 + 3 * DAY)
        auto_review_on_sell(store, "AAPL", 10, 190, sell_oid, 1000 + 3 * DAY)
        reviews = store.review_list()
        assert len(reviews) == 1
        assert reviews[0]["trade_id"] == sell_oid

    def test_review_idempotent(self, store):
        """同一订单不重复生成复盘"""
        _buy(store, "NVDA", 10, 400, 1000)
        sell_oid = _sell(store, "NVDA", 10, 440, 1000 + DAY)
        r1 = auto_review_on_sell(store, "NVDA", 10, 440, sell_oid, 1000 + DAY)
        r2 = auto_review_on_sell(store, "NVDA", 10, 440, sell_oid, 1000 + DAY)
        assert len(store.review_list()) == 1

    def test_panic_sell_detected(self, store):
        """持有 1 天亏损 5% 卖出 → 恐慌卖出"""
        _buy(store, "TSLA", 10, 200, 1000)
        sell_oid = _sell(store, "TSLA", 10, 190, 1000 + DAY)
        review = auto_review_on_sell(store, "TSLA", 10, 190, sell_oid, 1000 + DAY)
        patterns = [m["pattern"] for m in review["mistakes"]]
        assert "panic_sell" in patterns

    def test_xp_awarded(self, store):
        _buy(store, "NVDA", 10, 400, 1000)
        sell_oid = _sell(store, "NVDA", 10, 440, 1000 + DAY)
        auto_review_on_sell(store, "NVDA", 10, 440, sell_oid, 1000 + DAY)
        stats = store.get_learning_stats()
        assert stats["total_xp"] == 15

    def test_graceful_on_error(self, store):
        """异常时返回 None 而不抛错"""
        result = auto_review_on_sell(store, "INVALID", 10, 100, "bad-order", 1000)
        # 无买单历史也能正常生成（pnl=0），不抛异常即达标
        assert result is None or isinstance(result, dict)
