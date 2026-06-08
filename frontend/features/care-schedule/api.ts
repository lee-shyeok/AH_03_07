import { apiFetch } from "@/lib/api/client";

export type MedicalScheduleType =
  | "BLOOD_TEST"
  | "URINE_TEST"
  | "EYE_EXAM"
  | "APPOINTMENT"
  | "INJECTION";

export interface MedicalScheduleResponse {
  id: number;
  schedule_type: MedicalScheduleType;
  title: string | null;
  scheduled_date: string;
  reminder_days_before: number;
  note: string | null;
  created_at: string;
  updated_at: string;
}

export interface MedicalScheduleCreateRequest {
  schedule_type: MedicalScheduleType;
  title: string;
  scheduled_date: string; // "YYYY-MM-DD"
  reminder_days_before: number; // 1~30
  note?: string | null;
}

export type MedicalScheduleUpdateRequest = MedicalScheduleCreateRequest;

export async function listCareSchedules(
  from?: string,
  to?: string,
  type?: MedicalScheduleType
): Promise<MedicalScheduleResponse[]> {
  const params = new URLSearchParams();
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  if (type) params.set("type", type);
  const qs = params.toString();
  return apiFetch<MedicalScheduleResponse[]>(`/v1/care-schedules${qs ? `?${qs}` : ""}`);
}

export async function createCareSchedule(
  body: MedicalScheduleCreateRequest
): Promise<MedicalScheduleResponse> {
  return apiFetch<MedicalScheduleResponse>("/v1/care-schedules", {
    method: "POST",
    body,
  });
}

export async function updateCareSchedule(
  id: number,
  body: MedicalScheduleUpdateRequest
): Promise<MedicalScheduleResponse> {
  return apiFetch<MedicalScheduleResponse>(`/v1/care-schedules/${id}`, {
    method: "PUT",
    body,
  });
}

export async function deleteCareSchedule(id: number): Promise<void> {
  await apiFetch<void>(`/v1/care-schedules/${id}`, { method: "DELETE" });
}
