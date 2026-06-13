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
  timings?: string[];
  timing_times?: Record<string, string>;
  start_date?: string;
  end_date?: string;
}

export interface MedicationCreate {
  name: string;
  drug_class?: string;
  is_injection?: boolean;
  note?: string;
  timings?: string[];
  timing_times?: Record<string, string>;
  start_date?: string;
  end_date?: string;
}

export interface DrugReference {
  id?: number;
  drug_name: string;
  ingredient?: string;
  manufacturer?: string;
  source?: string;
}

export async function searchDrugReferences(query: string): Promise<DrugReference[]> {
  try {
    const res = await apiFetch<{ items?: DrugReference[] } | DrugReference[]>(
      `/v1/drug-references?query=${encodeURIComponent(query)}`
    );
    return Array.isArray(res) ? res : (res.items ?? []);
  } catch {
    return [];
  }
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

export async function checkMedicationLog(
  id: number,
  location?: { latitude?: number; longitude?: number }
): Promise<void> {
  await apiFetch(`/v1/medication-logs/${id}/check`, {
    method: "PUT",
    body: { taken: true, ...location },
  });
}
