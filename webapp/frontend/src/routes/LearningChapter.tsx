/**
 * LearningChapter.tsx — 课时阅读页（v2.2 8要素结构）
 *
 * 左文右练布局。每节课遵循 8 要素规范：
 *   问题 → 类比 → 核心概念 → 正文 → 互动练习 → 常见误区 → 课后总结
 */

import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Check, Lightbulb, AlertTriangle, BookOpen } from "lucide-react";
import { KLineChart } from "../features/KLineChart";
import { SandboxTradePanel } from "../features/SandboxTradePanel";
import { QuestCard, type QuestData } from "../features/QuestCard";
import { QuizRunner } from "../features/QuizRunner";

type Section = { heading: string; paragraphs: string[] };
type Interactive = { type: string; instructions?: string; question?: string;
  options?: string[]; answer?: number; explanation?: string; link?: string; text?: string;
  scenario?: string; hint?: string } | null;
type Concept = { term: string; definition: string };

type LessonData = {
  id: string; number: number; title: string; summary: string;
  category: string; stage_id: string; question: string; analogy: string;
  concept: Concept; sections: Section[]; interactive: Interactive;
  pitfall: string; xp: number; completed: boolean;
};

export function LearningChapter() {
  const { chapterId } = useParams<{ chapterId: string }>();
  const navigate = useNavigate();
  const [lesson, setLesson] = useState<LessonData | null>(null);
  const [loading, setLoading] = useState(true);
  const [markedDone, setMarkedDone] = useState(false);
  const [quests, setQuests] = useState<QuestData[]>([]);
  const [quizSelected, setQuizSelected] = useState<number | null>(null);
  const [quizResult, setQuizResult] = useState<"correct" | "wrong" | null>(null);
  const [lessonQuiz, setLessonQuiz] = useState<{ question: string; options: string[] }[] | null>(null);
  const [showQuiz, setShowQuiz] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chapterId) return;
    let cancelled = false;
    setLoading(true);
    fetch("/api/learning/chapters")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (!cancelled && d?.chapters) {
          const found = d.chapters.find((c: LessonData) => c.id === chapterId);
          setLesson(found || null);
          if (found?.completed) setMarkedDone(true);
        }
      })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [chapterId]);

  // Fetch quests
  useEffect(() => {
    if (!chapterId) return;
    fetch(`/api/learning/quests?chapter_id=${encodeURIComponent(chapterId)}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { if (d?.quests) setQuests(d.quests); })
      .catch(() => {});
  }, [chapterId, markedDone]);

  // v2.4: 加载课时测验
  useEffect(() => {
    if (!chapterId) return;
    fetch(`/api/learning/quiz/${chapterId}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { if (d?.questions?.length) setLessonQuiz(d.questions); })
      .catch(() => {});
  }, [chapterId]);

  // Scroll-completion
  useEffect(() => {
    if (!scrollRef.current || !chapterId || markedDone) return;
    const el = scrollRef.current;
    const checkScroll = () => {
      const threshold = el.scrollHeight - el.clientHeight - 120;
      if (el.scrollTop >= threshold && !markedDone) {
        setMarkedDone(true);
        fetch("/api/learning/progress", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ chapter_id: chapterId }),
        }).catch(() => {});
      }
    };
    el.addEventListener("scroll", checkScroll, { passive: true });
    return () => el.removeEventListener("scroll", checkScroll);
  }, [chapterId, markedDone]);

  const interactive = lesson?.interactive;

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-fg-muted text-sm">加载中...</div>;
  }
  if (!lesson) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <p className="text-fg-muted text-sm">课时未找到</p>
        <button onClick={() => navigate("/learning")} className="text-xs text-emerald-400">返回学习路径</button>
      </div>
    );
  }

  return (
    <div className="flex gap-0 h-full" style={{ minHeight: "calc(100vh - 4rem - 2rem)" }}>
      {/* === Left: Content === */}
      <div ref={scrollRef} className="flex-1 overflow-auto lg:pr-8">
        <button onClick={() => navigate("/learning")}
                className="inline-flex items-center gap-1.5 text-xs text-fg-muted hover:text-fg mb-6">
          <ArrowLeft className="h-3.5 w-3.5" /> 学习路径
        </button>

        {/* 元信息 */}
        <div className="mb-2 flex items-center gap-3">
          <span className="text-xs uppercase tracking-wider text-fg-dim">
            第 {lesson.number} 课 · {lesson.category}
          </span>
          <span className="text-[10px] text-fg-dim bg-bg-subtle px-2 py-0.5 rounded-full">
            {lesson.xp} XP
          </span>
        </div>
        <h1 className="text-2xl font-semibold text-fg tracking-tight mb-6">{lesson.title}</h1>

        {/* 1. 问题 */}
        <div className="mb-8 p-4 rounded-xl bg-blue-500/5 border border-blue-500/20">
          <p className="text-xs text-blue-300 font-semibold flex items-center gap-1.5 mb-2">
            <Lightbulb className="w-3.5 h-3.5" /> 思考
          </p>
          <p className="text-sm text-fg font-medium">{lesson.question}</p>
        </div>

        {/* 2. 生活类比 */}
        <div className="mb-8">
          <p className="text-xs text-fg-muted uppercase tracking-wider mb-2">生活类比</p>
          <div className="p-4 glass-light rounded-[12px] border border-line text-sm text-fg-muted leading-relaxed">
            {lesson.analogy}
          </div>
        </div>

        {/* 3. 核心概念 */}
        {lesson.concept && (
          <div className="mb-8 p-4 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
            <p className="text-xs text-emerald-400 font-semibold mb-1">
              {lesson.concept.term}
            </p>
            <p className="text-sm text-fg leading-relaxed">{lesson.concept.definition}</p>
          </div>
        )}

        {/* 4. 正文 */}
        <div className="space-y-8 mb-8">
          {lesson.sections.map((sec, i) => (
            <div key={i}>
              <h2 className="text-base font-semibold text-fg mb-3">{sec.heading}</h2>
              {sec.paragraphs.map((p, j) => (
                <p key={j} className="text-sm text-fg-muted leading-relaxed mb-3">{p}</p>
              ))}
            </div>
          ))}
        </div>

        {/* 5. 常见误区 */}
        {lesson.pitfall && (
          <div className="mb-8 p-4 rounded-lg bg-amber-500/5 border border-amber-500/20">
            <p className="text-xs text-amber-400 font-semibold flex items-center gap-1.5 mb-2">
              <AlertTriangle className="w-3.5 h-3.5" /> 常见误区
            </p>
            <p className="text-sm text-fg-muted leading-relaxed">{lesson.pitfall}</p>
          </div>
        )}

        {/* 6. 课后总结 */}
        <div className="mb-8 p-4 glass-light rounded-[12px] border border-line">
          <p className="text-xs text-fg-dim uppercase tracking-wider mb-1">
            <BookOpen className="w-3 h-3 inline mr-1" /> 总结
          </p>
          <p className="text-sm text-fg leading-relaxed">{lesson.summary}</p>
        </div>

        {/* 完成标记 */}
        <div className="pt-6 border-t border-line text-center pb-12">
          {markedDone ? (
            <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400">
              <Check className="h-3.5 w-3.5" /> 已完成（+{lesson.xp} XP）
            </span>
          ) : (
            <span className="text-xs text-fg-dim">继续阅读以标记完成</span>
          )}
        </div>

        {/* 移动端：课时测验直接显示在内容流中 */}
        {lessonQuiz && lessonQuiz.length > 0 && (
          <div className="lg:hidden pb-8">
            <div className="glass-card p-5">
              {!showQuiz ? (
                <button
                  onClick={() => setShowQuiz(true)}
                  className="w-full flex items-center justify-between"
                >
                  <div className="text-left">
                    <p className="text-sm font-semibold text-fg">📝 课时测验</p>
                    <p className="text-xs text-fg-dim mt-0.5">{lessonQuiz.length} 道题 · 每题 10 XP</p>
                  </div>
                  <span className="glass-btn-primary px-4 py-2 rounded-[10px] text-xs font-semibold">
                    开始测验
                  </span>
                </button>
              ) : (
                <QuizRunner
                  title={lesson?.title || "课时测验"}
                  questions={lessonQuiz}
                  submitUrl={`/api/learning/quiz/${chapterId}/submit`}
                  passScore={60}
                  onClose={() => setShowQuiz(false)}
                />
              )}
            </div>
          </div>
        )}
      </div>

      {/* === Right: Interactive (桌面端) === */}
      <div className="hidden lg:block w-[420px] shrink-0 border-l border-line pl-8">
        <h3 className="text-xs uppercase tracking-[0.15em] text-fg-dim mb-4">互动练习</h3>

        <div className="panel-card p-5">
          {interactive?.instructions && (
            <p className="text-sm text-fg-muted mb-4">{interactive.instructions}</p>
          )}

          {/* 测验题 */}
          {interactive?.type === "quiz" && interactive.question && (
            <div className="space-y-3">
              <p className="text-sm text-fg font-medium">{interactive.question}</p>
              <div className="space-y-2">
                {interactive.options?.map((opt, i) => {
                  let btnClass = "bg-bg-subtle border-line text-fg-muted hover:border-emerald-500/30";
                  if (quizSelected === i && quizResult === "correct") {
                    btnClass = "bg-emerald-500/10 border-emerald-500/30 text-emerald-400";
                  } else if (quizSelected === i && quizResult === "wrong") {
                    btnClass = "bg-rose-500/10 border-rose-500/30 text-rose-400";
                  } else if (quizSelected !== null && i === interactive.answer) {
                    btnClass = "bg-emerald-500/5 border-emerald-500/20 text-emerald-400";
                  }
                  return (
                    <button
                      key={i}
                      onClick={() => {
                        if (quizSelected !== null) return;
                        setQuizSelected(i);
                        setQuizResult(i === interactive.answer ? "correct" : "wrong");
                      }}
                      disabled={quizSelected !== null}
                      className={`w-full text-left px-3 py-2.5 rounded-lg border text-xs transition ${btnClass}`}
                    >
                      {opt}
                    </button>
                  );
                })}
              </div>
              {quizResult && (
                <div className={`p-3 rounded-lg text-xs ${
                  quizResult === "correct"
                    ? "bg-emerald-500/5 border border-emerald-500/20 text-emerald-400"
                    : "bg-amber-500/5 border border-amber-500/20 text-amber-400"
                }`}>
                  {interactive.explanation}
                </div>
              )}
            </div>
          )}

          {/* 沙盒交易 */}
          {interactive?.type === "sandbox_trade" && <SandboxTradePanel />}

          {/* 图表查看 */}
          {interactive?.type === "chart_view" && (
            <div>
              <div className="h-80"><KLineChart symbol="NVDA" /></div>
              <p className="text-xs text-fg-dim mt-2 leading-relaxed">
                观察 K 线的颜色（红/绿）、实体大小和影线长度。价格下方的柱状图是成交量。
              </p>
            </div>
          )}

          {/* 指标查看 */}
          {interactive?.type === "indicator_view" && (
            <div>
              <div className="h-72"><KLineChart symbol="NVDA" /></div>
              <p className="text-xs text-fg-dim mt-2 leading-relaxed">
                图表展示了 MA 均线、MACD 和 RSI。试着找到金叉和死叉信号。
              </p>
            </div>
          )}

          {/* 探索链接 */}
          {interactive?.type === "explore_link" && (
            <div className="text-center py-4">
              <a href={interactive.link} className="text-sm text-emerald-400 hover:text-emerald-300">
                {interactive.text}
              </a>
            </div>
          )}

          {/* 风险场景 */}
          {interactive?.type === "risk_scenario" && (
            <div className="space-y-3">
              <p className="text-sm text-fg-muted">{interactive.instructions}</p>
            </div>
          )}

          {/* 模拟 */}
          {interactive?.type === "simulate" && (
            <div className="space-y-3">
              <p className="text-sm text-fg font-medium">{interactive.scenario}</p>
              <p className="text-xs text-fg-dim">{interactive.hint}</p>
            </div>
          )}

          {/* 文本输入 */}
          {interactive?.type === "text_input" && (
            <div className="space-y-3">
              <p className="text-sm text-fg font-medium">{interactive.question}</p>
              <textarea
                placeholder="写下你的想法..."
                rows={3}
                className="w-full bg-bg-input border border-line rounded-lg px-3 py-2
                           text-sm text-fg resize-none focus:outline-none focus:border-emerald-500"
              />
            </div>
          )}

          {/* 风险计算 */}
          {interactive?.type === "risk_calc" && (
            <div className="space-y-3">
              <p className="text-sm text-fg-muted">{interactive.instructions}</p>
              <p className="text-xs text-fg-dim">参考答案：{interactive.answer}</p>
              <p className="text-xs text-fg-dim">{interactive.explanation}</p>
            </div>
          )}

          {/* 日记 */}
          {interactive?.type === "journal" && (
            <div className="space-y-3">
              <p className="text-sm text-fg-muted">{interactive.instructions}</p>
            </div>
          )}

          {/* 无互动 */}
          {!interactive && (
            <div className="text-sm text-fg-muted py-8 text-center">
              <p>此课时以阅读为主。</p>
              <p className="text-xs mt-2 text-fg-dim">完成阅读后继续下一课。</p>
            </div>
          )}
        </div>

        {/* 课时测验 (v2.4, 桌面端) */}
        {lessonQuiz && lessonQuiz.length > 0 && (
          <div className="mt-6 glass-card p-5 hidden lg:block">
            {!showQuiz ? (
              <button
                onClick={() => setShowQuiz(true)}
                className="w-full flex items-center justify-between group"
              >
                <div className="text-left">
                  <p className="text-sm font-semibold text-fg">📝 课时测验</p>
                  <p className="text-xs text-fg-dim mt-0.5">{lessonQuiz.length} 道题 · 每题 10 XP</p>
                </div>
                <span className="glass-btn-primary px-4 py-2 rounded-[10px] text-xs font-semibold">
                  开始测验
                </span>
              </button>
            ) : (
              <QuizRunner
                title={lesson?.title || "课时测验"}
                questions={lessonQuiz}
                submitUrl={`/api/learning/quiz/${chapterId}/submit`}
                passScore={60}
                onClose={() => setShowQuiz(false)}
              />
            )}
          </div>
        )}

        {/* 任务列表 */}
        {quests.length > 0 && (
          <div className="mt-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs uppercase tracking-[0.15em] text-fg-dim">
                任务 ({quests.filter((q) => q.completed).length}/{quests.length})
              </h3>
            </div>
            <div className="space-y-1.5">
              {quests.map((q) => (<QuestCard key={q.id} quest={q} />))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
