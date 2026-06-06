"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck, Check, ChevronLeft } from "lucide-react";
import { updateConsent } from "@/features/consent/api";
import { updateMode } from "@/features/auth/api";
import { setMode } from "@/features/auth/mode";

const PURPLE = "#7C5CCF";

const ITEMS = [
  "본 서비스는 의료 진단·처방·치료 결정을 수행하지 않습니다",
  "검사 결과 자동 판독·해석·정상/비정상 판정을 \n 수행하지 않습니다",
  "약물 효능·부작용·주의사항·식이 상호작용 정보는 \n 외부 공식 자료 진입점만 제공합니다 ",
  "임신·수유 등 민감 정보 수집에 동의합니다",
  "사용자가 입력한 정보의 정리·표시·외부 공식 자료 안내에 \n 한정합니다",
];

export default function ModeConsentPage() {
  const router = useRouter();
  const [checked, setChecked] = useState<boolean[]>(Array(ITEMS.length).fill(false));
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const allChecked = checked.every(Boolean);

  function toggle(i: number) {
    setChecked((prev) => prev.map((v, j) => (j === i ? !v : v)));
  }

  async function proceed() {
    if (!allChecked || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await updateConsent("sensitive_medical", true);
      await updateMode("autoimmune");
      setMode("autoimmune");
      router.replace("/disease/new");
    } catch (e) {
      setSubmitting(false);
      setError("동의 처리 중 문제가 발생했어요. 잠시 후 다시 시도해주세요.");
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col px-5 py-8">
      <div className="flex items-center gap-6">
        <button onClick={() => router.back()} aria-label="뒤로" className="-ml-1"><ChevronLeft className="h-6 w-6" /></button>
        <h1 className="text-[18px] font-bold">자가면역 모드 동의</h1>
      </div>

      {/* 보라 배너 */}
      <div className="mt-12 flex items-center gap-10 rounded-2xl border p-4" style={{ borderColor: PURPLE, background: PURPLE + "24" }}>
        <ShieldCheck className="h-6 w-6" style={{ color: PURPLE }} />
        <p className="text-sm font-semibold" style={{ color:"#191F28" }}>자가면역 모드는 특수한 의료 정보을 다룹니다</p>
      </div>

      <p className="mt-6 text-sm font-semibold text-muted-foreground">필수 동의 사항</p>
      <div className="mt-2 divide-y divide-border rounded-2xl border border-border bg-white">
        {ITEMS.map((item, i) => (
          <button key={i} onClick={() => toggle(i)} className="flex w-full items-start gap-3 px-4 py-4 text-left">
            <span
              className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded"
              style={checked[i] ? { background: PURPLE } : { border: "2px solid hsl(var(--border))" }}
            >
              {checked[i] && <Check className="h-3.5 w-3.5 text-white" />}
            </span>
            <span className="whitespace-pre-line text-sm">{item}</span>
          </button>
        ))}
      </div>

      <div className="mt-auto pt-8">
        <button
          onClick={proceed}
          disabled={!allChecked || submitting}
          className="w-full rounded-xl py-3.5 text-base font-bold text-white disabled:opacity-50"
          style={{ background: PURPLE }}
        >
          {submitting ? "처리 중…" : allChecked ? "전체 동의 후 계속" : "전체 동의가 필요합니다"}
        </button>
        {error && <p className="mt-3 text-center text-sm text-red-500">{error}</p>}
        <p className="mt-12 text-center text-xs text-muted-foreground">
          본 안내는 일반 정보이며 진단·처방을 대체하지 않습니다.<br />담당 의료진 상담을 권고합니다.
        </p>
      </div>
    </main>
  );
}
