/**
 * Me.tsx — 我的成长
 *
 * 展示学习等级、课程进度、知识图谱、成就、复盘记录。
 */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { LearningHeatmap } from "../features/LearningHeatmap";
import { SandboxEquityCurve } from "../features/SandboxEquityCurve";
import { Award, BookOpen, TrendingUp } from "lucide-react";

interface Profile {
  level: number;
  xp: number;
  nextLevelXp: number;
  chapterDone: number;
  chapterTotal: number;
  streak: number;
  questsCompleted: number;
  questsTotal: number;
  achievements: { id: string; name: string; desc: string; unlocked: boolean }[];
}

const LEVEL_NAMES = ["", "学徒", "见习", "初级", "中级", "高级", "专家", "大师"];

export function Me() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 并行加载 dashboard + 真实成就
    Promise.all([
      fetch("/api/learning/progress/dashboard").then((r) => r.json()).catch(() => null),
      fetch("/api/achievements").then((r) => r.json()).catch(() => []),
    ])
      .then(([data, achievements]) => {
        setProfile({
          level: data?.level_num || 1,
          xp: data?.total_xp || 0,
          nextLevelXp: data?.next_level_xp || 100,
          chapterDone: data?.chapters_completed || 0,
          chapterTotal: data?.chapters_total || 24,
          streak: data?.streak_days || 0,
          questsCompleted: data?.quests_completed || 0,
          questsTotal: data?.quests_total || 16,
          achievements: (achievements || []).map((a: any) => ({
            id: a.key, name: a.name, desc: a.desc, unlocked: a.unlocked,
          })),
        });
      })
      .catch(() => {
        setProfile({
          level: 1, xp: 0, nextLevelXp: 100,
          chapterDone: 0, chapterTotal: 24,
          streak: 0, questsCompleted: 0, questsTotal: 16,
          achievements: [],
        });
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto py-12 space-y-6 animate-pulse">
        <div className="h-8 w-48 bg-bg-subtle rounded" />
      </div>
    );
  }

  const p = profile!;
  const levelName = LEVEL_NAMES[p.level] || "学徒";
  const xpPct = Math.round((p.xp / p.nextLevelXp) * 100);

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 space-y-8">
      <div className="space-y-2">
        <p className="text-xs text-fg-muted uppercase tracking-wider">我的成长</p>
        <h1 className="text-2xl font-bold text-fg">你的学习之旅</h1>
      </div>

      {/* 等级卡片 */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 flex items-center justify-center
                          text-2xl font-black text-emerald-400">
            {p.level}
          </div>
          <div className="flex-1">
            <p className="text-lg font-bold text-fg">{levelName}</p>
            <p className="text-xs text-fg-muted">连续学习 {p.streak} 天</p>
          </div>
        </div>
        {/* XP 进度条 */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-fg-muted">
            <span>经验值</span>
            <span className="tabular">{p.xp} / {p.nextLevelXp}</span>
          </div>
          <div className="h-2 rounded-full bg-bg-subtle overflow-hidden">
            <div
              className="h-full rounded-full bg-emerald-500 transition-all"
              style={{ width: `${Math.min(xpPct, 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* 统计 */}
      <div className="grid grid-cols-3 gap-3">
        <Link to="/learning" className="glass-card p-4
                                        hover:border-emerald-500/30 transition text-center">
          <BookOpen className="w-5 h-5 text-emerald-400 mx-auto mb-1" />
          <p className="text-lg font-bold text-fg tabular">{p.chapterDone}/{p.chapterTotal}</p>
          <p className="text-xs text-fg-muted">已学章节</p>
        </Link>
        <div className="glass-card p-4 text-center">
          <Award className="w-5 h-5 text-amber-400 mx-auto mb-1" />
          <p className="text-lg font-bold text-fg tabular">{p.questsCompleted}/{p.questsTotal}</p>
          <p className="text-xs text-fg-muted">任务完成</p>
        </div>
        <Link to="/learning/dashboard" className="glass-card p-4
                                               hover:border-emerald-500/30 transition text-center">
          <TrendingUp className="w-5 h-5 text-blue-400 mx-auto mb-1" />
          <p className="text-lg font-bold text-fg tabular">{p.streak} 天</p>
          <p className="text-xs text-fg-muted">连续学习</p>
        </Link>
      </div>

      {/* 数据可视化：热力图 + 净值曲线 */}
      <LearningHeatmap />
      <SandboxEquityCurve />

      {/* 成就 */}
      {p.achievements.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs text-fg-muted uppercase tracking-wider">成就徽章</p>
          <div className="grid grid-cols-2 gap-2">
            {p.achievements.map((a) => (
              <div
                key={a.id}
                className={`glass-light rounded-[14px] p-3 text-xs transition ${
                  a.unlocked
                    ? "border-amber-400/30 shadow-[0_0_16px_rgba(251,191,36,0.1)]"
                    : "opacity-50"
                }`}
              >
                <p className={`font-semibold ${a.unlocked ? "text-amber-400" : "text-fg-dim"}`}>
                  {a.unlocked ? "⭐" : "🔒"} {a.name}
                </p>
                <p className="text-fg-dim mt-0.5">{a.desc}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 快捷入口 */}
      <div className="space-y-3">
        <Link
          to="/learning/dashboard"
          className="block glass-card p-4
                     hover:border-emerald-500/30 transition text-sm text-fg"
        >
          📊 查看详细学习进度 →
        </Link>
        <Link
          to="/journal"
          className="block glass-card p-4
                     hover:border-emerald-500/30 transition text-sm text-fg"
        >
          📝 查看交易复盘记录 →
        </Link>
      </div>
    </div>
  );
}
