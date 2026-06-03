import { loginSchema, signupSchema } from "./schema";

describe("auth Zod 스키마", () => {
  test("loginSchema: 올바른 입력 통과", () => {
    expect(loginSchema.safeParse({ email: "a@b.com", password: "x" }).success).toBe(true);
  });
  test("loginSchema: 잘못된 이메일 실패", () => {
    expect(loginSchema.safeParse({ email: "not-email", password: "x" }).success).toBe(false);
  });
  test("loginSchema: 빈 비밀번호 실패", () => {
    expect(loginSchema.safeParse({ email: "a@b.com", password: "" }).success).toBe(false);
  });

  test("signupSchema: 약한 비밀번호(숫자 없음) 실패", () => {
    const r = signupSchema.safeParse({
      email: "a@b.com", password: "abcdefgh", passwordConfirm: "abcdefgh", name: "홍길동", agree: true,
    });
    expect(r.success).toBe(false);
  });
  test("signupSchema: 비밀번호 불일치 실패", () => {
    const r = signupSchema.safeParse({
      email: "a@b.com", password: "abcd1234", passwordConfirm: "abcd9999", name: "홍길동", agree: true,
    });
    expect(r.success).toBe(false);
  });
  test("signupSchema: 약관 미동의 실패", () => {
    const r = signupSchema.safeParse({
      email: "a@b.com", password: "abcd1234", passwordConfirm: "abcd1234", name: "홍길동", agree: false,
    });
    expect(r.success).toBe(false);
  });
  test("signupSchema: 올바른 입력 통과", () => {
    const r = signupSchema.safeParse({
      email: "a@b.com", password: "abcd1234", passwordConfirm: "abcd1234", name: "홍길동", agree: true,
    });
    expect(r.success).toBe(true);
  });
});
