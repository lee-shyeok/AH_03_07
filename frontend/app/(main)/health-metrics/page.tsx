"use client";

import { useState } from "react";
import { Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

type Tab = "bp" | "glucose" | "weight";

const TABS: { key: Tab; label: string }[] = [
  { key: "bp", label: "혈압" },
  { key: "glucose", label: "혈당" },
  { key: "weight", label: "체중" },
];

// mock 데이터
const DATA = {
  bp: {
    latest: "128/82",
    unit: "mmHg",
    status: "정상",
    trend: [120, 124, 119, 138, 130, 133, 128],
    history: [
      { date: "05.20 (화)", value: "128/82", status: "정상" },
      { date: "05.19 (월)", value: "135/88", status: "주의" },
      { date: "05.18 (일)", value: "126/80", status: "정상" },
    ],
  },
  glucose: { latest: "98", unit: "mg/dL", status: "정상", trend: [95, 102, 98, 110, 100, 97, 98], history: [{ date: "05.20 (화)", value: "98", status: "정상" }] },
  weight: { latest: "75.0", unit: "kg", status: "정상", trend: [76, 75.5, 75.2, 75, 74.8, 75, 75], history: [{ date: "05.20 (화)", value: "75.0", status: "정상" }] },
};

function Sparkline({ data }: { data: number[] }) {
  const w = 300, h = 90, pad = 10;
  const min = Math.min(...data), max = Math.max(...data);
  const range = max - min || 1;
  const pts = data.map((v, i) => {
    const x = pad + (i * (w - 2 * pad)) / (data.length - 1);
    const y = h - pad - ((v - min) / range) * (h - 2 * pad);
    return { x, y };
  });
  const path = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full">
      <polyline points={path.replace(/[ML]/g, " ")} fill="none" stroke="hsl(var(--primary))" strokeWidth="2.5" />
      {pts.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r="3.5" fill="hsl(var(--primary))" />
      ))}
    </svg>
  );
}

export default function HealthMetricsPage() {
  const [tab, setTab] = useState<Tab>("bp");
  const [open, setOpen] = useState(false);
  const [val, setVal] = useState("");
  const [extra, setExtra] = useState<Record<Tab, { date: string; value: string; status: string }[]>>({
    bp: [], glucose: [], weight: [],
  });
  const d = DATA[tab];
  const history = [...extra[tab], ...d.history];

  function save() {
    const v = val.trim();
    if (!v) return;
    setExtra((prev) => ({
      ...prev,
      [tab]: [{ date: "오늘", value: v, status: "정상" }, ...prev[tab]],
    }));
    setVal("");
    setOpen(false);
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8 pb-28">
      <h1 className="text-2xl font-bold">건강 수치</h1>

      {/* 안내 배너 */}
      <div className="mt-5 flex items-center gap-3 rounded-2xl border border-primary/30 bg-secondary p-4">
        <Activity className="h-6 w-6 text-primary" />
        <div>
          <p className="font-bold">건강 수치 기록</p>
          <p className="text-sm text-secondary-foreground">혈압·혈당을 꾸준히 기록하세요</p>
        </div>
      </div>

      {/* 탭 */}
      <div className="mt-5 flex gap-2">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={
              "flex-1 rounded-full py-2.5 text-sm font-bold transition-colors " +
              (tab === t.key ? "bg-primary text-primary-foreground" : "border border-border text-foreground")
            }
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* 최근 측정 */}
      <Card className="mt-5 p-5">
        <p className="text-sm text-muted-foreground">최근 측정 · 2026.05.20</p>
        <div className="mt-1 flex items-end justify-between">
          <p className="text-3xl font-extrabold">
            {d.latest} <span className="text-base font-normal text-muted-foreground">{d.unit}</span>
          </p>
          <span className="rounded-md bg-secondary px-2.5 py-1 text-xs font-bold text-primary">{d.status}</span>
        </div>
      </Card>

      {/* 추이 차트 */}
      <Card className="mt-4 p-5">
        <p className="text-sm font-semibold text-muted-foreground">추이 (최근 7일)</p>
        <div className="mt-3">
          <Sparkline data={d.trend} />
        </div>
      </Card>

      {/* 기록 내역 */}
      <h2 className="mt-6 text-sm font-semibold text-muted-foreground">기록 내역</h2>
      <Card className="mt-2 divide-y divide-border">
        {history.map((h, i) => (
          <div key={i} className="flex items-center justify-between px-4 py-3.5">
            <span className="text-sm text-muted-foreground">{h.date}</span>
            <span className="font-bold">{h.value}</span>
            <span
              className={
                "rounded-md px-2 py-0.5 text-xs font-bold " +
                (h.status === "정상" ? "bg-secondary text-primary" : "bg-amber-100 text-amber-700")
              }
            >
              {h.status}
            </span>
          </div>
        ))}
      </Card>

      <div className="fixed inset-x-0 bottom-16 mx-auto max-w-md px-5">
        <Button className="w-full" size="lg" onClick={() => setOpen(true)}>+ 수치 입력</Button>
      </div>

      {/* 수치 입력 모달 */}
      {open && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40" onClick={() => setOpen(false)}>
          <div className="mx-auto w-full max-w-md rounded-t-2xl bg-card p-5" onClick={(e) => e.stopPropagation()}>
            <div className="mx-auto mb-3 h-1 w-10 rounded-full bg-muted-foreground/30" />
            <h2 className="font-bold">
              {TABS.find((t) => t.key === tab)?.label} 입력 <span className="text-sm font-normal text-muted-foreground">({d.unit})</span>
            </h2>
            <input
              autoFocus
              value={val}
              onChange={(e) => setVal(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && save()}
              placeholder={tab === "bp" ? "예: 120/80" : tab === "glucose" ? "예: 98" : "예: 75.0"}
              className="mt-3 w-full rounded-xl border border-border bg-background px-4 py-3 text-center text-lg outline-none focus:border-primary"
            />
            <Button className="mt-4 w-full" size="lg" onClick={save}>저장</Button>
          </div>
        </div>
      )}
    </main>
  );
}
