import { codeStepSchema, signupInfoSchema } from "./schema";

describe("이메일 인증 위저드 스키마", () => {
  test("codeStepSchema: 6자리 숫자만 통과", () => {
    expect(codeStepSchema.safeParse({ code: "123456" }).success).toBe(true);
    expect(codeStepSchema.safeParse({ code: "12345" }).success).toBe(false);
    expect(codeStepSchema.safeParse({ code: "abcdef" }).success).toBe(false);
  });

  const info = { password: "abcd123!", name: "홍길동", gender: "MALE" as const, birthDate: "1990-01-01", phone: "010-1234-5678" };
  test("signupInfoSchema: 정상 입력 통과", () => {
    expect(signupInfoSchema.safeParse(info).success).toBe(true);
  });
  test("signupInfoSchema: 특수문자 없는 비밀번호 실패", () => {
    expect(signupInfoSchema.safeParse({ ...info, password: "abcd1234" }).success).toBe(false);
  });
  test("signupInfoSchema: 잘못된 전화번호 실패", () => {
    expect(signupInfoSchema.safeParse({ ...info, phone: "12345" }).success).toBe(false);
  });
});
