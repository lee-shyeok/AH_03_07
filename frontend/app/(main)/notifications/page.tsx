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
  const { data: items = [], isLoading } = useNotifications();
  const markRead = useMarkRead();

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
    <main className="mx-auto w-full max-w-md px-5 pt-6">
      <div className="flex items-center gap-2">
        <button onClick={() => router.back()} className="p-1 text-foreground">
          <ChevronLeft className="h-6 w-6" />
        </button>
        <h1 className="text-2xl font-bold">알림</h1>
      </div>

      {isLoading ? (
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
                    className={"cursor-pointer p-4 " + (n.notification_type === "risk" ? "border-amber-400" : "")}
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">{emoji(n.notification_type)}</span>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <p className={"text-sm " + (n.is_read ? "font-normal" : "font-bold")}>{n.title}</p>
                          {!n.is_read && <span className="ml-2 h-2.5 w-2.5 shrink-0 rounded-full bg-destructive" />}
                        </div>
                        {n.body && <p className="mt-0.5 text-sm text-muted-foreground">{n.body}</p>}
                        {n.created_at && (
                          <p className="mt-2 text-right text-xs text-muted-foreground">{timeStr(n.created_at)}</p>
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
