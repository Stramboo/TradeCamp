/**
 * LearningHeatmap.tsx — 学习热力图 (v2.4 Phase 4)
 *
 * GitHub 风格贡献图，近 26 周，玻璃质感
 */
import { useEffect, useState } from "react";

interface HeatmapDay {
  date: string;
  xp: number;
  lessons: number;
  trades: number;
  level: number; // 0-4
}

const LEVEL_COLORS = [
  "bg-white/[0.04]",                    // 0 无活动
  "bg-emerald-500/25",                  // 1
  "bg-emerald-500/45",                  // 2
  "bg-emerald-500/70",                  // 3
  "bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.5)]", // 4
];

export function LearningHeatmap() {
  const [days, setDays] = useState<HeatmapDay[]>([]);

  useEffect(() => {
    fetch("/api/learning/heatmap?days=182")
      .then((r) => r.json())
      .then(setDays)
      .catch(() => {});
  }, []);

  // 构建 26 周 × 7 天的网格
  const dayMap = new Map(days.map((d) => [d.date, d]));
  const weeks: (HeatmapDay | null)[][] = [];
  const today = new Date();

  // 从 25 周前的周一开始
  const start = new Date(today);
  start.setDate(start.getDate() - start.getDay() - 7 * 25 + 1);

  for (let w = 0; w < 26; w++) {
    const week: (HeatmapDay | null)[] = [];
    for (let d = 0; d < 7; d++) {
      const date = new Date(start);
      date.setDate(start.getDate() + w * 7 + d);
      if (date > today) {
        week.push(null);
      } else {
        const key = date.toISOString().slice(0, 10);
        week.push(dayMap.get(key) || { date: key, xp: 0, lessons: 0, trades: 0, level: 0 });
      }
    }
    weeks.push(week);
  }

  const activeDays = days.filter((d) => d.xp > 0).length;

  return (
    <div className="glass-card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-fg-muted uppercase tracking-wider">学习热力图</p>
        <p className="text-[10px] text-fg-dim">近半年活跃 {activeDays} 天</p>
      </div>
      <div className="flex gap-[3px] overflow-x-auto pb-1">
        {weeks.map((week, wi) => (
          <div key={wi} className="flex flex-col gap-[3px]">
            {week.map((day, di) => (
              <div
                key={di}
                title={day ? `${day.date} · ${day.xp} XP · ${day.lessons} 课 · ${day.trades} 笔` : ""}
                className={`w-[11px] h-[11px] rounded-[3px] transition-colors ${
                  day === null ? "bg-transparent" : LEVEL_COLORS[day.level]
                }`}
              />
            ))}
          </div>
        ))}
      </div>
      <div className="flex items-center justify-end gap-1.5 text-[10px] text-fg-dim">
        <span>少</span>
        {LEVEL_COLORS.map((c, i) => (
          <div key={i} className={`w-[10px] h-[10px] rounded-[3px] ${c}`} />
        ))}
        <span>多</span>
      </div>
    </div>
  );
}
