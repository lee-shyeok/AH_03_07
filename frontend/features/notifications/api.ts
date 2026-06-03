// 알림 API (REQ-NOTI-004/005)
import { apiFetch } from "@/lib/api/client";

export interface AppNotification {
  id: number;
  title: string;
  body?: string;
  notification_type?: string;
  is_read: boolean;
  created_at?: string;
}

export async function getNotifications(): Promise<AppNotification[]> {
  const res = await apiFetch<
    { items?: AppNotification[]; notifications?: AppNotification[] } | AppNotification[]
  >("/v1/notifications");
  if (Array.isArray(res)) return res;
  return res.items ?? res.notifications ?? [];
}

export async function markRead(id: number): Promise<void> {
  await apiFetch(`/v1/notifications/${id}/read`, { method: "PATCH" });
}
