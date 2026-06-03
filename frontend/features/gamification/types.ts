// 게임화 (REQ-GAME-002) — Flutter gamification_models.dart 이식

export const LEVELS = [
  { points: 0, name: "건강 새싹" },
  { points: 100, name: "건강 관리자" },
  { points: 300, name: "건강 지킴이" },
  { points: 600, name: "건강 전문가" },
  { points: 1000, name: "건강 마스터" },
];

export interface UserPoints {
  totalPoints: number;
  todayCheckedIn: boolean;
}

export function levelOf(points: number): number {
  for (let i = LEVELS.length - 1; i >= 0; i--) {
    if (points >= LEVELS[i].points) return i + 1;
  }
  return 1;
}
export function levelName(points: number) {
  return LEVELS[levelOf(points) - 1].name;
}
export function progressRatio(points: number): number {
  const lv = levelOf(points);
  if (lv >= LEVELS.length) return 1;
  const cur = LEVELS[lv - 1].points;
  const next = LEVELS[lv].points;
  const range = next - cur;
  if (range === 0) return 1;
  return Math.min(1, Math.max(0, (points - cur) / range));
}
export function nextLevelPoints(points: number): number {
  const lv = levelOf(points);
  return lv >= LEVELS.length ? LEVELS[LEVELS.length - 1].points : LEVELS[lv].points;
}

export interface Badge {
  id: string;
  name: string;
  description: string;
  icon: string;
  earned: boolean;
}

export type RewardType = "title" | "theme";
export interface Reward {
  id: string;
  name: string;
  type: RewardType;
  requiredPoints: number;
  owned: boolean;
}
