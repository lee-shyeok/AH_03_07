// 의료문서/OCR API (REQ-OCR-005)
import { apiFetch } from "@/lib/api/client";

export interface MedicalDocument {
  id: number;
  document_type?: string;
  status?: string;
  created_at?: string;
}

export async function getDocuments(): Promise<MedicalDocument[]> {
  const res = await apiFetch<{ items?: MedicalDocument[] } | MedicalDocument[]>(
    "/v1/medical-documents"
  );
  return Array.isArray(res) ? res : (res.items ?? []);
}
