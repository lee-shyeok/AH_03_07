"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { FileText, ImageIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { getOcrJob, confirmDocument } from "@/features/documents/api";

interface Field {
  key: string;
  label: string;
  value: string;
  confidence: number;
}

function structuredDataToFields(
  data: Record<string, unknown>,
  score: number
): Field[] {
  return Object.entries(data).map(([key, val]) => ({
    key,
    label: key,
    value: String(val ?? ""),
    confidence: Math.round(score * 100),
  }));
}

function OcrReviewInner() {
  const router = useRouter();
  const params = useSearchParams();
  const documentId = Number(params.get("documentId"));
  const jobId = params.get("jobId") ?? "";

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
        if (job.structured_data) {
          setFields(
            structuredDataToFields(
              job.structured_data,
              job.confidence_score ?? 0
            )
          );
        }
      })
      .catch(() => setError("OCR 결과를 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  }, [jobId]);

  function setValue(key: string, value: string) {
    setFields((prev) => prev.map((f) => (f.key === key ? { ...f, value } : f)));
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
        <p className="text-center text-muted-foreground">OCR 결과 불러오는 중...</p>
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
      <div className="mt-5 flex items-center gap-3 rounded-2xl border border-primary/30 bg-secondary p-4">
        <FileText className="h-6 w-6 text-primary" />
        <div>
          <p className="font-bold">인식된 정보를 확인해주세요</p>
          <p className="text-sm text-secondary-foreground">확정 후에만 저장됩니다</p>
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

      {/* 버튼 */}
      <div className="fixed inset-x-0 bottom-16 mx-auto flex max-w-md gap-2 px-5">
        <Button
          variant="outline"
          className="flex-1"
          size="lg"
          onClick={() => setEditing((v) => !v)}
        >
          {editing ? "수정 완료" : "수정하기"}
        </Button>
        <Button
          className="flex-1"
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
          <p className="text-center text-muted-foreground">OCR 결과 불러오는 중...</p>
        </main>
      }
    >
      <OcrReviewInner />
    </Suspense>
  );
}
