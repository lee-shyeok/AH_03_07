"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { NotebookPen, Smile, Meh, Frown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

type Condition = "good" | "normal" | "bad";

const CONDITIONS: { key: Condition; label: string; icon: typeof Smile }[] = [
  { key: "good", label: "좋음", icon: Smile },
  { key: "normal", label: "보통", icon: Meh },
  { key: "bad", label: "나쁨", icon: Frown },
];

const RECENT = [
  { date: "05.19 (월)", cond: "good" as Condition, label: "컨디션 좋음" },
  { date: "05.18 (일)", cond: "normal" as Condition, label: "조금 피곤함" },
];

export default function DiaryPage() {
  const router = useRouter();
  const [cond, setCond] = useState<Condition>("good");
  const [note, setNote] = useState("");
  const [saved, setSaved] = useState(false);

  function save() {
    setSaved(true);
    setTimeout(() => router.back(), 800);
  }

  const firstWeekday = 5; // 2026-05-01 금
  const daysInMonth = 31;
  const today = 20;
  const recordedDays = new Set([11, 15, 18, 19]);
  const cells: (number | null)[] = [
    ...Array(firstWeekday).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];

  function condColor(c: Condition) {
    return c === "good" ? "text-primary" : c === "normal" ? "text-amber-500" : "text-destructive";
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8 pb-28">
      <h1 className="text-2xl font-bold">건강 일기</h1>

      {/* 안내 배너 */}
      <div className="mt-5 flex items-center gap-3 rounded-2xl border border-primary/30 bg-secondary p-4">
        <NotebookPen className="h-6 w-6 text-primary" />
        <div>
          <p className="font-bold">오늘의 건강 일기</p>
          <p className="text-sm text-secondary-foreground">매일의 컨디션을 기록하세요</p>
        </div>
      </div>

      {/* 캘린더 */}
      <Card className="mt-5 p-4">
        <p className="text-center font-bold">2026년 5월</p>
        <div className="mt-3 grid grid-cols-7 text-center text-xs">
          {["일", "월", "화", "수", "목", "금", "토"].map((d, i) => (
            <span key={d} className={i === 0 ? "text-destructive" : i === 6 ? "text-blue-500" : "text-muted-foreground"}>{d}</span>
          ))}
        </div>
        <div className="mt-2 grid grid-cols-7 gap-y-2 text-center text-sm">
          {cells.map((day, i) => (
            <div key={i} className="flex flex-col items-center">
              {day && (
                <>
                  <span className={"flex h-8 w-8 items-center justify-center rounded-full " + (day === today ? "bg-primary font-bold text-primary-foreground" : "")}>
                    {day}
                  </span>
                  {recordedDays.has(day) && day !== today && <span className="mt-0.5 h-1 w-1 rounded-full bg-primary" />}
                </>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* 오늘 컨디션 */}
      <p className="mt-6 text-sm text-muted-foreground">오늘 컨디션</p>
      <div className="mt-2 flex gap-2">
        {CONDITIONS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setCond(key)}
            className={"flex flex-1 flex-col items-center gap-1 rounded-xl border-2 py-3 " + (cond === key ? "border-primary bg-secondary" : "border-border")}
          >
            <Icon className={"h-7 w-7 " + (cond === key ? condColor(key) : "text-muted-foreground")} />
            <span className={"text-sm font-medium " + (cond === key ? "" : "text-muted-foreground")}>{label}</span>
          </button>
        ))}
      </div>

      {/* 오늘의 기록 */}
      <p className="mt-6 text-sm text-muted-foreground">오늘의 기록</p>
      <textarea
        value={note}
        onChange={(e) => setNote(e.target.value)}
        rows={3}
        placeholder="오늘 컨디션은 어땠나요?"
        className="mt-2 w-full rounded-xl border border-input bg-background px-4 py-3 text-sm"
      />

      {/* 최근 일기 */}
      <p className="mt-6 text-sm text-muted-foreground">최근 일기</p>
      <Card className="mt-2 divide-y divide-border">
        {RECENT.map((r, i) => {
          const Icon = CONDITIONS.find((c) => c.key === r.cond)!.icon;
          return (
            <div key={i} className="flex items-center gap-3 px-4 py-3.5">
              <Icon className={"h-6 w-6 " + condColor(r.cond)} />
              <span className="text-sm text-muted-foreground">{r.date}</span>
              <span className="ml-auto text-sm font-medium">{r.label}</span>
            </div>
          );
        })}
      </Card>

      <div className="fixed inset-x-0 bottom-16 mx-auto max-w-md px-5">
        <Button className="w-full" size="lg" disabled={saved} onClick={save}>{saved ? "저장됨 ✓" : "저장하기"}</Button>
      </div>
    </main>
  );
}
