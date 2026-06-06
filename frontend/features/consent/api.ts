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

const CONSENT_TYPE_MAP: Record<ConsentType, string> = {
  terms: "TERMS_OF_SERVICE",
  privacy: "PRIVACY_POLICY",
  sensitive_medical: "MEDICAL_DATA",
  marketing: "MARKETING",
};

// 동의 변경
export async function updateConsent(
  type: ConsentType,
  agreed: boolean,
  version: string = "1.0",
): Promise<void> {
  await apiFetch("/v1/users/me/consents", {
    method: "POST",
    body: { consent_type: CONSENT_TYPE_MAP[type], agreed, version },
  });
  logger.info("consent", "동의 변경", { type, agreed });
}
