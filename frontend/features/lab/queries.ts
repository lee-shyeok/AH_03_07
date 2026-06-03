// 검사결과 저장 (TanStack Query mutation) — 데모 폴백
import { useMutation } from "@tanstack/react-query";
import { createLabResult } from "./api";
import { withTimeout } from "@/lib/query/util";

export function useCreateLab() {
  return useMutation({
    mutationFn: async (payload: {
      test_date: string;
      items: { key: string; value: number }[];
      memo?: string;
    }) => {
      try {
        await withTimeout(createLabResult(payload));
      } catch {
        /* 백엔드 미가동(데모) */
      }
    },
  });
}
