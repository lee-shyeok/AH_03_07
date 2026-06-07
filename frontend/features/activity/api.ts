import { apiFetch } from "@/lib/api/client";

export interface ActivityLogUpsertRequest {
  log_date: string; // "YYYY-MM-DD"
  pain_vas: number;
  fatigue: number;
  morning_stiffness_minutes?: number | null;
  joint_swelling_areas?: string[] | null;
  daily_difficulty: number;
  free_memo?: string | null;
}

export interface ActivityLogResponse {
  id: number;
  log_date: string;
  pain_vas: number;
  fatigue: number;
  morning_stiffness_minutes: number | null;
  joint_swelling_areas: string[] | null;
  daily_difficulty: number;
  free_memo: string | null;
  created_at: string;
  updated_at: string;
}

export async function upsertActivityLog(
  payload: ActivityLogUpsertRequest
): Promise<ActivityLogResponse> {
  return apiFetch<ActivityLogResponse>("/v1/activity-logs", {
    method: "POST",
    body: payload,
  });
}

export async function getActivityLog(
  logDate: string
): Promise<ActivityLogResponse | null> {
  try {
    return await apiFetch<ActivityLogResponse>(`/v1/activity-logs/${logDate}`);
  } catch {
    return null;
  }
}

export async function listActivityLogs(
  from?: string,
  to?: string
): Promise<ActivityLogResponse[]> {
  const params = new URLSearchParams();
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  const qs = params.toString();
  return apiFetch<ActivityLogResponse[]>(`/v1/activity-logs${qs ? `?${qs}` : ""}`);
}
