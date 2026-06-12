// 복약/약물 API (REQ-NOTI-001, 약물 목록)
import { apiFetch } from "@/lib/api/client";

export interface Medication {
  id: number;
  name: string;
  frequency?: string;
  next_dose?: string;
  type?: string;
}

export interface MedicationDetail extends Medication {
  name_en?: string;
  dosage?: string;
  description?: string;
  drug_class?: string;
  is_injection?: boolean;
  note?: string;
}

export interface MedicationCreate {
  name: string;
  drug_class?: string;   // 일반 모드에서는 없어도 됨
  is_injection?: boolean;
  note?: string;
}

export async function getMedications(): Promise<Medication[]> {
  const res = await apiFetch<{ items?: Medication[] } | Medication[]>(
    "/v1/medications"
  );
  return Array.isArray(res) ? res : (res.items ?? []);
}

export async function getUserMedications(): Promise<MedicationDetail[]> {
  const res = await apiFetch<{ items?: MedicationDetail[] } | MedicationDetail[]>(
    "/v1/user-medications"
  );
  return Array.isArray(res) ? res : (res.items ?? []);
}

export async function getMedication(id: number): Promise<MedicationDetail> {
  const items = await getUserMedications();
  const found = items.find((m) => m.id === id);
  if (!found) throw new Error(`medication ${id} not found`);
  return found;
}

export async function createMedication(data: MedicationCreate): Promise<void> {
  await apiFetch("/v1/user-medications", { method: "POST", body: { medications: [data] } });
}

export async function deleteMedication(id: number): Promise<void> {
  await apiFetch(`/v1/user-medications/${id}`, { method: "DELETE" });
}

// 복약 체크 로그 (REQ-NOTI-001)
export interface MedicationLog {
  id: number;
  medication_id: number;
  medication_name: string;
  scheduled_time?: string;
  taken: boolean;
  taken_at?: string;
  dosage?: string;
  is_autoimmune_drug?: boolean;
}

export async function getMedicationLogs(date: string): Promise<MedicationLog[]> {
  const res = await apiFetch<{ items?: MedicationLog[] } | MedicationLog[]>(
    `/v1/medication-logs?from=${date}&to=${date}`
  );
  return Array.isArray(res) ? res : (res.items ?? []);
}

export async function checkMedicationLog(id: number): Promise<void> {
  await apiFetch(`/v1/medication-logs/${id}/check`, {
    method: "PUT",
    body: { taken: true },
  });
}
