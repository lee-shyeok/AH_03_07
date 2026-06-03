"use client";

import { ScanLine } from "lucide-react";
import { Card } from "@/components/ui/card";
import { useRecognitions } from "@/features/pills/queries";

export default function PillsPage() {
  const { data: items = [], isLoading } = useRecognitions();

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-10">
      <h1 className="text-2xl font-bold">약품 인식 내역</h1>

      {isLoading ? (
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
