// 안내 가이드 API (REQ-GUIDE-003~006)
// 백엔드 auto_guides 정본 (id=정수, 필드명 그대로)
import { apiFetch } from "@/lib/api/client";

export interface Guide {
  id: number;
  status?: string;
  created_at?: string;
  medication_general?: string;
  side_effect_monitoring?: string[] | string;
  lifestyle_info?: string;
  symptom_summary?: string;
  sources?: { title?: string; organization?: string }[];
  disclaimer?: string;
}

export async function getGuides(): Promise<Guide[]> {
  const res = await apiFetch<{ items?: Guide[] } | Guide[]>("/v1/guides");
  return Array.isArray(res) ? res : (res.items ?? []);
}

export async function getGuide(id: number): Promise<Guide> {
  return apiFetch<Guide>(`/v1/guides/${id}`);
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
