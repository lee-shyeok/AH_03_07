"use client";

import { useState } from "react";
import { Check, Clock } from "lucide-react";
import { Card } from "@/components/ui/card";

interface MedItem {
  id: number;
  name: string;
  type?: string;
  detail: string;
  taken: boolean;
  takenAt?: string;
}
interface Slot {
  time: string;
  items: MedItem[];
}

const INITIAL: Slot[] = [
  {
    time: "오전 9:00",
    items: [
      { id: 1, name: "메토트렉세이트 7.5mg", type: "자가면역", detail: "1정", taken: true, takenAt: "복용 09:05" },
      { id: 2, name: "폴산 5mg", type: "자가면역", detail: "1정", taken: true, takenAt: "복용 09:05" },
    ],
  },
  { time: "오후 13:00", items: [{ id: 3, name: "아세트아미노펜 500mg", detail: "해열·진통 · 1정", taken: false }] },
  { time: "오후 18:00", items: [{ id: 4, name: "아세트아미노펜 500mg", detail: "해열·진통 · 1정", taken: false }] },
];

export default function ChecklistPage() {
  const [slots, setSlots] = useState<Slot[]>(INITIAL);

  const all = slots.flatMap((s) => s.items);
  const total = all.length;
  const done = all.filter((i) => i.taken).length;

  function take(id: number) {
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, "0");
    const mm = String(now.getMinutes()).padStart(2, "0");
    setSlots((prev) =>
      prev.map((s) => ({
        ...s,
        items: s.items.map((it) =>
          it.id === id ? { ...it, taken: true, takenAt: `복용 ${hh}:${mm}` } : it
        ),
      }))
    );
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-8">
      <h1 className="text-2xl font-bold">복약 체크리스트</h1>

      {/* 날짜 + 진행률 */}
      <Card className="mt-5 p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xl font-bold">2026.05.20 (화)</p>
            <p className="mt-0.5 text-sm text-muted-foreground">오늘의 복약 일정</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-muted-foreground">완료</p>
            <p className="text-2xl font-extrabold text-primary">
              {done}<span className="text-base text-muted-foreground">/{total}</span>
            </p>
          </div>
        </div>
        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-muted">
          <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${(done / total) * 100}%` }} />
        </div>
      </Card>

      {/* 시간대별 */}
      <div className="mt-6 space-y-5 pb-6">
        {slots.map((slot) => (
          <div key={slot.time}>
            <p className="flex items-center gap-1.5 text-sm font-semibold text-primary">
              <Clock className="h-4 w-4" /> {slot.time}
            </p>
            <div className="mt-2 space-y-2">
              {slot.items.map((it) => (
                <Card
                  key={it.id}
                  className={"flex items-center gap-3 p-4 " + (it.taken ? "border-primary/20 bg-secondary" : "")}
                >
                  {it.taken ? (
                    <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary">
                      <Check className="h-5 w-5 text-primary-foreground" />
                    </span>
                  ) : (
                    <span className="h-8 w-8 rounded-full border-2 border-muted-foreground/30" />
                  )}
                  <div className="flex-1">
                    <p className={"font-semibold " + (it.taken ? "text-muted-foreground line-through" : "")}>
                      {it.name}
                    </p>
                    <div className="mt-0.5 flex items-center gap-1.5">
                      {it.type && (
                        <span className="rounded bg-[#F0E8FF] px-1.5 py-0.5 text-[11px] font-semibold text-[#7C5CCF]">
                          {it.type}
                        </span>
                      )}
                      <span className="text-xs text-muted-foreground">
                        {it.taken ? `${it.detail} · ${it.takenAt}` : it.detail}
                      </span>
                    </div>
                  </div>
                  {!it.taken && (
                    <button
                      onClick={() => take(it.id)}
                      className="rounded-lg bg-primary px-4 py-2 text-sm font-bold text-primary-foreground"
                    >
                      복용
                    </button>
                  )}
                </Card>
              ))}
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
