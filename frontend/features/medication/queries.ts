// 약물 목록/등록 서버 상태 (TanStack Query) — 로컬 저장 + 데모 폴백
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getUserMedications, createMedication, deleteMedication, type Medication, type MedicationDetail, type MedicationCreate } from "./api";
import { getLocalMeds, addLocalMed, markLocalMedDeleted, isDeletedMed } from "./local";
import { withTimeout } from "@/lib/query/util";

export const medicationKeys = { all: ["medications"] as const };

async function fetchMedications(): Promise<MedicationDetail[]> {
  const local = (getLocalMeds() as MedicationDetail[]).filter((m) => !isDeletedMed(m.id, m.name));
  let server: MedicationDetail[] = [];
  try {
    server = await withTimeout(getUserMedications());
  } catch {
    /* 백엔드 미가동 */
  }
  const base = server.length ? server : [];
  const merged = [...local];
  for (const m of base) {
    if (!isDeletedMed(m.id, m.name) && !merged.some((x) => x.id === m.id)) merged.push(m);
  }
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
    mutationFn: async ({ id, name }: { id: number; name: string }) => {
      markLocalMedDeleted(id, name);
      try { await deleteMedication(id); } catch { /* 백엔드 미가동 */ }
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: medicationKeys.all }),
  });
}
