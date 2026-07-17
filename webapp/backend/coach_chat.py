# -*- coding: utf-8 -*-
"""
coach_chat.py — AI 教练对话引擎 (v2.3 Phase 4)

功能:
  - 规则分类器：识别用户问题类型（概念/交易/市场/学习路径）
  - 术语解释：从 GLOSSARY 匹配并返回解释
  - 交易回顾：查询用户最近交易并生成分析
  - 学习推荐：根据进度推荐下一步课程
  - LLM 兜底：无法匹配时调用 DeepSeek（可选）
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================
# 问题类型识别
# ============================================================

QUESTION_PATTERNS = {
    "concept": [
        r"什么是(.+)",
        r"(.+?)是什么",
        r"解释(.+)",
        r"(.+?)的意思",
        r"如何理解(.+)",
    ],
    "trade_review": [
        r"我(最近|刚才|今天)的?(交易|操作|买卖)",
        r"帮我(看看|分析|复盘)",
        r"(这笔|这次)交易",
        r"我(买|卖)了(.+)",
    ],
    "market": [
        r"(大盘|市场|行情)(怎么样|如何|走势)",
        r"今天(股市|市场)",
        r"(美股|A股|港股)(怎么样|如何)",
        r"最近(市场|行情)",
    ],
    "learning": [
        r"我(该|应该)(学|学习|看)(什么|哪)",
        r"下一(步|课|阶段)",
        r"学习(计划|路径|建议)",
        r"怎么(开始|入门|学习)",
    ],
    "greeting": [
        r"^(你好|嗨|哈喽|hi|hello)",
        r"^(早上好|下午好|晚上好)",
    ],
    "help": [
        r"^(帮助|help|怎么用|如何使用)",
        r"^(你能做什么|你会什么)",
    ],
}


def classify_question(text: str) -> str:
    """
    识别用户问题类型

    返回:
        str: concept / trade_review / market / learning / greeting / help / general
    """
    text = text.strip().lower()

    for qtype, patterns in QUESTION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return qtype

    return "general"


def extract_term(text: str) -> Optional[str]:
    """从问题中提取术语"""
    # 匹配 "什么是XX" / "XX是什么" / "解释XX"
    patterns = [
        r"什么是([a-zA-Z\u4e00-\u9fff]+)",
        r"([a-zA-Z\u4e00-\u9fff]+)是什么",
        r"解释([a-zA-Z\u4e00-\u9fff]+)",
        r"([a-zA-Z\u4e00-\u9fff]+)的意思",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


# ============================================================
# 回复生成器
# ============================================================

def generate_greeting_response() -> str:
    """生成问候回复"""
    return """你好！我是你的 AI 交易教练 🤖

我可以帮你：
• 解释股票术语和概念
• 分析你的交易记录
• 解答市场相关问题
• 推荐学习路径

有什么想聊的吗？"""


def generate_help_response() -> str:
    """生成帮助回复"""
    return """我是 TradeCamp 的 AI 教练，可以帮你：

📚 **解释概念** — 问我"什么是PE"、"止损是什么意思"
📊 **分析交易** — 说"帮我看看最近的交易"
📈 **市场问题** — 问"今天大盘怎么样"
🎯 **学习建议** — 问"我下一步该学什么"

直接输入你的问题，我会尽力回答！"""


def generate_concept_response(term: str, glossary: list[dict]) -> str:
    """生成概念解释回复"""
    # 在术语表中查找
    term_lower = term.lower()
    for g in glossary:
        if term_lower in g["term"].lower() or g["term"].lower() in term_lower:
            return f"""**{g['term']}**

{g['definition']}

📚 想深入了解？去「学习」页面查看相关课程。"""

    # 未找到
    return f"""抱歉，我还没有收录「{term}」这个术语。

你可以：
• 去「学习」页面的术语表查找
• 换个方式描述你的问题
• 问我其他股票相关的问题"""


def generate_trade_review_response(trades: list[dict]) -> str:
    """生成交易回顾回复"""
    if not trades:
        return """你还没有任何交易记录。

建议先去「模拟练习」完成一笔交易，然后再来找我分析。

记住：每笔交易前都要想清楚——为什么买？准备持有多久？什么情况下卖？"""

    recent = trades[-5:]  # 最近5笔
    buy_count = sum(1 for t in recent if t.get("side") == "BUY")
    sell_count = sum(1 for t in recent if t.get("side") == "SELL")

    return f"""你最近有 {len(recent)} 笔交易（{buy_count} 买 / {sell_count} 卖）。

最近一笔：{recent[-1].get('side', '未知')} {recent[-1].get('symbol', '')} {recent[-1].get('quantity', 0)} 股 @ ${recent[-1].get('price', 0):.2f}

💡 建议：
• 去「我的成长」→「交易复盘」查看详细分析
• 每笔交易后写日志，记录你的思考过程
• 定期回顾：哪些交易赚钱了？为什么？"""


def generate_market_response() -> str:
    """生成市场相关回复"""
    return """我无法提供实时市场数据，但我可以帮你：

📊 **查看市场** — 去「世界市场」页面了解全球 8 大市场
📈 **分析个股** — 去「模拟练习」查看具体股票走势
📚 **学习分析** — 去「学习」页面第 4 阶段「理解股价和图表」

记住：市场短期是投票机，长期是称重机。不要被 daily 波动影响判断。"""


def generate_learning_response(progress: dict) -> str:
    """生成学习建议回复"""
    completed = progress.get("completed_lessons", 0)
    total = progress.get("total_lessons", 24)
    current_stage = progress.get("current_stage", 1)

    stage_names = {
        1: "股票是什么",
        2: "认识全球股票市场",
        3: "如何认识一家公司",
        4: "理解股价和图表",
        5: "建立风险意识",
        6: "模拟交易与复盘",
    }

    if completed == 0:
        return """欢迎来到 TradeCamp！🎉

建议从「学习」页面的第 1 阶段「股票是什么」开始。

第 1 课会告诉你：股票到底是什么？它和你有什么关系？

准备好开始了吗？"""

    if completed >= total:
        return """恭喜！你已经完成了所有课程 🎓

现在可以：
• 去「模拟练习」进行自由交易
• 在「世界市场」探索更多公司
• 定期回顾「交易复盘」，持续改进

学习是终身的，保持好奇心！"""

    next_stage = stage_names.get(current_stage, "下一阶段")
    return f"""你已经完成了 {completed}/{total} 课，很棒！

📚 当前阶段：{next_stage}

建议：
• 继续完成当前阶段的课程
• 每学完一课，去「模拟练习」实践一下
• 完成课后任务可以获得 XP 奖励

加油！"""


def generate_general_response() -> str:
    """生成通用回复"""
    return """我还在学习中，暂时无法理解你的问题。

你可以尝试：
• 问我股票术语（如"什么是PE"）
• 让我分析交易（如"帮我看看最近的交易"）
• 问学习建议（如"我下一步该学什么"）

或者去「学习」页面浏览课程内容。"""


# ============================================================
# 主对话函数
# ============================================================

def chat(message: str, context: dict) -> str:
    """
    处理用户消息，生成教练回复

    参数:
        message: 用户输入的消息
        context: 上下文 {glossary, trades, progress}

    返回:
        str: 教练回复
    """
    qtype = classify_question(message)

    if qtype == "greeting":
        return generate_greeting_response()

    if qtype == "help":
        return generate_help_response()

    if qtype == "concept":
        term = extract_term(message)
        if term:
            return generate_concept_response(term, context.get("glossary", []))
        return generate_general_response()

    if qtype == "trade_review":
        return generate_trade_review_response(context.get("trades", []))

    if qtype == "market":
        return generate_market_response()

    if qtype == "learning":
        return generate_learning_response(context.get("progress", {}))

    return generate_general_response()


__all__ = ["chat", "classify_question", "extract_term"]
