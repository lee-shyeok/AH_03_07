import { apiFetch } from "@/lib/api/client";

// ===== 생활맥락 (lupus-daily-context) =====
export type StressLevel = "LOW" | "MID" | "HIGH";

export interface LupusDailyContextUpsertRequest {
  log_date: string; // "YYYY-MM-DD"
  uv_exposure_minutes?: number | null;
  sleep_hours?: number | null;
  stress_level?: StressLevel | null;
  med_taken?: boolean | null;
  note?: string | null;
}

export interface LupusDailyContextResponse {
  id: number;
  log_date: string;
  uv_exposure_minutes: number | null;
  sleep_hours: number | null;
  stress_level: StressLevel | null;
  med_taken: boolean | null;
  note: string | null;
  created_at: string;
  updated_at: string;
}

export async function upsertLupusDailyContext(
  payload: LupusDailyContextUpsertRequest,
): Promise<LupusDailyContextResponse> {
  return apiFetch<LupusDailyContextResponse>("/v1/lupus-daily-context", {
    method: "POST",
    body: payload,
  });
}

export async function getLupusDailyContext(
  logDate: string,
): Promise<LupusDailyContextResponse | null> {
  try {
    return await apiFetch<LupusDailyContextResponse>(`/v1/lupus-daily-context/${logDate}`);
  } catch {
    return null;
  }
}

// ===== 피부·점막 증상 (lupus-skin-logs) =====
export type LupusSkinSymptomType = "RASH" | "ORAL_ULCER" | "HAIR_LOSS" | "RAYNAUD";

export interface LupusSkinLogResponse {
  id: number;
  symptom_type: LupusSkinSymptomType;
  log_date: string;
  note: string | null;
  created_at: string;
  updated_at: string;
}

export async function listLupusSkinLogs(): Promise<LupusSkinLogResponse[]> {
  return apiFetch<LupusSkinLogResponse[]>("/v1/lupus-skin-logs");
}

export async function createLupusSkinLog(payload: {
  symptom_type: LupusSkinSymptomType;
  log_date: string;
  note?: string | null;
}): Promise<LupusSkinLogResponse> {
  return apiFetch<LupusSkinLogResponse>("/v1/lupus-skin-logs", {
    method: "POST",
    body: payload,
  });
}

export async function deleteLupusSkinLog(logId: number): Promise<void> {
  await apiFetch<void>(`/v1/lupus-skin-logs/${logId}`, { method: "DELETE" });
}
