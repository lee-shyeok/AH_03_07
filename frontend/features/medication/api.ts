// 복약/약물 API (REQ-NOTI-001, 약물 목록)
import { apiFetch } from "@/lib/api/client";

export interface Medication {
  id: number;
  name: string;
  frequency?: string;
  next_dose?: string;
  type?: string;
}

export interface MedicationCreate {
  name: string;
  frequency?: string;
  type?: string;
}

export async function getMedications(): Promise<Medication[]> {
  const res = await apiFetch<{ items?: Medication[] } | Medication[]>(
    "/v1/medications"
  );
  return Array.isArray(res) ? res : (res.items ?? []);
}

export async function createMedication(data: MedicationCreate): Promise<void> {
  await apiFetch("/v1/medications", { method: "POST", body: data });
}
