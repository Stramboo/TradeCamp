/**
 * Today.tsx — 今日首页
 *
 * 回答唯一问题："我今天应该做什么？"
 *
 * 设计规则：
 * - 首屏只有一个主按钮
 * - 首屏主要卡片不超过三个
 * - 不显示总资产/今日盈亏/BUY SELL 推荐
 */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { GraduationCap, Gamepad2, Globe, MessageCircle } from "lucide-react";
import { CoachChat } from "../features/CoachChat";

interface LearningState {
  level: number;
  xp: number;
  nextXp: number;
  chapterDone: number;
  chapterTotal: number;
  currentChapterId: string;
  currentChapterTitle: string;
  currentLessonTitle: string;
  streak: number;
}

export function Today() {
  const [state, setState] = useState<LearningState | null>(null);
  const [loading, setLoading] = useState(true);
  const [showChat, setShowChat] = useState(false);

  useEffect(() => {
    fetch("/api/learning/chapters")
      .then((r) => r.json())
      .then((data) => {
        const chapters = data?.chapters || [];
        const done = chapters.filter((c: any) => c.completed).length;
        const current = chapters.find((c: any) => !c.completed);
        const stage = current?.category || "股票是什么";
        setState({
          level: 1,
          xp: done * 50,
          nextXp: 100,
          chapterDone: done,
          chapterTotal: chapters.length || 24,
          currentChapterId: current?.id || "ch01",
          currentChapterTitle: stage,
          currentLessonTitle: current?.title || "认识公司与股份",
          streak: 1,
        });
      })
      .catch(() => {
        setState({
          level: 1, xp: 0, nextXp: 100,
          chapterDone: 0, chapterTotal: 24,
          currentChapterId: "ch01",
          currentChapterTitle: "股票是什么",
          currentLessonTitle: "认识公司与股份",
          streak: 1,
        });
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto py-12 space-y-6 animate-pulse">
        <div className="h-8 w-48 bg-bg-subtle rounded" />
        <div className="h-4 w-64 bg-bg-subtle rounded" />
      </div>
    );
  }

  const isNew = state && state.chapterDone === 0;
  const isInProgress = state && state.chapterDone > 0 && state.chapterDone < state.chapterTotal;
  const isDone = state && state.chapterDone >= state.chapterTotal;

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 space-y-8">
      {/* Hero 区 */}
      <div className="space-y-2">
        <p className="text-xs text-fg-muted uppercase tracking-wider">
          今日
        </p>
        <h1 className="text-2xl font-bold text-fg">
          {isNew && "欢迎！让我们开始认识股票"}
          {isInProgress && "继续你的学习之旅"}
          {isDone && "你已经完成了所有课程！"}
        </h1>
        <p className="text-sm text-fg-muted leading-relaxed">
          {isNew && "不用担心，我们从最基础的概念开始。预计需要 10 分钟。"}
          {isInProgress &&
            `你已经完成了 ${state?.chapterDone}/${state?.chapterTotal} 章。今天继续学习 "${state?.currentChapterTitle}"。`
          }
          {isDone && "现在可以探索全球市场，或者进入模拟练习来测试你的判断。"}
        </p>
      </div>

      {/* 主任务卡片 */}
      <div className="rounded-xl bg-bg-panel border border-line p-6 space-y-4
                      shadow-sm">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center shrink-0">
            <GraduationCap className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="space-y-1 flex-1">
            <p className="text-xs text-fg-muted uppercase tracking-wider">今日主任务</p>
            <p className="text-lg font-semibold text-fg">
              {isNew && "第1课：认识公司与股份"}
              {isInProgress && `继续：${state?.currentLessonTitle || state?.currentChapterTitle}`}
              {isDone && "探索全球股票市场"}
            </p>
            <p className="text-xs text-fg-dim">
              {isNew && "股票是什么？公司为什么要上市？"}
              {isInProgress && `${state?.currentChapterTitle} — 预计 5-10 分钟`}
              {isDone && "了解世界各地的交易所和代表公司"}
            </p>
          </div>
        </div>

        {/* 唯一主按钮 */}
        <Link
          to={isDone ? "/explore" : `/learning/${state?.currentChapterId || "ch01"}`}
          className="block w-full text-center py-3 rounded-xl bg-emerald-500
                     text-bg font-bold text-sm hover:bg-emerald-400 transition"
        >
          {isNew && "开始第一课"}
          {isInProgress && "继续学习"}
          {isDone && "探索世界市场"}
        </Link>
      </div>

      {/* 学习进度小条 */}
      {state && state.chapterTotal > 0 && (
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs text-fg-muted">
            <span>学习进度</span>
            <span className="tabular">{state.chapterDone}/{state.chapterTotal} 章 · 连续 {state.streak} 天</span>
          </div>
          <div className="h-1.5 rounded-full bg-bg-subtle overflow-hidden">
            <div
              className="h-full rounded-full bg-emerald-500 transition-all duration-700"
              style={{ width: `${Math.round((state.chapterDone / state.chapterTotal) * 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* 可选探索任务 */}
      <div className="rounded-xl bg-bg-panel border border-line p-5 space-y-3">
        <p className="text-xs text-fg-muted uppercase tracking-wider">可选探索</p>
        <div className="grid grid-cols-2 gap-3">
          <Link
            to="/explore"
            className="flex items-center gap-2 p-3 rounded-lg bg-bg-subtle hover:bg-bg-hover
                       transition text-sm text-fg-muted hover:text-fg"
          >
            <Globe className="w-4 h-4 shrink-0" />
            <span>浏览全球市场</span>
          </Link>
          <Link
            to="/practice"
            className="flex items-center gap-2 p-3 rounded-lg bg-bg-subtle hover:bg-bg-hover
                       transition text-sm text-fg-muted hover:text-fg"
          >
            <Gamepad2 className="w-4 h-4 shrink-0" />
            <span>模拟练习</span>
          </Link>
        </div>
      </div>

      {/* 教练提示 */}
      <div className="p-4 rounded-xl bg-blue-500/5 border border-blue-500/20 space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-xs text-blue-300 font-medium">💡 教练提示</p>
          <button
            onClick={() => setShowChat(!showChat)}
            className="flex items-center gap-1 text-xs text-blue-300 hover:text-blue-200 transition"
          >
            <MessageCircle className="w-3 h-3" />
            {showChat ? "收起" : "向教练提问"}
          </button>
        </div>
        <p className="text-xs text-fg-muted leading-relaxed">
          {isNew && "不用着急，慢慢来。每节课只有 5-10 分钟，学完一章再做练习。"}
          {isInProgress && "记住：理解比速度重要。如果你有疑问，可以随时查看术语表。"}
          {isDone && "你已经掌握基础知识了。试试模拟练习，把学到的用起来。"}
        </p>
        {showChat && (
          <div className="mt-3 pt-3 border-t border-blue-500/20">
            <CoachChat onClose={() => setShowChat(false)} />
          </div>
        )}
      </div>
    </div>
  );
}
