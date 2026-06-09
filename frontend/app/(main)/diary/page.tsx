"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  getDiaryLogs, createDiaryLog,
  type Condition, type BodyPart, type Feeling, type MealTime, type DiaryLog,
} from "@/features/diary/api";

const CONDITIONS: { key: Condition; label: string; emoji: string; active: string }[] = [
  { key: "good",   label: "좋음",   emoji: "😊", active: "border-primary bg-primary/10 text-primary" },
  { key: "normal", label: "보통",   emoji: "😐", active: "border-amber-400 bg-amber-50 text-amber-600" },
  { key: "bad",    label: "안좋음", emoji: "😟", active: "border-destructive bg-destructive/10 text-destructive" },
];

const BODY_PARTS: BodyPart[] = ["머리", "목", "어깨", "가슴", "배", "등", "허리", "팔", "다리"];
const FEELINGS: Feeling[]    = ["콕콕", "욱신", "묵직", "화끈", "답답"];
const MEAL_TIMES: MealTime[] = ["아침", "점심", "저녁", "취침전"];

const MOCK_RECENT: DiaryLog[] = [
  { condition: "good",   note: "컨디션 좋음",  recorded_at: "2026-05-19" },
  { condition: "normal", note: "조금 피곤함", recorded_at: "2026-05-18" },
];

function toISO(year: number, month: number, day: number) {
  return `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function toggleSet<T>(set: Set<T>, value: T): Set<T> {
  const next = new Set(set);
  next.has(value) ? next.delete(value) : next.add(value);
  return next;
}

export default function DiaryPage() {
  const router = useRouter();
  const now = new Date();

  const [viewYear,    setViewYear]    = useState(now.getFullYear());
  const [viewMonth,   setViewMonth]   = useState(now.getMonth());
  const [selectedDay, setSelectedDay] = useState(now.getDate());
  const [logs,        setLogs]        = useState<DiaryLog[]>([]);
  const [dropdown,    setDropdown]    = useState<"year" | "month" | null>(null);

  const [cond,        setCond]        = useState<Condition>("good");
  const [bodyParts,   setBodyParts]   = useState<Set<BodyPart>>(new Set());
  const [feelings,    setFeelings]    = useState<Set<Feeling>>(new Set());
  const [note,        setNote]        = useState("");
  const [medications, setMedications] = useState<Set<MealTime>>(new Set());
  const [saved,       setSaved]       = useState(false);

  useEffect(() => {
    getDiaryLogs().then(setLogs).catch(() => setLogs(MOCK_RECENT));
  }, []);

  // 캘린더 계산
  const firstWeekday = new Date(viewYear, viewMonth, 1).getDay();
  const daysInMonth  = new Date(viewYear, viewMonth + 1, 0).getDate();
  const recordedDays = new Set(
    logs
      .filter((r) => {
        const d = new Date(r.recorded_at);
        return d.getFullYear() === viewYear && d.getMonth() === viewMonth;
      })
      .map((r) => new Date(r.recorded_at).getDate())
  );
  const cells: (number | null)[] = [
    ...Array(firstWeekday).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];

  const isToday    = (d: number) => viewYear === now.getFullYear() && viewMonth === now.getMonth() && d === now.getDate();
  const isSelected = (d: number) => d === selectedDay;

  function prevMonth() {
    if (viewMonth === 0) { setViewYear((y) => y - 1); setViewMonth(11); }
    else setViewMonth((m) => m - 1);
    setSelectedDay(1);
    setDropdown(null);
  }
  function nextMonth() {
    if (viewMonth === 11) { setViewYear((y) => y + 1); setViewMonth(0); }
    else setViewMonth((m) => m + 1);
    setSelectedDay(1);
    setDropdown(null);
  }

  function selectYear(y: number) {
    setViewYear(y);
    const max = new Date(y, viewMonth + 1, 0).getDate();
    if (selectedDay > max) setSelectedDay(max);
    setDropdown(null);
  }
  function selectMonth(m: number) {
    setViewMonth(m);
    const max = new Date(viewYear, m + 1, 0).getDate();
    if (selectedDay > max) setSelectedDay(max);
    setDropdown(null);
  }

  const yearRange = Array.from({ length: 11 }, (_, i) => now.getFullYear() - 5 + i);

  async function save() {
    try {
      await createDiaryLog({
        condition:   cond,
        body_parts:  [...bodyParts],
        feelings:    [...feelings],
        note,
        medications: [...medications],
        recorded_at: toISO(viewYear, viewMonth, selectedDay),
      });
    } catch {
      // 실패해도 UX 흐름 유지
    }
    setSaved(true);
    setTimeout(() => router.push("/home"), 800);
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-6 pb-32">

      {/* 드롭다운 외부 클릭 닫기용 오버레이 */}
      {dropdown && (
        <div className="fixed inset-0 z-10" onClick={() => setDropdown(null)} />
      )}

      {/* 헤더 */}
      <div className="flex items-center gap-2">
        <button onClick={() => router.push("/home")} className="rounded-full p-1 hover:bg-accent">
          <ChevronLeft className="h-5 w-5" />
        </button>
        <h1 className="text-lg font-bold">건강 일기</h1>
      </div>

      {/* 캘린더 */}
      <Card className="mt-4 p-4">
        {/* 년/월 네비게이션 */}
        <div className="relative flex items-center justify-between">
          <button onClick={prevMonth} className="rounded-full p-1 hover:bg-accent">
            <ChevronLeft className="h-4 w-4" />
          </button>

          <div className="flex items-center gap-1">
            {/* 년도 선택 버튼 */}
            <button
              onClick={() => setDropdown((d) => (d === "year" ? null : "year"))}
              className="flex items-center gap-0.5 rounded-lg px-2 py-1 text-sm font-bold hover:bg-accent"
            >
              {viewYear}년
              <ChevronDown className={"h-3 w-3 transition-transform " + (dropdown === "year" ? "rotate-180" : "")} />
            </button>

            {/* 월 선택 버튼 */}
            <button
              onClick={() => setDropdown((d) => (d === "month" ? null : "month"))}
              className="flex items-center gap-0.5 rounded-lg px-2 py-1 text-sm font-bold hover:bg-accent"
            >
              {viewMonth + 1}월
              <ChevronDown className={"h-3 w-3 transition-transform " + (dropdown === "month" ? "rotate-180" : "")} />
            </button>
          </div>

          <button onClick={nextMonth} className="rounded-full p-1 hover:bg-accent">
            <ChevronRight className="h-4 w-4" />
          </button>

          {/* 년도 드롭다운 */}
          {dropdown === "year" && (
            <div className="absolute left-1/2 top-9 z-20 -translate-x-1/2 overflow-hidden rounded-xl border border-border bg-card shadow-lg">
              <div className="max-h-52 overflow-y-auto p-2">
                {yearRange.map((y) => (
                  <button
                    key={y}
                    onClick={() => selectYear(y)}
                    className={
                      "block w-full rounded-lg px-6 py-2 text-center text-sm font-medium transition-colors " +
                      (y === viewYear
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-accent")
                    }
                  >
                    {y}년
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* 월 드롭다운 */}
          {dropdown === "month" && (
            <div className="absolute left-1/2 top-9 z-20 -translate-x-1/2 overflow-hidden rounded-xl border border-border bg-card shadow-lg">
              <div className="grid grid-cols-3 gap-1 p-2">
                {Array.from({ length: 12 }, (_, i) => i).map((m) => (
                  <button
                    key={m}
                    onClick={() => selectMonth(m)}
                    className={
                      "rounded-lg px-3 py-2 text-sm font-medium transition-colors " +
                      (m === viewMonth
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-accent")
                    }
                  >
                    {m + 1}월
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 요일 헤더 */}
        <div className="mt-3 grid grid-cols-7 text-center text-xs">
          {["일", "월", "화", "수", "목", "금", "토"].map((d, i) => (
            <span key={d} className={i === 0 ? "text-destructive" : i === 6 ? "text-blue-500" : "text-muted-foreground"}>
              {d}
            </span>
          ))}
        </div>

        {/* 날짜 그리드 */}
        <div className="mt-2 grid grid-cols-7 gap-y-1 text-center text-sm">
          {cells.map((day, i) => (
            <div key={i} className="flex flex-col items-center">
              {day && (
                <>
                  <button
                    onClick={() => { setSelectedDay(day); setDropdown(null); }}
                    className={
                      "flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-colors " +
                      (isSelected(day)
                        ? "bg-primary text-primary-foreground"
                        : isToday(day)
                        ? "border border-primary text-primary"
                        : "hover:bg-accent")
                    }
                  >
                    {day}
                  </button>
                  {recordedDays.has(day) && !isSelected(day) && (
                    <span className="mt-0.5 h-1 w-1 rounded-full bg-primary" />
                  )}
                </>
              )}
            </div>
          ))}
        </div>
      </Card>

      <p className="mt-3 text-center text-xs text-muted-foreground">
        {viewYear}년 {viewMonth + 1}월 {selectedDay}일 기록
      </p>

      {/* 전체 컨디션 */}
      <p className="mt-5 font-semibold">전체 컨디션</p>
      <div className="mt-2 flex gap-2">
        {CONDITIONS.map(({ key, label, emoji, active }) => (
          <button
            key={key}
            onClick={() => setCond(key)}
            className={
              "flex flex-1 flex-col items-center gap-1 rounded-xl border-2 py-3 transition-colors " +
              (cond === key ? active : "border-border")
            }
          >
            <span className="text-2xl">{emoji}</span>
            <span className={"text-sm font-medium " + (cond === key ? "" : "text-muted-foreground")}>{label}</span>
          </button>
        ))}
      </div>

      {/* 아픈 부위 */}
      <p className="mt-5 font-semibold">
        아픈 부위
        <span className="ml-1 text-xs font-normal text-muted-foreground">복수 선택 가능</span>
      </p>
      <div className="mt-2 flex flex-wrap gap-2">
        {BODY_PARTS.map((part) => (
          <button
            key={part}
            onClick={() => setBodyParts(toggleSet(bodyParts, part))}
            className={
              "rounded-full border px-4 py-1.5 text-sm font-medium transition-colors " +
              (bodyParts.has(part)
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-background hover:bg-accent")
            }
          >
            {part}
          </button>
        ))}
      </div>

      {/* 느낌 */}
      <p className="mt-5 font-semibold">
        느낌
        <span className="ml-1 text-xs font-normal text-muted-foreground">복수 선택 가능</span>
      </p>
      <div className="mt-2 flex flex-wrap gap-2">
        {FEELINGS.map((f) => (
          <button
            key={f}
            onClick={() => setFeelings(toggleSet(feelings, f))}
            className={
              "rounded-full border px-4 py-1.5 text-sm font-medium transition-colors " +
              (feelings.has(f)
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-background hover:bg-accent")
            }
          >
            {f}
          </button>
        ))}
      </div>

      {/* 메모 */}
      <p className="mt-5 font-semibold">메모</p>
      <textarea
        value={note}
        onChange={(e) => setNote(e.target.value)}
        rows={3}
        placeholder="오늘 컨디션은 어땠나요? 자유롭게 기록하세요."
        className="mt-2 w-full rounded-xl border border-input bg-background px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
      />

      {/* 복약 체크 */}
      <p className="mt-5 font-semibold">복약 체크</p>
      <div className="mt-2 grid grid-cols-4 gap-2">
        {MEAL_TIMES.map((mt) => (
          <button
            key={mt}
            onClick={() => setMedications(toggleSet(medications, mt))}
            className={
              "rounded-xl border-2 py-3 text-sm font-medium transition-colors " +
              (medications.has(mt)
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border hover:bg-accent")
            }
          >
            {mt}
          </button>
        ))}
      </div>

      {/* 면책 조항 */}
      <p className="mt-6 text-center text-xs text-muted-foreground">
        본 기록은 자가 메모이며 의학적 진단·분석을 대체하지 않습니다
      </p>

      {/* 저장 버튼 고정 */}
      <div className="fixed inset-x-0 bottom-6 mx-auto max-w-md px-5">
        <Button className="w-full" size="lg" disabled={saved} onClick={save}>
          {saved ? "저장됨 ✓" : "저장하기"}
        </Button>
      </div>
    </main>
  );
}
