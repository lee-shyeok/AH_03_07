// 동의 관리 API (NFR-COMPLI-001)
// 백엔드 경로는 연동 시 확인 필요 (현재 백엔드 다운으로 미검증)
import { apiFetch } from "@/lib/api/client";
import { logger } from "@/lib/logger/logger";
import type { ConsentItem, ConsentType } from "./types";

// 동의 현황/이력 조회
export async function getConsents(): Promise<ConsentItem[]> {
  const res = await apiFetch<{ items?: ConsentItem[] } | ConsentItem[]>(
    "/v1/users/me/consents"
  );
  return Array.isArray(res) ? res : (res.items ?? []);
}

// 동의 변경
export async function updateConsent(
  type: ConsentType,
  agreed: boolean
): Promise<void> {
  await apiFetch(`/v1/users/me/consents/${type}`, {
    method: "PUT",
    body: { agreed },
  });
  logger.info("consent", "동의 변경", { type, agreed });
}
