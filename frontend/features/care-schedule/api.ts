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
  title: string;
  scheduled_date: string;
  reminder_days_before: number[] | null;
  note: string | null;
  created_at: string;
  updated_at: string;
}

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
