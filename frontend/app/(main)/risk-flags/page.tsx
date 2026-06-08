"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ClipboardCheck } from "lucide-react";
import {
  listRiskFlags,
  updateRiskFlagStatus,
  type RiskFlagItem,
  type RiskFlagStatus,
  type RiskFlagSourceType,
} from "@/features/risk-flag/api";

const TABS: { key: RiskFlagStatus; label: string }[] = [
  { key: "ACTIVE", label: "활성" },
  { key: "RESOLVED", label: "해소됨" },
  { key: "DISMISSED", label: "숨김" },
];

const SOURCE_LABEL: Record<RiskFlagSourceType, string> = {
  SYMPTOM_CHECK: "증상 체크",
  RISK_PROFILE: "위험요인 프로필",
  LAB_RESULT: "검사 결과",
};

function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;
}

export default function RiskFlagsPage() {
  const [tab, setTab] = useState<RiskFlagStatus>("ACTIVE");
  const [flags, setFlags] = useState<RiskFlagItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [openDetail, setOpenDetail] = useState<number | null>(null);

  useEffect(() => {
    setLoading(true);
    listRiskFlags(tab)
      .then(setFlags)
      .catch(() => setFlags([]))
      .finally(() => setLoading(false));
  }, [tab]);

  async function changeStatus(id: number, status: "RESOLVED" | "DISMISSED") {
    try {
      await updateRiskFlagStatus(id, status);
      setFlags((prev) => prev.filter((f) => f.id !== id));
    } catch {
      /* 실패 시 유지 */
    }
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 pb-28 pt-8">
      <h1 className="text-3xl font-extrabold leading-tight">의료진 확인이<br />필요한 신호</h1>
      <p className="mt-2 text-sm text-muted-foreground">의료진 확인이 권고되는 신호 모음</p>

      {/* 면책 카드 (상시) */}
      <div className="mt-4 rounded-xl bg-muted p-3 text-xs leading-relaxed text-muted-foreground">
        본 앱은 진단·예측을 수행하지 않습니다. 의료진 확인이 권고되는 사용자 기록 기반 신호만 표시합니다.
      </div>

      <Link
        href="/symptom-check"
        className="mt-4 flex items-center justify-between rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3.5"
      >
        <span className="flex items-center gap-2 text-sm font-semibold text-destructive">
          <ClipboardCheck className="h-4 w-4" />
          주의 증상 체크하기
        </span>
        <span className="text-xs text-destructive">→</span>
      </Link>

      {/* 탭 */}
      <div className="mt-6 flex gap-2">
        {TABS.map((t) => {
          const on = t.key === tab;
          return (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className="flex-1 rounded-xl py-2 text-sm font-semibold transition"
              style={
                on
                  ? { background: "#F5C518", color: "#1a1a1a" }
                  : { background: "hsl(var(--muted))", color: "hsl(var(--muted-foreground))" }
              }
            >
              {t.label}
            </button>
          );
        })}
      </div>

      {/* 리스트 */}
      <div className="mt-4 space-y-3">
        {loading ? (
          <p className="py-10 text-center text-sm text-muted-foreground">불러오는 중...</p>
        ) : flags.length === 0 ? (
          <p className="py-12 text-center text-sm text-muted-foreground">현재 확인이 필요한 신호가 없습니다 ✅</p>
        ) : (
          flags.map((f) => {
            const isActive = f.status === "ACTIVE";
            return (
              <div
                key={f.id}
                className="rounded-2xl p-5"
                style={
                  isActive
                    ? { border: "2px solid #F5C518", background: "#FEF9E7" }
                    : { border: "1px solid hsl(var(--border))", background: "hsl(var(--muted) / 0.4)" }
                }
              >
                <p className="font-bold">⚠️ 의료진 확인 필요 신호{!isActive && " ✓"}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {formatDate(f.created_at)} · {SOURCE_LABEL[f.source_type] ?? f.source_type}
                </p>
                <p className="mt-2 whitespace-pre-line font-medium">{f.message || f.flag_label}</p>
                {f.consultation_recommended && (
                  <p className="mt-3 text-sm">💡 담당 의료진 상담을 권고드립니다.</p>
                )}

                {openDetail === f.id && (
                  <div className="mt-3 rounded-lg bg-white/60 p-3 text-left text-xs text-muted-foreground">
                    <p>유형: {f.flag_label}</p>
                    <p className="mt-1">분류: {f.category}</p>
                    <p className="mt-1">코드: {f.flag_code}</p>
                  </div>
                )}

                {isActive ? (
                  <div className="mt-4 grid grid-cols-3 gap-2">
                    <button
                      onClick={() => changeStatus(f.id, "RESOLVED")}
                      className="rounded-xl bg-white py-2.5 text-xs font-bold shadow-sm"
                    >
                      상담 완료
                    </button>
                    <button
                      onClick={() => changeStatus(f.id, "DISMISSED")}
                      className="rounded-xl bg-white py-2.5 text-xs font-bold shadow-sm"
                    >
                      숨김
                    </button>
                    <button
                      onClick={() => setOpenDetail((p) => (p === f.id ? null : f.id))}
                      className="rounded-xl bg-white py-2.5 text-xs font-bold shadow-sm"
                    >
                      상세 보기
                    </button>
                  </div>
                ) : (
                  <div className="mt-4 flex items-center justify-between">
                    <span className="text-xs font-bold text-muted-foreground">
                      {f.status === "RESOLVED" ? "상담 완료됨" : "숨김 처리됨"}
                    </span>
                    <button
                      onClick={() => setOpenDetail((p) => (p === f.id ? null : f.id))}
                      className="text-xs font-semibold text-muted-foreground underline"
                    >
                      상세 보기
                    </button>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </main>
  );
}
