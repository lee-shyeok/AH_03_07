"use client";

import { Bell } from "lucide-react";
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

export default function NotificationsPage() {
  const { data: items = [], isLoading } = useNotifications();
  const markRead = useMarkRead();

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-10">
      <h1 className="text-3xl font-bold">알림</h1>

      {isLoading ? (
        <p className="mt-8 text-sm text-muted-foreground">불러오는 중...</p>
      ) : items.length === 0 ? (
        <div className="mt-16 flex flex-col items-center text-muted-foreground">
          <Bell className="h-12 w-12 opacity-30" />
          <p className="mt-3 text-sm">알림이 없습니다.</p>
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {items.map((n) => (
            <Card
              key={n.id}
              onClick={() => !n.is_read && markRead.mutate(n.id)}
              className={"cursor-pointer p-4 " + (n.notification_type === "risk" ? "border-amber-400" : "")}
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl">{emoji(n.notification_type)}</span>
                <div className="flex-1">
                  <p className={"text-sm " + (n.is_read ? "font-normal" : "font-bold")}>{n.title}</p>
                  {n.body && <p className="mt-0.5 text-sm text-muted-foreground">{n.body}</p>}
                </div>
                {!n.is_read && <span className="mt-1 h-2.5 w-2.5 rounded-full bg-destructive" />}
              </div>
            </Card>
          ))}
        </div>
      )}
    </main>
  );
}
