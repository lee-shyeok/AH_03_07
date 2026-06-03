"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";

const PURPLE = "#7C5CCF";
const TABS = ["7일", "30일", "90일"];
const BARS = [4, 6, 5, 8, 5, 7, 9];
const DAYS = ["월", "화", "수", "목", "금", "토", "일"];

const METRICS = [
  { name: "통증", value: "5.5", delta: "0.3", dir: "up" },
  { name: "피로", value: "6.0", delta: "0.2", dir: "down" },
  { name: "강직", value: "4.0", delta: "", dir: "flat" },
  { name: "불편도", value: "6.5", delta: "0.5", dir: "up" },
];

export default function ActivityTrendPage() {
  const [tab, setTab] = useState("7일");

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-8">
      <h1 className="text-3xl font-extrabold">활성도 추이</h1>

      {/* 기간 탭 */}
      <div className="mt-5 flex gap-2">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className="rounded-full px-5 py-2 text-sm font-bold"
            style={tab === t ? { background: PURPLE, color: "#fff" } : { border: "1px solid hsl(var(--border))" }}
          >
            {t}
          </button>
        ))}
      </div>

      {/* 평균 */}
      <Card className="mt-5 p-5">
        <p className="text-sm text-muted-foreground">최근 {tab} 평균</p>
        <p className="mt-1 text-4xl font-extrabold" style={{ color: PURPLE }}>
          5.5 <span className="text-base font-normal text-muted-foreground">/ 10</span>
        </p>
        <p className="mt-1 text-sm text-primary">↑ 지난주보다 +0.5점</p>
      </Card>

      {/* 막대 차트 */}
      <Card className="mt-4 p-5">
        <div className="flex h-44 items-end justify-between gap-2">
          {BARS.map((v, i) => (
            <div key={i} className="flex flex-1 flex-col items-center gap-2">
              <div className="w-full rounded-t-md" style={{ height: `${v * 10}%`, background: i % 2 ? PURPLE : PURPLE + "55" }} />
              <span className="text-xs text-muted-foreground">{DAYS[i]}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* 지표별 추이 */}
      <Card className="mt-4 p-5">
        <p className="text-center font-bold">지표별 추이</p>
        <div className="mt-4 space-y-3">
          {METRICS.map((m) => (
            <div key={m.name} className="flex items-center justify-between">
              <span className="text-muted-foreground">{m.name}</span>
              <span className="flex items-center gap-2 font-bold">
                {m.value}
                {m.dir === "up" && <span className="text-destructive">▲ {m.delta}</span>}
                {m.dir === "down" && <span className="text-primary">▼ {m.delta}</span>}
                {m.dir === "flat" && <span className="text-muted-foreground">—</span>}
              </span>
            </div>
          ))}
        </div>
      </Card>
      <div className="pb-6" />
    </main>
  );
}
