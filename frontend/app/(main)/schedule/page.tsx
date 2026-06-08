"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  CalendarDays,
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

const PURPLE = "#7C5CCF";

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

const TYPE_OPTIONS: { value: MedicalScheduleType; label: string }[] = [
  { value: "APPOINTMENT", label: "진료" },
  { value: "BLOOD_TEST", label: "혈액검사" },
  { value: "URINE_TEST", label: "소변검사" },
  { value: "EYE_EXAM", label: "안과검사" },
  { value: "INJECTION", label: "주사" },
];

const REMINDERS = [1, 3, 7];
const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];

function pad(n: number) {
  return String(n).padStart(2, "0");
}
function keyOf(d: Date) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}
function fmtDate(iso: string) {
  const d = new Date(iso);
  return `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())} (${WEEKDAYS[d.getDay()]})`;
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
              <button
                onClick={() => { setMenuOpen(false); onEdit(); }}
                className="w-full px-4 py-2.5 text-left text-sm hover:bg-muted"
              >
                수정
              </button>
              <button
                onClick={() => { setMenuOpen(false); onDelete(); }}
                className="w-full px-4 py-2.5 text-left text-sm text-destructive hover:bg-muted"
              >
                삭제
              </button>
            </div>
          </>
        )}
      </div>
    </Card>
  );
}

const EMPTY_FORM = {
  schedule_type: "APPOINTMENT" as MedicalScheduleType,
  title: "",
  scheduled_date: keyOf(new Date()),
  reminder_days_before: 1,
  note: "",
};

export default function SchedulePage() {
  const router = useRouter();
  const now = new Date();
  const [view, setView] = useState<"calendar" | "list">("calendar");
  const [cursor, setCursor] = useState({ year: now.getFullYear(), month: now.getMonth() });
  const [selected, setSelected] = useState<string | null>(null);
  const [events, setEvents] = useState<MedicalScheduleResponse[]>([]);
  const [refreshKey, setRefreshKey] = useState(0);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    listCareSchedules()
      .then(setEvents)
      .catch(() => setEvents([]));
  }, [refreshKey]);

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
    const to = keyOf(new Date(t.getFullYear(), t.getMonth(), t.getDate() + 7));
    return events
      .filter((e) => {
        const k = keyOf(new Date(e.scheduled_date));
        return k >= from && k <= to;
      })
      .sort((a, b) => a.scheduled_date.localeCompare(b.scheduled_date));
  }, [events]);

  const allSorted = useMemo(
    () => [...events].sort((a, b) => a.scheduled_date.localeCompare(b.scheduled_date)),
    [events]
  );

  const todayKey = keyOf(new Date());
  const listToShow = selected ? byDay.get(selected) ?? [] : upcoming;

  function move(delta: number) {
    setSelected(null);
    setCursor((c) => {
      const d = new Date(c.year, c.month + delta, 1);
      return { year: d.getFullYear(), month: d.getMonth() };
    });
  }

  function openEdit(e: MedicalScheduleResponse) {
    setEditingId(e.id);
    setForm({
      schedule_type: e.schedule_type,
      title: e.title ?? "",
      scheduled_date: e.scheduled_date,
      reminder_days_before: e.reminder_days_before,
      note: e.note ?? "",
    });
    setModalOpen(true);
  }

  async function handleSave() {
    if (!form.title.trim()) return;
    setSaving(true);
    try {
      const body = {
        schedule_type: form.schedule_type,
        title: form.title.trim(),
        scheduled_date: form.scheduled_date,
        reminder_days_before: form.reminder_days_before,
        note: form.note.trim() || null,
      };
      if (editingId !== null) {
        await updateCareSchedule(editingId, body);
      } else {
        await createCareSchedule(body);
      }
      setModalOpen(false);
      setEditingId(null);
      setForm(EMPTY_FORM);
      setRefreshKey((k) => k + 1);
    } catch {
      /* 실패 시 유지 */
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("일정을 삭제할까요?")) return;
    try {
      await deleteCareSchedule(id);
      setRefreshKey((k) => k + 1);
    } catch {
      /* 실패 시 유지 */
    }
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8 pb-28">
      {/* 헤더 */}
      <div className="flex items-center gap-4">
        <button onClick={() => router.back()} aria-label="뒤로가기">
          <ChevronLeft className="h-6 w-6" />
        </button>
        <h1 className="text-2xl font-bold">검사·진료 일정</h1>
      </div>

      {/* 자가면역 배너 */}
      <div
        className="mt-8 flex items-center gap-3 rounded-2xl border p-4"
        style={{ borderColor: PURPLE + "55", background: PURPLE + "12" }}
      >
        <CalendarDays className="h-6 w-6" style={{ color: PURPLE }} />
        <div>
          <p className="font-bold">자가면역 일정 통합 관리</p>
          <p className="text-sm" style={{ color: PURPLE }}>검사·진료·주사를 한 번에</p>
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
              style={on ? { background: PURPLE, color: "#fff" } : { background: PURPLE + "14", color: PURPLE }}
            >
              {v === "calendar" ? "월간" : "리스트"}
            </button>
          );
        })}
      </div>

      {view === "calendar" ? (
        <>
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
                <span key={d} className={i === 0 ? "text-destructive" : i === 6 ? "text-blue-500" : "text-muted-foreground"}>
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
                listToShow.map((e) => <EventCard key={e.id} e={e} onEdit={() => openEdit(e)} onDelete={() => handleDelete(e.id)} />)
              )}
            </div>
          </section>
        </>
      ) : (
        <section className="mt-5">
          <h2 className="text-sm text-muted-foreground">전체 일정</h2>
          <div className="mt-2 space-y-3">
            {allSorted.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">등록된 일정이 없어요.</p>
            ) : (
              allSorted.map((e) => <EventCard key={e.id} e={e} onEdit={() => openEdit(e)} onDelete={() => handleDelete(e.id)} />)
            )}
          </div>
        </section>
      )}

      {/* + 일정 추가 FAB */}
      <div className="pointer-events-none fixed inset-x-0 bottom-20 mx-auto flex max-w-md justify-end px-5">
        <button
          onClick={() => { setEditingId(null); setForm(EMPTY_FORM); setModalOpen(true); }}
          aria-label="일정 추가"
          className="pointer-events-auto flex h-14 w-14 items-center justify-center rounded-full text-white shadow-lg"
          style={{ background: PURPLE }}
        >
          <Plus className="h-6 w-6" />
        </button>
      </div>

      {/* 일정 추가 모달 */}
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
                const on = form.schedule_type === o.value;
                const color = TYPE_META[o.value].color;
                return (
                  <button
                    key={o.value}
                    onClick={() => setForm((f) => ({ ...f, schedule_type: o.value }))}
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
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              maxLength={200}
              placeholder="예: 류마티스내과 진료"
              className="mt-2 w-full rounded-xl border px-3 py-2.5 text-sm"
            />

            <p className="mt-4 text-sm font-semibold">날짜</p>
            <input
              type="date"
              value={form.scheduled_date}
              onChange={(e) => setForm((f) => ({ ...f, scheduled_date: e.target.value }))}
              className="mt-2 w-full rounded-xl border px-3 py-2.5 text-sm"
            />

            <p className="mt-4 text-sm font-semibold">미리 알림</p>
            <div className="mt-2 flex gap-2">
              {REMINDERS.map((d) => {
                const on = form.reminder_days_before === d;
                return (
                  <button
                    key={d}
                    onClick={() => setForm((f) => ({ ...f, reminder_days_before: d }))}
                    className="flex-1 rounded-xl border py-2 text-sm font-medium"
                    style={on ? { borderColor: PURPLE, color: PURPLE, background: PURPLE + "12" } : { borderColor: "#e5e7eb", color: "#6b7280" }}
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
              value={form.note}
              onChange={(e) => setForm((f) => ({ ...f, note: e.target.value }))}
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
                onClick={handleSave}
                disabled={saving || !form.title.trim()}
                className="flex-1 rounded-xl py-3 font-bold text-white disabled:opacity-50"
                style={{ background: PURPLE }}
              >
                {saving ? "저장 중..." : editingId !== null ? "수정" : "저장"}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
