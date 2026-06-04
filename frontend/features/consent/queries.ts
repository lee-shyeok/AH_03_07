// 동의 관리 서버 상태 (TanStack Query) — 데모 폴백 + 낙관적 업데이트
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getConsents, updateConsent } from "./api";
import type { ConsentItem, ConsentType } from "./types";
import { withTimeout } from "@/lib/query/util";

export const consentKeys = { all: ["consents"] as const };

// 백엔드 미가동 시 기본 동의 상태(필수 동의됨 / 마케팅 미동의)
const DUMMY: ConsentItem[] = [
  { consent_type: "terms", agreed: true },
  { consent_type: "privacy", agreed: true },
  { consent_type: "sensitive_medical", agreed: true },
  { consent_type: "marketing", agreed: false },
];

export function useConsents() {
  return useQuery({
    queryKey: consentKeys.all,
    queryFn: async () => {
      try {
        const data = await withTimeout(getConsents());
        return data.length ? data : DUMMY;
      } catch {
        return DUMMY;
      }
    },
  });
}

export function useUpdateConsent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ type, agreed }: { type: ConsentType; agreed: boolean }) => {
      try {
        await withTimeout(updateConsent(type, agreed));
      } catch {
        /* 백엔드 미가동(데모) — 로컬 상태만 변경 */
      }
    },
    // 낙관적 업데이트: 토글 즉시 반영
    onMutate: async ({ type, agreed }) => {
      await qc.cancelQueries({ queryKey: consentKeys.all });
      const prev = qc.getQueryData<ConsentItem[]>(consentKeys.all);
      qc.setQueryData<ConsentItem[]>(consentKeys.all, (old) =>
        (old ?? DUMMY).map((c) => (c.consent_type === type ? { ...c, agreed } : c))
      );
      return { prev };
    },
    onError: (_e, _v, ctx) => {
      if (ctx?.prev) qc.setQueryData(consentKeys.all, ctx.prev);
    },
  });
}
