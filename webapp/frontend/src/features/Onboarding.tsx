/**
 * Onboarding.tsx — Liquid Glass 三步引导向导 (v2.4 Phase 9)
 *
 * 欢迎 → 目标选择 → 经验自评 → 个性化起点
 * 保持 `onboarding_completed` localStorage 契约不变
 */

import { useState, useEffect } from "react";
import { ArrowRight, ArrowLeft, TrendingUp, GraduationCap, Gamepad2 } from "lucide-react";

const STORAGE_KEY = "onboarding_completed";

const GOALS = [
  { id: "learn", icon: GraduationCap, title: "系统学习", desc: "从零开始，按阶段学习股票知识" },
  { id: "practice", icon: Gamepad2, title: "模拟练习", desc: "直接上手，用虚拟资金练习交易" },
  { id: "explore", icon: TrendingUp, title: "探索市场", desc: "了解全球市场和优秀公司" },
];

const LEVELS = [
  { id: "beginner", title: "完全新手", desc: "从未接触过股票" },
  { id: "some", title: "略有了解", desc: "知道一些基本概念" },
  { id: "experienced", title: "有经验", desc: "有过真实交易经历" },
];

export function Onboarding({ onDone }: { onDone: () => void }) {
  const [visible, setVisible] = useState(false);
  const [step, setStep] = useState(0);
  const [goal, setGoal] = useState("");
  const [level, setLevel] = useState("");

  useEffect(() => {
    const done = localStorage.getItem(STORAGE_KEY);
    if (done === "1") {
      onDone();
      return;
    }
    const t = setTimeout(() => setVisible(true), 80);
    return () => clearTimeout(t);
  }, []);

  function handleFinish() {
    // 保存偏好到后端（fire-and-forget）
    fetch("/api/prefs/onboarding_goal", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value: goal }),
    }).catch(() => {});
    fetch("/api/prefs/onboarding_level", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value: level }),
    }).catch(() => {});

    localStorage.setItem(STORAGE_KEY, "1");
    setVisible(false);
    setTimeout(onDone, 300);
  }

  return (
    <div className={`fixed inset-0 z-50 flex items-center justify-center transition-all duration-500 ${
      visible ? "opacity-100" : "opacity-0 pointer-events-none"
    }`}>
      {/* 氛围光背景 */}
      <div className="ambient-bg" aria-hidden="true" />
      <div className="absolute inset-0 bg-bg/80" />

      <div className="relative w-full max-w-md px-6">
        {/* 玻璃卡片 */}
        <div className="glass-card specular-edge p-8 space-y-6">
          {/* 进度指示 */}
          <div className="flex justify-center gap-2">
            {[0, 1, 2].map((i) => (
              <div key={i} className={`h-1 rounded-full transition-all duration-300 ${
                i === step ? "w-8 bg-emerald-400" : i < step ? "w-4 bg-emerald-400/40" : "w-4 bg-white/[0.1]"
              }`} />
            ))}
          </div>

          {/* Step 0: 欢迎 */}
          {step === 0 && (
            <div className="text-center space-y-4 animate-[slideUp_0.4s_ease]">
              <div className="w-16 h-16 mx-auto rounded-[18px] bg-gradient-to-br from-emerald-400 to-emerald-600
                              flex items-center justify-center shadow-[0_8px_32px_rgba(16,185,129,0.4)]">
                <TrendingUp className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-fg tracking-tight">欢迎来到 TradeCamp</h1>
              <p className="text-sm text-fg-muted leading-relaxed">
                从零开始学习股票交易<br />
                用虚拟资金安全练习，逐步建立投资能力
              </p>
              <button onClick={() => setStep(1)}
                      className="glass-btn-primary inline-flex items-center gap-2 px-8 py-3 rounded-[14px] text-sm font-bold">
                开始 <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Step 1: 目标选择 */}
          {step === 1 && (
            <div className="space-y-4 animate-[slideUp_0.4s_ease]">
              <div className="text-center">
                <h2 className="text-lg font-bold text-fg">你的目标是？</h2>
                <p className="text-xs text-fg-dim mt-1">我们会为你推荐合适的起点</p>
              </div>
              <div className="space-y-2">
                {GOALS.map((g) => (
                  <button key={g.id} onClick={() => setGoal(g.id)}
                          className={`w-full flex items-center gap-3 p-4 rounded-[14px] text-left transition-all ${
                            goal === g.id
                              ? "bg-emerald-500/15 border border-emerald-400/40"
                              : "glass-light hover:bg-white/[0.08]"
                          }`}>
                    <g.icon className={`w-5 h-5 shrink-0 ${goal === g.id ? "text-emerald-400" : "text-fg-dim"}`} />
                    <div>
                      <p className={`text-sm font-semibold ${goal === g.id ? "text-fg" : "text-fg-muted"}`}>{g.title}</p>
                      <p className="text-xs text-fg-dim">{g.desc}</p>
                    </div>
                  </button>
                ))}
              </div>
              <div className="flex gap-2">
                <button onClick={() => setStep(0)} className="glass-btn px-4 py-2.5 rounded-[12px] text-sm text-fg-muted">
                  <ArrowLeft className="w-4 h-4" />
                </button>
                <button onClick={() => goal && setStep(2)} disabled={!goal}
                        className="glass-btn-primary flex-1 py-2.5 rounded-[12px] text-sm font-bold disabled:opacity-40">
                  下一步
                </button>
              </div>
            </div>
          )}

          {/* Step 2: 经验自评 */}
          {step === 2 && (
            <div className="space-y-4 animate-[slideUp_0.4s_ease]">
              <div className="text-center">
                <h2 className="text-lg font-bold text-fg">你的经验水平？</h2>
                <p className="text-xs text-fg-dim mt-1">帮助我们调整内容难度</p>
              </div>
              <div className="space-y-2">
                {LEVELS.map((l) => (
                  <button key={l.id} onClick={() => setLevel(l.id)}
                          className={`w-full flex items-center gap-3 p-4 rounded-[14px] text-left transition-all ${
                            level === l.id
                              ? "bg-emerald-500/15 border border-emerald-400/40"
                              : "glass-light hover:bg-white/[0.08]"
                          }`}>
                    <div>
                      <p className={`text-sm font-semibold ${level === l.id ? "text-fg" : "text-fg-muted"}`}>{l.title}</p>
                      <p className="text-xs text-fg-dim">{l.desc}</p>
                    </div>
                  </button>
                ))}
              </div>
              <div className="flex gap-2">
                <button onClick={() => setStep(1)} className="glass-btn px-4 py-2.5 rounded-[12px] text-sm text-fg-muted">
                  <ArrowLeft className="w-4 h-4" />
                </button>
                <button onClick={() => level && handleFinish()} disabled={!level}
                        className="glass-btn-primary flex-1 py-2.5 rounded-[12px] text-sm font-bold disabled:opacity-40">
                  开始旅程 🚀
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
