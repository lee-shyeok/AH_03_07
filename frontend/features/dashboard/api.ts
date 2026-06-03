// 대시보드 API (REQ-MYPG-001)
import { apiFetch } from "@/lib/api/client";

export interface MedicationStatus {
  label: string;
  done: boolean;
}

export interface DashboardData {
  user_name?: string;
  user_type?: "general" | "autoimmune";
  medications?: MedicationStatus[];
  health_tips?: string[];
}

export async function getDashboard(): Promise<DashboardData> {
  return apiFetch<DashboardData>("/v1/dashboard");
}
