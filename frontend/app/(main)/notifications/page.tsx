"use client";

import { useRouter } from "next/navigation";
import { ChevronLeft, Pill, AlertTriangle, BarChart3, CheckCircle2, Bell, BookOpen } from "lucide-react";
import { Card } from "@/components/ui/card";
import { useNotifications, useMarkRead } from "@/features/notifications/queries";
import { type AppNotification } from "@/features/notifications/api";
import { getMode } from "@/features/auth/mode";

const GREEN = "#03C85F";
const PURPLE = "#7C5CCF";


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

  const items = apiItems;

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
      ) : items.length === 0 ? (
        <p className="mt-8 text-center text-sm text-muted-foreground">알림이 없습니다.</p>
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
