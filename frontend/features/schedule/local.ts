// 일정 로컬 저장 (데모) — 백엔드 미가동 시에도 추가·표시
import type { MedicalScheduleResponse } from "../care-schedule/api";

const CARE_KEY = "mg_care_schedules_v1";

export function getLocalCareSchedules(): MedicalScheduleResponse[] {
  if (typeof window === "undefined") return [];
  try { return JSON.parse(window.localStorage.getItem(CARE_KEY) ?? "[]"); } catch { return []; }
}

export function addLocalCareSchedule(s: MedicalScheduleResponse): void {
  const list = getLocalCareSchedules().filter((x) => x.id !== s.id);
  window.localStorage.setItem(CARE_KEY, JSON.stringify([s, ...list]));
}

export function updateLocalCareSchedule(id: number, updated: MedicalScheduleResponse): void {
  window.localStorage.setItem(
    CARE_KEY,
    JSON.stringify(getLocalCareSchedules().map((x) => (x.id === id ? updated : x)))
  );
}

export function deleteLocalCareSchedule(id: number): void {
  window.localStorage.setItem(
    CARE_KEY,
    JSON.stringify(getLocalCareSchedules().filter((x) => x.id !== id))
  );
}
