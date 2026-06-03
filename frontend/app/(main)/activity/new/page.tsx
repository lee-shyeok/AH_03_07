"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Calendar, ArrowLeft, ArrowRight } from "lucide-react";
import { Card } from "@/components/ui/card";

const PURPLE = "#7C5CCF";
const METRICS = [
  { key: "pain", label: "통증" },
  { key: "fatigue", label: "피로" },
  { key: "stiffness", label: "강직" },
  { key: "discomfort", label: "불편도" },
];

export default function ActivityNewPage() {
  const router = useRouter();
  const [scores, setScores] = useState<Record<string, number>>({
    pain: 5, fatigue: 6, stiffness: 4, discomfort: 7,
  });

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8 pb-28">
      <h1 className="text-3xl font-extrabold leading-tight">오늘 컨디션은<br />어떠셨나요?</h1>

      {/* 날짜 네비 */}
      <div className="mt-4 flex items-center justify-center gap-3 text-muted-foreground">
        <button aria-label="이전"><ArrowLeft className="h-5 w-5" /></button>
        <span className="flex items-center gap-1.5 font-bold text-foreground">
          <Calendar className="h-4 w-4" /> 2024.05.17
        </span>
        <button aria-label="다음"><ArrowRight className="h-5 w-5" /></button>
      </div>

      <div className="mt-6 space-y-4">
        {METRICS.map((m) => (
          <Card key={m.key} className="p-4">
            <div className="flex items-center justify-between">
              <span className="font-semibold">{m.label}</span>
              <span className="text-xl font-extrabold" style={{ color: PURPLE }}>{scores[m.key]}</span>
            </div>
            <input
              type="range"
              min={0}
              max={10}
              value={scores[m.key]}
              onChange={(e) => setScores((s) => ({ ...s, [m.key]: Number(e.target.value) }))}
              className="mt-3 w-full"
              style={{ accentColor: PURPLE }}
            />
            <div className="mt-1 flex justify-between text-xs text-muted-foreground">
              <span>좋음 0</span>
              <span>나쁨 10</span>
            </div>
          </Card>
        ))}
      </div>

      <div className="fixed inset-x-0 bottom-16 mx-auto max-w-md px-5">
        <button
          onClick={() => router.replace("/home")}
          className="w-full rounded-xl py-3.5 text-base font-bold text-white"
          style={{ background: PURPLE }}
        >
          저장하기
        </button>
      </div>
    </main>
  );
}
