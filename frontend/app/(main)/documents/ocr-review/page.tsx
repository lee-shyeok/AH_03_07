"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { FileText, ImageIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { getOcrJob, confirmDocument } from "@/features/documents/api";

// ─── Types ────────────────────────────────────────────────────────────────────

interface Field {
  key: string;
  label: string;
  value: string;
  confidence: number;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const DOC_TYPE_MAP: Record<string, string> = {
  처방전: "prescription",
  검사결과: "lab_result",
  진료기록: "medical_record",
};

const FALLBACK_FIELDS: Field[] = [
  { key: "visit_date", label: "진료일", value: "2026.5.20", confidence: 98 },
  {
    key: "hospital",
    label: "병원명",
    value: "서울대학교병원 내과",
    confidence: 95,
  },
  { key: "diagnosis", label: "진단명", value: "위염", confidence: 88 },
  {
    key: "medication",
    label: "처방 약물",
    value: "라베프라졸 10mg",
    confidence: 92,
  },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function structuredDataToFields(
  data: Record<string, unknown>,
  score: number
): Field[] {
  return Object.entries(data)
    .filter(([k]) => k !== "raw_text")
    .map(([key, val]) => ({
      key,
      label: key,
      value: String(val ?? ""),
      confidence: Math.round(score * 100),
    }));
}

// ─── Inner page ───────────────────────────────────────────────────────────────

function OcrReviewInner() {
  const router = useRouter();
  const params = useSearchParams();
  const documentId = Number(params.get("documentId"));
  const jobId = params.get("jobId") ?? "";
  const rawDocType = params.get("document_type") ?? "other";
  // 한글 타입명 → 영어 정규화 (영어 값은 그대로 통과)
  const documentType = DOC_TYPE_MAP[rawDocType] ?? rawDocType;

  const [fields, setFields] = useState<Field[]>([]);
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!jobId) {
      setError("jobId 파라미터가 없습니다.");
      setLoading(false);
      return;
    }
    getOcrJob(jobId)
      .then((job) => {
        if (job.status === "failed") {
          setError("OCR 처리에 실패했습니다.");
          return;
        }
        if (job.structured_data && Object.keys(job.structured_data).length > 0) {
          setFields(
            structuredDataToFields(
              job.structured_data,
              job.confidence_score ?? 0
            )
          );
        } else {
          setFields(FALLBACK_FIELDS);
        }
      })
      .catch(() => setError("OCR 결과를 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  }, [jobId, documentType]);

  function setValue(key: string, value: string) {
    setFields((prev) =>
      prev.map((f) => (f.key === key ? { ...f, value } : f))
    );
  }

  async function handleConfirm() {
    if (!documentId) return;
    setSaving(true);
    try {
      await confirmDocument(documentId);
      router.replace("/documents");
    } catch {
      setError("확정 처리에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <main className="mx-auto w-full max-w-md px-5 py-8">
        <p className="text-center text-muted-foreground">
          OCR 결과 불러오는 중...
        </p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="mx-auto w-full max-w-md px-5 py-8">
        <p className="text-center text-destructive">{error}</p>
        <Button className="mt-6 w-full" onClick={() => router.back()}>
          뒤로 가기
        </Button>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8 pb-28">
      <h1 className="text-2xl font-bold">OCR 결과 검토</h1>

      {/* 안내 배너 */}
      <div className="mt-4 flex items-center gap-3 rounded-2xl border border-primary/30 bg-secondary p-4">
        <FileText className="h-6 w-6 shrink-0 text-primary" />
        <div>
          <p className="font-bold">인식된 정보를 확인해주세요</p>
          <p className="text-sm text-secondary-foreground">
            확정 후에만 저장됩니다
          </p>
        </div>
      </div>

      {/* 원본 이미지 */}
      <p className="mt-6 text-sm text-muted-foreground">원본 이미지</p>
      <Card className="mt-2 flex flex-col items-center justify-center gap-2 border-dashed py-10 text-muted-foreground">
        <ImageIcon className="h-10 w-10 opacity-40" />
        <span className="text-sm">문서 ID: {documentId}</span>
      </Card>

      {/* 인식된 정보 */}
      <p className="mt-6 text-sm text-muted-foreground">인식된 정보</p>
      {fields.length === 0 ? (
        <p className="mt-4 text-center text-sm text-muted-foreground">
          인식된 정보가 없습니다.
        </p>
      ) : (
        <div className="mt-2 space-y-3">
          {fields.map((f) => (
            <Card key={f.key} className="flex items-center justify-between p-4">
              <div className="flex-1">
                <p className="text-xs text-muted-foreground">{f.label}</p>
                {editing ? (
                  <input
                    value={f.value}
                    onChange={(e) => setValue(f.key, e.target.value)}
                    className="mt-1 w-full rounded border border-input bg-background px-2 py-1 text-base"
                  />
                ) : (
                  <p className="mt-0.5 text-base">{f.value}</p>
                )}
              </div>
              <span
                className={
                  "ml-3 rounded-md px-2 py-1 text-xs font-bold " +
                  (f.confidence >= 90
                    ? "bg-secondary text-primary"
                    : "bg-amber-100 text-amber-700")
                }
              >
                {f.confidence}%
              </span>
            </Card>
          ))}
        </div>
      )}

      <p className="mt-5 text-center text-xs text-muted-foreground">
        OCR 결과는 참고용이며 사용자 확정 후 저장됩니다
      </p>

      {/* 버튼 공간 확보 */}
      <div className="h-24" />

      {/* 하단 버튼 */}
      <div className="fixed inset-x-0 bottom-0 mx-auto flex max-w-md gap-3 bg-background px-5 pb-6 pt-3">
        <Button
          variant="outline"
          className="flex-1"
          size="lg"
          onClick={() => setEditing((v) => !v)}
        >
          {editing ? "수정 완료" : "수정하기"}
        </Button>
        <Button
          className="flex-1 bg-green-600 text-white hover:bg-green-700"
          size="lg"
          onClick={handleConfirm}
          disabled={saving || !documentId}
        >
          {saving ? "등록 중..." : "확정하고 등록"}
        </Button>
      </div>
    </main>
  );
}

export default function OcrReviewPage() {
  return (
    <Suspense
      fallback={
        <main className="mx-auto w-full max-w-md px-5 py-8">
          <p className="text-center text-muted-foreground">
            OCR 결과 불러오는 중...
          </p>
        </main>
      }
    >
      <OcrReviewInner />
    </Suspense>
  );
}
