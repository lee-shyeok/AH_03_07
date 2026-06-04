"use client";

import { useRouter } from "next/navigation";
import { UserPlus } from "lucide-react";
import { setMode } from "@/features/auth/mode";

const GREEN = "hsl(142 71% 45%)";
const PURPLE = "#7C5CCF";

type Mode = "general" | "autoimmune";

export default function ModeSelectPage() {
  const router = useRouter();

  function select(mode: Mode) {
    setMode(mode);
    router.replace(mode === "autoimmune" ? "/mode-consent" : "/home");
  }

  const cards: { key: Mode; title: string; lines: string[]; color: string; emoji: string }[] = [
    { key: "autoimmune", title: "자가면역환자", lines: ["활성도 추적", "면역약물 특화 정보"], color: GREEN, emoji: "🟢" },
    { key: "general", title: "일반 환자", lines: ["복약 관리", "일반 의료 정보"], color: PURPLE, emoji: "🟣" },
  ];

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col px-6 pb-10 pt-12">
      <h1 className="mt-6 text-3xl font-extrabold leading-tight">
        어떤 도움이<br />필요하신가요?
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">맞춤 가이드를 제공해드릴게요</p>

      <div className="mt-12 space-y-4">
        {cards.map((c) => (
          <button
            key={c.key}
            onClick={() => select(c.key)}
            className="flex w-full items-center gap-4 rounded-2xl border-2 bg-card p-5 text-left transition-all hover:scale-[1.02] active:scale-[0.98]"
            style={{ borderColor: c.color, boxShadow: `inset 0 0 0 1px ${c.color}40` }}
          >
            <div
              className="flex h-16 w-16 items-center justify-center rounded-full text-4xl shadow-md"
              style={{ background: `radial-gradient(circle at 35% 35%, ${c.color}cc, ${c.color})` }}
            >
              <UserPlus className="h-8 w-8 text-white drop-shadow" />
            </div>
            <div className="flex-1">
              <p className="text-lg font-bold" style={{ color: c.color }}>{c.title}</p>
              {c.lines.map((l) => (
                <p key={l} className="text-sm text-muted-foreground">{l}</p>
              ))}
            </div>
            <span style={{ color: c.color }}>›</span>
          </button>
        ))}
      </div>

      <div className="mt-auto flex justify-center pt-8">
        <button onClick={() => select("general")} className="text-sm text-muted-foreground">
          나중에 선택할게요
        </button>
      </div>
    </main>
  );
}
