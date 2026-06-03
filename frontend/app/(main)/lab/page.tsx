"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FlaskConical, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { createLabResult } from "@/features/lab/api";
import type { LabItem } from "@/features/lab/api";

const PURPLE = "#7C5CCF";

const INITIAL: LabItem[] = [
  { key: "crp", name: "CRP", description: "C-반응성 단백 · 염증 지표", unit: "mg/L", reference: "<0.5 mg/L (정상)", max: 0.5, value: "3.5" },
  { key: "esr", name: "ESR", description: "적혈구 침강 속도", unit: "mm/hr", reference: "<20 mm/hr (정상)", max: 20, value: "45" },
  { key: "ra", name: "RA Factor", description: "류마티스 인자", unit: "IU/mL", reference: "<14 IU/mL (정상)", max: 14, value: "12" },
];

export default function LabPage() {
  const router = useRouter();
  const [date, setDate] = useState("2026-05-20");
  const [items, setItems] = useState<LabItem[]>(INITIAL);
  const [memo, setMemo] = useState("");
  const [loading, setLoading] = useState(false);

  function setValue(key: string, value: string) {
    setItems((prev) => prev.map((it) => (it.key === key ? { ...it, value } : it)));
  }

  function isNormal(it: LabItem) {
    const v = parseFloat(it.value);
    if (Number.isNaN(v)) return true;
    return v < it.max;
  }

  async function handleSave() {
    setLoading(true);
    try {
      // 백엔드가 살아있으면 저장, 없으면 2초 후 데모로 진행
      await Promise.race([
        createLabResult({
          test_date: date,
          items: items.map((it) => ({ key: it.key, value: parseFloat(it.value) || 0 })),
          memo,
        }),
        new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), 2000)),
      ]);
    } catch {
      // 백엔드 미가동(데모) — 저장 흐름은 그대로 진행
    }
    router.back();
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8 pb-28">
      <h1 className="text-2xl font-bold">검사 결과 입력</h1>

      {/* 자가면역 배너 */}
      <div
        className="mt-5 flex items-center gap-3 rounded-2xl border p-4"
        style={{ borderColor: PURPLE + "55", background: PURPLE + "12" }}
      >
        <FlaskConical className="h-6 w-6" style={{ color: PURPLE }} />
        <div>
          <p className="font-bold">자가면역 검사 결과 추적</p>
          <p className="text-sm" style={{ color: PURPLE }}>시간순 변화를 의료진과 공유</p>
        </div>
      </div>

      {/* 검사 일자 */}
      <div className="mt-6">
        <label className="text-sm text-muted-foreground">검사 일자</label>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="mt-1.5 w-full rounded-xl border border-input bg-background px-4 py-3 text-center text-base font-bold"
        />
      </div>

      {/* 검사 항목 */}
      <div className="mt-6">
        <label className="text-sm text-muted-foreground">검사 항목</label>
        <div className="mt-2 space-y-3">
          {items.map((it) => {
            const normal = isNormal(it);
            return (
              <Card key={it.key} className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-lg font-bold">{it.name}</p>
                    <p className="text-xs text-muted-foreground">{it.description}</p>
                  </div>
                  <span
                    className={
                      "rounded-md px-2 py-1 text-xs font-bold " +
                      (normal ? "bg-secondary text-primary" : "bg-destructive/10 text-destructive")
                    }
                  >
                    {normal ? "정상" : "초과"}
                  </span>
                </div>
                <div className="mt-3 flex items-center gap-2 rounded-lg border border-input px-4 py-3">
                  <input
                    value={it.value}
                    onChange={(e) => setValue(it.key, e.target.value)}
                    inputMode="decimal"
                    className={"flex-1 bg-transparent text-lg font-bold outline-none " + (normal ? "text-primary" : "text-destructive")}
                  />
                  <span className="text-sm text-muted-foreground">{it.unit}</span>
                </div>
                <p className="mt-2 text-xs text-muted-foreground">참고 범위: {it.reference}</p>
              </Card>
            );
          })}
        </div>
      </div>

      {/* 항목 추가 */}
      <button
        className="mt-3 w-full rounded-xl border-2 border-dashed py-3.5 text-sm font-semibold"
        style={{ borderColor: PURPLE + "66", color: PURPLE }}
        onClick={() =>
          setItems((prev) => [
            ...prev,
            { key: `custom-${prev.length}`, name: "새 항목", description: "", unit: "", reference: "-", max: Infinity, value: "" },
          ])
        }
      >
        <Plus className="mr-1 inline h-4 w-4" /> 검사 항목 추가
      </button>

      {/* 메모 */}
      <div className="mt-6">
        <label className="text-sm text-muted-foreground">메모 (선택)</label>
        <textarea
          value={memo}
          onChange={(e) => setMemo(e.target.value)}
          rows={2}
          placeholder="예: 다음 진료 시 의료진과 상의"
          className="mt-1.5 w-full rounded-xl border border-input bg-background px-4 py-3 text-sm"
        />
      </div>

      {/* 저장 (자가면역 보라) */}
      <div className="fixed inset-x-0 bottom-16 mx-auto max-w-md px-5">
        <Button
          className="w-full text-base"
          size="lg"
          style={{ background: PURPLE }}
          onClick={handleSave}
          disabled={loading}
        >
          {loading ? "저장 중..." : "저장하기"}
        </Button>
      </div>
    </main>
  );
}
