/**
 * SandboxEquityCurve.tsx — 沙盒净值曲线 (v2.4 Phase 4)
 *
 * 纯 SVG 折线图，玻璃质感，数据来自后端持久化快照
 */
import { useEffect, useState } from "react";

interface Snapshot {
  ts: number;
  equity: number;
  cash: number;
  market_value: number;
}

export function SandboxEquityCurve({ initialCash = 100000 }: { initialCash?: number }) {
  const [data, setData] = useState<Snapshot[]>([]);

  useEffect(() => {
    fetch("/api/sandbox/equity-curve?limit=200")
      .then((r) => r.json())
      .then(setData)
      .catch(() => {});
  }, []);

  if (data.length < 2) {
    return (
      <div className="glass-card p-5 text-center">
        <p className="text-xs text-fg-dim">净值曲线</p>
        <p className="text-xs text-fg-muted mt-2">完成几笔交易后，这里会显示净值变化</p>
      </div>
    );
  }

  const W = 560;
  const H = 140;
  const PAD = 8;

  const equities = data.map((d) => d.equity);
  const min = Math.min(...equities, initialCash);
  const max = Math.max(...equities, initialCash);
  const span = max - min || 1;

  const points = data.map((d, i) => {
    const x = PAD + (i / (data.length - 1)) * (W - PAD * 2);
    const y = H - PAD - ((d.equity - min) / span) * (H - PAD * 2);
    return `${x},${y}`;
  }).join(" ");

  const lastEquity = equities[equities.length - 1];
  const firstEquity = equities[0];
  const change = lastEquity - firstEquity;
  const changePct = firstEquity > 0 ? (change / firstEquity) * 100 : 0;
  const isUp = change >= 0;
  const lineColor = isUp ? "#34D399" : "#FB7185";

  // 基准线（初始资金）
  const baseY = H - PAD - ((initialCash - min) / span) * (H - PAD * 2);

  return (
    <div className="glass-card p-4 space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-xs text-fg-muted uppercase tracking-wider">净值曲线</p>
        <p className={`text-sm font-bold tabular ${isUp ? "text-emerald-400" : "text-rose-400"}`}>
          {isUp ? "+" : ""}{changePct.toFixed(2)}%
        </p>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
        <defs>
          <linearGradient id="eqFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={lineColor} stopOpacity="0.25" />
            <stop offset="100%" stopColor={lineColor} stopOpacity="0" />
          </linearGradient>
        </defs>
        {/* 基准线 */}
        <line x1={PAD} y1={baseY} x2={W - PAD} y2={baseY}
              stroke="rgba(255,255,255,0.15)" strokeDasharray="4 4" strokeWidth="1" />
        {/* 填充区域 */}
        <polygon points={`${PAD},${H - PAD} ${points} ${W - PAD},${H - PAD}`}
                 fill="url(#eqFill)" />
        {/* 折线 */}
        <polyline points={points} fill="none" stroke={lineColor}
                  strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
        {/* 末端发光点 */}
        <circle cx={W - PAD} cy={H - PAD - ((lastEquity - min) / span) * (H - PAD * 2)}
                r="3.5" fill={lineColor}>
          <animate attributeName="opacity" values="1;0.4;1" dur="2s" repeatCount="indefinite" />
        </circle>
      </svg>
      <div className="flex justify-between text-[10px] text-fg-dim">
        <span>{new Date(data[0].ts).toLocaleDateString()}</span>
        <span className="tabular">${lastEquity.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
      </div>
    </div>
  );
}
