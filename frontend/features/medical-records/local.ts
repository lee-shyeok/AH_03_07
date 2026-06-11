// 진료기록 로컬 저장 (데모) — 백엔드 미가동 시에도 저장·조회 가능
// 백엔드가 살아나면 api.ts의 서버 데이터와 병합되어 표시됨.
import type { MedicalRecord, MedicalRecordCreate } from "./api";

const KEY = "mg_records_v1";

// 첫 진입 시 예시 1건 (빈 화면 방지)
const SEED: MedicalRecord[] = [
  {
    id: 1,
    hospital_name: "서울대학교병원",
    department: "류마티스내과",
    visit_date: "2026-05-12",
    diagnosis: "류마티스 관절염 추적관찰",
    memo: "MTX 용량 유지",
  },
];

export function getLocalRecords(): MedicalRecord[] {
  if (typeof window === "undefined") return [];
  const raw = window.localStorage.getItem(KEY);
  if (raw == null) {
    window.localStorage.setItem(KEY, JSON.stringify(SEED));
    return SEED;
  }
  try {
    return JSON.parse(raw) as MedicalRecord[];
  } catch {
    return [];
  }
}

export function addLocalRecord(data: MedicalRecordCreate): MedicalRecord {
  const list = getLocalRecords();
  // 로컬 id: 현재 최대값 + 1 (Date 사용 없이 결정적)
  const nextId = list.reduce((m, r) => Math.max(m, r.id), 0) + 1;
  const rec: MedicalRecord = { id: nextId, ...data };
  window.localStorage.setItem(KEY, JSON.stringify([rec, ...list]));
  return rec;
}

export function updateLocalRecord(id: number, data: Partial<MedicalRecordCreate>): MedicalRecord | null {
  if (typeof window === "undefined") return null;
  const list = getLocalRecords();
  const idx = list.findIndex((r) => r.id === id);
  if (idx === -1) return null;
  const updated = { ...list[idx], ...data };
  list[idx] = updated;
  window.localStorage.setItem(KEY, JSON.stringify(list));
  return updated;
}

export function deleteLocalRecord(id: number) {
  if (typeof window === "undefined") return;
  const next = getLocalRecords().filter((r) => r.id !== id);
  window.localStorage.setItem(KEY, JSON.stringify(next));
}
