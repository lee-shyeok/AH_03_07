"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronLeft, Pill, Plus, Search, Trash2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { useMedications, useDeleteMedication } from "@/features/medication/queries";
import { DRUG_CLASS_LABEL, DRUG_CLASS_COLOR } from "@/features/medication/schema";
import { getMode, type UserMode } from "@/features/auth/mode";

const TIMING_LABEL: Record<string, string> = {
  "아침": "아침",
  "점심": "점심",
  "저녁": "저녁",
  "취침 전": "취침전",
  "취침전": "취침전",
};

function daysRemaining(endDate?: string): number | null {
  if (!endDate) return null;
  const end = new Date(endDate);
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  end.setHours(0, 0, 0, 0);
  return Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

function DDay({ endDate }: { endDate?: string }) {
  const days = daysRemaining(endDate);
  if (days === null) return null;
  if (days < 0)
    return (
      <span className="rounded px-1.5 py-0.5 text-[11px] font-semibold bg-gray-100 text-gray-500">
        종료
      </span>
    );
  const urgent = days <= 7;
  return (
    <span
      className={`rounded px-1.5 py-0.5 text-[11px] font-semibold ${
        urgent ? "bg-yellow-100 text-yellow-700" : "bg-blue-50 text-blue-600"
      }`}
    >
      {days === 0 ? "D-Day" : `D-${days}`}
    </span>
  );
}

function TimingBadges({ timings }: { timings?: string[] }) {
  if (!timings?.length) return null;
  return (
    <div className="mt-1.5 flex flex-wrap gap-1">
      {timings.map((t) => (
        <span
          key={t}
          className="rounded bg-orange-50 px-1.5 py-0.5 text-[11px] font-semibold text-orange-600"
        >
          {TIMING_LABEL[t] ?? t}
        </span>
      ))}
    </div>
  );
}

function DrugClassBadge({ drugClass }: { drugClass?: string }) {
  if (!drugClass) return null;
  const label = DRUG_CLASS_LABEL[drugClass] ?? drugClass;
  const color = DRUG_CLASS_COLOR[drugClass] ?? "#6B7280";
  return (
    <span
      className="inline-block rounded-full px-2 py-0.5 text-[11px] font-semibold"
      style={{ background: color + "1A", color }}
    >
      {label}
    </span>
  );
}

type FilterType = "전체" | "자가면역" | "일반";

export default function MedicationPage() {
  const router = useRouter();
  const { data: meds = [], isLoading } = useMedications();
  const deleteMutation = useDeleteMedication();
  const [confirmItem, setConfirmItem] = useState<{ id: number; name: string } | null>(null);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<FilterType>("전체");
  const [mode, setMode] = useState<UserMode>("general");

  useEffect(() => { setMode(getMode()); }, []);

  const isAuto = mode === "autoimmune";

  function handleDelete(item: { id: number; name: string }) {
    deleteMutation.mutate(item, {
      onSuccess: () => setConfirmItem(null),
      onError: () => setConfirmItem(null),
    });
  }

  const filtered = meds.filter((m) => {
    const matchSearch = m.name.toLowerCase().includes(search.toLowerCase());
    if (!matchSearch) return false;
    if (filter === "자가면역") return !!m.drug_class;
    if (filter === "일반") return !m.drug_class;
    return true;
  });

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-8 pb-28">
      {/* 헤더 */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => router.back()}
          className="rounded-full p-1 hover:bg-accent"
          aria-label="뒤로가기"
        >
          <ChevronLeft className="h-5 w-5" />
        </button>
        <h1 className="flex-1 text-xl font-bold">내 약물 목록</h1>
        <Link
          href="/medication/new"
          className="flex items-center gap-1 rounded-xl bg-primary px-3 py-2 text-xs font-bold text-primary-foreground"
        >
          <Plus className="h-4 w-4" />
          직접 등록
        </Link>
      </div>

      {/* 검색바 */}
      <div className="mt-4 flex items-center gap-2 rounded-xl bg-muted px-3 py-2.5">
        <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="약품명 검색"
          className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
        />
      </div>

      {/* 필터 탭 — 자가면역 모드만 표시 */}
      {isAuto && (
        <div className="mt-3 flex gap-2">
          {(["전체", "자가면역", "일반"] as FilterType[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`rounded-full px-3.5 py-1.5 text-xs font-semibold transition-colors ${
                filter === f
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      )}

      <p className="mt-3 text-sm text-muted-foreground">복용 중인 약 {filtered.length}개</p>

      {isLoading ? (
        <p className="mt-8 text-sm text-muted-foreground">불러오는 중...</p>
      ) : filtered.length === 0 ? (
        <div className="mt-16 flex flex-col items-center text-muted-foreground">
          <Pill className="h-12 w-12 opacity-30" />
          <p className="mt-3 text-sm">등록된 약물이 없습니다.</p>
        </div>
      ) : (
        <div className="mt-4 space-y-3">
          {filtered.map((m) => (
            <Card key={m.id} className="p-4">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
                  <Pill className="h-5 w-5 text-primary" />
                </div>

                <Link href={`/medication/${m.id}`} className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <p className="truncate font-semibold">{m.name}</p>
                    {m.is_injection && (
                      <span
                        className="shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold"
                        style={{ background: "#EF444420", color: "#EF4444" }}
                      >
                        주사제
                      </span>
                    )}
                  </div>

                  {/* 자가면역 약물 뱃지 + D-Day */}
                  <div className="mt-1 flex flex-wrap items-center gap-1.5">
                    <DrugClassBadge drugClass={m.drug_class} />
                    <DDay endDate={m.end_date} />
                  </div>

                  {/* 복용 일정 */}
                  {m.timings?.length ? (
                    <TimingBadges timings={m.timings} />
                  ) : m.frequency ? (
                    <p className="mt-1 text-xs text-muted-foreground">{m.frequency}</p>
                  ) : null}
                </Link>

                <button
                  onClick={() => setConfirmItem({ id: m.id, name: m.name })}
                  aria-label="삭제"
                  className="shrink-0 rounded-full p-2 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* 삭제 확인 모달 */}
      {confirmItem !== null && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 px-5 pb-8"
          onClick={() => setConfirmItem(null)}
        >
          <div
            className="w-full max-w-md rounded-2xl bg-background p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <p className="text-center text-base font-bold">약물을 삭제할까요?</p>
            <p className="mt-1 text-center text-sm text-muted-foreground">
              삭제하면 복구할 수 없습니다.
            </p>
            <div className="mt-5 flex gap-3">
              <button
                onClick={() => setConfirmItem(null)}
                className="flex-1 rounded-xl border border-border py-3 text-sm font-semibold"
              >
                취소
              </button>
              <button
                onClick={() => handleDelete(confirmItem)}
                disabled={deleteMutation.isPending}
                className="flex-1 rounded-xl bg-destructive py-3 text-sm font-semibold text-white disabled:opacity-60"
              >
                {deleteMutation.isPending ? "삭제 중..." : "삭제"}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
