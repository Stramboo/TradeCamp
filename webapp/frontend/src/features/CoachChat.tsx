/**
 * CoachChat.tsx — AI 教练对话组件 (v2.3 Phase 4)
 *
 * 聊天式 UI：消息气泡 + 输入框 + 快捷问题
 */
import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, X } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "coach";
  content: string;
  ts: number;
}

const QUICK_QUESTIONS = [
  "我今天该学什么？",
  "什么是止损？",
  "帮我看看最近的交易",
  "什么是PE？",
];

export function CoachChat({ onClose }: { onClose?: () => void }) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "coach",
      content: "你好！我是你的 AI 交易教练 🤖\n\n我可以帮你：\n• 解释股票术语和概念\n• 分析你的交易记录\n• 解答市场相关问题\n• 推荐学习路径\n\n有什么想聊的吗？",
      ts: Date.now(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (text?: string) => {
    const msg = text || input.trim();
    if (!msg || loading) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: msg,
      ts: Date.now(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/coach/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg }),
      });
      const data = await res.json();

      const coachMsg: Message = {
        id: `coach-${Date.now()}`,
        role: "coach",
        content: data.response,
        ts: data.ts,
      };
      setMessages((prev) => [...prev, coachMsg]);
    } catch (e) {
      const errorMsg: Message = {
        id: `error-${Date.now()}`,
        role: "coach",
        content: "抱歉，我暂时无法回答。请稍后再试。",
        ts: Date.now(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full max-h-[600px] rounded-xl bg-bg-panel border border-line overflow-hidden">
      {/* 头部 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-line bg-bg-subtle">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-emerald-500/10 flex items-center justify-center">
            <Bot className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <p className="text-sm font-semibold text-fg">AI 教练</p>
            <p className="text-[10px] text-fg-dim">随时为你解答</p>
          </div>
        </div>
        {onClose && (
          <button onClick={onClose} className="p-1 rounded hover:bg-bg-hover text-fg-dim">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[300px]">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                msg.role === "coach" ? "bg-emerald-500/10" : "bg-blue-500/10"
              }`}
            >
              {msg.role === "coach" ? (
                <Bot className="w-4 h-4 text-emerald-400" />
              ) : (
                <User className="w-4 h-4 text-blue-400" />
              )}
            </div>
            <div
              className={`max-w-[80%] rounded-xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-line ${
                msg.role === "coach"
                  ? "bg-bg-subtle text-fg"
                  : "bg-emerald-500/10 text-fg"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-emerald-500/10 flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="bg-bg-subtle rounded-xl px-4 py-2.5">
              <div className="flex gap-1">
                <span className="w-2 h-2 rounded-full bg-fg-dim animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 rounded-full bg-fg-dim animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 rounded-full bg-fg-dim animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 快捷问题 */}
      {messages.length <= 2 && (
        <div className="px-4 pb-2">
          <p className="text-[10px] text-fg-dim mb-2">试试这些问题：</p>
          <div className="flex flex-wrap gap-2">
            {QUICK_QUESTIONS.map((q) => (
              <button
                key={q}
                onClick={() => handleSend(q)}
                className="text-xs px-3 py-1.5 rounded-full bg-bg-subtle text-fg-muted hover:bg-bg-hover hover:text-fg transition"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 输入框 */}
      <div className="p-4 border-t border-line">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="输入你的问题..."
            className="flex-1 h-10 px-4 rounded-lg bg-bg-subtle text-sm text-fg placeholder:text-fg-dim focus:outline-none focus:ring-1 focus:ring-emerald-500/50"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            className="w-10 h-10 rounded-lg bg-emerald-500 text-white flex items-center justify-center hover:bg-emerald-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
