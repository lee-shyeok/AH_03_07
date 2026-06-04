// 인증 입력 검증 스키마 (Zod) — 클라이언트 즉시 검증
// 주의: 클라 검증은 UX용이며 보안 경계가 아님 — 서버 검증을 항상 신뢰.
import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().min(1, "이메일을 입력하세요").email("올바른 이메일 형식이 아닙니다"),
  password: z.string().min(1, "비밀번호를 입력하세요"),
});
export type LoginInput = z.infer<typeof loginSchema>;

export const signupSchema = z
  .object({
    email: z.string().min(1, "이메일을 입력하세요").email("올바른 이메일 형식이 아닙니다"),
    password: z
      .string()
      .min(8, "비밀번호는 8자 이상이어야 합니다")
      .regex(/[A-Za-z]/, "영문을 포함해야 합니다")
      .regex(/[0-9]/, "숫자를 포함해야 합니다"),
    passwordConfirm: z.string().min(1, "비밀번호를 한 번 더 입력하세요"),
    name: z.string().min(1, "이름을 입력하세요").max(40),
    agree: z.boolean().refine((v) => v === true, { message: "이용약관에 동의해주세요" }),
  })
  .refine((v) => v.password === v.passwordConfirm, {
    path: ["passwordConfirm"],
    message: "비밀번호가 일치하지 않습니다",
  });
export type SignupInput = z.infer<typeof signupSchema>;

// ── 이메일 인증 3단계 위저드 ──────────────────────────────
export const emailStepSchema = z.object({
  email: z.string().min(1, "이메일을 입력하세요").email("올바른 이메일 형식이 아닙니다"),
});
export type EmailStepInput = z.infer<typeof emailStepSchema>;

export const codeStepSchema = z.object({
  code: z.string().regex(/^\d{6}$/, "6자리 숫자 코드를 입력하세요"),
});
export type CodeStepInput = z.infer<typeof codeStepSchema>;

export const signupInfoSchema = z.object({
  password: z
    .string()
    .min(8, "비밀번호는 8자 이상이어야 합니다")
    .regex(/[A-Za-z]/, "영문을 포함해야 합니다")
    .regex(/[0-9]/, "숫자를 포함해야 합니다")
    .regex(/[^A-Za-z0-9]/, "특수문자를 포함해야 합니다"),
  name: z.string().min(1, "이름을 입력하세요").max(40),
  gender: z.enum(["MALE", "FEMALE"]),
  birthDate: z.string().min(1, "생년월일을 선택하세요"),
  phone: z.string().regex(/^01[016789]-?\d{3,4}-?\d{4}$/, "올바른 전화번호 형식이 아닙니다"),
});
export type SignupInfoInput = z.infer<typeof signupInfoSchema>;
