"use client";

import { useState } from "react";
import { CalendarDays, FlaskConical, Syringe, Stethoscope } from "lucide-react";
import { Card } from "@/components/ui/card";

const PURPLE = "#7C5CCF";

type EventType = "exam" | "injection" | "visit";
interface ScheduleEvent {
  day: number;
  title: string;
  date: string;
  detail: string;
  type: EventType;
  badge: string;
}

const EVENTS: ScheduleEvent[] = [
  { day: 25, title: "정기 혈액 검사", date: "2026.05.25 (월) · 오전 09:30", detail: "서울대병원 류마티스내과", type: "exam", badge: "검사" },
  { day: 2, title: "메토트렉세이트 주사", date: "2026.06.02 (화) · 매주 반복", detail: "자가 주사 · 알림 ON", type: "injection", badge: "주사" },
  { day: 8, title: "류마티스내과 진료", date: "2026.06.08 (월) · 오후 02:00", detail: "김의사 · 서울대병원", type: "visit", badge: "진료" },
];

const ICONS = { exam: FlaskConical, injection: Syringe, visit: Stethoscope };
const BADGE_BG: Record<EventType, string> = {
  exam: "#EDE7FB",
  injection: "#FDE4E4",
  visit: "#E3F3E6",
};

export default function SchedulePage() {
  const [month] = useState({ year: 2026, m: 5 });
  // 2026-05-01 = 금요일 → 앞 공백 5칸 (일~목)
  const firstWeekday = 5;
  const daysInMonth = 31;
  const today = 20;
  const eventDays = new Set(EVENTS.map((e) => e.day));

  const cells: (number | null)[] = [
    ...Array(firstWeekday).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8">
      <h1 className="text-2xl font-bold">검사·진료 일정</h1>

      {/* 자가면역 배너 */}
      <div
        className="mt-5 flex items-center gap-3 rounded-2xl border p-4"
        style={{ borderColor: PURPLE + "55", background: PURPLE + "12" }}
      >
        <CalendarDays className="h-6 w-6" style={{ color: PURPLE }} />
        <div>
          <p className="font-bold">자가면역 일정 통합 관리</p>
          <p className="text-sm" style={{ color: PURPLE }}>검사·진료·주사를 한 번에</p>
        </div>
      </div>

      {/* 캘린더 */}
      <Card className="mt-5 p-4">
        <p className="text-center font-bold">{month.year}년 {month.m}월</p>
        <div className="mt-3 grid grid-cols-7 text-center text-xs">
          {["일", "월", "화", "수", "목", "금", "토"].map((d, i) => (
            <span key={d} className={i === 0 ? "text-destructive" : i === 6 ? "text-blue-500" : "text-muted-foreground"}>
              {d}
            </span>
          ))}
        </div>
        <div className="mt-2 grid grid-cols-7 gap-y-2 text-center text-sm">
          {cells.map((day, i) => (
            <div key={i} className="flex flex-col items-center">
              {day && (
                <>
                  <span
                    className={
                      "flex h-8 w-8 items-center justify-center rounded-full " +
                      (day === today ? "font-bold text-white" : "")
                    }
                    style={day === today ? { background: PURPLE } : undefined}
                  >
                    {day}
                  </span>
                  {eventDays.has(day) && day !== today && (
                    <span className="mt-0.5 h-1 w-1 rounded-full" style={{ background: PURPLE }} />
                  )}
                </>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* 다가올 일정 */}
      <section className="mt-6">
        <h2 className="text-sm text-muted-foreground">곧 다가올 일정</h2>
        <div className="mt-2 space-y-3">
          {EVENTS.map((e, i) => {
            const Icon = ICONS[e.type];
            return (
              <Card key={i} className="flex items-center gap-3 p-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl" style={{ background: BADGE_BG[e.type] }}>
                  <Icon className="h-6 w-6" style={{ color: e.type === "injection" ? "#E05555" : e.type === "visit" ? "#3A9B57" : PURPLE }} />
                </div>
                <div className="flex-1">
                  <p className="font-bold">{e.title}</p>
                  <p className="text-xs text-muted-foreground">{e.date}</p>
                  <p className="text-xs text-muted-foreground">{e.detail}</p>
                </div>
                <span className="rounded-md px-2 py-1 text-xs font-bold" style={{ background: BADGE_BG[e.type], color: e.type === "injection" ? "#E05555" : e.type === "visit" ? "#3A9B57" : PURPLE }}>
                  {e.badge}
                </span>
              </Card>
            );
          })}
        </div>
      </section>
    </main>
  );
}
