"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, Circle, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { updateConsent } from "@/features/consent/api";
import { withTimeout } from "@/lib/query/util";

const ITEMS = [
  "본 앱은 진단이나 처방을 수행하지 않습니다",
  "모든 의료 정보는 참고용이며 의료진 상담이 필요합니다",
  "안전 관리를 위해 위험요인 프로필 입력에 동의합니다",
  "임신·수유 등 민감 정보 수집에 동의합니다",
  "모든 안내는 검증된 출처 기반 정보입니다",
] as const;

export default function ConsentPage() {
  const router = useRouter();
  const [checked, setChecked] = useState<boolean[]>(Array(ITEMS.length).fill(false));
  const [loading, setLoading] = useState(false);

  const allChecked = checked.every(Boolean);

  function toggle(i: number) {
    setChecked((prev) => prev.map((v, idx) => (idx === i ? !v : v)));
  }

  async function handleConfirm() {
    if (!allChecked || loading) return;
    setLoading(true);
    try {
      await withTimeout(updateConsent("sensitive_medical", true));
    } catch {
      /* 백엔드 미가동 시 무시 */
    } finally {
      setLoading(false);
      router.push("/");
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-md flex-col min-h-dvh px-6 py-10">
      {/* 헤더 */}
      <div className="flex flex-col items-center gap-3 mb-8">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[#EDE9FF]">
          <ShieldCheck className="h-7 w-7 text-[#7C5CCF]" />
        </div>
        <h1 className="text-xl font-bold">자가면역 모드 동의</h1>
        <p className="text-center text-sm text-muted-foreground leading-5">
          자가면역 모드는 특수한 의료 정보를 다룹니다
        </p>
      </div>

      {/* 체크박스 목록 */}
      <ul className="flex-1 space-y-3">
        {ITEMS.map((label, i) => (
          <li key={i}>
            <button
              type="button"
              onClick={() => toggle(i)}
              className="flex w-full items-start gap-3 rounded-2xl border bg-white p-4 text-left transition-colors hover:bg-[#F5F0FF]"
            >
              {checked[i] ? (
                <CheckCircle2 className="mt-0.5 h-5 w-5 flex-shrink-0 text-[#7C5CCF]" />
              ) : (
                <Circle className="mt-0.5 h-5 w-5 flex-shrink-0 text-muted-foreground/40" />
              )}
              <span className="text-sm leading-5">{label}</span>
            </button>
          </li>
        ))}
      </ul>

      {/* 하단 영역 */}
      <div className="mt-8 space-y-4">
        <Button
          className="w-full h-12 text-sm font-semibold"
          disabled={!allChecked || loading}
          onClick={handleConfirm}
        >
          {loading ? "처리 중..." : "전체 동의 후 계속"}
        </Button>
        <p className="text-center text-[11px] leading-5 text-muted-foreground px-2">
          본 안내는 일반 정보이며 진단·처방을 대체하지 않습니다.{" "}
          담당 의료진 상담을 권고합니다
        </p>
      </div>
    </main>
  );
}
