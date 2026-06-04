"use client";

import Link from "next/link";
import { Plus, Trash2, FileText } from "lucide-react";
import { Card } from "@/components/ui/card";
import { useRecords, useDeleteRecord } from "@/features/medical-records/queries";

export default function RecordsPage() {
  const { data: records = [], isLoading } = useRecords();
  const del = useDeleteRecord();

  function handleDelete(id: number) {
    if (!confirm("이 진료기록을 삭제하시겠습니까?")) return;
    del.mutate(id);
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">진료기록</h1>
        <Link
          href="/records/new"
          className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground"
          aria-label="진료기록 추가"
        >
          <Plus className="h-5 w-5" />
        </Link>
      </div>

      {isLoading ? (
        <p className="mt-8 text-sm text-muted-foreground">불러오는 중...</p>
      ) : records.length === 0 ? (
        <div className="mt-16 flex flex-col items-center text-muted-foreground">
          <FileText className="h-12 w-12 opacity-30" />
          <p className="mt-3 text-sm">진료기록이 없습니다.</p>
          <Link href="/records/new" className="mt-2 text-sm text-primary hover:underline">
            첫 진료기록 추가하기
          </Link>
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {records.map((r) => (
            <Card key={r.id} className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-semibold">{r.hospital_name || "병원"}</p>
                  {r.department && <p className="text-xs text-muted-foreground">{r.department}</p>}
                  {r.diagnosis && <p className="mt-1 text-sm text-foreground">{r.diagnosis}</p>}
                  {r.visit_date && <p className="mt-1 text-xs text-muted-foreground">{r.visit_date}</p>}
                </div>
                <button
                  onClick={() => handleDelete(r.id)}
                  className="text-muted-foreground hover:text-destructive"
                  aria-label="삭제"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </main>
  );
}
