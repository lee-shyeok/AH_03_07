// 약물 목록/등록 서버 상태 (TanStack Query) — 로컬 저장 + 데모 폴백
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getMedications, createMedication, type Medication, type MedicationCreate } from "./api";
import { getLocalMeds, addLocalMed } from "./local";
import { withTimeout } from "@/lib/query/util";

export const medicationKeys = { all: ["medications"] as const };

const DUMMY: Medication[] = [
  { id: 1, name: "메토트렉세이트(MTX)", frequency: "주 1회 (금)" },
  { id: 2, name: "엽산", frequency: "주 1회 (토)" },
  { id: 3, name: "하이드록시클로로퀸", frequency: "1일 1회" },
];

async function fetchMedications(): Promise<Medication[]> {
  const local = getLocalMeds();
  let server: Medication[] = [];
  try {
    server = await withTimeout(getMedications());
  } catch {
    /* 백엔드 미가동(데모) */
  }
  const base = server.length ? server : DUMMY;
  const merged = [...local];
  for (const m of base) if (!merged.some((x) => x.id === m.id)) merged.push(m);
  return merged;
}

export function useMedications() {
  return useQuery({ queryKey: medicationKeys.all, queryFn: fetchMedications });
}

export function useCreateMedication() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: MedicationCreate) => {
      addLocalMed(data); // 데모: 항상 로컬 저장 → 목록에 즉시 반영
      try {
        await withTimeout(createMedication(data));
      } catch {
        /* 백엔드 미가동 */
      }
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: medicationKeys.all }),
  });
}
