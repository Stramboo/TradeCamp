# -*- coding: utf-8 -*-
"""
diagnosis_service.py — 弱项诊断与自适应学习引擎 (v2.5 Phase 2a)

功能:
  - 6 维能力雷达图：知识/判断/纪律/风控/情绪/复盘
  - 弱项诊断：融合 quiz/scenario/emotion/review 多源数据
  - 动态学习路径推荐：基于弱项 + 间隔重复
  - "你可能犯的错误"预测：基于历史行为模式
"""

import logging
from datetime import date, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


def diagnose_ability(store) -> dict:
    """
    6 维能力诊断

    维度:
      knowledge: 知识掌握（quiz 正确率 + 知识点掌握度）
      judgment: 判断力（scenario 情景题得分）
      discipline: 纪律性（交易计划完成率 + 止损执行）
      risk_control: 风控（仓位管理 + 止损使用率）
      emotion: 情绪管理（情绪训练理性度 + 情绪决策占比）
      review_skill: 复盘能力（复盘评分 + 复盘频率）
    """
    try:
        # 1. 知识维度：quiz 正确率
        quiz_results = []
        try:
            # 从 quiz_results 表读取（通过 userstore）
            with store._lock:
                rows = store._get_conn().execute(
                    "SELECT score, correct_count, total_questions FROM quiz_results ORDER BY id DESC LIMIT 30"
                ).fetchall()
            quiz_results = [{"score": r["score"], "correct": r["correct_count"],
                             "total": r["total_questions"]} for r in rows]
        except Exception:
            pass

        knowledge_score = 50  # 默认
        if quiz_results:
            avg_score = sum(q["score"] for q in quiz_results) / len(quiz_results)
            knowledge_score = int(avg_score)

        # 知识点掌握度（错题本）
        mistake_stats = store.mistake_stats()
        total_mistakes = sum(s["total_wrong"] for s in mistake_stats.values())
        knowledge_score = max(0, knowledge_score - min(50, total_mistakes * 5))

        # 2. 判断维度：scenario 情景题
        judgment_score = 50
        try:
            scenario_mistakes = [m for m in store.mistake_list() if m["source"] == "scenario"]
            if scenario_mistakes:
                # 有错题说明判断力有待提升
                judgment_score = max(20, 80 - len(scenario_mistakes) * 10)
            else:
                judgment_score = 70  # 无错题，基础分
        except Exception:
            pass

        # 3. 纪律维度：交易计划 + 止损执行
        discipline_score = 50
        try:
            plans = store.trade_plan_list(20)
            orders = store.sandbox_orders_list(20)
            if plans and orders:
                # 有计划且交易的比率
                plan_rate = min(len(plans), len(orders)) / max(len(orders), 1)
                discipline_score = int(40 + plan_rate * 60)
            elif orders:
                # 有交易但无计划，纪律性低
                discipline_score = 30
        except Exception:
            pass

        # 4. 风控维度：止损使用率 + 复盘错误模式
        risk_score = 50
        try:
            reviews = store.review_list(20)
            if reviews:
                # 有止损的比例
                stop_loss_used = sum(1 for r in reviews if r.get("mistakes"))
                panic_sells = sum(1 for r in reviews
                                  if any(m.get("pattern") == "panic_sell" for m in r.get("mistakes", [])))
                if len(reviews) > 0:
                    risk_score = int(60 - panic_sells / len(reviews) * 40)
                    risk_score = max(10, min(100, risk_score))
        except Exception:
            pass

        # 5. 情绪维度：情绪训练理性度
        emotion_score = 50
        try:
            emotion_journals = store.emotion_journal_list(20)
            if emotion_journals:
                avg_rationality = sum(j["rationality_score"] for j in emotion_journals) / len(emotion_journals)
                emotion_score = int(avg_rationality)
        except Exception:
            pass

        # 6. 复盘维度：复盘频率 + 评分
        review_score = 50
        try:
            reviews = store.review_list(50)
            if reviews:
                avg_review_score = sum(r["score"] for r in reviews) / len(reviews)
                frequency_bonus = min(20, len(reviews) * 2)
                review_score = int(avg_review_score * 0.7 + frequency_bonus)
                review_score = min(100, review_score)
        except Exception:
            pass

        scores = {
            "knowledge": knowledge_score,
            "judgment": judgment_score,
            "discipline": discipline_score,
            "risk_control": risk_score,
            "emotion": emotion_score,
            "review_skill": review_score,
        }

        # 弱项排序
        sorted_dims = sorted(scores.items(), key=lambda x: x[1])
        weak_points = [d for d, s in sorted_dims if s < 60]

        # 保存快照
        try:
            store.ability_snapshot_save(scores, ",".join(weak_points))
        except Exception:
            pass

        return {
            "scores": scores,
            "weak_points": weak_points,
            "strongest": sorted_dims[-1][0] if sorted_dims else None,
            "weakest": sorted_dims[0][0] if sorted_dims else None,
            "overall": int(sum(scores.values()) / len(scores)),
        }
    except Exception as e:
        logger.warning(f"能力诊断失败: {e}")
        return {"scores": {}, "weak_points": [], "overall": 0}


# 维度中文名
DIMENSION_NAMES = {
    "knowledge": "知识掌握",
    "judgment": "判断力",
    "discipline": "纪律性",
    "risk_control": "风控能力",
    "emotion": "情绪管理",
    "review_skill": "复盘能力",
}

# 弱项 → 推荐内容映射
WEAK_POINT_RECOMMENDATIONS = {
    "knowledge": [
        {"type": "review_mistakes", "title": "复习错题本", "desc": "你有未掌握的知识点", "link": "/me/mistakes"},
        {"type": "retake_quiz", "title": "重做课时测验", "desc": "巩固薄弱知识点", "link": "/learning"},
    ],
    "judgment": [
        {"type": "scenario_practice", "title": "练习情景判断题", "desc": "提升决策判断力", "link": "/learning"},
        {"type": "historical_replay", "title": "历史事件回放", "desc": "从历史中学习判断", "link": "/practice/replay"},
    ],
    "discipline": [
        {"type": "trade_plan", "title": "写交易计划", "desc": "每笔交易前必写计划", "link": "/practice/free"},
        {"type": "scenario_practice", "title": "纪律情景训练", "desc": "练习止损纪律", "link": "/practice"},
    ],
    "risk_control": [
        {"type": "position_sizing", "title": "仓位管理练习", "desc": "学习 2% 规则", "link": "/learning/ch19"},
        {"type": "review_mistakes", "title": "复盘错误模式", "desc": "识别你的风控漏洞", "link": "/me/reviews"},
    ],
    "emotion": [
        {"type": "emotion_training", "title": "情绪训练", "desc": "FOMO/恐慌/贪婪专项训练", "link": "/practice/emotion"},
        {"type": "meditation", "title": "交易前冥想", "desc": "建立冷静仪式", "link": "/practice/emotion"},
    ],
    "review_skill": [
        {"type": "review_center", "title": "复盘中心", "desc": "深度复盘你的交易", "link": "/me/reviews"},
        {"type": "journal", "title": "写交易日志", "desc": "记录决策与反思", "link": "/practice/free"},
    ],
}


def recommend_learning_path(store) -> list[dict]:
    """
    基于弱项的动态学习路径推荐

    返回优先级排序的推荐列表
    """
    diagnosis = diagnose_ability(store)
    weak_points = diagnosis.get("weak_points", [])
    recommendations = []

    for wp in weak_points:
        recs = WEAK_POINT_RECOMMENDATIONS.get(wp, [])
        for r in recs:
            recommendations.append({
                **r,
                "dimension": wp,
                "dimension_name": DIMENSION_NAMES.get(wp, wp),
                "priority": "high",
            })

    # 如果无弱项，推荐进阶内容
    if not recommendations:
        recommendations = [
            {"type": "advanced", "title": "探索高阶分析", "desc": "你的基础已扎实，试试深度分析",
             "link": "/explore", "priority": "low"},
            {"type": "emotion_advanced", "title": "进阶情绪训练", "desc": "挑战复杂情绪场景",
             "link": "/practice/emotion", "priority": "low"},
        ]

    return recommendations[:5]  # 最多 5 条


def predict_mistakes(store) -> list[dict]:
    """
    "你可能犯的错误"预测

    基于历史行为模式预测潜在错误
    """
    predictions = []

    try:
        # 1. 追涨倾向：近期 BUY 行为
        orders = store.sandbox_orders_list(20)
        if orders:
            recent_buys = [o for o in orders[-10:] if o.get("side") == "BUY"]
            if len(recent_buys) >= 5:
                predictions.append({
                    "pattern": "fomo_tendency",
                    "title": "你可能正在追涨",
                    "desc": "你近期交易频繁，注意 FOMO 倾向。每次买入前问自己：这是计划内的吗？",
                    "severity": "warning",
                })

        # 2. 止损不执行：复盘中的 panic_sell
        reviews = store.review_list(20)
        if reviews:
            panic_count = sum(1 for r in reviews
                              if any(m.get("pattern") == "panic_sell" for m in r.get("mistakes", [])))
            if panic_count >= 2:
                predictions.append({
                    "pattern": "panic_sell_risk",
                    "title": "你有恐慌卖出倾向",
                    "desc": f"最近 {panic_count} 次复盘检测到恐慌卖出。建议设好止损并严格执行。",
                    "severity": "danger",
                })

        # 3. 情绪决策：情绪训练理性度低
        emotion_journals = store.emotion_journal_list(10)
        if emotion_journals:
            avg_rationality = sum(j["rationality_score"] for j in emotion_journals) / len(emotion_journals)
            if avg_rationality < 50:
                predictions.append({
                    "pattern": "emotional_decision",
                    "title": "你的情绪决策偏多",
                    "desc": "情绪训练理性度偏低，建议多练习 FOMO/恐慌场景。",
                    "severity": "warning",
                })

        # 4. 仓位集中：持仓数量少但单只占比高
        account = store.sandbox_get()
        positions = account.get("positions", [])
        if positions and len(positions) <= 2:
            total_value = sum(p["quantity"] * p["avg_cost"] for p in positions)
            if total_value > 0:
                max_position = max(p["quantity"] * p["avg_cost"] for p in positions)
                if max_position / total_value > 0.6:
                    predictions.append({
                        "pattern": "concentration_risk",
                        "title": "仓位过于集中",
                        "desc": "单只股票占比超 60%，建议分散到 5-10 只不同行业股票。",
                        "severity": "warning",
                    })

        # 5. 不复盘：有交易但无复盘
        if orders and not reviews:
            predictions.append({
                "pattern": "no_review",
                "title": "你从不复盘",
                "desc": "有交易记录但没有复盘。不复盘的交易=浪费学费。去复盘中心看看吧。",
                "severity": "info",
            })

    except Exception as e:
        logger.warning(f"错误预测失败: {e}")

    return predictions


__all__ = [
    "diagnose_ability", "recommend_learning_path", "predict_mistakes",
    "DIMENSION_NAMES", "WEAK_POINT_RECOMMENDATIONS",
]
