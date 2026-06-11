// 진료기록 서버 상태 (TanStack Query) — 데모 폴백(로컬 저장) 유지
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getRecords, getRecord, createRecord, updateRecord, deleteRecord, type MedicalRecord } from "./api";
import { getLocalRecords, addLocalRecord, updateLocalRecord, deleteLocalRecord } from "./local";
import type { RecordInput } from "./schema";
import { withTimeout } from "@/lib/query/util";

export const recordKeys = {
  all: ["records"] as const,
  detail: (id: number) => ["records", id] as const,
};

// 로컬 저장분 + (가능하면) 서버 데이터를 병합. 백엔드 미가동 시 로컬만 반환.
async function fetchRecords(): Promise<MedicalRecord[]> {
  const local = getLocalRecords();
  let server: MedicalRecord[] = [];
  try {
    server = await withTimeout(getRecords());
  } catch {
    /* 백엔드 미가동(데모) — 로컬만 사용 */
  }
  const merged = [...local];
  for (const s of server) if (!merged.some((r) => r.id === s.id)) merged.push(s);
  return merged;
}

export function useRecords() {
  return useQuery({ queryKey: recordKeys.all, queryFn: fetchRecords });
}

export function useRecord(id: number) {
  return useQuery({
    queryKey: recordKeys.detail(id),
    queryFn: async () => {
      // 로컬 먼저 찾기
      const local = getLocalRecords().find((r) => r.id === id);
      try {
        return await withTimeout(getRecord(id));
      } catch {
        return local ?? null;
      }
    },
    enabled: !!id,
  });
}

export function useCreateRecord() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: RecordInput) => {
      addLocalRecord(data); // 데모: 항상 로컬 저장
      try {
        await withTimeout(createRecord(data));
      } catch {
        /* 백엔드 미가동 — 로컬 저장으로 충분 */
      }
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: recordKeys.all }),
  });
}

export function useUpdateRecord() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<import("./schema").RecordInput> }) => {
      updateLocalRecord(id, data);
      try {
        await withTimeout(updateRecord(id, data));
      } catch {
        /* 백엔드 미가동 — 로컬 수정만 적용 */
      }
    },
    onSuccess: (_v, { id }) => {
      qc.invalidateQueries({ queryKey: recordKeys.all });
      qc.invalidateQueries({ queryKey: recordKeys.detail(id) });
    },
  });
}

export function useDeleteRecord() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      deleteLocalRecord(id);
      try {
        await withTimeout(deleteRecord(id));
      } catch {
        /* 백엔드 미가동 — 로컬 삭제만 적용 */
      }
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: recordKeys.all }),
  });
}
