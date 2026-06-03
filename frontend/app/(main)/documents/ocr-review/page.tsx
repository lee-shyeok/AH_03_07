"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FileText, ImageIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface Field {
  key: string;
  label: string;
  value: string;
  confidence: number;
}

const INITIAL: Field[] = [
  { key: "visit_date", label: "진료일", value: "2026.5.20", confidence: 98 },
  { key: "hospital", label: "병원명", value: "서울대학교병원 내과", confidence: 95 },
  { key: "diagnosis", label: "진단명", value: "위염", confidence: 88 },
  { key: "medication", label: "처방 약물", value: "라베프라졸 10mg", confidence: 92 },
];

export default function OcrReviewPage() {
  const router = useRouter();
  const [fields, setFields] = useState<Field[]>(INITIAL);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  function setValue(key: string, value: string) {
    setFields((prev) => prev.map((f) => (f.key === key ? { ...f, value } : f)));
  }

  async function handleConfirm() {
    setSaving(true);
    // 백엔드: PUT /v1/medical-documents/{id}/confirm
    setTimeout(() => {
      setSaving(false);
      router.replace("/documents");
    }, 600);
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
        <span className="text-sm">진료기록_240517.pdf</span>
      </Card>

      {/* 인식된 정보 */}
      <p className="mt-6 text-sm text-muted-foreground">인식된 정보</p>
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
                (f.confidence >= 90 ? "bg-secondary text-primary" : "bg-amber-100 text-amber-700")
              }
            >
              {f.confidence}%
            </span>
          </Card>
        ))}
      </div>

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
        <Button className="flex-1" size="lg" onClick={handleConfirm} disabled={saving}>
          {saving ? "등록 중..." : "확정하고 등록"}
        </Button>
      </div>
    </main>
  );
}
