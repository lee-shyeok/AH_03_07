"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { FlaskConical, MoreVertical, Plus, X } from "lucide-react";
import { Card } from "@/components/ui/card";
import {
  deleteLabResult,
  listLabResults,
  updateLabResult,
  type LabResultResponse,
} from "@/features/lab-results/api";
import { getMode, type UserMode } from "@/features/auth/mode";

const PURPLE = "#7C5CCF";

const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];

function pad(n: number) {
  return String(n).padStart(2, "0");
}
function fmtDateLabel(iso: string) {
  const d = new Date(iso);
  return `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())} (${WEEKDAYS[d.getDay()]})`;
}

type EditState = {
  id: number;
  test_date: string;
  test_type: string;
  user_recorded_value: string;
  reference_range: string;
  note: string;
};

export default function LabResultsListPage() {
  const router = useRouter();
  const [results, setResults] = useState<LabResultResponse[]>([]);
  const [refreshKey, setRefreshKey] = useState(0);
  const [menuId, setMenuId] = useState<number | null>(null);
  const [edit, setEdit] = useState<EditState | null>(null);
  const [editSaving, setEditSaving] = useState(false);
  const [period, setPeriod] = useState<"6m" | "1y" | "2y">("6m");
  const [mode, setMode] = useState<UserMode>("general");

  useEffect(() => {
    setMode(getMode());
  }, []);

  useEffect(() => {
    listLabResults()
      .then(setResults)
      .catch(() => setResults([]));
  }, [refreshKey]);

  const sorted = useMemo(
    () =>
      [...results].sort(
        (a, b) =>
          b.test_date.localeCompare(a.test_date) || b.created_at.localeCompare(a.created_at)
      ),
    [results]
  );

  const cutoff = useMemo(() => {
    const d = new Date();
    d.setMonth(d.getMonth() - (period === "6m" ? 6 : period === "1y" ? 12 : 24));
    return d;
  }, [period]);

  const filtered = useMemo(
    () => sorted.filter((r) => new Date(r.test_date) >= cutoff),
    [sorted, cutoff],
  );

  const grouped = useMemo(() => {
    const m = new Map<string, LabResultResponse[]>();
    for (const r of filtered) {
      const day = r.test_date.slice(0, 10);
      if (!m.has(day)) m.set(day, []);
      m.get(day)!.push(r);
    }
    return Array.from(m.entries());
  }, [filtered]);

  function openEdit(r: LabResultResponse) {
    setEdit({
      id: r.id,
      test_date: r.test_date.slice(0, 10),
      test_type: r.test_type,
      user_recorded_value: r.user_recorded_value,
      reference_range: r.reference_range ?? "",
      note: r.note ?? "",
    });
    setMenuId(null);
  }
  async function handleEditSave() {
    if (!edit || !edit.test_type.trim() || !edit.user_recorded_value.trim()) return;
    setEditSaving(true);
    try {
      await updateLabResult(edit.id, {
        test_date: edit.test_date,
        test_type: edit.test_type.trim(),
        user_recorded_value: edit.user_recorded_value.trim(),
        reference_range: edit.reference_range.trim() || null,
        note: edit.note.trim() || null,
      });
      setEdit(null);
      setRefreshKey((k) => k + 1);
    } catch {
      /* noop */
    } finally {
      setEditSaving(false);
    }
  }
  async function handleDelete(r: LabResultResponse) {
    setMenuId(null);
    if (!window.confirm("이 검사 결과를 삭제할까요?")) return;
    try {
      await deleteLabResult(r.id);
      setRefreshKey((k) => k + 1);
    } catch {
      /* noop */
    }
  }

  return (
    <main className="mx-auto min-h-screen w-full max-w-md px-5 py-8">
      <h1 className="text-2xl font-bold">검사 결과</h1>

      {/* 기간 토글 */}
      <div className="mt-3 flex gap-1.5">
        {(["6m", "1y", "2y"] as const).map((p) => {
          const label = p === "6m" ? "6개월" : p === "1y" ? "1년" : "2년";
          const active = period === p;
          return (
            <button
              key={p}
              type="button"
              onClick={() => setPeriod(p)}
              className={
                active
                  ? "rounded-full px-3 py-1 text-sm font-semibold transition text-primary-foreground"
                  : "rounded-full px-3 py-1 text-sm font-semibold transition text-muted-foreground border border-border"
              }
              style={active ? { backgroundColor: PURPLE } : undefined}
            >
              {label}
            </button>
          );
        })}
      </div>

      {filtered.length === 0 ? (
        <p className="py-20 text-center text-sm text-muted-foreground">
          선택한 기간에 기록한 검사 결과가 없어요.
          {mode === "autoimmune" && (
            <>
              <br />
              오른쪽 아래 + 버튼으로 추가하세요.
            </>
          )}
        </p>
      ) : (
        <div className="mt-4">
          {grouped.map(([day, rows]) => (
            <div key={day} className="mt-6">
              <p className="mb-2 text-sm font-semibold text-muted-foreground">
                {fmtDateLabel(day)}
              </p>
              <div className="space-y-3">
                {rows.map((r) => (
            <Card key={r.id} className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <FlaskConical className="h-4 w-4" style={{ color: PURPLE }} />
                  <div>
                    <p className="font-bold">{r.test_type}</p>
                  </div>
                </div>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setMenuId((m) => (m === r.id ? null : r.id))}
                    aria-label="메뉴"
                    className="p-1 text-muted-foreground"
                  >
                    <MoreVertical className="h-5 w-5" />
                  </button>
                  {menuId === r.id && (
                    <div className="absolute right-0 z-10 mt-1 w-24 overflow-hidden rounded-lg border bg-background py-1 shadow-md">
                      <button
                        type="button"
                        onClick={() => openEdit(r)}
                        className="block w-full px-3 py-1.5 text-left text-sm hover:bg-muted"
                      >
                        수정
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(r)}
                        className="block w-full px-3 py-1.5 text-left text-sm text-destructive hover:bg-muted"
                      >
                        삭제
                      </button>
                    </div>
                  )}
                </div>
              </div>
              <div className="mt-3 space-y-1.5 text-sm">
                <div className="flex justify-between gap-3">
                  <span className="text-muted-foreground">수치</span>
                  <span className="text-right font-medium">{r.user_recorded_value}</span>
                </div>
                {r.reference_range && (
                  <div className="flex justify-between gap-3">
                    <span className="text-muted-foreground">참고범위</span>
                    <span className="text-right">{r.reference_range}</span>
                  </div>
                )}
                {r.note && <p className="pt-1 text-xs text-muted-foreground">{r.note}</p>}
              </div>
            </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* FAB → 자가면역 모드에서만 표시 */}
      {mode === "autoimmune" && (
        <div className="pointer-events-none fixed inset-x-0 bottom-20 mx-auto flex max-w-md justify-end px-5">
          <button
            type="button"
            onClick={() => router.push("/lab-results")}
            aria-label="검사 결과 추가"
            className="pointer-events-auto flex h-14 w-14 items-center justify-center rounded-full text-primary-foreground shadow-lg"
            style={{ backgroundColor: PURPLE }}
          >
            <Plus className="h-6 w-6" />
          </button>
        </div>
      )}

      {/* 수정 모달 */}
      {edit && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-5"
          onClick={() => setEdit(null)}
        >
          <div
            className="max-h-[85vh] w-full max-w-sm overflow-y-auto rounded-3xl bg-background p-5"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold">검사 결과 수정</h2>
              <button type="button" onClick={() => setEdit(null)} aria-label="닫기">
                <X className="h-5 w-5 text-muted-foreground" />
              </button>
            </div>

            <p className="mt-4 text-sm font-semibold">검사일자</p>
            <input
              type="date"
              value={edit.test_date}
              onChange={(e) => setEdit({ ...edit, test_date: e.target.value })}
              className="mt-2 w-full rounded-xl border px-3 py-2.5 text-sm"
            />

            <p className="mt-4 text-sm font-semibold">검사 종류</p>
            <input
              value={edit.test_type}
              onChange={(e) => setEdit({ ...edit, test_type: e.target.value })}
              maxLength={128}
              className="mt-2 w-full rounded-xl border px-3 py-2.5 text-sm"
            />

            <p className="mt-4 text-sm font-semibold">수치</p>
            <input
              value={edit.user_recorded_value}
              onChange={(e) => setEdit({ ...edit, user_recorded_value: e.target.value })}
              maxLength={64}
              className="mt-2 w-full rounded-xl border px-3 py-2.5 text-sm"
            />

            <p className="mt-4 text-sm font-semibold">
              참고범위 <span className="font-normal text-muted-foreground">(검사지 그대로, 선택)</span>
            </p>
            <input
              value={edit.reference_range}
              onChange={(e) => setEdit({ ...edit, reference_range: e.target.value })}
              className="mt-2 w-full rounded-xl border px-3 py-2.5 text-sm"
            />

            <p className="mt-4 text-sm font-semibold">
              메모 <span className="font-normal text-muted-foreground">(선택)</span>
            </p>
            <textarea
              value={edit.note}
              onChange={(e) => setEdit({ ...edit, note: e.target.value })}
              rows={2}
              className="mt-2 w-full rounded-xl border px-3 py-2.5 text-sm"
            />

            <div className="mt-5 flex gap-2">
              <button
                type="button"
                onClick={() => setEdit(null)}
                className="flex-1 rounded-xl border py-3 font-bold"
              >
                취소
              </button>
              <button
                type="button"
                onClick={handleEditSave}
                disabled={editSaving || !edit.test_type.trim() || !edit.user_recorded_value.trim()}
                className="flex-1 rounded-xl py-3 font-bold text-primary-foreground disabled:opacity-50"
                style={{ backgroundColor: PURPLE }}
              >
                {editSaving ? "저장 중..." : "수정"}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
