"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Bell, ChevronLeft } from "lucide-react";
import { Card } from "@/components/ui/card";
import { getNotifications, markRead } from "@/features/notifications/api";
import type { AppNotification } from "@/features/notifications/api";

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

const DUMMY: AppNotification[] = [
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
  const [items, setItems] = useState<AppNotification[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.race([
      getNotifications(),
      new Promise<AppNotification[]>((_, reject) => setTimeout(() => reject(new Error("timeout")), 2000)),
    ])
      .then((data) => setItems(data.length ? data : DUMMY))
      .catch(() => setItems(DUMMY))
      .finally(() => setLoading(false));
  }, []);

  async function handleClick(n: AppNotification) {
    if (!n.is_read) {
      try {
        await markRead(n.id);
        setItems((prev) =>
          prev.map((x) => (x.id === n.id ? { ...x, is_read: true } : x))
        );
      } catch {
        /* no-op */
      }
    }
    if (n.notification_type === "risk") {
      router.push("/symptom-check");
    }
  }

  const groups = items.reduce((acc, n) => {
    const key = dateGroup(n.created_at);
    if (!acc[key]) acc[key] = [];
    acc[key].push(n);
    return acc;
  }, {} as Record<string, AppNotification[]>);

  const groupKeys = ["오늘", "어제", ...Object.keys(groups).filter((k) => k !== "오늘" && k !== "어제")].filter((k) => groups[k]);

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-6">
      <div className="flex items-center gap-2">
        <button onClick={() => router.back()} className="p-1 text-foreground">
          <ChevronLeft className="h-6 w-6" />
        </button>
        <h1 className="text-2xl font-bold">알림</h1>
      </div>

      {loading ? (
        <p className="mt-8 text-sm text-muted-foreground">불러오는 중...</p>
      ) : items.length === 0 ? (
        <div className="mt-16 flex flex-col items-center text-muted-foreground">
          <Bell className="h-12 w-12 opacity-30" />
          <p className="mt-3 text-sm">알림이 없습니다.</p>
        </div>
      ) : (
        <div className="mt-6 space-y-6">
          {groupKeys.map((group) => (
            <div key={group}>
              <h2 className="mb-3 text-sm font-semibold text-muted-foreground">{group}</h2>
              <div className="space-y-3">
                {groups[group].map((n) => (
                  <Card
                    key={n.id}
                    onClick={() => handleClick(n)}
                    className={
                      "cursor-pointer p-4 " +
                      (n.notification_type === "risk" ? "border-amber-400" : "")
                    }
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">{emoji(n.notification_type)}</span>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <p className={"text-sm " + (n.is_read ? "font-normal" : "font-bold")}>
                            {n.title}
                          </p>
                          {!n.is_read && <span className="ml-2 h-2.5 w-2.5 shrink-0 rounded-full bg-destructive" />}
                        </div>
                        {n.body && (
                          <p className="mt-0.5 text-sm text-muted-foreground">{n.body}</p>
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
