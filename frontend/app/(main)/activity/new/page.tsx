"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
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
      <h1 className="text-2xl font-bold">활성도 기록</h1>
      <p className="mt-1 text-sm text-muted-foreground">오늘 컨디션을 0~10으로 기록하세요</p>

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
