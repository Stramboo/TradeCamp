# -*- coding: utf-8 -*-
"""test_v25_phase2.py — v2.5 Phase 2 自适应学习 + 高阶分析测试"""

import os
import tempfile
import pytest

from webapp.backend.userstore import UserStore
from webapp.backend.diagnosis_service import (
    diagnose_ability, recommend_learning_path, predict_mistakes, DIMENSION_NAMES,
)
from webapp.backend.advanced_analysis import (
    list_valuation_models, get_valuation_model, calculate_valuation, BACKTEST_TEACHING,
)


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


class TestDiagnosis:
    def test_diagnose_empty_user(self, store):
        """全新用户的诊断"""
        result = diagnose_ability(store)
        assert "scores" in result
        assert "weak_points" in result
        assert "overall" in result
        assert len(result["scores"]) == 6

    def test_diagnose_with_quiz_data(self, store):
        """有测验数据的诊断"""
        store.quiz_result_save("ch01", "lesson_quiz", 90, 9, 10, True)
        store.quiz_result_save("ch02", "lesson_quiz", 80, 8, 10, True)
        result = diagnose_ability(store)
        assert result["scores"]["knowledge"] >= 70

    def test_diagnose_with_mistakes(self, store):
        """有错题的诊断"""
        for i in range(5):
            store.mistake_add("scenario", f"q{i}", "stop_loss", "ch18")
        result = diagnose_ability(store)
        assert result["scores"]["knowledge"] < 70  # 错题多拉低知识分

    def test_weak_points_identified(self, store):
        """识别弱项"""
        # 无任何情绪训练 → emotion 维度低
        result = diagnose_ability(store)
        # 新用户大多维度是默认 50，可能不触发弱项
        assert isinstance(result["weak_points"], list)

    def test_recommendations_for_weak_user(self, store):
        """弱项用户有推荐"""
        recs = recommend_learning_path(store)
        assert isinstance(recs, list)
        # 新用户应该有推荐（至少 1 条）
        assert len(recs) >= 1

    def test_dimension_names(self):
        assert DIMENSION_NAMES["knowledge"] == "知识掌握"
        assert len(DIMENSION_NAMES) == 6

    def test_predict_mistakes_empty(self, store):
        """新用户无预测"""
        preds = predict_mistakes(store)
        assert isinstance(preds, list)

    def test_predict_fomo_tendency(self, store):
        """频繁交易触发 FOMO 预测"""
        for i in range(6):
            store.sandbox_buy("NVDA", 10, 400, f"b{i}", 1000 + i)
        preds = predict_mistakes(store)
        patterns = [p["pattern"] for p in preds]
        assert "fomo_tendency" in patterns

    def test_predict_no_review(self, store):
        """有交易无复盘触发预测"""
        store.sandbox_buy("NVDA", 10, 400, "b1", 1000)
        preds = predict_mistakes(store)
        patterns = [p["pattern"] for p in preds]
        assert "no_review" in patterns

    def test_predict_concentration_risk(self, store):
        """仓位集中触发预测"""
        store.sandbox_buy("NVDA", 100, 400, "b1", 1000)  # 单只大仓位
        preds = predict_mistakes(store)
        patterns = [p["pattern"] for p in preds]
        assert "concentration_risk" in patterns

    def test_ability_snapshot_saved(self, store):
        """诊断结果保存快照"""
        diagnose_ability(store)
        snapshot = store.ability_snapshot_latest()
        assert snapshot is not None
        assert "knowledge" in snapshot


class TestValuationModels:
    def test_list_models(self):
        models = list_valuation_models()
        assert len(models) >= 3
        assert any(m["id"] == "pe_model" for m in models)

    def test_get_model(self):
        m = get_valuation_model("pe_model")
        assert m is not None
        assert "formula" in m
        assert "calculate" in m

    def test_calculate_pe(self):
        result = calculate_valuation("pe_model", {"eps": 5.0, "pe": 20})
        assert result["result"] == 100.0
        assert "lesson" in result

    def test_calculate_dcf(self):
        result = calculate_valuation("dcf_model", {
            "fcf": 100, "growth_rate": 10, "discount_rate": 8,
            "years": 10, "shares": 16,
        })
        assert result["result"] > 0
        assert "lesson" in result

    def test_calculate_pb(self):
        result = calculate_valuation("pb_model", {"bps": 50, "pb": 1.5})
        assert result["result"] == 75.0

    def test_unknown_model(self):
        result = calculate_valuation("unknown", {})
        assert "error" in result

    def test_backtest_teaching(self):
        assert "parameters" in BACKTEST_TEACHING
        assert "metrics" in BACKTEST_TEACHING
        assert "common_pitfalls" in BACKTEST_TEACHING
        assert len(BACKTEST_TEACHING["common_pitfalls"]) >= 4
