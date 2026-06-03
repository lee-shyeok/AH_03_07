// NFR-SEC-001: JWT 인증 API 클라이언트
// - baseUrl은 /api (next.config rewrite로 EC2 프록시 → Mixed Content/CORS 회피)
// - credentials: 'include' 로 httpOnly refresh 쿠키 동반
// - 401 시 토큰 자동 갱신 후 1회 재시도

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, message: string, body?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  /** 내부 재시도 플래그 (자동 갱신 후 무한루프 방지) */
  _retry?: boolean;
};

// access token은 메모리 보관 (XSS 표면 최소화). refresh는 httpOnly 쿠키(서버 관리).
let accessToken: string | null = null;
export function setAccessToken(token: string | null) {
  accessToken = token;
}
export function getAccessToken() {
  return accessToken;
}

// 동시 401 다발 시 갱신은 1회만 (Completer 패턴)
let refreshPromise: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        // 백엔드: GET /api/v1/auth/token/refresh (refresh는 쿠키로 전송)
        const res = await fetch(`${BASE_URL}/v1/auth/token/refresh`, {
          method: "GET",
          credentials: "include",
        });
        if (!res.ok) return false;
        const data = await res.json().catch(() => null);
        if (data?.access_token) {
          setAccessToken(data.access_token);
          return true;
        }
        return false;
      } catch {
        return false;
      } finally {
        // 다음 갱신을 위해 해제
        setTimeout(() => (refreshPromise = null), 0);
      }
    })();
  }
  return refreshPromise;
}

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { body, headers, _retry, ...rest } = options;

  const finalHeaders: Record<string, string> = {
    ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    ...(headers as Record<string, string>),
  };

  const res = await fetch(`${BASE_URL}${path}`, {
    ...rest,
    headers: finalHeaders,
    credentials: "include",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  // 401 → 토큰 갱신 후 1회 재시도
  if (res.status === 401 && !_retry) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      return apiFetch<T>(path, { ...options, _retry: true });
    }
  }

  const text = await res.text();
  const data = text ? safeJson(text) : null;

  if (!res.ok) {
    const message =
      (data as { detail?: string })?.detail || `요청 실패 (${res.status})`;
    throw new ApiError(res.status, message, data);
  }

  return data as T;
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}
