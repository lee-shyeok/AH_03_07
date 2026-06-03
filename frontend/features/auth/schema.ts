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
