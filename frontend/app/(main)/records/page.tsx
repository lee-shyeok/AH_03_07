"use client";

import { useState, useMemo, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronLeft, Plus, Trash2, FileText, ChevronDown, ChevronRight, Pill } from "lucide-react";
import { Card } from "@/components/ui/card";
import { useRecords, useDeleteRecord } from "@/features/medical-records/queries";
import { getMode } from "@/features/auth/mode";
import { getDocuments, MedicalDocument } from "@/features/documents/api";

const PAGE_SIZE = 10;

const AUTOIMMUNE_KEYWORDS = ["류마티스", "루푸스", "강직성척추염", "쇼그렌", "자가면역", "전신홍반", "크론", "베체트"];

function isAutoimmuneDx(diagnosis?: string): boolean {
  if (!diagnosis) return false;
  return AUTOIMMUNE_KEYWORDS.some((k) => diagnosis.includes(k));
}

export default function RecordsPage() {
  const router = useRouter();
  const { data: records = [], isLoading } = useRecords();
  const del = useDeleteRecord();
  const [isAuto, setIsAuto] = useState(false);

  useEffect(() => { setIsAuto(getMode() === "autoimmune"); }, []);

  const [ocrDocs, setOcrDocs] = useState<MedicalDocument[]>([]);
  const [ocrLoading, setOcrLoading] = useState(true);

  useEffect(() => {
    getDocuments()
      .then((docs) =>
        setOcrDocs(
          docs.filter(
            (d) => d.document_type === "진료기록" || d.document_type === "처방전"
          )
        )
      )
      .catch(() => setOcrDocs([]))
      .finally(() => setOcrLoading(false));
  }, []);

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
        <button onClick={() => router.back()} className="rounded-full p-1 hover:bg-accent" aria-label="뒤로가기">
          <ChevronLeft className="h-5 w-5" />
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
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-semibold">{r.hospital_name || "병원"}</p>
                      {r.department && <span className="text-xs text-muted-foreground">{r.department}</span>}
                      {isAuto && isAutoimmuneDx(r.diagnosis) && (
                        <span className="rounded-full bg-[#EDE7FB] px-2 py-0.5 text-[10px] font-bold text-[#7C5CCF]">자가면역</span>
                      )}
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
      {/* OCR 등록 문서 섹션 */}
      <div className="mt-8">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold">OCR 등록 문서</h2>
          <Link href="/documents" className="text-xs text-primary hover:underline">
            전체 보기
          </Link>
        </div>

        {ocrLoading ? (
          <p className="mt-3 text-sm text-muted-foreground">불러오는 중...</p>
        ) : ocrDocs.length === 0 ? (
          <div className="mt-3 flex flex-col items-center gap-2 rounded-2xl border border-dashed border-border py-8 text-muted-foreground">
            <FileText className="h-8 w-8 opacity-30" />
            <p className="text-sm">OCR로 등록된 문서가 없습니다.</p>
            <Link href="/documents/ocr-review" className="text-xs text-primary hover:underline">
              처방전 업로드하기
            </Link>
          </div>
        ) : (
          <div className="mt-3 space-y-2">
            {ocrDocs.map((doc) => {
              const isPrescription = doc.document_type === "처방전";
              return (
                <Link
                  key={doc.id}
                  href={`/documents/ocr-review?documentId=${doc.id}&document_type=${doc.document_type ?? "진료기록"}`}
                >
                  <Card className="flex items-center gap-3 p-3 hover:bg-accent">
                    <div
                      className={
                        "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl " +
                        (isPrescription
                          ? "bg-secondary text-primary"
                          : "bg-secondary text-primary")
                      }
                    >
                      {isPrescription ? (
                        <Pill className="h-5 w-5" />
                      ) : (
                        <FileText className="h-5 w-5" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold">{doc.document_type ?? "문서"}</p>
                      <p className="truncate text-xs text-muted-foreground">
                        {doc.file_name ?? `문서 #${doc.id}`}
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-1">
                      {doc.created_at && (
                        <span className="text-xs text-muted-foreground">
                          {doc.created_at.slice(0, 10)}
                        </span>
                      )}
                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </Card>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}
