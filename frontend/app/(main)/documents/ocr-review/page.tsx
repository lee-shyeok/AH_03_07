"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { FileText, ImageIcon, ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { getOcrJob, confirmDocument, uploadDocument, startOcrJob, type MedicationItem } from "@/features/documents/api";

// ─── Types ────────────────────────────────────────────────────────────────────

interface Field {
  key: string;
  label: string;
  value: string;
  confidence: number;
}

const FALLBACK_FIELDS: Field[] = [
  { key: "visit_date", label: "진료일", value: "2026.5.20", confidence: 98 },
  { key: "hospital", label: "병원명", value: "서울대학교병원 내과", confidence: 95 },
  { key: "diagnosis", label: "진단명", value: "위염", confidence: 88 },
  { key: "medication", label: "처방 약물", value: "라베프라졸 10mg", confidence: 92 },
];

const MEDICATION_LABELS: Record<keyof MedicationItem, string> = {
  drug_name_user_input: "약품명",
  dosage: "용량",
  frequency: "복용 횟수",
  duration_days: "기간(일)",
  drug_category: "약물 분류",
};

// ─── Inner page ───────────────────────────────────────────────────────────────

function OcrReviewInner() {
  const router = useRouter();
  const params = useSearchParams();
  const documentId = Number(params.get("documentId"));
  const jobId = params.get("jobId") ?? "";

  const [localDocumentId, setLocalDocumentId] = useState(documentId);
  const [localJobId, setLocalJobId] = useState(jobId);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [medications, setMedications] = useState<MedicationItem[]>([]);
  const [fields, setFields] = useState<Field[]>([]);
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setUploading(true);
    setError(null);
    try {
      const docType = params.get("document_type") ?? "prescription";
      const doc = await uploadDocument(file, docType);
      const job = await startOcrJob(doc.id);
      setLocalDocumentId(doc.id);
      setLocalJobId(job.job_id);
      setLoading(true);
    } catch {
      setError("파일 업로드에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setUploading(false);
    }
  }

  useEffect(() => {
      if (!localJobId) {
          setFields(FALLBACK_FIELDS);
          setLoading(false);
          return;
      }
      const poll = setInterval(async () => {
          try {
              const job = await getOcrJob(String(localJobId), localDocumentId);
              if (job.status === "completed") {
                  clearInterval(poll);
                  if (Array.isArray(job.structured_data) && job.structured_data.length > 0) {
                      setMedications(job.structured_data as MedicationItem[]);
                  } else if (job.raw_text) {
                      const lines = job.raw_text.split("\n").filter(Boolean);
                      setFields(lines.map((line, i) => ({
                          key: String(i),
                          label: String(i + 1),
                          value: line,
                          confidence: Math.round((job.confidence_score ?? 0) * 100),
                      })));
                  } else {
                      setFields(FALLBACK_FIELDS);
                  }
                  setLoading(false);
              } else if (job.status === "failed") {
                  clearInterval(poll);
                  setError("OCR 처리에 실패했습니다.");
                  setLoading(false);
              }
          } catch {
              clearInterval(poll);
              setError("OCR 결과를 불러오지 못했습니다.");
              setLoading(false);
          }
      }, 2000);

      return () => clearInterval(poll);
  }, [localJobId]);

  function setValue(key: string, value: string) {
    setFields((prev) =>
      prev.map((f) => (f.key === key ? { ...f, value } : f))
    );
  }

  async function handleConfirm() {
    if (!localDocumentId) return;
    setSaving(true);
    try {
      await confirmDocument(localDocumentId);
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
    <main className="mx-auto w-full max-w-md px-5 pt-6 pb-10">
      <button
        onClick={() => router.back()}
        className="mb-2 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        aria-label="뒤로 가기"
      >
        <ChevronLeft className="h-4 w-4" />
        뒤로 가기
      </button>
      <h1 className="text-2xl font-bold">OCR 결과 검토</h1>

      {/* 안내 배너 */}
      <div className="mt-4 flex items-center gap-3 rounded-2xl border border-primary/30 bg-secondary p-4">
        <FileText className="h-6 w-6 text-primary" />
        <div>
          <p className="font-bold">인식된 정보를 확인해주세요</p>
          <p className="text-sm text-secondary-foreground">
            확정 후에만 저장됩니다
          </p>
        </div>
      </div>

      {/* 원본 이미지 */}
      <p className="mt-5 text-sm text-muted-foreground">원본 이미지</p>
      <label className="block cursor-pointer">
        <input
          type="file"
          accept="image/*,application/pdf"
          className="sr-only"
          onChange={handleFileChange}
          disabled={uploading}
        />
        <Card className="mt-2 flex flex-col items-center justify-center gap-2 border-dashed py-10 text-muted-foreground hover:bg-accent transition-colors">
          {previewUrl && selectedFile?.type.startsWith("image/") ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={previewUrl} alt="업로드된 이미지" className="max-h-40 rounded-lg object-contain" />
          ) : (
            <ImageIcon className="h-10 w-10 opacity-40" />
          )}
          <span className="text-sm">
            {uploading
              ? "업로드 중..."
              : selectedFile
              ? selectedFile.name
              : "이미지 또는 PDF를 선택하세요"}
          </span>
          {!selectedFile && (
            <span className="rounded-lg bg-primary px-4 py-1.5 text-xs font-semibold text-primary-foreground">
              파일 선택
            </span>
          )}
        </Card>
      </label>

      {/* 인식된 정보 */}
      <p className="mt-5 text-sm text-muted-foreground">인식된 정보</p>
      {medications.length > 0 ? (
        <div className="mt-2 space-y-3">
          {medications.map((med, idx) => (
            <Card key={idx} className="p-4">
              <p className="mb-2 text-xs font-bold text-primary">약품 {idx + 1}</p>
              {(Object.keys(MEDICATION_LABELS) as (keyof MedicationItem)[]).map((k) => {
                const val = med[k];
                if (val === undefined || val === null) return null;
                return (
                  <div key={k} className="flex justify-between border-b py-1.5 last:border-0">
                    <span className="text-xs text-muted-foreground">{MEDICATION_LABELS[k]}</span>
                    <span className="text-sm font-medium">{String(val)}</span>
                  </div>
                );
              })}
            </Card>
          ))}
        </div>
      ) : fields.length === 0 ? (
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

      <p className="mt-4 text-center text-xs text-muted-foreground">
        OCR 결과는 참고용이며 사용자 확정 후 저장됩니다
      </p>

      {/* 버튼 공간 확보 */}
      <div className="h-24" />

      {/* 버튼 */}
      <div className="fixed inset-x-0 bottom-0 mx-auto flex max-w-md gap-3 px-5 pb-6 pt-3 bg-background">
        {medications.length === 0 && (
          <Button
            variant="outline"
            className="flex-1"
            size="lg"
            onClick={() => setEditing((v) => !v)}
          >
            {editing ? "수정 완료" : "수정하기"}
          </Button>
        )}
        <Button
          className="flex-1 bg-green-600 text-white hover:bg-green-700"
          size="lg"
          onClick={handleConfirm}
          disabled={saving || !localDocumentId || uploading}
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
