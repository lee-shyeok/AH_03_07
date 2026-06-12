// 의료문서/OCR API (REQ-OCR-005)
import { apiFetch, getAccessToken } from "@/lib/api/client";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";

export interface MedicalDocument {
  id: number;
  document_type?: string;
  file_name?: string;
  status?: string;
  created_at?: string;
  updated_at?: string;
}

export interface OcrJob {
  job_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  structured_data?: Record<string, unknown>;
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
  const formData = new FormData();
  formData.append("file", file);
  formData.append("document_type", document_type);
  const token = getAccessToken();
  const res = await fetch(`${BASE_URL}/v1/medical-documents`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
    credentials: "include",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Upload failed: ${res.status} ${text}`);
  }
  return res.json();
}

export async function deleteDocument(id: number): Promise<void> {
  await apiFetch<void>(`/v1/medical-documents/${id}`, { method: "DELETE" });
}

export async function startOcrJob(documentId: number): Promise<OcrJob> {
  return apiFetch<OcrJob>(`/v1/medical-documents/${documentId}/ocr-jobs`, {
    method: "POST",
  });
}

export async function getOcrJob(jobId: string): Promise<OcrJob> {
  return apiFetch<OcrJob>(`/v1/ocr-jobs/${jobId}`);
}

export async function confirmDocument(
  documentId: number
): Promise<ConfirmedDocument> {
  return apiFetch<ConfirmedDocument>(
    `/v1/medical-documents/${documentId}/confirm`,
    { method: "PUT" }
  );
}
