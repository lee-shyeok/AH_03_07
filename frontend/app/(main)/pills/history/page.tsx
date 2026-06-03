"use client";

import { useEffect, useState } from "react";
import { ScanLine } from "lucide-react";
import { Card } from "@/components/ui/card";
import { getRecognitions } from "@/features/pills/api";
import type { PillRecognition } from "@/features/pills/api";

// 백엔드 미가동 시 보여줄 예시 인식 내역(데모)
const DUMMY: PillRecognition[] = [
  { id: 1, drug_name: "타이레놀정 500mg", confidence: 0.97 },
  { id: 2, drug_name: "아스피린프로텍트정 100mg", confidence: 0.91 },
  { id: 3, drug_name: "리리카캡슐 75mg", confidence: 0.84 },
];

export default function PillsPage() {
  const [items, setItems] = useState<PillRecognition[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 백엔드가 살아있으면 실데이터, 없으면 2초 후 예시 표시
    Promise.race([
      getRecognitions(),
      new Promise<PillRecognition[]>((_, reject) => setTimeout(() => reject(new Error("timeout")), 2000)),
    ])
      .then((data) => setItems(data.length ? data : DUMMY))
      .catch(() => setItems(DUMMY))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-10">
      <h1 className="text-2xl font-bold">약품 인식 내역</h1>

      {loading ? (
        <p className="mt-8 text-sm text-muted-foreground">불러오는 중...</p>
      ) : items.length === 0 ? (
        <div className="mt-16 flex flex-col items-center text-muted-foreground">
          <ScanLine className="h-12 w-12 opacity-30" />
          <p className="mt-3 text-sm">인식 내역이 없습니다.</p>
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {items.map((p) => (
            <Card key={p.id} className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <ScanLine className="h-6 w-6 text-primary" />
                <span className="font-semibold">{p.drug_name ?? "약품"}</span>
              </div>
              {typeof p.confidence === "number" && (
                <span className="rounded-full bg-secondary px-2.5 py-1 text-xs font-bold text-secondary-foreground">
                  {Math.round(p.confidence * 100)}%
                </span>
              )}
            </Card>
          ))}
        </div>
      )}
    </main>
  );
}
