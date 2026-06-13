"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronLeft, Plus, Trash2, FileText, ChevronDown, ChevronRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { useRecords, useDeleteRecord } from "@/features/medical-records/queries";

const PAGE_SIZE = 10;

export default function RecordsPage() {
  const router = useRouter();
  const { data: records = [], isLoading } = useRecords();
  const del = useDeleteRecord();

  const [sort, setSort] = useState<"newest" | "oldest">("newest");
  const [filterHospital, setFilterHospital] = useState("");
  const [filterDiagnosis, setFilterDiagnosis] = useState("");
  const [filterFrom, setFilterFrom] = useState("");
  const [filterTo, setFilterTo] = useState("");
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    let list = [...records];
    if (filterHospital) list = list.filter((r) => r.hospital_name?.includes(filterHospital));
    if (filterDiagnosis) list = list.filter((r) => r.diagnosis?.includes(filterDiagnosis));
    if (filterFrom) list = list.filter((r) => r.visit_date && r.visit_date >= filterFrom);
    if (filterTo) list = list.filter((r) => r.visit_date && r.visit_date <= filterTo);
    list.sort((a, b) => {
      const da = a.visit_date ?? "";
      const db = b.visit_date ?? "";
      return sort === "newest" ? db.localeCompare(da) : da.localeCompare(db);
    });
    return list;
  }, [records, sort, filterHospital, filterDiagnosis, filterFrom, filterTo]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  function handleDelete(id: number) {
    if (!confirm("이 진료기록을 삭제하시겠습니까?")) return;
    del.mutate(id);
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 pb-10 pt-6">
      <div className="flex items-center gap-2">
        <button onClick={() => router.back()} className="p-1 text-foreground" aria-label="뒤로가기">
          <ChevronLeft className="h-6 w-6" />
        </button>
        <h1 className="flex-1 text-2xl font-bold">진료기록</h1>
        <Link href="/records/new" className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground" aria-label="진료기록 추가">
          <Plus className="h-5 w-5" />
        </Link>
      </div>

      {/* 필터 */}
      <div className="mt-4 space-y-2 rounded-2xl border border-border p-4">
        <div className="flex gap-2">
          <input type="date" value={filterFrom} onChange={(e) => { setFilterFrom(e.target.value); setPage(1); }} className="flex-1 rounded-lg border border-input bg-background px-3 py-2 text-sm" placeholder="시작일" />
          <span className="self-center text-muted-foreground">~</span>
          <input type="date" value={filterTo} onChange={(e) => { setFilterTo(e.target.value); setPage(1); }} className="flex-1 rounded-lg border border-input bg-background px-3 py-2 text-sm" placeholder="종료일" />
        </div>
        <input value={filterHospital} onChange={(e) => { setFilterHospital(e.target.value); setPage(1); }} placeholder="의료기관 검색" className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm" />
        <input value={filterDiagnosis} onChange={(e) => { setFilterDiagnosis(e.target.value); setPage(1); }} placeholder="진단명 검색" className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm" />
      </div>

      {/* 정렬 */}
      <div className="mt-3 flex items-center justify-between">
        <span className="text-sm text-muted-foreground">총 {filtered.length}건</span>
        <div className="relative">
          <select value={sort} onChange={(e) => { setSort(e.target.value as "newest" | "oldest"); setPage(1); }} className="appearance-none rounded-lg border border-input bg-background py-1.5 pl-3 pr-8 text-sm">
            <option value="newest">최신순</option>
            <option value="oldest">오래된순</option>
          </select>
          <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
        </div>
      </div>

      {isLoading ? (
        <p className="mt-8 text-sm text-muted-foreground">불러오는 중...</p>
      ) : filtered.length === 0 ? (
        <div className="mt-16 flex flex-col items-center text-muted-foreground">
          <FileText className="h-12 w-12 opacity-30" />
          <p className="mt-3 text-sm">진료기록이 없습니다.</p>
          <Link href="/records/new" className="mt-2 text-sm text-primary hover:underline">첫 진료기록 추가하기</Link>
        </div>
      ) : (
        <>
          <div className="mt-3 space-y-3">
            {paged.map((r) => (
              <Card key={r.id} className="p-4">
                <div className="flex items-start justify-between">
                  <Link href={`/records/${r.id}`} className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-semibold">{r.hospital_name || "병원"}</p>
                      {r.department && <span className="text-xs text-muted-foreground">{r.department}</span>}
                    </div>
                    {r.diagnosis && <p className="mt-1 text-sm">{r.diagnosis}</p>}
                    <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
                      {r.visit_date && <span>📅 {r.visit_date}</span>}
                    </div>
                  </Link>
                  <div className="ml-2 flex shrink-0 items-center gap-1">
                    <button onClick={() => handleDelete(r.id)} className="text-muted-foreground hover:text-destructive" aria-label="삭제">
                      <Trash2 className="h-4 w-4" />
                    </button>
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* 페이지네이션 */}
          {totalPages > 1 && (
            <div className="mt-4 flex items-center justify-center gap-2">
              <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="rounded-lg border border-border px-3 py-1.5 text-sm disabled:opacity-40">이전</button>
              <span className="text-sm text-muted-foreground">{page} / {totalPages}</span>
              <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="rounded-lg border border-border px-3 py-1.5 text-sm disabled:opacity-40">다음</button>
            </div>
          )}
        </>
      )}
    </main>
  );
}
