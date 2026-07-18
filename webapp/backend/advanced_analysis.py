# -*- coding: utf-8 -*-
"""
advanced_analysis.py — 高阶分析课程内容 (v2.5 Phase 2b)

框定为"高阶课程"而非独立工具，包含：
- 估值模型教学（DCF/PE/PB 交互式计算器）
- 财务速览教学模板
- 回测教学版参数说明
"""

# 估值模型教学
VALUATION_MODELS = {
    "pe_model": {
        "id": "pe_model", "title": "市盈率（PE）估值",
        "description": "最常用的相对估值法。通过比较公司 PE 与行业平均，判断高估或低估。",
        "formula": "合理价格 = 每股收益(EPS) × 合理PE",
        "inputs": [
            {"key": "eps", "label": "每股收益 EPS", "default": 5.0, "unit": "美元"},
            {"key": "pe", "label": "合理 PE", "default": 20, "unit": "倍"},
        ],
        "calculate": lambda inputs: inputs["eps"] * inputs["pe"],
        "result_label": "合理价格",
        "lesson": "PE 估值的关键在于「合理 PE」的选取。新用户常犯错误：用当前 PE 判断贵贱，而忽略了增长率。高增长公司 PE 高是合理的（用 PEG 判断）。",
        "example": "苹果 EPS=$6，行业平均 PE=25，合理价格=$150。如果当前价格 $120，可能被低估。",
    },
    "dcf_model": {
        "id": "dcf_model", "title": "现金流折现（DCF）估值",
        "description": "巴菲特最爱的估值法。把公司未来能产生的现金流折算到今天。",
        "formula": "合理价格 = Σ(未来现金流 / (1+折现率)^年数)",
        "inputs": [
            {"key": "fcf", "label": "当前自由现金流", "default": 100, "unit": "亿美元"},
            {"key": "growth_rate", "label": "预期增长率", "default": 10, "unit": "%"},
            {"key": "discount_rate", "label": "折现率", "default": 8, "unit": "%"},
            {"key": "years", "label": "预测年限", "default": 10, "unit": "年"},
            {"key": "shares", "label": "总股本", "default": 16, "unit": "亿股"},
        ],
        "calculate": lambda inputs: sum(
            inputs["fcf"] * (1 + inputs["growth_rate"] / 100) ** (y + 1) /
            (1 + inputs["discount_rate"] / 100) ** (y + 1)
            for y in range(int(inputs["years"]))
        ) / inputs["shares"],
        "result_label": "每股合理价格",
        "lesson": "DCF 对增长率和折现率极度敏感。增长率从 10% 改到 15%，估值可能翻倍。新手要学会做敏感性分析——不同假设下的估值范围。",
        "example": "公司 FCF=100亿，增长 10%，折现 8%，10 年，16 亿股 → 合理价约 $65/股。",
    },
    "pb_model": {
        "id": "pb_model", "title": "市净率（PB）估值",
        "description": "适合银行、保险等资产密集型公司。比较股价与每股净资产。",
        "formula": "合理价格 = 每股净资产(BPS) × 合理PB",
        "inputs": [
            {"key": "bps", "label": "每股净资产 BPS", "default": 50, "unit": "美元"},
            {"key": "pb", "label": "合理 PB", "default": 1.5, "unit": "倍"},
        ],
        "calculate": lambda inputs: inputs["bps"] * inputs["pb"],
        "result_label": "合理价格",
        "lesson": "PB 适合重资产行业（银行、地产）。PB<1 表示股价低于净资产，可能是价值陷阱也可能是机会——需要结合 ROE 判断。",
        "example": "银行 BPS=$30，合理 PB=1.2，合理价格=$36。",
    },
}


# 回测教学版参数说明
BACKTEST_TEACHING = {
    "title": "策略回测教学版",
    "description": "用历史数据验证交易策略。记住：回测好≠实盘好，但回测差=实盘一定差。",
    "parameters": [
        {"key": "strategy", "label": "策略类型", "options": ["均线交叉", "动量", "均值回归", "定投"],
         "teaching": "均线交叉最简单，适合新手。动量策略在趋势市好，均值回归在震荡市好。"},
        {"key": "period", "label": "回测周期", "default": "5年",
         "teaching": "至少 5 年，包含牛熊市。1 年的回测没有意义（可能只是运气）。"},
        {"key": "initial_capital", "label": "初始资金", "default": 100000,
         "teaching": "用你实盘的真实资金规模回测，结果才有参考价值。"},
        {"key": "commission", "label": "手续费率", "default": 0.025, "unit": "%",
         "teaching": "必须包含手续费！很多策略回测赚钱，扣手续费就亏了。"},
    ],
    "metrics": [
        {"key": "total_return", "label": "总收益率", "teaching": "与买入持有对比。如果跑不赢买入持有，策略没意义。"},
        {"key": "max_drawdown", "label": "最大回撤", "teaching": "比收益率更重要！回撤 50% 需要涨 100% 才能回本。"},
        {"key": "sharpe_ratio", "label": "夏普比率", "teaching": "风险调整后收益。>1 算不错，>2 是优秀。"},
        {"key": "win_rate", "label": "胜率", "teaching": "胜率不重要，盈亏比才重要。40% 胜率但盈亏比 3:1 的策略是赚钱的。"},
    ],
    "common_pitfalls": [
        "过度拟合：参数调到历史最优，但未来无效",
        "幸存者偏差：只回测现存公司，忽略已退市的",
        "前视偏差：用了当时不可能知道的信息",
        "忽略滑点：大资金无法以收盘价成交",
    ],
}


def list_valuation_models() -> list[dict]:
    """列出所有估值模型"""
    return [{"id": m["id"], "title": m["title"], "description": m["description"]}
            for m in VALUATION_MODELS.values()]


def get_valuation_model(model_id: str) -> dict | None:
    """获取估值模型详情"""
    m = VALUATION_MODELS.get(model_id)
    if not m:
        return None
    return m


def calculate_valuation(model_id: str, inputs: dict) -> dict:
    """计算估值"""
    m = VALUATION_MODELS.get(model_id)
    if not m:
        return {"error": "模型不存在"}
    try:
        result = m["calculate"](inputs)
        return {
            "model_id": model_id,
            "result": round(result, 2),
            "result_label": m["result_label"],
            "lesson": m["lesson"],
        }
    except Exception as e:
        return {"error": f"计算失败: {e}"}


__all__ = [
    "VALUATION_MODELS", "BACKTEST_TEACHING",
    "list_valuation_models", "get_valuation_model", "calculate_valuation",
]
