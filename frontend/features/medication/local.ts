// 약물 로컬 저장 (데모) — 백엔드 미가동 시에도 등록·표시
import type { Medication, MedicationCreate } from "./api";

const KEY = "mg_medications_v1";

export function getLocalMeds(): Medication[] {
  if (typeof window === "undefined") return [];
  const raw = window.localStorage.getItem(KEY);
  if (!raw) return [];
  try {
    return JSON.parse(raw) as Medication[];
  } catch {
    return [];
  }
}

export function addLocalMed(data: MedicationCreate): Medication {
  const list = getLocalMeds();
  const nextId = list.reduce((m, r) => Math.max(m, r.id), 1000) + 1; // 더미(1~3)와 충돌 방지
  const med: Medication = { id: nextId, ...data };
  window.localStorage.setItem(KEY, JSON.stringify([med, ...list]));
  return med;
}
