"use client";

import { useEffect, useState } from "react";
import { Bell } from "lucide-react";
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

// 백엔드 미가동 시 보여줄 예시 알림(데모)
const DUMMY: AppNotification[] = [
  { id: 1, title: "복약 시간이에요 💊", body: "오후 약(MTX) 복용할 시간입니다.", notification_type: "medication", is_read: false },
  { id: 2, title: "활성도 점검 알림", body: "이번 주 활성도를 기록해주세요.", notification_type: "activity", is_read: false },
  { id: 3, title: "고위험 신호 감지", body: "최근 CRP 수치가 참고 범위를 초과했어요. 의료진 상담을 권장합니다.", notification_type: "risk", is_read: false },
  { id: 4, title: "새 맞춤 안내문 도착", body: "여름철 자외선 관리 가이드가 도착했어요.", notification_type: "guide", is_read: true },
  { id: 5, title: "출석체크 완료", body: "오늘도 건강 관리 성공! +10P 적립되었습니다.", notification_type: "done", is_read: true },
];

export default function NotificationsPage() {
  const [items, setItems] = useState<AppNotification[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 백엔드가 살아있으면 실데이터, 없으면 2초 후 예시 알림 표시
    Promise.race([
      getNotifications(),
      new Promise<AppNotification[]>((_, reject) => setTimeout(() => reject(new Error("timeout")), 2000)),
    ])
      .then((data) => setItems(data.length ? data : DUMMY))
      .catch(() => setItems(DUMMY))
      .finally(() => setLoading(false));
  }, []);

  async function handleClick(n: AppNotification) {
    if (n.is_read) return;
    try {
      await markRead(n.id);
      setItems((prev) =>
        prev.map((x) => (x.id === n.id ? { ...x, is_read: true } : x))
      );
    } catch {
      /* no-op */
    }
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-10">
      <h1 className="text-3xl font-bold">알림</h1>

      {loading ? (
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
              onClick={() => handleClick(n)}
              className={
                "cursor-pointer p-4 " +
                (n.notification_type === "risk" ? "border-amber-400" : "")
              }
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl">{emoji(n.notification_type)}</span>
                <div className="flex-1">
                  <p className={"text-sm " + (n.is_read ? "font-normal" : "font-bold")}>
                    {n.title}
                  </p>
                  {n.body && (
                    <p className="mt-0.5 text-sm text-muted-foreground">{n.body}</p>
                  )}
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
