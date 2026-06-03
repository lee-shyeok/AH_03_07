// 사용자 모드(일반/자가면역) 로컬 저장 — REQ-MODE-001/003
// 백엔드 연동 시 PATCH /v1/users/me { user_type } 로 교체.
export type UserMode = "general" | "autoimmune";

const KEY = "mg_user_type";

export function getMode(): UserMode {
  if (typeof window === "undefined") return "general";
  const v = window.localStorage.getItem(KEY);
  return v === "autoimmune" ? "autoimmune" : "general";
}

export function setMode(mode: UserMode) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(KEY, mode);
}
