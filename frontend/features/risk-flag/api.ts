import { apiFetch } from "@/lib/api/client";

export type RiskFlagStatus = "ACTIVE" | "RESOLVED" | "DISMISSED";
export type RiskFlagSourceType = "SYMPTOM_CHECK" | "RISK_PROFILE" | "LAB_RESULT";

export interface RiskFlagItem {
  id: number;
  source_type: RiskFlagSourceType;
  source_id: number | null;
  flag_code: string;
  flag_label: string;
  category: string;
  message: string;
  red_flag: boolean;
  consultation_recommended: boolean;
  status: RiskFlagStatus;
  created_at: string;
}

export async function listRiskFlags(
  status?: RiskFlagStatus
): Promise<RiskFlagItem[]> {
  const params = new URLSearchParams();
  if (status) params.set("flag_status", status);
  const qs = params.toString();
  return apiFetch<RiskFlagItem[]>(`/v1/risk-flags${qs ? `?${qs}` : ""}`);
}

export async function updateRiskFlagStatus(
  id: number,
  status: "RESOLVED" | "DISMISSED"
): Promise<RiskFlagItem> {
  return apiFetch<RiskFlagItem>(`/v1/risk-flags/${id}`, {
    method: "PATCH",
    body: { status },
  });
}
