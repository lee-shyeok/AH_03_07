"use client";

import Link from "next/link";
import { BookOpen } from "lucide-react";
import { Card } from "@/components/ui/card";
import { useGuides } from "@/features/guides/queries";

export default function GuidesPage() {
  const { data: guides = [], isLoading } = useGuides();

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-10">
      <h1 className="text-2xl font-bold">맞춤 안내문</h1>

      {isLoading ? (
        <p className="mt-8 text-sm text-muted-foreground">불러오는 중...</p>
      ) : guides.length === 0 ? (
        <div className="mt-16 flex flex-col items-center text-muted-foreground">
          <BookOpen className="h-12 w-12 opacity-30" />
          <p className="mt-3 text-sm">생성된 안내문이 없습니다.</p>
          <p className="mt-1 text-xs">진료기록에서 안내문을 생성해보세요.</p>
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {guides.map((g) => (
            <Link key={g.id} href={`/guides/${g.id}`}>
              <Card className="p-4 hover:bg-accent">
                <div className="flex items-center justify-between">
                  <span className="font-bold">맞춤 건강 안내문</span>
                  {g.status && (
                    <span className="rounded bg-secondary px-2 py-0.5 text-[11px] font-bold text-secondary-foreground">
                      {g.status}
                    </span>
                  )}
                </div>
                {g.symptom_summary && (
                  <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">
                    {g.symptom_summary}
                  </p>
                )}
                {g.created_at && (
                  <p className="mt-2 text-xs text-muted-foreground">
                    {g.created_at.slice(0, 10)}
                  </p>
                )}
              </Card>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
