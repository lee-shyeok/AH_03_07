import { recordSchema } from "./schema";

describe("medical-records Zod 스키마", () => {
  test("필수값(병원명/방문일) 있으면 통과", () => {
    expect(recordSchema.safeParse({ hospital_name: "서울병원", visit_date: "2026-06-10" }).success).toBe(true);
  });
  test("병원명 누락 시 실패", () => {
    expect(recordSchema.safeParse({ hospital_name: "", visit_date: "2026-06-10" }).success).toBe(false);
  });
  test("방문일 누락 시 실패", () => {
    expect(recordSchema.safeParse({ hospital_name: "서울병원", visit_date: "" }).success).toBe(false);
  });
});
