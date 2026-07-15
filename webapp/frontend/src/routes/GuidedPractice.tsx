/**
 * GuidedPractice.tsx — 引导式第一次模拟交易
 *
 * 系统逐步引导新用户完成第一笔模拟交易：
 *   选择公司 → 阅读介绍 → 写买入理由 → 设定仓位 → 提交订单
 *
 * 每一步只有一个主要按钮。
 */
import { useState } from "react";
import { Link } from "react-router-dom";
import { Check } from "lucide-react";

const STEPS = ["选择公司", "了解公司", "买入理由", "确定仓位", "确认下单"] as const;

const COMPANIES = [
  { symbol: "AAPL", name: "Apple", desc: "iPhone、Mac 和 Apple Watch 的制造商", product: "手机 / 电脑" },
  { symbol: "TSLA", name: "Tesla", desc: "电动汽车和清洁能源公司", product: "汽车 / 能源" },
  { symbol: "MSFT", name: "Microsoft", desc: "Windows、Office 和云服务提供商", product: "软件 / 云" },
  { symbol: "NVDA", name: "NVIDIA", desc: "显卡和 AI 芯片领导者", product: "芯片 / AI" },
];

export function GuidedPractice() {
  const [step, setStep] = useState(0);
  const [selected, setSelected] = useState<(typeof COMPANIES)[0] | null>(null);
  const [reason, setReason] = useState("");
  const [positionPct, setPositionPct] = useState(10);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  function handleSelect(c: (typeof COMPANIES)[0]) {
    setSelected(c);
    setError("");
    setStep(1);
  }

  function handleNext() {
    if (step === 1) { setStep(2); return; }
    if (step === 2) {
      if (!reason.trim()) { setError("请输入你的买入理由"); return; }
      if (reason.trim().length < 5) { setError("理由再详细一点，至少 5 个字"); return; }
      setError("");
      setStep(3);
      return;
    }
    if (step === 3) {
      setStep(4);
      return;
    }
  }

  async function handleSubmit() {
    setSubmitted(true);
    // 创建交易计划
    try {
      await fetch("/api/trade-plans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: selected?.symbol || "AAPL",
          direction: "long",
          reason,
          max_loss_pct: 5,
          position_pct: positionPct,
          planned_holding: "短期(1-5天)",
        }),
      });
      // 创建模拟订单（固定价格，引导模式用）
      await fetch("/api/sandbox/order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: selected?.symbol || "AAPL",
          side: "BUY",
          quantity: 10,
          price: 150,
        }),
      });
    } catch {
      // 网络错误容忍
    }
  }

  if (submitted) {
    return (
      <div className="max-w-xl mx-auto py-12 px-4 text-center space-y-6">
        <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 mx-auto flex items-center justify-center">
          <Check className="w-8 h-8 text-emerald-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-fg">恭喜！你完成了第一笔模拟交易</h2>
          <p className="text-sm text-fg-muted mt-2">
            你选择了 {selected?.name}，以约 ${10 * 150} 的金额买入 10 股。
          </p>
        </div>
        <div className="p-4 rounded-xl bg-bg-panel border border-line text-xs text-fg-muted text-left space-y-2">
          <p>📋 你的交易计划：</p>
          <p>· 理由：{reason}</p>
          <p>· 仓位：不超过 {positionPct}%</p>
          <p>· 最大亏损：5%</p>
          <p>· 计划持有：短期（1-5天）</p>
        </div>
        <div className="flex gap-3 justify-center">
          <Link
            to="/learning"
            className="px-6 py-2.5 rounded-xl bg-emerald-500 text-bg font-bold text-sm
                       hover:bg-emerald-400 transition"
          >
            继续学习
          </Link>
          <Link
            to="/me"
            className="px-6 py-2.5 rounded-xl bg-bg-panel border border-line
                       text-fg font-medium text-sm hover:bg-bg-hover transition"
          >
            查看成长
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto py-8 px-4 space-y-8">
      <div className="space-y-2">
        <p className="text-xs text-fg-muted uppercase tracking-wider">引导式练习</p>
        <h1 className="text-2xl font-bold text-fg">你的第一次模拟交易</h1>
        <p className="text-sm text-fg-muted">系统会一步步引导你，不用紧张。</p>
      </div>

      {/* 步骤指示器 */}
      <div className="flex items-center gap-2">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold
              ${i <= step ? "bg-emerald-500 text-bg" : "bg-bg-subtle text-fg-dim"}`}>
              {i < step ? <Check className="w-3 h-3" /> : i + 1}
            </div>
            <span className={`text-xs ${i <= step ? "text-fg" : "text-fg-dim"}`}>{s}</span>
            {i < STEPS.length - 1 && <div className="w-4 h-px bg-line" />}
          </div>
        ))}
      </div>

      {/* Step 0: 选择公司 */}
      {step === 0 && (
        <div className="space-y-3">
          <p className="text-sm text-fg-muted">先选一家你熟悉或感兴趣的公司：</p>
          {COMPANIES.map((c) => (
            <button
              key={c.symbol}
              onClick={() => handleSelect(c)}
              className="w-full text-left rounded-xl bg-bg-panel border border-line p-4
                         hover:border-emerald-500/30 transition"
            >
              <p className="text-sm font-semibold text-fg">{c.name} ({c.symbol})</p>
              <p className="text-xs text-fg-dim mt-1">{c.desc}</p>
              <p className="text-xs text-fg-dim">{c.product}</p>
            </button>
          ))}
        </div>
      )}

      {/* Step 1: 了解公司 */}
      {step === 1 && selected && (
        <div className="space-y-4">
          <div className="rounded-xl bg-bg-panel border border-line p-5 space-y-3">
            <p className="text-sm font-semibold text-fg">{selected.name} ({selected.symbol})</p>
            <p className="text-xs text-fg-muted leading-relaxed">{selected.desc}</p>
            <div className="flex gap-2 text-xs">
              <span className="px-2 py-1 rounded bg-bg-subtle text-fg-dim">{selected.product}</span>
            </div>
            <div className="p-3 rounded-lg bg-blue-500/5 border border-blue-500/20 text-xs text-fg-muted leading-relaxed">
              💡 提示：买股票就是买公司的一部分。如果你喜欢这家公司的产品，可以把它作为研究的起点。
              但要记住：好公司不一定等于好价格。
            </div>
          </div>
          <button onClick={handleNext} className="w-full py-3 rounded-xl bg-emerald-500 text-bg font-bold text-sm
                                                  hover:bg-emerald-400 transition">
            继续
          </button>
        </div>
      )}

      {/* Step 2: 买入理由 */}
      {step === 2 && (
        <div className="space-y-4">
          <div className="space-y-2">
            <p className="text-sm text-fg">你为什么想买 {selected?.name}？</p>
            <p className="text-xs text-fg-muted">写一句话就够了。比如："我认为 iPhone 销量会继续增长"</p>
            <textarea
              value={reason}
              onChange={(e) => { setReason(e.target.value); setError(""); }}
              placeholder="我认为..."
              rows={2}
              className="w-full bg-bg-input border border-line rounded-lg px-3 py-2
                         text-sm text-fg resize-none focus:outline-none focus:border-emerald-500"
            />
            {error && <p className="text-xs text-rose-400">{error}</p>}
          </div>
          <button onClick={handleNext} className="w-full py-3 rounded-xl bg-emerald-500 text-bg font-bold text-sm
                                                  hover:bg-emerald-400 transition">
            继续
          </button>
        </div>
      )}

      {/* Step 3: 确定仓位 */}
      {step === 3 && (
        <div className="space-y-4">
          <div className="space-y-2">
            <p className="text-sm text-fg">你准备用账户中多少比例的资金买这支股票？</p>
            <p className="text-xs text-fg-muted">建议不超过 10%。新手最重要的是控制风险。</p>
            <div className="grid grid-cols-4 gap-2">
              {[5, 10, 15, 20].map((pct) => (
                <button
                  key={pct}
                  onClick={() => setPositionPct(pct)}
                  className={`py-3 rounded-lg border text-sm font-semibold transition
                    ${positionPct === pct
                      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                      : "bg-bg-subtle border-line text-fg-muted hover:border-emerald-500/20"
                    }`}
                >
                  {pct}%
                </button>
              ))}
            </div>
            {positionPct > 10 && (
              <p className="text-xs text-amber-400">仓位超过 10%，风险较高。建议新手从 5-10% 开始。</p>
            )}
          </div>
          <button onClick={handleNext} className="w-full py-3 rounded-xl bg-emerald-500 text-bg font-bold text-sm
                                                  hover:bg-emerald-400 transition">
            继续
          </button>
        </div>
      )}

      {/* Step 4: 确认下单 */}
      {step === 4 && (
        <div className="space-y-4">
          <div className="rounded-xl bg-bg-panel border border-line p-5 space-y-2 text-sm">
            <p className="font-semibold text-fg">确认你的交易：</p>
            <div className="text-fg-muted text-xs space-y-1">
              <p>公司：{selected?.name} ({selected?.symbol})</p>
              <p>理由：{reason}</p>
              <p>仓位：不超过 {positionPct}%</p>
              <p>最大亏损：5%（超过就止损）</p>
              <p>数量：10 股（引导模式固定数量）</p>
            </div>
          </div>
          <button onClick={handleSubmit} className="w-full py-3 rounded-xl bg-emerald-500 text-bg font-bold text-sm
                                                  hover:bg-emerald-400 transition">
            确认并下单
          </button>
          <button onClick={() => setStep(0)} className="w-full py-2 text-xs text-fg-dim hover:text-fg transition">
            重新选择
          </button>
        </div>
      )}
    </div>
  );
}
