// 인증 도메인 타입 (백엔드 routers/auth.py 기준)

export type Gender = "MALE" | "FEMALE";

export interface SignupRequest {
  email: string;
  password: string;
  name: string;
  gender: Gender;
  birth_date: string; // YYYY-MM-DD
  phone_number: string; // 010-0000-0000
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  // refresh_token은 httpOnly 쿠키로 내려옴 (body에 없음)
}

export interface UserProfile {
  id: number;
  email: string;
  name: string;
  gender?: Gender;
  birth_date?: string;
  phone_number?: string;
  height?: number;
  weight?: number;
  user_type?: "general" | "autoimmune";
}
