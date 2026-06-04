// 인증 API (백엔드 routers/auth.py: /v1/auth/*)
import { apiFetch, setAccessToken } from "@/lib/api/client";
import { logger } from "@/lib/logger/logger";
import type {
  LoginRequest,
  LoginResponse,
  SignupRequest,
  UserProfile,
} from "./types";

// REQ-USER-002: 이메일 인증코드 발송
export async function sendEmailVerifyCode(email: string): Promise<void> {
  await apiFetch("/v1/auth/email-verify/send", {
    method: "POST",
    body: { email },
  });
  logger.info("auth", "이메일 인증코드 발송", { email });
}

// REQ-USER-002: 이메일 인증코드 확인
export async function confirmEmailVerifyCode(
  email: string,
  code: string
): Promise<void> {
  await apiFetch("/v1/auth/email-verify/confirm", {
    method: "POST",
    body: { email, code },
  });
  logger.info("auth", "이메일 인증 완료", { email });
}

// REQ-USER-001: 회원가입
export async function signup(req: SignupRequest): Promise<void> {
  await apiFetch("/v1/auth/signup", { method: "POST", body: req });
  logger.info("auth", "회원가입 완료", { email: req.email });
}

// REQ-USER-003: 로그인 (access_token 반환, refresh는 쿠키)
export async function login(req: LoginRequest): Promise<LoginResponse> {
  const res = await apiFetch<LoginResponse>("/v1/auth/login", {
    method: "POST",
    body: req,
  });
  if (res?.access_token) setAccessToken(res.access_token);
  logger.info("auth", "로그인 성공", { email: req.email });
  return res;
}

// REQ-USER-005: 로그아웃
export async function logout(): Promise<void> {
  try {
    await apiFetch("/v1/auth/logout", { method: "POST" });
  } catch {
    // 서버 실패해도 클라이언트 토큰은 비움
  }
  setAccessToken(null);
  logger.info("auth", "로그아웃");
}

// REQ-USER-006: 내 정보 조회
export async function getMe(): Promise<UserProfile> {
  return apiFetch<UserProfile>("/v1/users/me");
}

// REQ-USER-008: 회원탈퇴 (탈퇴 시 의료 데이터 즉시 삭제 — NFR-COMPLI-001)
export async function withdraw(): Promise<void> {
  await apiFetch("/v1/users/me", { method: "DELETE" });
  setAccessToken(null);
  logger.warn("auth", "회원탈퇴 완료");
}

// REQ-MODE-001/002: 모드 조회·전환
export interface ModeResponse {
  mode: "general" | "autoimmune";
  selected_at: string;
  updated_at: string;
}

export async function getMode(): Promise<ModeResponse> {
  return apiFetch<ModeResponse>("/v1/users/me/mode");
}

export async function updateMode(mode: "general" | "autoimmune"): Promise<ModeResponse> {
  return apiFetch<ModeResponse>("/v1/users/me/mode", { method: "PUT", body: { mode } });
}
