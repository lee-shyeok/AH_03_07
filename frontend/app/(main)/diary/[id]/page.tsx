"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { ChevronLeft } from "lucide-react";
import { Card } from "@/components/ui/card";
import { getDiaryLogs, type DiaryLog } from "@/features/diary/api";

const CONDITION_DISPLAY: Record<string, { emoji: string; label: string; color: string }> = {
  good:   { emoji: "😊", label: "좋음",   color: "text-primary" },
  normal: { emoji: "😐", label: "보통",   color: "text-amber-500" },
  bad:    { emoji: "😟", label: "안좋음", color: "text-destructive" },
  GOOD:   { emoji: "😊", label: "좋음",   color: "text-primary" },
  NORMAL: { emoji: "😐", label: "보통",   color: "text-amber-500" },
  BAD:    { emoji: "😟", label: "안좋음", color: "text-destructive" },
};

function formatDate(dateStr: string) {
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return "-";
  return `${d.getFullYear()}년 ${d.getMonth() + 1}월 ${d.getDate()}일`;
}

export default function DiaryDetailPage() {
  const router = useRouter();
  const { id } = useParams<{ id: string }>();
  const [log, setLog] = useState<DiaryLog | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDiaryLogs()
      .then((data) => {
        const found = data.find((l) => String(l.id) === id) ?? null;
        setLog(found);
      })
      .catch(() => setLog(null))
      .finally(() => setLoading(false));
  }, [id]);

  const condKey = log?.condition ?? log?.overall_condition ?? "normal";
  const cond = CONDITION_DISPLAY[condKey] ?? CONDITION_DISPLAY.normal;
  const dateStr = log?.log_date ?? log?.recorded_at ?? "";
  const noteStr = log?.note ?? log?.memo;

  return (
    <main className="mx-auto w-full max-w-md px-5 py-6 pb-32">
      <div className="flex items-center gap-2">
        <button onClick={() => router.push("/diary")} className="rounded-full p-1 hover:bg-accent">
          <ChevronLeft className="h-5 w-5" />
        </button>
        <h1 className="text-lg font-bold">일기 상세</h1>
      </div>

      {loading && (
        <p className="mt-8 text-center text-sm text-muted-foreground">불러오는 중...</p>
      )}
      {!loading && !log && (
        <p className="mt-8 text-center text-sm text-muted-foreground">기록을 찾을 수 없어요.</p>
      )}
      {!loading && log && (
        <div className="mt-4 flex flex-col gap-3">
          {/* 날짜 + 컨디션 */}
          <Card className="p-4">
            <p className="text-xs text-muted-foreground">{dateStr ? formatDate(dateStr) : "-"}</p>
            <div className="mt-2 flex items-center gap-3">
              <span className="text-4xl">{cond.emoji}</span>
              <p className={`text-lg font-bold ${cond.color}`}>{cond.label}</p>
            </div>
          </Card>

          {/* 아픈 부위 */}
          {log.body_parts && log.body_parts.length > 0 && (
            <Card className="p-4">
              <p className="mb-2 text-xs font-semibold text-muted-foreground">아픈 부위</p>
              <div className="flex flex-wrap gap-2">
                {log.body_parts.map((part) => (
                  <span
                    key={part}
                    className="rounded-full bg-accent px-3 py-1 text-xs font-medium"
                  >
                    {part}
                  </span>
                ))}
              </div>
            </Card>
          )}

          {/* 느낌 */}
          {log.feelings && log.feelings.length > 0 && (
            <Card className="p-4">
              <p className="mb-2 text-xs font-semibold text-muted-foreground">느낌</p>
              <div className="flex flex-wrap gap-2">
                {log.feelings.map((f) => (
                  <span
                    key={f}
                    className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary"
                  >
                    {f}
                  </span>
                ))}
              </div>
            </Card>
          )}

          {/* 메모 */}
          {noteStr && (
            <Card className="p-4">
              <p className="mb-1 text-xs font-semibold text-muted-foreground">메모</p>
              <p className="text-sm leading-relaxed">{noteStr}</p>
            </Card>
          )}
        </div>
      )}
    </main>
  );
}