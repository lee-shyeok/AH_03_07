// 인증 클라이언트 상태 (zustand) — 최소화 원칙
// - 액세스 토큰은 lib/api/client.ts 메모리에만 보관(localStorage 미저장, XSS 표면 최소화)
// - 이 store는 토큰의 미러가 아니라 "로그인 사용자(user)"와 인증 여부만 보유
// - 서버 데이터(목록/조회)는 절대 여기 담지 않음 → TanStack Query 캐시 사용
import { create } from "zustand";
import { setAccessToken } from "@/lib/api/client";
import type { UserProfile } from "@/features/auth/types";

interface AuthState {
  user: UserProfile | null;
  isAuthenticated: boolean;
  /** 로그인 성공 시: 토큰(메모리) + 사용자 설정 */
  setSession: (accessToken: string, user?: UserProfile | null) => void;
  setUser: (user: UserProfile | null) => void;
  /** 로그아웃: 토큰/사용자 제거 */
  clear: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  setSession: (accessToken, user = null) => {
    setAccessToken(accessToken); // 메모리 보관
    set({ user, isAuthenticated: true });
  },
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  clear: () => {
    setAccessToken(null);
    set({ user: null, isAuthenticated: false });
  },
}));
