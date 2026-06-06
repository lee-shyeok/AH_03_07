"use client";

import { useRouter } from "next/navigation";
import { Bell, ChevronLeft } from "lucide-react";
import { Card } from "@/components/ui/card";
import { useNotifications, useMarkRead } from "@/features/notifications/queries";

function emoji(type?: string) {
  switch (type) {
    case "medication": return "💊";
    case "risk": return "⚠️";
    case "activity": return "📊";
    case "done": return "✅";
    case "guide": return "📋";
    default: return "🔔";
  }
}

function makeDate(offsetDays: number, time: string) {
  const d = new Date();
  d.setDate(d.getDate() - offsetDays);
  const [h, m] = time.split(":").map(Number);
  d.setHours(h, m, 0, 0);
  return d.toISOString();
}

const DUMMY_NOTIFICATIONS = [
  { id: 1, title: "복약 시간", body: "아침약을 복용해주세요", notification_type: "medication", is_read: false, created_at: makeDate(0, "09:00") },
  { id: 2, title: "의료진 확인 신호", body: "통증 점수 패턴 감지", notification_type: "risk", is_read: false, created_at: makeDate(0, "07:00") },
  { id: 3, title: "활성도 기록", body: "오늘 컨디션을 기록해주세요", notification_type: "activity", is_read: true, created_at: makeDate(1, "21:00") },
  { id: 4, title: "약 복용 완료", body: "저녁약 복용 완료", notification_type: "done", is_read: true, created_at: makeDate(1, "19:30") },
];

function dateGroup(isoStr?: string): string {
  if (!isoStr) return "이전";
  const d = new Date(isoStr);
  const now = new Date();
  const yesterday = new Date();
  yesterday.setDate(now.getDate() - 1);
  if (d.toDateString() === now.toDateString()) return "오늘";
  if (d.toDateString() === yesterday.toDateString()) return "어제";
  return d.toLocaleDateString("ko-KR", { month: "long", day: "numeric" });
}

function timeStr(isoStr?: string): string {
  if (!isoStr) return "";
  const d = new Date(isoStr);
  return d.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit", hour12: false });
}

export default function NotificationsPage() {
  const router = useRouter();
  const { data: apiItems = [], isLoading } = useNotifications();
  const markRead = useMarkRead();

  // created_at 없는 항목은 오늘 날짜로 채움
  const rawItems = apiItems.length > 0 ? apiItems : DUMMY_NOTIFICATIONS;
  const items = rawItems.map((n, i) => ({
    ...n,
    created_at: n.created_at ?? new Date(Date.now() - i * 60000).toISOString(),
  }));

  function handleClick(n: typeof items[0]) {
    if (!n.is_read) markRead.mutate(n.id);
    if (n.notification_type === "risk") router.push("/symptom-check");
  }

  const groups = items.reduce((acc, n) => {
    const key = dateGroup(n.created_at);
    if (!acc[key]) acc[key] = [];
    acc[key].push(n);
    return acc;
  }, {} as Record<string, typeof items>);

  const groupKeys = ["오늘", "어제", ...Object.keys(groups).filter((k) => k !== "오늘" && k !== "어제")].filter((k) => groups[k]);

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-6 pb-24">
      <div className="flex items-center gap-2">
        <button onClick={() => router.back()} className="p-1 text-foreground">
          <ChevronLeft className="h-6 w-6" />
        </button>
        <h1 className="text-3xl font-extrabold">알림</h1>
      </div>

      {isLoading ? (
        <p className="mt-8 text-sm text-muted-foreground">불러오는 중...</p>
      ) : (
        <div className="mt-6 space-y-8">
          {groupKeys.map((group) => (
            <div key={group}>
              <h2 className="mb-4 text-sm font-semibold text-muted-foreground">{group}</h2>
              <div className="flex flex-col gap-4">
                {groups[group].map((n) => (
                  <Card
                    key={n.id}
                    onClick={() => handleClick(n)}
                    className={
                      "cursor-pointer rounded-2xl p-4 shadow-sm " +
                      (n.notification_type === "risk"
                        ? "border-2 border-amber-400 bg-amber-50/30"
                        : "border border-border bg-card")
                    }
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-3xl leading-none">{emoji(n.notification_type)}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <p className={"text-base leading-snug " + (n.is_read ? "font-medium text-foreground" : "font-bold text-foreground")}>
                            {n.title}
                          </p>
                          {!n.is_read && (
                            <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-red-500" />
                          )}
                        </div>
                        {n.body && (
                          <p className="mt-1 text-sm text-muted-foreground">{n.body}</p>
                        )}
                        {n.created_at && (
                          <p className="mt-2 text-right text-xs text-muted-foreground">
                            {timeStr(n.created_at)}
                          </p>
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
