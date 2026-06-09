// 약품 인식 내역 서버 상태 (TanStack Query) — 데모 폴백 유지
import { useQuery } from "@tanstack/react-query";
import { getRecognitions, type PillRecognition } from "./api";
import { withTimeout } from "@/lib/query/util";

export const pillKeys = { recognitions: ["pill-recognitions"] as const };

const DUMMY: PillRecognition[] = [
  { id: 1, drug_name: "타이레놀정 500mg", confidence: 0.97 },
  { id: 2, drug_name: "아스피린프로텍트정 100mg", confidence: 0.91 },
  { id: 3, drug_name: "리리카캡슐 75mg", confidence: 0.84 },
];

export function useRecognitions() {
  return useQuery({
    queryKey: pillKeys.recognitions,
    queryFn: async () => {
      try {
        const data = await withTimeout(getRecognitions());
        return data.length ? data : DUMMY;
      } catch {
        return DUMMY;
      }
    },
  });
}

export const usePillRecognitions = useRecognitions;
