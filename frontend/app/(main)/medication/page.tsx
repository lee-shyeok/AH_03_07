"use client";

import { useState } from "react";
import Link from "next/link";
import { Pill, Plus, Trash2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { useMedications, useDeleteMedication } from "@/features/medication/queries";
import { DRUG_CLASS_LABEL, DRUG_CLASS_COLOR } from "@/features/medication/schema";

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

export default function MedicationPage() {
  const { data: meds = [], isLoading } = useMedications();
  const deleteMutation = useDeleteMedication();
  const [confirmId, setConfirmId] = useState<number | null>(null);

  function handleDelete(id: number) {
    deleteMutation.mutate(id, {
      onSuccess: () => setConfirmId(null),
      onError: () => setConfirmId(null),
    });
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-10 pb-28">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">내 약물 목록</h1>
        <Link
          href="/medication/new"
          className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground"
          aria-label="약 등록"
        >
          <Plus className="h-5 w-5" />
        </Link>
      </div>
      <p className="mt-1 text-sm text-muted-foreground">복용 중인 약 {meds.length}개</p>

      {isLoading ? (
        <p className="mt-8 text-sm text-muted-foreground">불러오는 중...</p>
      ) : meds.length === 0 ? (
        <div className="mt-16 flex flex-col items-center text-muted-foreground">
          <Pill className="h-12 w-12 opacity-30" />
          <p className="mt-3 text-sm">등록된 약물이 없습니다.</p>
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {meds.map((m) => (
              <Card key={m.id} className="flex items-center gap-3 p-4">
                {/* 약 아이콘 */}
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
                  <Pill className="h-5 w-5 text-primary" />
                </div>

                {/* 약 정보 — 클릭 시 상세 */}
                <Link href={`/medication/${m.id}`} className="flex-1 min-w-0">
                  <p className="truncate font-semibold">{m.name}</p>
                  <div className="mt-1 flex flex-wrap items-center gap-1.5">
                    <DrugClassBadge drugClass={m.drug_class} />
                    {m.is_injection && (
                      <span
                        className="inline-block rounded-full px-2 py-0.5 text-[11px] font-semibold"
                        style={{ background: "#EF444420", color: "#EF4444" }}
                      >
                        주사제
                      </span>
                    )}
                    {m.frequency && (
                      <span className="text-xs text-muted-foreground">{m.frequency}</span>
                    )}
                  </div>
                  {m.note && (
                    <p className="mt-0.5 truncate text-xs text-muted-foreground">{m.note}</p>
                  )}
                </Link>

                {/* 삭제 버튼 */}
                <button
                  onClick={() => setConfirmId(m.id)}
                  aria-label="삭제"
                  className="shrink-0 rounded-full p-2 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </Card>
          ))}
        </div>
      )}

      {/* 삭제 확인 모달 */}
      {confirmId !== null && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 px-5 pb-8"
          onClick={() => setConfirmId(null)}
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
                onClick={() => setConfirmId(null)}
                className="flex-1 rounded-xl border border-border py-3 text-sm font-semibold"
              >
                취소
              </button>
              <button
                onClick={() => handleDelete(confirmId)}
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
