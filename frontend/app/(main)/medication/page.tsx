"use client";

import Link from "next/link";
import { Pill, Plus } from "lucide-react";
import { Card } from "@/components/ui/card";
import { useMedications } from "@/features/medication/queries";

export default function MedicationPage() {
  const { data: meds = [], isLoading } = useMedications();

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">내 약물 목록</h1>
        <Link
          href="/medication/new"
          className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground"
          aria-label="약 등록"
        >
          <Plus className="h-5 w-5" />
        </Link>
      </div>
      <p className="mt-1 text-sm text-muted-foreground">복용 중인 약 {meds.length}개</p>

      {isLoading ? (
        <p className="mt-8 text-sm text-muted-foreground">불러오는 중...</p>
      ) : meds.length === 0 ? (
        <div className="mt-16 flex flex-col items-center text-muted-foreground">
          <Pill className="h-12 w-12 opacity-30" />
          <p className="mt-3 text-sm">등록된 약물이 없습니다.</p>
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {meds.map((m) => (
            <Link key={m.id} href={`/medication/${m.id}`}>
              <Card className="flex items-center gap-3 p-4 hover:bg-accent">
                <Pill className="h-7 w-7 text-primary" />
                <div className="flex-1">
                  <p className="font-semibold">{m.name}</p>
                  {m.frequency && (
                    <p className="text-xs text-muted-foreground">{m.frequency}</p>
                  )}
                  {m.next_dose && (
                    <p className="text-xs text-muted-foreground">다음 복용: {m.next_dose}</p>
                  )}
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
