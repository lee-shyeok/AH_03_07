// 포인트 · 방 상태 로컬 저장소 (Flutter RoomService / GamificationService 이식)
// 백엔드 연동 시 이 함수들을 API 호출로 교체하면 됨.
import { EMPTY_ROOM, type RoomState } from "./room";
import { DUMMY_POINTS } from "./data";

const POINTS_KEY = "mg_points_v1";
const CHECKIN_KEY = "mg_checkin_v1";
const ROOM_KEY = "mg_room_v1";

function browser() {
  return typeof window !== "undefined";
}

// ── 포인트 ─────────────────────────────────────────────────
export function getPoints(): number {
  if (!browser()) return DUMMY_POINTS.totalPoints;
  const raw = window.localStorage.getItem(POINTS_KEY);
  if (raw == null) return DUMMY_POINTS.totalPoints;
  const n = parseInt(raw, 10);
  return Number.isFinite(n) ? n : DUMMY_POINTS.totalPoints;
}

export function setPoints(value: number) {
  if (!browser()) return;
  window.localStorage.setItem(POINTS_KEY, String(Math.max(0, value)));
}

export function isCheckedInToday(): boolean {
  if (!browser()) return false;
  return window.localStorage.getItem(CHECKIN_KEY) === todayKey();
}

export function markCheckedIn() {
  if (!browser()) return;
  window.localStorage.setItem(CHECKIN_KEY, todayKey());
}

function todayKey(): string {
  // Date.now() 사용 가능 환경(브라우저)에서만 호출됨
  const d = new Date();
  return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
}

// ── 방 상태 ────────────────────────────────────────────────
export function loadRoom(): RoomState {
  if (!browser()) return { ...EMPTY_ROOM };
  const raw = window.localStorage.getItem(ROOM_KEY);
  if (!raw) return { ...EMPTY_ROOM };
  try {
    const parsed = JSON.parse(raw) as Partial<RoomState>;
    return {
      wallpaperIndex: parsed.wallpaperIndex ?? 0,
      floorIndex: parsed.floorIndex ?? 0,
      ownedItemIds: parsed.ownedItemIds ?? [],
      placedItems: parsed.placedItems ?? [],
    };
  } catch {
    return { ...EMPTY_ROOM };
  }
}

export function saveRoom(state: RoomState) {
  if (!browser()) return;
  window.localStorage.setItem(ROOM_KEY, JSON.stringify(state));
}
