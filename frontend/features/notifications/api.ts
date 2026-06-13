// 알림 API (REQ-NOTI-004/005/008)
import { apiFetch } from "@/lib/api/client";

export interface AppNotification {
  id: number;
  title: string;
  body?: string;
  notification_type?: string;
  is_read: boolean;
  created_at?: string;
}

export interface NotificationSettings {
  enabled: boolean;
  time: string;
  repeat: string;
  early_reminder: boolean;
  missed_reminder: boolean;
  location_record: boolean;
  channels: {
    app: boolean;
    kakao: boolean;
    email: boolean;
  };
  timing_times?: {
    morning?: string;
    afternoon?: string;
    evening?: string;
    bedtime?: string;
  };
  quiet_hours?: {
    enabled: boolean;
    start: string;
    end: string;
  };
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

export async function getNotificationSettings(): Promise<NotificationSettings> {
  return apiFetch<NotificationSettings>("/v1/notifications/settings");
}

export async function updateNotificationSettings(
  data: NotificationSettings
): Promise<NotificationSettings> {
  return apiFetch<NotificationSettings>("/v1/notifications/settings", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}
