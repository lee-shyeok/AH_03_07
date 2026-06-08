"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  FlaskConical,
  Stethoscope,
  Syringe,
  type LucideIcon,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import {
  listCareSchedules,
  type MedicalScheduleResponse,
  type MedicalScheduleType,
} from "@/features/care-schedule/api";

const PURPLE = "#7C5CCF";

// 유형색: 진료(초록) / 검사(보라) / 주사(빨강) — 백신(파랑)은 백엔드 타입 없음
const TYPE_META: Record<
  MedicalScheduleType,
  { label: string; color: string; bg: string; icon: LucideIcon }
> = {
  APPOINTMENT: { label: "진료", color: "#27AE60", bg: "#E3F3E6", icon: Stethoscope },
  BLOOD_TEST: { label: "검사", color: PURPLE, bg: "#EDE7FB", icon: FlaskConical },
  URINE_TEST: { label: "검사", color: PURPLE, bg: "#EDE7FB", icon: FlaskConical },
  EYE_EXAM: { label: "검사", color: PURPLE, bg: "#EDE7FB", icon: FlaskConical },
  INJECTION: { label: "주사", color: "#EF5B5B", bg: "#FDE4E4", icon: Syringe },
};

const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];

function pad(n: number) {
  return String(n).padStart(2, "0");
}
function keyOf(d: Date) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}
function fmtDateTime(iso: string) {
  const d = new Date(iso);
  const wd = WEEKDAYS[d.getDay()];
  const base = `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())} (${wd})`;
  const hasTime = iso.includes("T") && !(d.getHours() === 0 && d.getMinutes() === 0);
  return hasTime ? `${base} · ${pad(d.getHours())}:${pad(d.getMinutes())}` : base;
}

export default function SchedulePage() {
  const router = useRouter();
  const now = new Date();
  const [cursor, setCursor] = useState({ year: now.getFullYear(), month: now.getMonth() });
  const [selected, setSelected] = useState<string | null>(null);
  const [monthEvents, setMonthEvents] = useState<MedicalScheduleResponse[]>([]);
  const [upcoming, setUpcoming] = useState<MedicalScheduleResponse[]>([]);

  // 6주 셀 (이웃달 포함)
  const cells = useMemo(() => {
    const first = new Date(cursor.year, cursor.month, 1);
    const startWeekday = first.getDay();
    const daysInMonth = new Date(cursor.year, cursor.month + 1, 0).getDate();
    const total = Math.ceil((startWeekday + daysInMonth) / 7) * 7;
    return Array.from({ length: total }, (_, i) => {
      const date = new Date(cursor.year, cursor.month, i - startWeekday + 1);
      return { date, inMonth: date.getMonth() === cursor.month };
    });
  }, [cursor]);

  // 보이는 범위 일정 조회
  useEffect(() => {
    if (cells.length === 0) return;
    const from = keyOf(cells[0].date);
    const to = keyOf(cells[cells.length - 1].date);
    listCareSchedules(from, to)
      .then(setMonthEvents)
      .catch(() => setMonthEvents([]));
  }, [cells]);

  // 다가오는 7일
  useEffect(() => {
    const t = new Date();
    const from = keyOf(t);
    const to = keyOf(new Date(t.getFullYear(), t.getMonth(), t.getDate() + 7));
    listCareSchedules(from, to)
      .then((rows) =>
        setUpcoming([...rows].sort((a, b) => a.scheduled_date.localeCompare(b.scheduled_date)))
      )
      .catch(() => setUpcoming([]));
  }, []);

  // 날짜별 이벤트 맵
  const byDay = useMemo(() => {
    const m = new Map<string, MedicalScheduleResponse[]>();
    for (const e of monthEvents) {
      const k = keyOf(new Date(e.scheduled_date));
      if (!m.has(k)) m.set(k, []);
      m.get(k)!.push(e);
    }
    return m;
  }, [monthEvents]);

  const todayKey = keyOf(new Date());
  const selectedEvents = selected ? byDay.get(selected) ?? [] : [];
  const listToShow = selected ? selectedEvents : upcoming;

  function move(delta: number) {
    setSelected(null);
    setCursor((c) => {
      const d = new Date(c.year, c.month + delta, 1);
      return { year: d.getFullYear(), month: d.getMonth() };
    });
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8 pb-28">
      {/* 헤더 */}
      <div className="flex items-center gap-6">
        <button onClick={() => router.back()} aria-label="뒤로가기">
          <ChevronLeft className="h-6 w-6" />
        </button>
        <h1 className="text-2xl font-bold">검사·진료 일정</h1>
      </div>

      {/* 자가면역 배너 */}
      <div
        className="mt-12 flex items-center gap-3 rounded-2xl border p-4"
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
        <div className="flex items-center justify-between">
          <button onClick={() => move(-1)} aria-label="이전 달" className="p-1 text-muted-foreground">
            <ChevronLeft className="h-5 w-5" />
          </button>
          <p className="font-bold">
            {cursor.year}년 {cursor.month + 1}월
          </p>
          <button onClick={() => move(1)} aria-label="다음 달" className="p-1 text-muted-foreground">
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>

        <div className="mt-3 grid grid-cols-7 text-center text-xs">
          {WEEKDAYS.map((d, i) => (
            <span
              key={d}
              className={i === 0 ? "text-destructive" : i === 6 ? "text-blue-500" : "text-muted-foreground"}
            >
              {d}
            </span>
          ))}
        </div>

        <div className="mt-2 grid grid-cols-7 gap-y-1 text-center text-sm">
          {cells.map(({ date, inMonth }, i) => {
            const k = keyOf(date);
            const isToday = k === todayKey;
            const isSelected = k === selected;
            const types = Array.from(new Set((byDay.get(k) ?? []).map((e) => e.schedule_type)));
            return (
              <button key={i} onClick={() => setSelected((s) => (s === k ? null : k))} className="flex flex-col items-center py-1">
                <span
                  className={
                    "flex h-8 w-8 items-center justify-center rounded-full " +
                    (isToday ? "font-bold text-white" : inMonth ? "" : "text-muted-foreground/40")
                  }
                  style={
                    isToday
                      ? { background: PURPLE }
                      : isSelected
                      ? { background: PURPLE + "22", color: PURPLE }
                      : undefined
                  }
                >
                  {date.getDate()}
                </span>
                <span className="mt-0.5 flex h-1.5 items-center gap-0.5">
                  {types.slice(0, 3).map((t) => (
                    <span key={t} className="h-1.5 w-1.5 rounded-full" style={{ background: TYPE_META[t].color }} />
                  ))}
                </span>
              </button>
            );
          })}
        </div>
      </Card>

      {/* 리스트: 선택일 or 다가오는 7일 */}
      <section className="mt-6">
        <div className="flex items-center justify-between">
          <h2 className="text-sm text-muted-foreground">
            {selected
              ? `${Number(selected.slice(5, 7))}월 ${Number(selected.slice(8, 10))}일 일정`
              : "곧 다가올 일정 (7일)"}
          </h2>
          {selected && (
            <button onClick={() => setSelected(null)} className="text-xs text-muted-foreground underline">
              다가오는 일정 보기
            </button>
          )}
        </div>

        <div className="mt-2 space-y-3">
          {listToShow.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              {selected ? "이 날 일정이 없어요." : "다가오는 7일 일정이 없어요."}
            </p>
          ) : (
            listToShow.map((e) => {
              const meta = TYPE_META[e.schedule_type];
              const Icon = meta.icon;
              return (
                <Card key={e.id} className="flex items-center gap-3 p-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl" style={{ background: meta.bg }}>
                    <Icon className="h-6 w-6" style={{ color: meta.color }} />
                  </div>
                  <div className="flex-1">
                    <p className="font-bold">{e.title}</p>
                    <p className="text-xs text-muted-foreground">{fmtDateTime(e.scheduled_date)}</p>
                    {e.note && <p className="text-xs text-muted-foreground">{e.note}</p>}
                  </div>
                  <span className="rounded-md px-2 py-1 text-xs font-bold" style={{ background: meta.bg, color: meta.color }}>
                    {meta.label}
                  </span>
                </Card>
              );
            })
          )}
        </div>
      </section>
    </main>
  );
}
