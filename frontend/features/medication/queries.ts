// 약물 목록 서버 상태 (TanStack Query) — 데모 폴백 유지
import { useQuery } from "@tanstack/react-query";
import { getMedications, type Medication } from "./api";
import { withTimeout } from "@/lib/query/util";

export const medicationKeys = { all: ["medications"] as const };

const DUMMY: Medication[] = [
  { id: 1, name: "메토트렉세이트(MTX)", frequency: "주 1회 (금)" },
  { id: 2, name: "엽산", frequency: "주 1회 (토)" },
  { id: 3, name: "하이드록시클로로퀸", frequency: "1일 1회" },
];

export function useMedications() {
  return useQuery({
    queryKey: medicationKeys.all,
    queryFn: async () => {
      try {
        const data = await withTimeout(getMedications());
        return data.length ? data : DUMMY;
      } catch {
        return DUMMY;
      }
    },
  });
}
