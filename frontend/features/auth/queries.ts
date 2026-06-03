// 인증 서버 통신 (TanStack Query). 토큰/사용자 상태는 zustand auth store로 반영.
import { useMutation, useQuery } from "@tanstack/react-query";
import { login, logout, getMe } from "./api";
import type { LoginRequest } from "./types";
import { useAuthStore } from "@/stores/auth";

export const authKeys = {
  me: ["auth", "me"] as const,
};

// 로그인: 성공 시 토큰(메모리) 저장 후 내 정보 조회하여 store 반영
export function useLogin() {
  const setSession = useAuthStore((s) => s.setSession);
  const setUser = useAuthStore((s) => s.setUser);
  return useMutation({
    mutationFn: async (input: LoginRequest) => {
      const res = await login(input); // 내부에서 access token 메모리 저장
      setSession(res.access_token, null);
      try {
        const me = await getMe();
        setUser(me);
      } catch {
        // 사용자 조회 실패해도 로그인 자체는 성공 처리
      }
      return res;
    },
  });
}

export function useLogout() {
  const clear = useAuthStore((s) => s.clear);
  return useMutation({
    mutationFn: async () => {
      await logout();
    },
    onSettled: () => clear(),
  });
}

// 내 정보 조회 (인증된 경우에만 활성화하여 불필요한 401 방지)
export function useMe(enabled = true) {
  const setUser = useAuthStore((s) => s.setUser);
  return useQuery({
    queryKey: authKeys.me,
    queryFn: async () => {
      const me = await getMe();
      setUser(me);
      return me;
    },
    enabled,
    retry: false,
  });
}
