// 안내 가이드 API (REQ-GUIDE-003~006)
// 백엔드 auto_guides 정본 (id=정수, 필드명 그대로)
import { apiFetch } from "@/lib/api/client";

export interface GuideSource {
  citation_order: number;
  source_title: string;
  source_org: string;
  source_page: number | null;
  source_url: string | null;
  used_for_section: string | null;
}

export type GuideSectionType =
  | "MEDICATION_GENERAL"
  | "SIDE_EFFECT"
  | "LIFESTYLE"
  | "SYMPTOM_SUMMARY";

export interface GuideSection {
  section_type: GuideSectionType;
  section_title: string;
  section_content: string;
  display_order: number;
}

export interface Guide {
  id: number;
  status?: string;
  created_at?: string;
  medication_general?: string;
  side_effect_monitoring?: string[] | string;
  lifestyle_info?: string;
  symptom_summary?: string;
  sources?: GuideSource[];
  disclaimer?: string;
}

export async function getGuides(): Promise<Guide[]> {
  const res = await apiFetch<{ items?: Guide[] } | Guide[]>("/v1/guides");
  return Array.isArray(res) ? res : (res.items ?? []);
}

export async function getGuide(id: number): Promise<Guide> {
  return apiFetch<Guide>(`/v1/guides/${id}`);
}

export async function getSources(guideId: number): Promise<GuideSource[]> {
  return apiFetch<GuideSource[]>(`/v1/guides/${guideId}/sources`);
}

export async function getSections(guideId: number): Promise<GuideSection[]> {
  return apiFetch<GuideSection[]>(`/v1/guides/${guideId}/sections`);
}

export async function regenerateGuide(id: number): Promise<void> {
  await apiFetch(`/v1/guides/${id}/regenerate`, { method: "POST" });
}

export async function feedbackGuide(
  id: number,
  rating: number,
  comment?: string
): Promise<void> {
  await apiFetch(`/v1/guides/${id}/feedback`, {
    method: "POST",
    body: { rating, comment },
  });
}

export interface ContentConversionResponse {
  file_urls: string[];
}

export interface TTSResponse {
  file_url: string;
}

export async function generateCardNews(guideId: number): Promise<ContentConversionResponse> {
  return apiFetch<ContentConversionResponse>("/v1/contents/card-news", {
    method: "POST",
    body: { guide_id: guideId },
  });
}

export async function generateTTS(guideId: number): Promise<TTSResponse> {
  return apiFetch<TTSResponse>("/v1/contents/tts", {
    method: "POST",
    body: { guide_id: guideId },
  });
}

// REQ-AUTO-005: 안내문 생성 job
export interface GuideJob {
  status: string; // PENDING | PROCESSING | COMPLETED | BLOCKED | FAILED
  guide_id: number | null;
  blocked_reason: string | null; // HIGH_RISK_GATE_BLOCKED | SAFETY_FILTER_BLOCKED
  error_message: string | null;
  trigger_emergency_modal: boolean;
}

export async function createGuide(): Promise<{ job_id: number; status: string }> {
  return apiFetch<{ job_id: number; status: string }>("/v1/guides/generate", {
    method: "POST",
  });
}

export async function getGuideJob(jobId: number): Promise<GuideJob> {
  return apiFetch<GuideJob>(`/v1/guide-generation-jobs/${jobId}`);
}

export async function deleteGuide(id: number): Promise<void> {
  await apiFetch(`/v1/guides/${id}`, { method: "DELETE" });
}
