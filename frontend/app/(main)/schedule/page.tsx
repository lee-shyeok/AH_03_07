"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { getMode } from "@/features/auth/mode";
import {
  CalendarDays,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  FlaskConical,
  MoreVertical,
  Plus,
  Stethoscope,
  Syringe,
  X,
  type LucideIcon,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import {
  createCareSchedule,
  deleteCareSchedule,
  listCareSchedules,
  updateCareSchedule,
  type MedicalScheduleResponse,
  type MedicalScheduleType,
} from "@/features/care-schedule/api";
import {
  getLocalCareSchedules, addLocalCareSchedule, updateLocalCareSchedule, deleteLocalCareSchedule,
} from "@/features/schedule/local";

const PURPLE = "#7C5CCF";

const TYPE_META: Record<
  MedicalScheduleType,
  { label: string; color: string; bg: string; icon: LucideIcon }
> = {
  APPOINTMENT: { label: "진료", color: "#27AE60", bg: "#E3F3E6", icon: Stethoscope },
  BLOOD_TEST:  { label: "검사", color: PURPLE,    bg: "#EDE7FB", icon: FlaskConical },
  URINE_TEST:  { label: "검사", color: PURPLE,    bg: "#EDE7FB", icon: FlaskConical },
  EYE_EXAM:    { label: "검사", color: PURPLE,    bg: "#EDE7FB", icon: FlaskConical },
  INJECTION:   { label: "주사", color: "#EF5B5B", bg: "#FDE4E4", icon: Syringe },
};

const TYPE_OPTIONS: { value: MedicalScheduleType; label: string }[] = [
  { value: "APPOINTMENT", label: "진료" },
  { value: "BLOOD_TEST",  label: "혈액검사" },
  { value: "URINE_TEST",  label: "소변검사" },
  { value: "EYE_EXAM",    label: "안과검사" },
  { value: "INJECTION",   label: "주사" },
];

const REMINDERS = [1, 3, 7];

const WEEKDAY = ["일", "월", "화", "수", "목", "금", "토"] as const;

function pad(n: number) { return String(n).padStart(2, "0"); }
function keyOf(d: Date)  { return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; }
function fmtDate(iso: string) {
  const d = new Date(iso);
  return `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())} (${WEEKDAY[d.getDay()]})`;
}

function EventCard({
  e,
  onEdit,
  onDelete,
}: {
  e: MedicalScheduleResponse;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const meta = TYPE_META[e.schedule_type];
  const Icon = meta.icon;
  return (
    <Card className="relative flex items-center gap-3 p-4">
      <div className="flex h-12 w-12 items-center justify-center rounded-xl" style={{ background: meta.bg }}>
        <Icon className="h-6 w-6" style={{ color: meta.color }} />
      </div>
      <div className="flex-1">
        <p className="font-bold">{e.title}</p>
        <p className="text-xs text-muted-foreground">{fmtDate(e.scheduled_date)}</p>
        {e.note && <p className="text-xs text-muted-foreground">{e.note}</p>}
      </div>
      <span className="rounded-md px-2 py-1 text-xs font-bold" style={{ background: meta.bg, color: meta.color }}>
        {meta.label}
      </span>
      <div className="relative">
        <button
          onClick={() => setMenuOpen((v) => !v)}
          aria-label="더보기"
          className="rounded-full p-1 text-muted-foreground hover:bg-muted"
        >
          <MoreVertical className="h-4 w-4" />
        </button>
        {menuOpen && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
            <div className="absolute right-0 top-7 z-20 min-w-[90px] overflow-hidden rounded-xl border bg-background shadow-lg">
              <button onClick={() => { setMenuOpen(false); onEdit(); }} className="w-full px-4 py-2.5 text-left text-sm hover:bg-muted">수정</button>
              <button onClick={() => { setMenuOpen(false); onDelete(); }} className="w-full px-4 py-2.5 text-left text-sm text-destructive hover:bg-muted">삭제</button>
            </div>
          </>
        )}
      </div>
    </Card>
  );
}

export default function SchedulePage() {
  const router = useRouter();
  const now = new Date();
  const [mode, setMode] = useState<"general" | "autoimmune">("general");
  const ACCENT   = mode === "autoimmune" ? PURPLE : "hsl(var(--primary))";
  const ACCENT14 = mode === "autoimmune" ? PURPLE + "14" : "hsl(var(--primary) / 0.1)";
  const ACCENT22 = mode === "autoimmune" ? PURPLE + "22" : "hsl(var(--primary) / 0.13)";
  const ACCENT66 = mode === "autoimmune" ? PURPLE + "66" : "hsl(var(--primary) / 0.4)";
  const ACCENT99 = mode === "autoimmune" ? PURPLE + "99" : "hsl(var(--primary) / 0.6)";
  const ACCENT12 = mode === "autoimmune" ? PURPLE + "12" : "hsl(var(--primary) / 0.07)";

  useEffect(() => { setMode(getMode()); }, []);

  const [view, setView] = useState<"calendar" | "list">("calendar");
  const [cursor, setCursor] = useState({ year: now.getFullYear(), month: now.getMonth() });
  const [selected, setSelected] = useState<string | null>(null);
  const [events, setEvents] = useState<MedicalScheduleResponse[]>([]);
  const [refreshKey] = useState(0);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [careForm, setCareForm] = useState({
    schedule_type: "APPOINTMENT" as MedicalScheduleType,
    title: "",
    scheduled_date: keyOf(new Date()),
    reminder_days_before: 1,
    note: "",
  });
  const [careSaving, setCareSaving] = useState(false);

  const [month, setMonth] = useState({ year: now.getFullYear(), m: now.getMonth() + 1 });
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const [showPicker, setShowPicker] = useState(false);
  const [pickerYear, setPickerYear] = useState(now.getFullYear());
  const pickerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const local = getLocalCareSchedules();
    listCareSchedules()
      .then((data) => {
        const merged = [...local];
        for (const e of data) {
          if (!merged.some((x) => x.id === e.id)) merged.push(e);
        }
        setEvents(merged);
      })
      .catch(() => setEvents(local));
  }, [refreshKey]);

  useEffect(() => {
    if (!showPicker) return;
    function onClickOutside(e: MouseEvent) {
      if (pickerRef.current && !pickerRef.current.contains(e.target as Node)) {
        setShowPicker(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [showPicker]);

  const firstWeekday = new Date(month.year, month.m - 1, 1).getDay();
  const daysInMonth  = new Date(month.year, month.m, 0).getDate();
  const isCurrentMonth = month.year === now.getFullYear() && month.m === now.getMonth() + 1;
  const todayDay = isCurrentMonth ? now.getDate() : -1;

  const cells: (number | null)[] = [
    ...Array.from({ length: firstWeekday }, () => null as null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];
  while (cells.length % 7 !== 0) cells.push(null);

  const monthEvents = events.filter((e) => {
    const d = new Date(e.scheduled_date);
    return d.getFullYear() === month.year && d.getMonth() + 1 === month.m;
  });
  const eventDays = new Set(monthEvents.map((e) => new Date(e.scheduled_date).getDate()));
  const visibleEvents = selectedDay !== null
    ? monthEvents.filter((e) => new Date(e.scheduled_date).getDate() === selectedDay)
    : monthEvents;

  const careCalendarCells = useMemo(() => {
    const first = new Date(cursor.year, cursor.month, 1);
    const startWeekday = first.getDay();
    const daysInMonthHead = new Date(cursor.year, cursor.month + 1, 0).getDate();
    const total = Math.ceil((startWeekday + daysInMonthHead) / 7) * 7;
    return Array.from({ length: total }, (_, i) => {
      const date = new Date(cursor.year, cursor.month, i - startWeekday + 1);
      return { date, inMonth: date.getMonth() === cursor.month };
    });
  }, [cursor]);

  const byDay = useMemo(() => {
    const m = new Map<string, MedicalScheduleResponse[]>();
    for (const e of events) {
      const k = keyOf(new Date(e.scheduled_date));
      if (!m.has(k)) m.set(k, []);
      m.get(k)!.push(e);
    }
    return m;
  }, [events]);

  const upcoming = useMemo(() => {
    const t = new Date();
    const from = keyOf(t);
    const to   = keyOf(new Date(t.getFullYear(), t.getMonth(), t.getDate() + 7));
    return events
      .filter((e) => { const k = keyOf(new Date(e.scheduled_date)); return k >= from && k <= to; })
      .sort((a, b) => a.scheduled_date.localeCompare(b.scheduled_date));
  }, [events]);

  const allSorted = useMemo(
    () => [...events].sort((a, b) => a.scheduled_date.localeCompare(b.scheduled_date)),
    [events]
  );

  const todayKey  = keyOf(new Date());
  const listToShow = selected ? byDay.get(selected) ?? [] : upcoming;

  function move(delta: number) {
    setSelected(null);
    setCursor((c) => {
      const d = new Date(c.year, c.month + delta, 1);
      return { year: d.getFullYear(), month: d.getMonth() };
    });
  }

  function openCareEdit(e: MedicalScheduleResponse) {
    setEditingId(e.id);
    setCareForm({
      schedule_type: e.schedule_type,
      title: e.title ?? "",
      scheduled_date: e.scheduled_date,
      reminder_days_before: e.reminder_days_before,
      note: e.note ?? "",
    });
    setModalOpen(true);
  }

  async function handleCareSave() {
    if (!careForm.title.trim()) return;
    setCareSaving(true);

    const tempId = editingId ?? Date.now();
    const nowISO = new Date().toISOString();
    const localItem: MedicalScheduleResponse = {
      id: tempId,
      schedule_type: careForm.schedule_type,
      title: careForm.title.trim(),
      scheduled_date: careForm.scheduled_date,
      reminder_days_before: careForm.reminder_days_before,
      note: careForm.note.trim() || null,
      created_at: nowISO,
      updated_at: nowISO,
    };

    // 즉시 로컬 저장 + 상태 반영
    if (editingId !== null) {
      updateLocalCareSchedule(editingId, localItem);
      setEvents((prev) => prev.map((e) => e.id === editingId ? localItem : e));
    } else {
      addLocalCareSchedule(localItem);
      setEvents((prev) => [...prev, localItem]);
    }
    setModalOpen(false);
    setEditingId(null);
    setCareForm({ schedule_type: "APPOINTMENT", title: "", scheduled_date: keyOf(new Date()), reminder_days_before: 1, note: "" });
    setCareSaving(false);

    // 백엔드 저장 시도 (실패해도 로컬에는 저장됨)
    try {
      const body = {
        schedule_type: careForm.schedule_type,
        title: careForm.title.trim(),
        scheduled_date: careForm.scheduled_date,
        reminder_days_before: careForm.reminder_days_before,
        note: careForm.note.trim() || null,
      };
      if (editingId !== null) {
        const saved = await updateCareSchedule(editingId, body);
        updateLocalCareSchedule(editingId, saved);
        setEvents((prev) => prev.map((e) => e.id === editingId ? saved : e));
      } else {
        const saved = await createCareSchedule(body);
        deleteLocalCareSchedule(tempId);
        addLocalCareSchedule(saved);
        setEvents((prev) => prev.map((e) => e.id === tempId ? saved : e));
      }
    } catch {
      /* 백엔드 미가동 — 로컬 유지 */
    }
  }

  async function handleCareDelete(id: number) {
    if (!confirm("일정을 삭제할까요?")) return;
    deleteLocalCareSchedule(id);
    setEvents((prev) => prev.filter((e) => e.id !== id));
    try { await deleteCareSchedule(id); } catch { /* 백엔드 미가동 */ }
  }

  function prevMonth() {
    setSelectedDay(null);
    setMonth((p) => p.m === 1 ? { year: p.year - 1, m: 12 } : { ...p, m: p.m - 1 });
  }
  function nextMonth() {
    setSelectedDay(null);
    setMonth((p) => p.m === 12 ? { year: p.year + 1, m: 1 } : { ...p, m: p.m + 1 });
  }
  function selectMonthFromPicker(m: number) {
    setSelectedDay(null);
    setMonth({ year: pickerYear, m });
    setShowPicker(false);
  }
  function openPickerToggle() {
    setPickerYear(month.year);
    setShowPicker((v) => !v);
  }
  function handleDayClick(day: number) {
    setSelectedDay((prev) => prev === day ? null : day);
  }

  function openAdd() {
    setEditingId(null);
    setCareForm({
      schedule_type: "APPOINTMENT",
      title: "",
      scheduled_date: selectedDay !== null
        ? `${month.year}-${pad(month.m)}-${pad(selectedDay)}`
        : keyOf(new Date()),
      reminder_days_before: 1,
      note: "",
    });
    setModalOpen(true);
  }

  const sectionTitle = selectedDay !== null
    ? `${month.m}월 ${selectedDay}일 (${WEEKDAY[new Date(month.year, month.m - 1, selectedDay).getDay()]}) 일정`
    : `${month.year}년 ${month.m}월 일정`;

  return (
    <>
      <main className="mx-auto w-full max-w-md px-5 py-8">
        {/* 헤더 */}
        <div className="mb-5 flex items-center gap-3">
          <button
            onClick={() => router.push("/home")}
            className="flex h-9 w-9 items-center justify-center rounded-full hover:bg-muted text-lg font-semibold"
            aria-label="뒤로가기"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <h1 className="text-2xl font-bold">검사·진료 일정</h1>
        </div>

        {/* 일정 배너 — 모드별 분기 */}
        <div
          className={
            mode === "autoimmune"
              ? "flex items-center gap-3 rounded-2xl border p-4"
              : "flex items-center gap-3 rounded-2xl border p-4 border-primary/30 bg-primary/5"
          }
          style={
            mode === "autoimmune"
              ? { borderColor: PURPLE + "55", background: PURPLE + "12" }
              : undefined
          }
        >
          <CalendarDays className="h-6 w-6" style={{ color: ACCENT }} />
          <div>
            <p className="font-bold">
              {mode === "autoimmune" ? "자가면역 일정 통합 관리" : "검사·진료 일정 관리"}
            </p>
            <p className="text-sm" style={{ color: ACCENT }}>
              {mode === "autoimmune" ? "검사·진료·주사를 한 번에" : "예약·검사 일정을 한눈에 확인하세요"}
            </p>
          </div>
        </div>

        {/* 뷰 토글 */}
        <div className="mt-5 flex gap-2">
          {(["calendar", "list"] as const).map((v) => {
            const on = view === v;
            return (
              <button
                key={v}
                onClick={() => setView(v)}
                className="flex-1 rounded-xl py-2 text-sm font-semibold"
                style={on ? { background: ACCENT, color: "#fff" } : { background: ACCENT14, color: ACCENT }}
              >
                {v === "calendar" ? "월간" : "리스트"}
              </button>
            );
          })}
        </div>

        {view === "calendar" ? (
          /* ── 월간 캘린더 뷰 ── */
          <>
            <Card className="relative mt-5 p-4">
              {/* 월 네비게이션 */}
              <div className="flex items-center justify-between">
                <button onClick={prevMonth} className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-muted" aria-label="이전 달">
                  <ChevronLeft className="h-5 w-5" />
                </button>
                <button onClick={openPickerToggle} className="flex items-center gap-1 rounded-lg px-2 py-1 font-bold hover:bg-muted">
                  {month.year}년 {month.m}월
                  <ChevronDown
                    className="h-4 w-4 transition-transform"
                    style={{ transform: showPicker ? "rotate(180deg)" : "rotate(0deg)", color: ACCENT }}
                  />
                </button>
                <button onClick={nextMonth} className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-muted" aria-label="다음 달">
                  <ChevronRight className="h-5 w-5" />
                </button>
              </div>

              {/* 연/월 피커 */}
              {showPicker && (
                <div ref={pickerRef} className="absolute left-0 right-0 top-14 z-20 mx-4 rounded-2xl border bg-white p-4 shadow-lg">
                  <div className="mb-3 flex items-center justify-between">
                    <button onClick={() => setPickerYear((y) => y - 1)} className="flex h-7 w-7 items-center justify-center rounded-full hover:bg-muted">
                      <ChevronLeft className="h-4 w-4" />
                    </button>
                    <span className="font-bold">{pickerYear}년</span>
                    <button onClick={() => setPickerYear((y) => y + 1)} className="flex h-7 w-7 items-center justify-center rounded-full hover:bg-muted">
                      <ChevronRight className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="grid grid-cols-4 gap-2">
                    {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => {
                      const isSel = pickerYear === month.year && m === month.m;
                      return (
                        <button
                          key={m}
                          onClick={() => selectMonthFromPicker(m)}
                          className="rounded-xl py-2 text-sm font-bold transition-colors"
                          style={isSel ? { background: ACCENT, color: "#fff" } : { color: "#333" }}
                        >
                          {m}월
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* 요일 헤더 */}
              <div className="mt-4 grid grid-cols-7 text-center text-xs">
                {WEEKDAY.map((d, i) => (
                  <span key={d} className={i === 0 ? "text-destructive" : i === 6 ? "text-blue-500" : "text-muted-foreground"}>
                    {d}
                  </span>
                ))}
              </div>

              {/* 날짜 셀 */}
              <div className="mt-2 grid grid-cols-7 gap-y-1 text-center text-sm">
                {cells.map((day, i) => {
                  if (!day) return <div key={i} />;
                  const isToday    = day === todayDay;
                  const isSel      = day === selectedDay;
                  const hasEvent   = eventDays.has(day);
                  let spanStyle: React.CSSProperties = {};
                  let spanClass = "flex h-8 w-8 items-center justify-center rounded-full cursor-pointer transition-colors ";
                  if (isToday)     { spanClass += "font-bold text-white"; spanStyle = { background: ACCENT }; }
                  else if (isSel)  { spanClass += "font-bold"; spanStyle = { background: ACCENT22, color: ACCENT, outline: `2px solid ${ACCENT}` }; }
                  else             { spanClass += "hover:bg-muted/60"; }
                  return (
                    <div key={i} className="flex flex-col items-center" onClick={() => handleDayClick(day)}>
                      <span className={spanClass} style={spanStyle}>{day}</span>
                      {hasEvent && !isToday && <span className="mt-0.5 h-1 w-1 rounded-full" style={{ background: isSel ? ACCENT : ACCENT99 }} />}
                      {hasEvent && isToday  && <span className="mt-0.5 h-1 w-1 rounded-full bg-white opacity-80" />}
                    </div>
                  );
                })}
              </div>
            </Card>

            {/* 일정 목록 */}
            <section className="mt-6">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold text-muted-foreground">{sectionTitle}</h2>
                {selectedDay !== null && (
                  <button onClick={() => setSelectedDay(null)} className="text-xs text-muted-foreground underline underline-offset-2">
                    전체 보기
                  </button>
                )}
              </div>
              <div className="mt-2 space-y-3">
                {visibleEvents.length === 0 && (
                  <p className="py-6 text-center text-sm text-muted-foreground">
                    {selectedDay !== null ? "이 날의 일정이 없습니다." : "이 달의 일정이 없습니다."}
                  </p>
                )}
                {visibleEvents.map((e) => {
                  const meta = TYPE_META[e.schedule_type];
                  const Icon = meta.icon;
                  return (
                    <Card
                      key={e.id}
                      className="flex cursor-pointer items-center gap-3 p-4 transition-colors hover:bg-muted/40 active:bg-muted/60"
                      onClick={() => openCareEdit(e)}
                    >
                      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl" style={{ background: meta.bg }}>
                        <Icon className="h-6 w-6" style={{ color: meta.color }} />
                      </div>
                      <div className="flex-1 overflow-hidden">
                        <p className="truncate font-bold">{e.title}</p>
                        <p className="truncate text-xs text-muted-foreground">{fmtDate(e.scheduled_date)}</p>
                        {e.note && <p className="truncate text-xs text-muted-foreground">{e.note}</p>}
                      </div>
                      <span className="shrink-0 rounded-md px-2 py-1 text-xs font-bold" style={{ background: meta.bg, color: meta.color }}>
                        {meta.label}
                      </span>
                    </Card>
                  );
                })}
              </div>
              <button
                onClick={openAdd}
                className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl border-2 border-dashed py-4 text-sm font-bold transition-colors hover:bg-muted/40"
                style={{ borderColor: ACCENT66, color: ACCENT }}
              >
                <Plus className="h-5 w-5" />
                {selectedDay !== null ? `${month.m}월 ${selectedDay}일 일정 추가` : "일정 추가"}
              </button>
            </section>

            {/* FAB — calendar view */}
            <div className="pointer-events-none fixed inset-x-0 bottom-20 mx-auto flex max-w-md justify-end px-5">
              <button
                onClick={openAdd}
                aria-label="일정 추가"
                className="pointer-events-auto flex h-14 w-14 items-center justify-center rounded-full text-white shadow-lg"
                style={{ background: ACCENT }}
              >
                <Plus className="h-6 w-6" />
              </button>
            </div>
          </>
        ) : (
          /* ── 리스트 뷰 ── */
          <>
            <Card className="mt-5 p-4">
              <div className="flex items-center justify-between">
                <button onClick={() => move(-1)} aria-label="이전 달" className="p-1 text-muted-foreground">
                  <ChevronLeft className="h-5 w-5" />
                </button>
                <p className="font-bold">{cursor.year}년 {cursor.month + 1}월</p>
                <button onClick={() => move(1)} aria-label="다음 달" className="p-1 text-muted-foreground">
                  <ChevronRight className="h-5 w-5" />
                </button>
              </div>
              <div className="mt-3 grid grid-cols-7 text-center text-xs">
                {WEEKDAY.map((d, i) => (
                  <span key={d} className={i === 0 ? "text-destructive" : i === 6 ? "text-blue-500" : "text-muted-foreground"}>{d}</span>
                ))}
              </div>
              <div className="mt-2 grid grid-cols-7 gap-y-1 text-center text-sm">
                {careCalendarCells.map(({ date, inMonth }, i) => {
                  const k         = keyOf(date);
                  const isToday   = k === todayKey;
                  const isSel     = k === selected;
                  const types     = Array.from(new Set((byDay.get(k) ?? []).map((e) => e.schedule_type)));
                  return (
                    <button key={i} onClick={() => setSelected((s) => s === k ? null : k)} className="flex flex-col items-center py-1">
                      <span
                        className={"flex h-8 w-8 items-center justify-center rounded-full " + (isToday ? "font-bold text-white" : inMonth ? "" : "text-muted-foreground/40")}
                        style={isToday ? { background: ACCENT } : isSel ? { background: ACCENT22, color: ACCENT } : undefined}
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

            <section className="mt-6">
              <div className="flex items-center justify-between">
                <h2 className="text-sm text-muted-foreground">
                  {selected ? `${Number(selected.slice(5, 7))}월 ${Number(selected.slice(8, 10))}일 일정` : "곧 다가올 일정 (7일)"}
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
                  listToShow.map((e) => <EventCard key={e.id} e={e} onEdit={() => openCareEdit(e)} onDelete={() => handleCareDelete(e.id)} />)
                )}
              </div>
            </section>

            <section className="mt-5">
              <h2 className="text-sm text-muted-foreground">전체 일정</h2>
              <div className="mt-2 space-y-3">
                {allSorted.length === 0 ? (
                  <p className="py-8 text-center text-sm text-muted-foreground">등록된 일정이 없어요.</p>
                ) : (
                  allSorted.map((e) => <EventCard key={e.id} e={e} onEdit={() => openCareEdit(e)} onDelete={() => handleCareDelete(e.id)} />)
                )}
              </div>
            </section>

            {/* FAB */}
            <div className="pointer-events-none fixed inset-x-0 bottom-20 mx-auto flex max-w-md justify-end px-5">
              <button
                onClick={() => {
                  setEditingId(null);
                  setCareForm({ schedule_type: "APPOINTMENT", title: "", scheduled_date: keyOf(new Date()), reminder_days_before: 1, note: "" });
                  setModalOpen(true);
                }}
                aria-label="일정 추가"
                className="pointer-events-auto flex h-14 w-14 items-center justify-center rounded-full text-white shadow-lg"
                style={{ background: ACCENT }}
              >
                <Plus className="h-6 w-6" />
              </button>
            </div>
          </>
        )}
      </main>

      {/* 일정 추가/수정 모달 */}
      {modalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-5" onClick={() => { setModalOpen(false); setEditingId(null); }}>
          <div className="max-h-[85vh] w-full max-w-md overflow-y-auto rounded-3xl bg-background p-5" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold">{editingId !== null ? "일정 수정" : "일정 추가"}</h2>
              <button onClick={() => { setModalOpen(false); setEditingId(null); }} aria-label="닫기">
                <X className="h-5 w-5 text-muted-foreground" />
              </button>
            </div>

            <p className="mt-4 text-sm font-semibold">유형</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {TYPE_OPTIONS.map((o) => {
                const on = careForm.schedule_type === o.value;
                const color = TYPE_META[o.value].color;
                return (
                  <button
                    key={o.value}
                    onClick={() => setCareForm((f) => ({ ...f, schedule_type: o.value }))}
                    className="rounded-full border px-3 py-1.5 text-sm font-medium"
                    style={on ? { borderColor: color, color, background: color + "12" } : { borderColor: "#e5e7eb", color: "#6b7280" }}
                  >
                    {o.label}
                  </button>
                );
              })}
            </div>

            <p className="mt-4 text-sm font-semibold">제목</p>
            <input
              value={careForm.title}
              onChange={(e) => setCareForm((f) => ({ ...f, title: e.target.value }))}
              maxLength={200}
              placeholder="예: 류마티스내과 진료"
              className="mt-2 w-full rounded-xl border px-3 py-2.5 text-sm"
            />

            <p className="mt-4 text-sm font-semibold">날짜</p>
            <input
              type="date"
              value={careForm.scheduled_date}
              onChange={(e) => setCareForm((f) => ({ ...f, scheduled_date: e.target.value }))}
              className="mt-2 w-full rounded-xl border px-3 py-2.5 text-sm"
            />

            <p className="mt-4 text-sm font-semibold">미리 알림</p>
            <div className="mt-2 flex gap-2">
              {REMINDERS.map((d) => {
                const on = careForm.reminder_days_before === d;
                return (
                  <button
                    key={d}
                    onClick={() => setCareForm((f) => ({ ...f, reminder_days_before: d }))}
                    className="flex-1 rounded-xl border py-2 text-sm font-medium"
                    style={on ? { borderColor: ACCENT, color: ACCENT, background: ACCENT12 } : { borderColor: "#e5e7eb", color: "#6b7280" }}
                  >
                    {d}일 전
                  </button>
                );
              })}
            </div>

            <p className="mt-4 text-sm font-semibold">
              메모 <span className="font-normal text-muted-foreground">(의료기관 등)</span>
            </p>
            <textarea
              value={careForm.note}
              onChange={(e) => setCareForm((f) => ({ ...f, note: e.target.value }))}
              maxLength={500}
              rows={2}
              placeholder="의료기관·메모"
              className="mt-2 w-full rounded-xl border px-3 py-2.5 text-sm"
            />

            <div className="mt-5 flex gap-2">
              <button onClick={() => { setModalOpen(false); setEditingId(null); }} className="flex-1 rounded-xl border py-3 font-bold">
                취소
              </button>
              <button
                onClick={handleCareSave}
                disabled={careSaving || !careForm.title.trim()}
                className="flex-1 rounded-xl py-3 font-bold text-white disabled:opacity-50"
                style={{ background: ACCENT }}
              >
                {careSaving ? "저장 중..." : editingId !== null ? "수정" : "저장"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
