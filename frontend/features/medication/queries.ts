// 약물 목록/등록 서버 상태 (TanStack Query) — 로컬 저장 + 데모 폴백
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getUserMedications, createMedication, deleteMedication, type Medication, type MedicationDetail, type MedicationCreate } from "./api";
import { getLocalMeds, addLocalMed } from "./local";
import { withTimeout } from "@/lib/query/util";
import { getMode } from "@/features/auth/mode";

export const medicationKeys = { all: ["medications"] as const };

/** 일반 모드 더미 */
const GENERAL_DUMMY: MedicationDetail[] = [
  { id: 1, name: "타이레놀 500mg", frequency: "1일 3회 (아침·점심·저녁)" },
  { id: 2, name: "이부프로펜 400mg", frequency: "필요 시 1회 (식후)" },
  { id: 3, name: "오메프라졸 20mg", frequency: "1일 1회 (아침 공복)" },
];

/** 자가면역 모드 더미 */
const AUTOIMMUNE_DUMMY: MedicationDetail[] = [
  { id: 1, name: "메토트렉세이트(MTX)", frequency: "주 1회 (금)", drug_class: "IMMUNOSUPPRESSANT" },
  { id: 2, name: "엽산 1mg", frequency: "주 1회 (토)" },
  { id: 3, name: "하이드록시클로로퀸 200mg", frequency: "1일 1회", drug_class: "ANTIMALARIAL" },
];

async function fetchMedications(): Promise<MedicationDetail[]> {
  const local = getLocalMeds() as MedicationDetail[];
  const mode = getMode();
  let server: MedicationDetail[] = [];
  try {
    server = await withTimeout(getUserMedications());
  } catch {
    /* 백엔드 미가동(데모) */
  }
  const DUMMY = mode === "autoimmune" ? AUTOIMMUNE_DUMMY : GENERAL_DUMMY;
  const base = server.length ? server : (DUMMY as MedicationDetail[]);
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

export function useDeleteMedication() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteMedication(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: medicationKeys.all }),
  });
}
