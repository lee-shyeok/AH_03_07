"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, TrendingUp } from "lucide-react";
import { Card } from "@/components/ui/card";
import { getActivityLog, type ActivityLogResponse } from "@/features/activity/api";

const PURPLE = "#7C5CCF";

function todayStr(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function formatDisplay(dateStr: string): string {
  return dateStr.replace(/-/g, ".");
}

function addDays(dateStr: string, delta: number): string {
  const d = new Date(dateStr);
  d.setDate(d.getDate() + delta);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function Bar({ value, max = 10 }: { value: number; max?: number }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
      <div
        className="h-full rounded-full"
        style={{ width: `${(value / max) * 100}%`, background: PURPLE + "99" }}
      />
    </div>
  );
}

function avg(log: ActivityLogResponse) {
  return ((log.pain_vas + log.fatigue + log.daily_difficulty) / 3).toFixed(1);
}

export default function ActivityViewPage() {
  const router = useRouter();
  const [logDate, setLogDate] = useState(todayStr());
  const [log, setLog] = useState<ActivityLogResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    getActivityLog(logDate)
      .then(setLog)
      .finally(() => setLoading(false));
  }, [logDate]);

  return (
    <main className="mx-auto w-full max-w-md px-5 pb-28 pt-6">
      {/* 헤더 */}
      <div className="flex items-center gap-2">
        <button onClick={() => router.back()} aria-label="뒤로가기">
          <ChevronLeft className="h-6 w-6" />
        </button>
        <h1 className="text-xl font-bold">활성도 기록</h1>
        <button
          onClick={() => router.push("/activity/trend")}
          className="ml-auto flex items-center gap-1 text-sm font-semibold"
          style={{ color: PURPLE }}
        >
          <TrendingUp className="h-4 w-4" /> 추이
        </button>
      </div>

      {/* 날짜 네비 */}
      <Card className="mt-4 flex items-center justify-between p-4">
        <button
          aria-label="이전"
          className="text-xl text-muted-foreground"
          onClick={() => setLogDate((d) => addDays(d, -1))}
        >
          ‹
        </button>
        <span className="font-bold" style={{ color: PURPLE }}>
          {formatDisplay(logDate)}
        </span>
        <button
          aria-label="다음"
          className="text-xl text-muted-foreground"
          onClick={() => setLogDate((d) => addDays(d, 1))}
          disabled={logDate >= todayStr()}
        >
          ›
        </button>
      </Card>

      {loading && (
        <p className="mt-6 text-center text-sm text-muted-foreground">불러오는 중...</p>
      )}

      {!loading && !log && (
        <div className="mt-10 text-center">
          <p className="text-muted-foreground">이 날의 활성도 기록이 없어요.</p>
          <button
            onClick={() => router.push(`/activity/new?date=${logDate}`)}
            className="mt-4 rounded-xl px-6 py-3 font-bold text-white"
            style={{ background: PURPLE }}
          >
            기록하기
          </button>
        </div>
      )}

      {!loading && log && (
        <>
          {/* 평균 활성도 */}
          <Card className="mt-4 p-5 text-center">
            <p className="text-sm text-muted-foreground">평균 활성도</p>
            <p className="mt-1 text-3xl font-extrabold" style={{ color: PURPLE }}>
              {avg(log)}
              <span className="text-base font-normal text-muted-foreground">/10</span>
            </p>
            <div className="mt-3">
              <Bar value={parseFloat(avg(log))} />
            </div>
          </Card>

          {/* 지표별 기록 */}
          <p className="mt-6 text-sm font-semibold text-muted-foreground">지표별 기록</p>
          <div className="mt-2 flex flex-col gap-3">
            {[
              { label: "통증", value: log.pain_vas, max: 10 },
              { label: "피로", value: log.fatigue, max: 10 },
              {
                label: "아침 강직",
                value: log.morning_stiffness_minutes ?? 0,
                max: 120,
                unit: "분",
              },
              { label: "일상 불편도", value: log.daily_difficulty, max: 10 },
            ].map((m) => (
              <Card key={m.label} className="p-4">
                <div className="flex items-center justify-between">
                  <span className="font-semibold">{m.label}</span>
                  <span className="text-sm font-bold" style={{ color: PURPLE }}>
                    {m.value}
                    {m.unit ? m.unit : "/10"}
                  </span>
                </div>
                <div className="mt-2">
                  <Bar value={m.value} max={m.max} />
                </div>
              </Card>
            ))}
          </div>

              {/* 관절 부종 부위 */}
              {log.joint_swelling_areas && log.joint_swelling_areas.length > 0 && (
                <>
                  <p className="mt-6 text-sm font-semibold text-muted-foreground">관절 부종 부위</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {log.joint_swelling_areas.map((area) => (
                      <span
                        key={area}
                        className="rounded-full px-3 py-1.5 text-sm"
                        style={{ background: PURPLE + "1A", color: PURPLE }}
                      >
                        {area}
                      </span>
                    ))}
                  </div>
                </>
              )}

          {/* 메모 */}
          {log.free_memo && (
            <>
              <p className="mt-6 text-sm font-semibold text-muted-foreground">메모</p>
              <Card className="mt-2 p-4 text-sm text-muted-foreground">{log.free_memo}</Card>
            </>
          )}

          {/* 수정 버튼 */}
          <div className="fixed inset-x-0 bottom-16 mx-auto max-w-md px-5">
            <button
              onClick={() => router.push(`/activity/new?date=${logDate}`)}
              className="w-full rounded-xl py-3.5 font-bold text-white"
              style={{ background: PURPLE }}
            >
              수정하기
            </button>
          </div>
        </>
      )}
    </main>
  );
}
