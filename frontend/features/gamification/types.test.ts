import { levelOf, levelName, progressRatio, nextLevelPoints } from "./types";

describe("gamification 포인트 레벨 계산 (REQ-GAME-002)", () => {
  test("levelOf: 포인트 구간별 레벨", () => {
    expect(levelOf(0)).toBe(1);
    expect(levelOf(99)).toBe(1);
    expect(levelOf(100)).toBe(2);
    expect(levelOf(300)).toBe(3);
    expect(levelOf(600)).toBe(4);
    expect(levelOf(1000)).toBe(5);
    expect(levelOf(5000)).toBe(5);
  });

  test("levelName: 레벨별 이름", () => {
    expect(levelName(0)).toBe("건강 새싹");
    expect(levelName(240)).toBe("건강 관리자");
    expect(levelName(1000)).toBe("건강 마스터");
  });

  test("progressRatio: 0~1 범위, 다음 레벨 진척도", () => {
    expect(progressRatio(0)).toBe(0);
    expect(progressRatio(100)).toBe(0); // 레벨 2 시작
    expect(progressRatio(200)).toBeCloseTo(0.5); // 100~300 중간
    expect(progressRatio(1000)).toBe(1); // 최고 레벨
    expect(progressRatio(99999)).toBe(1);
  });

  test("nextLevelPoints: 다음 레벨 포인트", () => {
    expect(nextLevelPoints(0)).toBe(100);
    expect(nextLevelPoints(240)).toBe(300);
    expect(nextLevelPoints(1000)).toBe(1000); // 최고
  });
});
