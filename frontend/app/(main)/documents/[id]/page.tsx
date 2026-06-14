"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ChevronLeft, FileText, FlaskConical, Pill, Package } from "lucide-react";
import { Card } from "@/components/ui/card";
import {
  getDocument,
  getOcrJobs,
  type MedicalDocument,
  type OcrJob,
  type MedicationItem,
} from "@/features/documents/api";

// ─── Constants ────────────────────────────────────────────────────────────────

const DOC_TYPE_LABELS: Record<string, string> = {
  prescription: "처방전",
  medical_record: "진료기록",
  pill_bag: "약 봉투",
  lab_result: "검사결과",
  health_checkup: "건강검진",
  other: "기타",
};

const DOC_TYPE_ICONS: Record<string, React.ElementType> = {
  prescription: Pill,
  medical_record: FileText,
  pill_bag: Package,
  lab_result: FlaskConical,
  health_checkup: FlaskConical,
  other: FileText,
};

const MEDICATION_LABELS: Record<keyof MedicationItem, string> = {
  drug_name_user_input: "약품명",
  dosage: "용량",
  frequency: "복용 횟수",
  duration_days: "기간(일)",
  drug_category: "약물 분류",
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function toDisplayDate(dateStr: string | undefined): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const documentId = Number(id);

  const [doc, setDoc] = useState<MedicalDocument | null>(null);
  const [latestJob, setLatestJob] = useState<OcrJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [docData, jobs] = await Promise.all([
          getDocument(documentId),
          getOcrJobs(documentId),
        ]);
        setDoc(docData);
        if (jobs.length > 0) {
          setLatestJob(jobs[0]);
        }
      } catch {
        setError("문서를 불러오지 못했습니다.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [documentId]);

  if (loading) {
    return (
      <main className="mx-auto w-full max-w-md px-5 py-8">
        <p className="text-center text-muted-foreground">불러오는 중...</p>
      </main>
    );
  }

  if (error || !doc) {
    return (
      <main className="mx-auto w-full max-w-md px-5 py-8">
        <p className="text-center text-destructive">{error ?? "문서를 찾을 수 없습니다."}</p>
        <button
          onClick={() => router.back()}
          className="mt-6 w-full rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground"
        >
          뒤로 가기
        </button>
      </main>
    );
  }

  const typeKey = doc.document_type ?? "other";
  const typeLabel = DOC_TYPE_LABELS[typeKey] ?? typeKey;
  const Icon = DOC_TYPE_ICONS[typeKey] ?? FileText;
  const medications = Array.isArray(latestJob?.structured_data)
    ? (latestJob!.structured_data as MedicationItem[])
    : [];

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-6 pb-10">
      {/* 헤더 */}
      <button
        onClick={() => router.back()}
        className="mb-2 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        aria-label="뒤로 가기"
      >
        <ChevronLeft className="h-4 w-4" />
        뒤로 가기
      </button>

      {/* 문서 기본 정보 */}
      <Card className="mt-4 flex items-center gap-4 p-4">
        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-secondary text-primary">
          <Icon className="h-7 w-7" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-bold text-lg">{typeLabel}</p>
          <p className="truncate text-sm text-muted-foreground">
            {doc.original_filename ?? doc.file_name ?? `문서 #${doc.id}`}
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {toDisplayDate(doc.created_at)}
          </p>
        </div>
        {doc.is_user_confirmed && (
          <span className="shrink-0 rounded-full bg-green-100 px-2.5 py-1 text-xs font-semibold text-green-700">
            확정됨
          </span>
        )}
      </Card>

      {/* OCR 결과 */}
      <p className="mt-6 text-sm font-semibold text-muted-foreground">인식된 약품 정보</p>

      {!latestJob ? (
        <p className="mt-4 text-center text-sm text-muted-foreground">OCR 결과가 없습니다.</p>
      ) : latestJob.status === "pending" || latestJob.status === "processing" ? (
        <p className="mt-4 text-center text-sm text-muted-foreground">OCR 처리 중...</p>
      ) : latestJob.status === "failed" ? (
        <p className="mt-4 text-center text-sm text-destructive">OCR 처리에 실패했습니다.</p>
      ) : medications.length > 0 ? (
        <div className="mt-2 space-y-3">
          {medications.map((med, idx) => (
            <Card key={idx} className="p-4">
              <p className="mb-2 text-xs font-bold text-primary">약품 {idx + 1}</p>
              {(Object.keys(MEDICATION_LABELS) as (keyof MedicationItem)[]).map((k) => {
                const val = med[k];
                if (val === undefined || val === null) return null;
                return (
                  <div key={String(k)} className="flex justify-between border-b py-1.5 last:border-0">
                    <span className="text-xs text-muted-foreground">{MEDICATION_LABELS[k]}</span>
                    <span className="text-sm font-medium">{String(val)}</span>
                  </div>
                );
              })}
            </Card>
          ))}
        </div>
      ) : latestJob.raw_text ? (
        <div className="mt-2 space-y-2">
          {latestJob.raw_text
            .split("\n")
            .filter(Boolean)
            .map((line, i) => (
              <Card key={i} className="px-4 py-3">
                <p className="text-sm">{line}</p>
              </Card>
            ))}
        </div>
      ) : (
        <p className="mt-4 text-center text-sm text-muted-foreground">인식된 내용이 없습니다.</p>
      )}

      {/* 신뢰도 */}
      {latestJob?.confidence_score != null && (
        <p className="mt-4 text-center text-xs text-muted-foreground">
          OCR 신뢰도: {Math.round(latestJob.confidence_score * 100)}%
        </p>
      )}
    </main>
  );
}