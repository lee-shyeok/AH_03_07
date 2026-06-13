// 약물 로컬 저장 (데모) — 백엔드 미가동 시에도 등록·표시
import type { Medication, MedicationCreate } from "./api";

const KEY = "mg_medications_v1";
const DELETED_KEY = "mg_deleted_meds_v2"; // v2: {id, name} 형태로 변경

interface DeletedEntry { id: number; name: string }

export function getLocalMeds(): Medication[] {
  if (typeof window === "undefined") return [];
  const raw = window.localStorage.getItem(KEY);
  if (!raw) return [];
  try { return JSON.parse(raw) as Medication[]; } catch { return []; }
}

export function getDeletedMeds(): DeletedEntry[] {
  if (typeof window === "undefined") return [];
  const raw = window.localStorage.getItem(DELETED_KEY);
  if (!raw) return [];
  try { return JSON.parse(raw) as DeletedEntry[]; } catch { return []; }
}

/** 하위 호환: ID 배열로 반환 */
export function getDeletedMedIds(): number[] {
  return getDeletedMeds().map((d) => d.id);
}

export function isDeletedMed(id: number, name: string): boolean {
  const list = getDeletedMeds();
  return list.some((d) => d.id === id || d.name === name);
}

export function addLocalMed(data: MedicationCreate): Medication {
  const list = getLocalMeds();
  const nextId = list.reduce((m, r) => Math.max(m, r.id), 1000) + 1; // 더미(1~3)와 충돌 방지
  const med: Medication = { id: nextId, ...data };
  window.localStorage.setItem(KEY, JSON.stringify([med, ...list]));
  return med;
}

export function markLocalMedDeleted(id: number, name: string): void {
  // 로컬 목록에서 제거
  const list = getLocalMeds();
  window.localStorage.setItem(KEY, JSON.stringify(list.filter((m) => m.id !== id)));
  // 삭제 {id, name} 기록 — ID 뿐 아니라 이름으로도 필터 (DUMMY ↔ 서버 ID 불일치 방지)
  const deleted = getDeletedMeds();
  if (!deleted.some((d) => d.id === id)) {
    window.localStorage.setItem(DELETED_KEY, JSON.stringify([...deleted, { id, name }]));
  }
}
