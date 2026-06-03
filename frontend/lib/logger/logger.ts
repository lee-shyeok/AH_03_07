// NFR-MNTN-001: 구조화 로그
// 개발: 콘솔, 프로덕션: 향후 수집 엔드포인트로 전송 가능하도록 구조화

type LogLevel = "debug" | "info" | "warn" | "error";
type LogCategory =
  | "auth"
  | "api"
  | "consent"
  | "navigation"
  | "userAction"
  | "system";

interface LogEntry {
  ts: string;
  level: LogLevel;
  category: LogCategory;
  message: string;
  meta?: Record<string, unknown>;
}

const isDev = process.env.NODE_ENV !== "production";

function emit(entry: LogEntry) {
  // 민감정보(비밀번호/토큰)는 호출부에서 제외할 것
  if (isDev) {
    const fn =
      entry.level === "error"
        ? console.error
        : entry.level === "warn"
          ? console.warn
          : console.log;
    fn(`[${entry.category}] ${entry.message}`, entry.meta ?? "");
  }
  // TODO(prod): 수집 엔드포인트로 전송 (배치)
}

function log(
  level: LogLevel,
  category: LogCategory,
  message: string,
  meta?: Record<string, unknown>
) {
  emit({ ts: new Date().toISOString(), level, category, message, meta });
}

export const logger = {
  debug: (c: LogCategory, m: string, meta?: Record<string, unknown>) =>
    log("debug", c, m, meta),
  info: (c: LogCategory, m: string, meta?: Record<string, unknown>) =>
    log("info", c, m, meta),
  warn: (c: LogCategory, m: string, meta?: Record<string, unknown>) =>
    log("warn", c, m, meta),
  error: (c: LogCategory, m: string, meta?: Record<string, unknown>) =>
    log("error", c, m, meta),
};
