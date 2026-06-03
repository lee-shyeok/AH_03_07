"use client";

import { useEffect, useRef, useState } from "react";
import { Send } from "lucide-react";
import { createSession, sendMessage } from "@/features/chat/api";
import type { ChatMessage } from "@/features/chat/api";

export default function ChatPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    createSession()
      .then(setSessionId)
      .catch(() => setError("챗봇 세션을 시작하지 못했습니다."));
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || !sessionId || sending) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setSending(true);
    try {
      const reply = await sendMessage(sessionId, text);
      setMessages((prev) => [...prev, reply]);
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
        <h1 className="text-lg font-bold">AI 건강 챗봇</h1>
        <p className="text-xs text-muted-foreground">복약·생활습관 등 건강 질문을 해보세요</p>
      </header>

      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {error && <p className="text-center text-sm text-destructive">{error}</p>}
        {messages.length === 0 && !error && (
          <p className="mt-8 text-center text-sm text-muted-foreground">
            궁금한 점을 입력해보세요 🩺
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={"flex " + (m.role === "user" ? "justify-end" : "justify-start")}
          >
            <div
              className={
                "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm " +
                (m.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-foreground")
              }
            >
              {m.content}
            </div>
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
    </div>
  );
}
