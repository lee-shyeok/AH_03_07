// 진료기록 API (REQ-MEDI-001~005)
import { apiFetch } from "@/lib/api/client";

export interface MedicalRecord {
  id: number;
  hospital_name?: string;
  department?: string;
  visit_date?: string; // YYYY-MM-DD
  diagnosis?: string;
  memo?: string;
  created_at?: string;
}

export interface MedicalRecordCreate {
  hospital_name: string;
  department?: string;
  visit_date: string;
  diagnosis?: string;
  memo?: string;
}

export async function getRecords(): Promise<MedicalRecord[]> {
  const res = await apiFetch<{ items?: MedicalRecord[] } | MedicalRecord[]>(
    "/v1/medical-records"
  );
  return Array.isArray(res) ? res : (res.items ?? []);
}

export async function getRecord(id: number): Promise<MedicalRecord> {
  return apiFetch<MedicalRecord>(`/v1/medical-records/${id}`);
}

export async function createRecord(data: MedicalRecordCreate): Promise<void> {
  await apiFetch("/v1/medical-records", { method: "POST", body: data });
}

export async function updateRecord(id: number, data: Partial<MedicalRecordCreate>): Promise<MedicalRecord> {
  return apiFetch<MedicalRecord>(`/v1/medical-records/${id}`, { method: "PATCH", body: data });
}

export async function deleteRecord(id: number): Promise<void> {
  await apiFetch(`/v1/medical-records/${id}`, { method: "DELETE" });
}
