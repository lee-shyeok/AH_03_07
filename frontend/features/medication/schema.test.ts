import { medicationSchema } from "./schema";

const base = { name: "MTX", category: "면역억제제", dose: "1", unit: "정", freq: 2, timings: ["아침"] };

describe("medication Zod 스키마", () => {
  test("정상 입력 통과", () => {
    expect(medicationSchema.safeParse(base).success).toBe(true);
  });
  test("약품명 없으면 실패", () => {
    expect(medicationSchema.safeParse({ ...base, name: "" }).success).toBe(false);
  });
  test("복용량 없으면 실패", () => {
    expect(medicationSchema.safeParse({ ...base, dose: "" }).success).toBe(false);
  });
  test("복용 횟수 범위(1~4) 밖이면 실패", () => {
    expect(medicationSchema.safeParse({ ...base, freq: 5 }).success).toBe(false);
  });
});
