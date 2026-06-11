"use client";

import { useRouter } from "next/navigation";
import { ChevronLeft, Pill, AlertTriangle, BarChart3, CheckCircle2, Bell, BookOpen } from "lucide-react";
import { Card } from "@/components/ui/card";
import { useNotifications, useMarkRead } from "@/features/notifications/queries";
import { type AppNotification } from "@/features/notifications/api";
import { getMode } from "@/features/auth/mode";

const GREEN = "#03C85F";
const PURPLE = "#7C5CCF";

function makeIso(daysAgo: number, hours: number, minutes: number): string {
  const d = new Date();
  d.setDate(d.getDate() - daysAgo);
  d.setHours(hours, minutes, 0, 0);
  return d.toISOString();
}

const FALLBACK_ITEMS: AppNotification[] = [
  { id: 1, title: "복약 시간이에요", body: "아침약 복용해주세요", notification_type: "medication", is_read: false, created_at: makeIso(0, 9, 0) },
  { id: 2, title: "의료진 확인 신호", body: "통증 점수 7점 이상", notification_type: "risk", is_read: false, created_at: makeIso(0, 7, 0) },
  { id: 5, title: "처방 종료 예정", body: "메토트렉세이트 처방이 3일 후 종료됩니다", notification_type: "prescription_end", is_read: false, created_at: makeIso(0, 8, 0) },
  { id: 3, title: "활성도 기록 알림", body: "오늘 컨디션을 기록해주세요", notification_type: "activity", is_read: true, created_at: makeIso(1, 21, 0) },
  { id: 4, title: "약 복용 완료", body: "저녁약 복용 완료", notification_type: "done", is_read: true, created_at: makeIso(1, 19, 30) },
];

function NotifIcon({ type, accent }: { type?: string; accent: string }) {
  const base = "flex h-11 w-11 shrink-0 items-center justify-center rounded-full";
  if (type === "risk") {
    return (
      <div className={base} style={{ background: "#FEF3C720" }}>
        <AlertTriangle className="h-5 w-5 text-amber-500" />
      </div>
    );
  }
  const Icon =
    type === "medication" || type === "prescription_end" || type === "medication_end" ? Pill
    : type === "activity" ? BarChart3
    : type === "done" ? CheckCircle2
    : type === "guide" ? BookOpen
    : Bell;
  return (
    <div className={base} style={{ background: accent + "20" }}>
      <Icon className="h-5 w-5" style={{ color: accent }} />
    </div>
  );
}

function makeDate(offsetDays: number, time: string) {
  const d = new Date();
  d.setDate(d.getDate() - offsetDays);
  const [h, m] = time.split(":").map(Number);
  d.setHours(h, m, 0, 0);
  return d.toISOString();
}

const DUMMY_NOTIFICATIONS: AppNotification[] = [
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
  const markReadMutation = useMarkRead();
  const isAutoimmune = getMode() === "autoimmune";
  const accent = isAutoimmune ? PURPLE : GREEN;

  // 백엔드 데이터에 created_at이 있으면 사용, 없으면 DUMMY로 대체
  const hasProperDates = apiItems.length > 0 && apiItems.some(n => n.created_at);
  const items = hasProperDates ? apiItems : DUMMY_NOTIFICATIONS;

  function handleClick(n: AppNotification) {
    if (!n.is_read) markReadMutation.mutate(n.id);
    switch (n.notification_type) {
      case "risk":         router.push("/symptom-check"); break;
      case "medication":   router.push("/notifications/settings"); break;
      case "prescription_end":
      case "done":         router.push("/medication"); break;
      case "activity":     router.push("/diary"); break;
      case "guide":        router.push("/guides"); break;
    }
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
                    className="cursor-pointer rounded-2xl p-4 shadow-sm transition-colors hover:bg-accent/40"
                    style={
                      n.notification_type === "risk"
                        ? { border: "2px solid #F59E0B", background: "#FFFBEB" }
                        : !n.is_read
                        ? { borderColor: accent + "40", borderWidth: "1.5px" }
                        : undefined
                    }
                  >
                    <div className="flex items-start gap-3">
                      <NotifIcon type={n.notification_type} accent={accent} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <p className={"text-base leading-snug " + (n.is_read ? "font-medium text-muted-foreground" : "font-bold text-foreground")}>
                            {n.title}
                          </p>
                          {!n.is_read && (
                            <span
                              className="h-2.5 w-2.5 shrink-0 rounded-full"
                              style={{ background: accent }}
                            />
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
