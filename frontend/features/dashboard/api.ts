// 대시보드 API (REQ-MYPG-001)
import { apiFetch } from "@/lib/api/client";
import type { RiskFlagItem } from "@/features/risk-flag/api";

export interface MedicationStatus {
  label: string;
  done: boolean;
}

export interface MedicationResponse {
  id: string;
  drug_name_user_input: string;
  dosage: string | null;
  frequency: string | null;
  duration_days: number | null;
  start_date: string | null;
  end_date: string | null;
  is_autoimmune_drug: boolean;
  drug_category: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface DashboardData {
  today_medications: MedicationResponse[];
  recent_activity: unknown[];
  pending_schedules: unknown[];
  active_risk_flags: RiskFlagItem[];
}

export async function getDashboard(): Promise<DashboardData> {
  return apiFetch<DashboardData>("/v1/dashboard");
}
