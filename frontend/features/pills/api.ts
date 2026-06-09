// 약품 인식 API (REQ-PILL-004)
import { apiFetch } from "@/lib/api/client";

export interface PillRecognition {
  id: number;
  drug_name?: string;
  confidence?: number;
  created_at?: string;
}

export interface PillCandidate {
  name?: string;
  drug_name?: string;
  ingredient?: string;
  category?: string;
  confidence: number;
}

export interface DrugInfo {
  name?: string;
  drug_name?: string;
  item_name?: string;
  entp_name?: string;
  efcy_qesitm?: string;
  ingredient?: string;
  category?: string;
}

export async function getRecognitions(): Promise<PillRecognition[]> {
  const res = await apiFetch<
    { items?: PillRecognition[] } | PillRecognition[]
  >("/v1/pills/recognitions");
  return Array.isArray(res) ? res : (res.items ?? []);
}

export async function recognizePill(file: File): Promise<PillCandidate[]> {
  const form = new FormData();
  form.append("file", file);
  const res = await apiFetch<{ candidates?: PillCandidate[] } | PillCandidate[]>(
    "/v1/pills/recognize",
    { method: "POST", body: form }
  );
  return Array.isArray(res) ? res : (res.candidates ?? []);
}

export async function searchDrugReferences(query: string): Promise<DrugInfo[]> {
  const res = await apiFetch<{ items?: DrugInfo[] } | DrugInfo[]>(
    `/v1/pills/search?q=${encodeURIComponent(query)}`
  );
  return Array.isArray(res) ? res : (res.items ?? []);
}
