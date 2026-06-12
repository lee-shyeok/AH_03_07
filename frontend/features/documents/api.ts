// 의료문서/OCR API (REQ-OCR-005)
import { apiFetch } from "@/lib/api/client";

export interface MedicalDocument {
  id: number;
  document_type?: string;
  file_name?: string;
  status?: string;
  created_at?: string;
  updated_at?: string;
}

export interface MedicationItem {
  drug_name_user_input: string;
  dosage?: string;
  frequency?: string;
  duration_days?: number;
  drug_category?: string;
}

export interface OcrJob {
  job_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  raw_text?: string;
  structured_data?: MedicationItem[];
  confidence_score?: number;
  error_message?: string;
}

export interface ConfirmedDocument {
  structured_data: Record<string, unknown>;
  user_confirmed: true;
}

export interface GetDocumentsParams {
  document_type?: string;
  page?: number;
  size?: number;
}

export async function getDocuments(
  params?: GetDocumentsParams
): Promise<MedicalDocument[]> {
  const query = new URLSearchParams();
  if (params?.document_type) query.set("document_type", params.document_type);
  if (params?.page !== undefined) query.set("page", String(params.page));
  if (params?.size !== undefined) query.set("size", String(params.size));
  const qs = query.toString();
  const res = await apiFetch<{ items?: MedicalDocument[] } | MedicalDocument[]>(
    `/v1/medical-documents${qs ? `?${qs}` : ""}`
  );
  return Array.isArray(res) ? res : (res.items ?? []);
}

export async function getDocument(id: number): Promise<MedicalDocument> {
  return apiFetch<MedicalDocument>(`/v1/medical-documents/${id}`);
}

export async function uploadDocument(
  file: File,
  document_type: string
): Promise<MedicalDocument> {
  const body = new FormData();
  body.append("file", file);
  body.append("document_type", document_type);
  return apiFetch<MedicalDocument>("/v1/medical-documents", {
    method: "POST",
    body,
  });
}

export async function deleteDocument(id: number): Promise<void> {
  await apiFetch<void>(`/v1/medical-documents/${id}`, { method: "DELETE" });
}

export async function startOcrJob(documentId: number): Promise<OcrJob> {
  return apiFetch<OcrJob>(`/v1/medical-documents/${documentId}/ocr-jobs`, {
    method: "POST",
  });
}

export async function getOcrJob(jobId: string, documentId: number): Promise<OcrJob> {
  return apiFetch<OcrJob>(`/v1/medical-documents/${documentId}/ocr-jobs/${jobId}`);
}

export async function confirmDocument(
  documentId: number
): Promise<ConfirmedDocument> {
  return apiFetch<ConfirmedDocument>(
    `/v1/medical-documents/${documentId}/confirm`,
    { method: "PUT" }
  );
}
