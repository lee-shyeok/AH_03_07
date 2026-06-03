// 동의 관리 도메인 (NFR-COMPLI-001)

export type ConsentType =
  | "terms" // 서비스 이용약관 (필수)
  | "privacy" // 개인정보 처리방침 (필수)
  | "sensitive_medical" // 민감 의료정보 처리 (필수)
  | "marketing"; // 마케팅 수신 (선택)

export interface ConsentItem {
  consent_type: ConsentType;
  agreed: boolean;
  agreed_at?: string;
}

export interface ConsentMeta {
  type: ConsentType;
  label: string;
  required: boolean;
}

export const CONSENT_META: ConsentMeta[] = [
  { type: "terms", label: "서비스 이용약관", required: true },
  { type: "privacy", label: "개인정보 처리방침", required: true },
  { type: "sensitive_medical", label: "민감 의료정보 처리 동의", required: true },
  { type: "marketing", label: "마케팅 정보 수신 (선택)", required: false },
];
