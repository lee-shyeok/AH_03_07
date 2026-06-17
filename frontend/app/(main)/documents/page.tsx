"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { FileText, FlaskConical, Pill, Plus, ChevronLeft, Trash2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { getDocuments, deleteDocument, MedicalDocument } from "@/features/documents/api";

type Tab = "처방전" | "검사" | "진료기록";
const TABS: Tab[] = ["처방전", "검사", "진료기록"];

const FALLBACK_DOCS: MedicalDocument[] = [
  { id: 1, document_type: "진료기록", file_name: "진료기록", created_at: "2026-05-20" },
  { id: 2, document_type: "검사결과", file_name: "검사결과", created_at: "2026-05-12" },
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
  const month = d.getMonth() + 1;
  const day = d.getDate();
  const hours = String(d.getHours()).padStart(2, "0");
  const minutes = String(d.getMinutes()).padStart(2, "0");
  return `${month}월 ${day}일 ${hours}:${minutes}`;
}

const TAB_MATCH: Record<"처방전" | "검사", (type: string) => boolean> = {
  처방전: (t) => t === "처방전" || t === "prescription",
  검사: (t) => t === "검사결과" || t === "lab_result",
};

export default function DocumentsPage() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("처방전");
  const [docs, setDocs] = useState<MedicalDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<Set<number>>(new Set());

  async function handleDelete(e: React.MouseEvent, id: number) {
    e.stopPropagation();
    if (!confirm("이 문서를 삭제하시겠습니까?")) return;
    setDeleting((prev) => new Set(prev).add(id));
    try {
      await deleteDocument(id);
      setDocs((prev) => prev.filter((d) => d.id !== id));
    } catch {
      alert("삭제에 실패했습니다.");
    } finally {
      setDeleting((prev) => { const s = new Set(prev); s.delete(id); return s; });
    }
  }

  useEffect(() => {
    getDocuments()
      .then(setDocs)
      .catch(() => setDocs(FALLBACK_DOCS))
      .finally(() => setLoading(false));
  }, []);

  const filtered =
    tab === "진료기록"
      ? []
      : docs.filter((d) => TAB_MATCH[tab](d.document_type ?? ""));

  const months = Array.from(new Set(filtered.map((d) => toMonth(d.created_at))));

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-8">
      <div className="flex items-center gap-2">
        <button onClick={() => router.back()} aria-label="뒤로 가기" className="text-muted-foreground hover:text-foreground">
          <ChevronLeft className="h-6 w-6" />
        </button>
        <h1 className="text-2xl font-bold">의료문서</h1>
      </div>

      {/* 탭 */}
      <div className="mt-4 flex gap-2">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={
              "rounded-full px-4 py-2 text-sm font-semibold " +
              (tab === t ? "bg-primary text-primary-foreground" : "border border-border")
            }
          >
            {t}
          </button>
        ))}
      </div>

      {/* 진료기록 탭 — /records 링크 */}
      {tab === "진료기록" && (
        <div className="mt-10 flex flex-col items-center gap-4">
          <p className="text-sm text-muted-foreground">진료기록은 기록 페이지에서 확인하세요.</p>
          <Link
            href="/records"
            className="rounded-2xl bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground"
          >
            진료기록 보러 가기
          </Link>
        </div>
      )}

      {/* 처방전 / 검사 탭 */}
      {tab !== "진료기록" && (
        <>
          {/* 추가 버튼 */}
          {!loading && (
            <button
              onClick={() =>
                router.push(
                  tab === "처방전"
                    ? "/documents/ocr-review?document_type=prescription"
                    : "/documents/ocr-review?document_type=lab_result"
                )
              }
              className="mt-4 flex w-full items-center gap-2 rounded-2xl border-2 border-dashed border-primary/40 bg-secondary/30 px-4 py-3 text-primary"
            >
              <Plus className="h-4 w-4 shrink-0" />
              <span className="text-sm font-semibold">
                {tab === "처방전" ? "처방전 추가" : "검사 추가"}
              </span>
            </button>
          )}

          {loading && (
            <p className="mt-10 text-center text-sm text-muted-foreground">불러오는 중...</p>
          )}

          {/* 월별 그룹 */}
          {!loading && (
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
                              onClick={() => router.push(`/documents/${d.id}`)}
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
                              <button
                                onClick={(e) => handleDelete(e, d.id)}
                                disabled={deleting.has(d.id)}
                                aria-label="문서 삭제"
                                className="ml-1 rounded-full p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive disabled:opacity-40"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </Card>
                          );
                        })}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </>
      )}
    </main>
  );
}
