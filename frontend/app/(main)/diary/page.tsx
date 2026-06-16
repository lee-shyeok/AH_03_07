"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight, ChevronDown, Plus, Trash2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { getDiaryLogs, deleteDiaryLog, type DiaryLog } from "@/features/diary/api";

const CONDITION_DISPLAY: Record<string, { emoji: string; label: string; color: string }> = {
  good:   { emoji: "😊", label: "좋음",   color: "text-primary" },
  normal: { emoji: "😐", label: "보통",   color: "text-amber-500" },
  bad:    { emoji: "😟", label: "안좋음", color: "text-destructive" },
  GOOD:   { emoji: "😊", label: "좋음",   color: "text-primary" },
  NORMAL: { emoji: "😐", label: "보통",   color: "text-amber-500" },
  BAD:    { emoji: "😟", label: "안좋음", color: "text-destructive" },
};

type FilterRange = "1w" | "1m" | "3m" | "all";

const FILTER_OPTIONS: { label: string; value: FilterRange }[] = [
  { label: "1주일", value: "1w" },
  { label: "1개월", value: "1m" },
  { label: "3개월", value: "3m" },
  { label: "전체",  value: "all" },
];

function getDateStr(log: DiaryLog) {
  return log.log_date ?? log.recorded_at ?? "";
}

function getMonthKey(dateStr: string) {
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return "날짜 없음";
  return `${d.getFullYear()}년 ${d.getMonth() + 1}월`;
}

function formatDay(dateStr: string) {
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return "-";
  return `${d.getMonth() + 1}월 ${d.getDate()}일`;
}

function filterByRange(logs: DiaryLog[], range: FilterRange): DiaryLog[] {
  if (range === "all") return logs;
  const now = new Date();
  const cutoff = new Date(now);
  if (range === "1w") cutoff.setDate(now.getDate() - 7);
  else if (range === "1m") cutoff.setMonth(now.getMonth() - 1);
  else if (range === "3m") cutoff.setMonth(now.getMonth() - 3);
  return logs.filter((log) => {
    const ds = getDateStr(log);
    return ds ? new Date(ds) >= cutoff : false;
  });
}

export default function DiaryPage() {
  const router = useRouter();
  const [logs, setLogs] = useState<DiaryLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FilterRange>("all");
  const [openMonths, setOpenMonths] = useState<Set<string>>(new Set());
  const [deletingId, setDeletingId] = useState<string | number | null>(null);

  useEffect(() => {
    getDiaryLogs()
      .then((data) => {
        const sorted = [...data].sort((a, b) => getDateStr(b).localeCompare(getDateStr(a)));
        setLogs(sorted);
        // 초기에 모든 월 펼침
        const keys = new Set(sorted.map((l) => getMonthKey(getDateStr(l))));
        setOpenMonths(keys);
      })
      .catch(() => setLogs([]))
      .finally(() => setLoading(false));
  }, []);

  const filtered = filterByRange(logs, filter);

  // 년/월 기준 그룹핑
  const grouped: { monthKey: string; items: DiaryLog[] }[] = [];
  for (const log of filtered) {
    const key = getMonthKey(getDateStr(log));
    const last = grouped[grouped.length - 1];
    if (last && last.monthKey === key) {
      last.items.push(log);
    } else {
      grouped.push({ monthKey: key, items: [log] });
    }
  }

  function toggleMonth(key: string) {
    setOpenMonths((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  }

  async function handleDelete(e: React.MouseEvent, log: DiaryLog) {
    e.stopPropagation();
    if (!log.id) return;
    if (!confirm("이 기록을 삭제할까요?")) return;
    setDeletingId(log.id);
    try {
      await deleteDiaryLog(log.id);
      setLogs((prev) => prev.filter((l) => l.id !== log.id));
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-6 pb-32">
      <div className="flex items-center gap-2">
        <button onClick={() => router.push("/home")} className="rounded-full p-1 hover:bg-accent">
          <ChevronLeft className="h-5 w-5" />
        </button>
        <h1 className="text-lg font-bold">건강 일기</h1>
      </div>

      {/* 기간 필터 */}
      <div className="mt-4 flex gap-2">
        {FILTER_OPTIONS.map(({ label, value }) => (
          <button
            key={value}
            onClick={() => setFilter(value)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              filter === value
                ? "bg-primary text-primary-foreground"
                : "bg-accent text-muted-foreground hover:bg-accent/80"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="mt-4 flex flex-col gap-3">
        {loading && (
          <p className="mt-8 text-center text-sm text-muted-foreground">불러오는 중...</p>
        )}
        {!loading && filtered.length === 0 && (
          <p className="mt-8 text-center text-sm text-muted-foreground">
            기록이 없어요. + 버튼으로 첫 기록을 남겨보세요.
          </p>
        )}

        {grouped.map(({ monthKey, items }) => {
          const isOpen = openMonths.has(monthKey);
          return (
            <section key={monthKey} className="overflow-hidden rounded-xl border bg-card">
              {/* Accordion 헤더 */}
              <button
                onClick={() => toggleMonth(monthKey)}
                className="flex w-full items-center justify-between px-4 py-3 hover:bg-accent/50"
              >
                <span className="text-sm font-bold">{monthKey}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">{items.length}개</span>
                  <ChevronDown
                    className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${
                      isOpen ? "rotate-180" : ""
                    }`}
                  />
                </div>
              </button>

              {/* Accordion 바디 */}
              {isOpen && (
                <div className="flex flex-col divide-y">
                  {items.map((log, i) => {
                    const condKey = log.condition ?? log.overall_condition ?? "normal";
                    const cond = CONDITION_DISPLAY[condKey] ?? CONDITION_DISPLAY.normal;
                    const dateStr = getDateStr(log);
                    const noteStr = log.note ?? log.memo;
                    const isDeleting = deletingId === log.id;
                    return (
                      <div
                        key={log.id ?? i}
                        className="flex cursor-pointer items-center gap-3 px-4 py-3 transition-colors hover:bg-accent/30"
                        onClick={() => router.push(`/diary/${log.id}`)}
                      >
                        <span className="text-2xl">{cond.emoji}</span>
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-semibold">{dateStr ? formatDay(dateStr) : "-"}</p>
                          <p className={`text-xs font-medium ${cond.color}`}>{cond.label}</p>
                          {noteStr && (
                            <p className="mt-0.5 truncate text-xs text-muted-foreground">{noteStr}</p>
                          )}
                        </div>
                        <button
                          onClick={(e) => handleDelete(e, log)}
                          disabled={isDeleting}
                          className="rounded-full p-1.5 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive disabled:opacity-40"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                        <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
                      </div>
                    );
                  })}
                </div>
              )}
            </section>
          );
        })}
      </div>

      {/* 플로팅 + 버튼 */}
      <button
        onClick={() => router.push("/diary/new")}
        className="fixed bottom-24 right-5 flex h-14 w-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg transition-colors hover:bg-primary/90"
      >
        <Plus className="h-6 w-6" />
      </button>
    </main>
  );
}