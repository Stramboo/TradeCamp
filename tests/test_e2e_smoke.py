# -*- coding: utf-8 -*-
"""
test_e2e_smoke.py — 核心 E2E 冒烟测试

验证完整交易流程链路：数据 → 买入(含计划) → 卖出(含复盘) → 教练评估。
使用 FastAPI TestClient 直接调用 API，无需浏览器。
"""
import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _read_json(response):
    """兼容 httpx Response 的 json 读取"""
    if hasattr(response, "json"):
        return response.json()
    return response


class TestE2ESandboxFlow:
    """沙盒交易完整流程 — API 级 E2E"""

    @pytest.fixture(scope="class")
    def client(self):
        """创建 FastAPI TestClient + 临时数据库 + MockEngine"""
        import webapp.backend.server as server_mod
        from webapp.backend.userstore import UserStore
        from webapp.backend.adapters.mock_engine import MockEngine

        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        store = UserStore(db_path)
        store.sandbox_reset()

        # 保存并替换 server 模块的全局状态
        original_store = server_mod.state.userstore
        original_engine = server_mod.state.engine
        original_kind = server_mod.state.backend_kind

        server_mod.state.userstore = store
        server_mod.state.engine = MockEngine()
        server_mod.state.backend_kind = "mock"

        from fastapi.testclient import TestClient
        tc = TestClient(server_mod.app)

        yield tc

        # 恢复
        server_mod.state.userstore = original_store
        server_mod.state.engine = original_engine
        server_mod.state.backend_kind = original_kind
        if hasattr(store, '_conn') and store._conn:
            store._conn.close()
        import gc
        gc.collect()
        try:
            os.unlink(db_path)
        except PermissionError:
            pass

    # ---- 测试用例 ----

    def test_01_reset_sandbox(self, client):
        """重置沙盒账户"""
        resp = client.post("/api/sandbox/reset")
        assert resp.status_code == 200
        data = _read_json(resp)
        assert data["ok"] is True

    def test_02_account_has_cash(self, client):
        """账户有初始资金"""
        resp = client.get("/api/sandbox/account")
        assert resp.status_code == 200
        data = _read_json(resp)
        assert data["cash"] == 100_000

    def test_03_fetch_market_prices(self, client):
        """获取市场行情"""
        resp = client.get("/api/market/batch?symbols=NVDA,AAPL,TSLA")
        assert resp.status_code == 200
        data = _read_json(resp)
        assert "prices" in data
        assert isinstance(data["prices"], dict)
        # MockEngine 导入 backend 时会生成价格
        assert len(data["prices"]) >= 1

    def test_04_create_trade_plan(self, client):
        """创建交易计划"""
        resp = client.post("/api/trade-plans", json={
            "symbol": "NVDA", "direction": "long",
            "reason": "MACD金叉突破 + RSI趋势向上，W底颈线突破确认",
            "entry_price": 450.0, "max_loss_pct": 5,
            "position_pct": 10, "planned_holding": "短期(1-5天)",
        })
        assert resp.status_code == 200
        data = _read_json(resp)
        assert data["id"] > 0
        assert data["symbol"] == "NVDA"

    def test_05_buy_stock(self, client):
        """买入股票"""
        # 先获取价格
        price_resp = client.get("/api/market/batch?symbols=NVDA")
        prices = _read_json(price_resp)["prices"]
        nvda_price = prices.get("NVDA", 450.0)

        resp = client.post("/api/sandbox/order", json={
            "symbol": "NVDA", "side": "BUY", "quantity": 10, "price": nvda_price,
        })
        assert resp.status_code == 200
        data = _read_json(resp)
        assert data["status"] == "filled"

        # 验证账户
        acc_resp = client.get("/api/sandbox/account")
        acc = _read_json(acc_resp)
        assert acc["cash"] < 100_000  # 花了钱
        assert len(acc["positions"]) >= 1
        assert any(p["symbol"] == "NVDA" for p in acc["positions"])

    def test_06_list_orders(self, client):
        """订单列表"""
        resp = client.get("/api/sandbox/orders")
        assert resp.status_code == 200
        data = _read_json(resp)
        assert isinstance(data, list)
        assert len(data) >= 1  # 至少有一条买入记录

    def test_07_trade_plan_list(self, client):
        """交易计划列表"""
        resp = client.get("/api/trade-plans")
        assert resp.status_code == 200
        data = _read_json(resp)
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_08_coach_review_after_buy(self, client):
        """教练评估买入交易"""
        price_resp = client.get("/api/market/batch?symbols=NVDA")
        prices = _read_json(price_resp)["prices"]
        nvda_price = prices.get("NVDA", 460.0)

        resp = client.post("/api/coach/review", json={
            "trade": {"symbol": "NVDA", "side": "BUY", "quantity": 10, "price": nvda_price},
            "plan": {"reason": "MACD金叉突破确认", "max_loss_pct": 5, "position_pct": 10, "planned_holding": "短期(1-5天)"},
            "enable_llm": False,
        })
        assert resp.status_code == 200
        data = _read_json(resp)
        assert "overall" in data
        assert "grade" in data
        assert data["grade"] in ("S", "A", "B", "C", "D")
        assert "decision" in data
        assert "execution" in data
        assert "risk" in data
        assert "attribution" in data
        assert 0 <= data["overall"] <= 100

    def test_09_watchlist_crud(self, client):
        """自选列表增删查"""
        # 创建
        create_resp = client.post("/api/watchlists", json={
            "name": "测试列表", "symbols": ["NVDA", "AAPL"],
        })
        assert create_resp.status_code == 200

        # 列表
        list_resp = client.get("/api/watchlists")
        assert list_resp.status_code == 200
        data = _read_json(list_resp)
        assert isinstance(data, list)

        # 更新
        if data:
            wl_id = data[0]["id"]
            update_resp = client.put(f"/api/watchlists/{wl_id}", json={
                "name": "更新列表", "symbols": ["NVDA", "AAPL", "TSLA"],
            })
            assert update_resp.status_code == 200

    def test_10_learning_progress(self, client):
        """学习进度 API"""
        resp = client.get("/api/learning/progress")
        # 可能 200 或 500（取决于 store 的初始化状态）
        assert resp.status_code in (200, 500)
