// 약품 인식 API (REQ-PILL-004)
import { apiFetch } from "@/lib/api/client";

export interface PillRecognition {
  id: number;
  drug_name?: string;
  confidence?: number;
  created_at?: string;
}

export async function getRecognitions(): Promise<PillRecognition[]> {
  const res = await apiFetch<
    { items?: PillRecognition[] } | PillRecognition[]
  >("/v1/pills/recognitions");
  return Array.isArray(res) ? res : (res.items ?? []);
}
