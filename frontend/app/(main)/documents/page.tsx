"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ChevronLeft, Search, FileText, FlaskConical, Pill } from "lucide-react";
import { Card } from "@/components/ui/card";
import { getDocuments, MedicalDocument } from "@/features/documents/api";

type Filter = "전체" | "진료기록" | "검사결과" | "처방전";
const FILTERS: Filter[] = ["전체", "진료기록", "검사결과", "처방전"];

const FALLBACK_DOCS: MedicalDocument[] = [
  { id: 1, document_type: "진료기록", file_name: "진료기록", created_at: "2026-05-20" },
  { id: 2, document_type: "검사결과", file_name: "검사결과", created_at: "2026-05-12" },
  { id: 3, document_type: "처방전", file_name: "처방전", created_at: "2026-04-25" },
];

const ICONS = { 진료기록: FileText, 검사결과: FlaskConical, 처방전: Pill } as const;
const ICON_BG = {
  진료기록: "bg-secondary text-primary",
  검사결과: "bg-[#F0E8FF] text-[#7C5CCF]",
  처방전: "bg-secondary text-primary",
} as const;

type DocType = keyof typeof ICONS;

function toDocType(raw: string | undefined): DocType {
  if (raw === "진료기록" || raw === "검사결과" || raw === "처방전") return raw;
  return "진료기록";
}

function toMonth(dateStr: string | undefined): string {
  if (!dateStr) return "날짜 미상";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return "날짜 미상";
  return `${d.getFullYear()}년 ${d.getMonth() + 1}월`;
}

function toDisplayDate(dateStr: string | undefined): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;
}

export default function DocumentsPage() {
  const router = useRouter();
  const [filter, setFilter] = useState<Filter>("전체");
  const [docs, setDocs] = useState<MedicalDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDocuments()
      .then(setDocs)
      .catch(() => setDocs(FALLBACK_DOCS))
      .finally(() => setLoading(false));
  }, []);

  const filtered = docs.filter(
    (d) => filter === "전체" || toDocType(d.document_type) === filter
  );
  const months = Array.from(new Set(filtered.map((d) => toMonth(d.created_at))));

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button onClick={() => router.back()} className="rounded-full p-1 hover:bg-accent" aria-label="뒤로가기">
            <ChevronLeft className="h-5 w-5" />
          </button>
          <h1 className="text-2xl font-bold">의료문서</h1>
        </div>
        <Link href="/search" aria-label="검색">
          <Search className="h-6 w-6" />
        </Link>
      </div>

      {/* 필터 */}
      <div className="mt-4 flex gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={
              "rounded-full px-4 py-2 text-sm font-semibold " +
              (filter === f ? "bg-primary text-primary-foreground" : "border border-border")
            }
          >
            {f}
          </button>
        ))}
      </div>

      {/* 상태 처리 */}
      {loading && (
        <p className="mt-10 text-center text-sm text-muted-foreground">불러오는 중...</p>
      )}
      {error && (
        <p className="mt-10 text-center text-sm text-destructive">{error}</p>
      )}

      {/* 월별 그룹 */}
      {!loading && !error && (
        <div className="mt-6 space-y-6 pb-6">
          {months.length === 0 ? (
            <p className="mt-10 text-center text-sm text-muted-foreground">문서가 없습니다</p>
          ) : (
            months.map((month) => (
              <div key={month}>
                <p className="text-sm font-bold text-muted-foreground">{month}</p>
                <div className="mt-2 space-y-3">
                  {filtered
                    .filter((d) => toMonth(d.created_at) === month)
                    .map((d) => {
                      const type = toDocType(d.document_type);
                      const Icon = ICONS[type];
                      return (
                        <Card
                          key={d.id}
                          className="flex cursor-pointer items-center gap-3 p-4 hover:bg-accent"
                          onClick={() =>
                            router.push(`/documents/ocr-review?documentId=${d.id}&document_type=${d.document_type ?? "other"}`)
                          }
                        >
                          <div
                            className={
                              "flex h-12 w-12 items-center justify-center rounded-xl " +
                              ICON_BG[type]
                            }
                          >
                            <Icon className="h-6 w-6" />
                          </div>
                          <div className="flex-1">
                            <p className="font-bold">{type}</p>
                            <p className="text-xs text-muted-foreground">
                              {d.file_name ?? `문서 #${d.id}`}
                            </p>
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {toDisplayDate(d.created_at)}
                          </span>
                        </Card>
                      );
                    })}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </main>
  );
}
