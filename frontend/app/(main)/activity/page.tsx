"use client";

import { useRouter } from "next/navigation";
import { Calendar, ArrowLeft, ArrowRight } from "lucide-react";
import { Card } from "@/components/ui/card";

const PURPLE = "#7C5CCF";
const METRICS = [
  { label: "통증", value: 5 },
  { label: "피로", value: 6 },
  { label: "강직", value: 4 },
  { label: "불편도", value: 7 },
];

function Bar({ value, color = PURPLE }: { value: number; color?: string }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
      <div className="h-full rounded-full" style={{ width: `${value * 10}%`, background: color }} />
    </div>
  );
}

export default function ActivityViewPage() {
  const router = useRouter();

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8 pb-28">
      <h1 className="text-xl font-bold">활성도 기록</h1>

      {/* 날짜 네비 */}
      <Card className="mt-4 flex items-center justify-between p-4">
        <button aria-label="이전"><ArrowLeft className="h-5 w-5 text-muted-foreground" /></button>
        <span className="flex items-center gap-2 font-bold">
          <Calendar className="h-5 w-5" /> 2024.05.17
        </span>
        <button aria-label="다음"><ArrowRight className="h-5 w-5 text-muted-foreground" /></button>
      </Card>

      {/* 평균 활성도 */}
      <Card className="mt-4 p-5 text-center">
        <p className="text-sm text-muted-foreground">평균 활성도</p>
        <p className="mt-1 text-3xl font-extrabold" style={{ color: PURPLE }}>
          5.5<span className="text-base font-normal text-muted-foreground">/10</span>
        </p>
        <div className="mt-3"><Bar value={5.5} color={PURPLE + "99"} /></div>
        <p className="mt-2 text-sm text-muted-foreground">&quot;보통&quot; 컨디션</p>
      </Card>

      {/* 지표별 기록 */}
      <p className="mt-6 text-sm font-semibold text-muted-foreground">지표별 기록</p>
      <div className="mt-2 space-y-3">
        {METRICS.map((m) => (
          <Card key={m.label} className="p-4">
            <div className="flex items-center justify-between">
              <span className="font-semibold">{m.label}</span>
              <span className="text-sm font-bold" style={{ color: PURPLE }}>{m.value}/10</span>
            </div>
            <div className="mt-2"><Bar value={m.value} color={PURPLE + "99"} /></div>
          </Card>
        ))}
      </div>

      {/* 메모 */}
      <p className="mt-6 text-sm text-muted-foreground">메모 (선택)</p>
      <Card className="mt-2 p-4 text-sm text-muted-foreground">
        오늘은 평소보다 컨디션이 좋지 않았습니다. 아침에 통증이 심해서 활동량이 적었어요.
      </Card>

      {/* 수정/삭제 */}
      <div className="fixed inset-x-0 bottom-16 mx-auto flex max-w-md gap-2 px-5">
        <button onClick={() => router.push("/activity/new")} className="flex-1 rounded-xl py-3.5 font-bold text-white" style={{ background: PURPLE }}>
          수정
        </button>
        <button className="flex-1 rounded-xl border-2 border-destructive py-3.5 font-bold text-destructive">
          삭제
        </button>
      </div>
    </main>
  );
}
