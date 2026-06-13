"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Send, ThumbsUp, ThumbsDown } from "lucide-react";
import { createSession, sendMessage } from "@/features/chat/api";
import type { ChatMessage } from "@/features/chat/api";


const DISCLAIMER = "본 답변은 정보 제공 목적이며 의료 진단·처방을 대체하지 않습니다. 증상이 심각하면 의료진에게 상담하세요.";

const RED_FLAG_KEYWORDS = ["가슴 통증", "호흡곤란", "의식", "쓰러", "응급", "심정지", "뇌졸중", "119"];

function hasRedFlag(text: string) {
  return RED_FLAG_KEYWORDS.some((k) => text.includes(k));
}

export default function ChatPage() {
  const router = useRouter();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [feedback, setFeedback] = useState<Record<number, "up" | "down">>({});
  const [emergency, setEmergency] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    createSession().then(setSessionId).catch(() => {});
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || sending) return;

    if (hasRedFlag(text)) {
      setEmergency(true);
      return;
    }

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setSending(true);
    try {
      if (sessionId) {
        const reply = await sendMessage(sessionId, text);
        setMessages((prev) => [...prev, reply]);
      } else {
        setMessages((prev) => [...prev, { role: "assistant", content: "서버에 연결할 수 없습니다." }]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "응답을 받지 못했습니다. 잠시 후 다시 시도해주세요." },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-4rem)] w-full max-w-md flex-col">
      <header className="border-b border-border px-5 py-4">
        <div className="flex items-center gap-2">
          <button onClick={() => router.back()} className="flex items-center justify-center rounded-full p-1.5 hover:bg-muted text-lg font-semibold" aria-label="뒤로가기">
            &lt;
          </button>
          <h1 className="text-lg font-bold">AI 건강 챗봇</h1>
        </div>
        <p className="mt-0.5 text-xs text-muted-foreground">복약·생활습관 등 건강 질문을 해보세요</p>
      </header>

      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {messages.length === 0 && (
          <p className="mt-8 text-center text-sm text-muted-foreground">
            궁금한 점을 입력해보세요 🩺
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={"flex flex-col " + (m.role === "user" ? "items-end" : "items-start")}>
            <div
              className={
                "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm " +
                (m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted text-foreground")
              }
            >
              {m.content}
            </div>
            {/* 어시스턴트 메시지 하단: 👍/👎 + 면책 */}
            {m.role === "assistant" && (
              <div className="mt-1 flex items-center gap-2 px-1">
                <button
                  onClick={() => setFeedback((prev) => ({ ...prev, [i]: "up" }))}
                  className={"rounded-full p-1 text-xs transition-colors " + (feedback[i] === "up" ? "text-primary" : "text-muted-foreground hover:text-primary")}
                  aria-label="좋아요"
                >
                  <ThumbsUp className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => setFeedback((prev) => ({ ...prev, [i]: "down" }))}
                  className={"rounded-full p-1 text-xs transition-colors " + (feedback[i] === "down" ? "text-destructive" : "text-muted-foreground hover:text-destructive")}
                  aria-label="싫어요"
                >
                  <ThumbsDown className="h-3.5 w-3.5" />
                </button>
              </div>
            )}
          </div>
        ))}
        {sending && (
          <div className="flex justify-start">
            <div className="rounded-2xl bg-muted px-4 py-2.5 text-sm text-muted-foreground">
              입력 중...
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* 면책 조항 고정 (NFR-SAFE-001) */}
      <p className="border-t border-border px-4 py-2 text-center text-[10px] text-muted-foreground">
        {DISCLAIMER}
      </p>

      <form onSubmit={handleSend} className="flex gap-2 border-t border-border p-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="메시지를 입력하세요"
          className="flex-1 rounded-full border border-input bg-background px-4 py-2.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="flex h-11 w-11 items-center justify-center rounded-full bg-primary text-primary-foreground disabled:opacity-50"
          aria-label="전송"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>

      {/* 응급 상황 모달 (NFR-SAFE-001 Red Flag) */}
      {emergency && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-6">
          <div className="w-full max-w-sm rounded-2xl bg-card p-6 text-center shadow-xl">
            <p className="text-3xl">🚨</p>
            <h2 className="mt-3 text-lg font-bold text-destructive">응급 상황이 의심됩니다</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              즉시 119에 신고하거나 가까운 응급실로 이동하세요.
              AI 챗봇은 응급 상황 대처를 대신할 수 없습니다.
            </p>
            <a
              href="tel:119"
              className="mt-4 block w-full rounded-xl bg-destructive py-3 font-bold text-white"
            >
              119 응급 전화
            </a>
            <button
              onClick={() => setEmergency(false)}
              className="mt-2 w-full rounded-xl border border-border py-3 text-sm font-medium"
            >
              계속 입력하기
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
