"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck, Check } from "lucide-react";

const PURPLE = "#7C5CCF";

const ITEMS = [
  "본 앱은 진단이나\n처방을 수행하지 않습니다",
  "모든 의료 정보는 참고용이며\n의료진 상담이 필요합니다",
  "안전 관리를 위해\n위험요인 프로필 입력에 동의합니다",
  "임신·수유 등 민감 정보 수집에 동의합니다",
  "모든 안내는 검증된 출처 기반 정보입니다",
];

export default function ModeConsentPage() {
  const router = useRouter();
  const [checked, setChecked] = useState<boolean[]>(Array(ITEMS.length).fill(false));
  const allChecked = checked.every(Boolean);

  function toggle(i: number) {
    setChecked((prev) => prev.map((v, j) => (j === i ? !v : v)));
  }

  function proceed() {
    // 전체 동의 처리
    router.replace("/disease/new");
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col px-5 py-8">
      <div className="flex items-center gap-2">
        <button onClick={() => router.back()} aria-label="뒤로" className="-ml-1 text-xl">‹</button>
        <h1 className="text-lg font-bold">자가면역 모드 동의</h1>
      </div>

      {/* 보라 배너 */}
      <div className="mt-5 flex items-center gap-3 rounded-2xl border p-4" style={{ borderColor: PURPLE + "55", background: PURPLE + "12" }}>
        <ShieldCheck className="h-5 w-5" style={{ color: PURPLE }} />
        <p className="text-sm font-semibold" style={{ color: PURPLE }}>자가면역 모드는 특수한 의료 정보을 다룹니다</p>
      </div>

      <p className="mt-6 text-sm font-semibold text-muted-foreground">필수 동의 사항</p>
      <div className="mt-2 divide-y divide-border rounded-2xl border border-border">
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
          disabled={!allChecked}
          className="w-full rounded-xl py-3.5 text-base font-bold text-white disabled:opacity-50"
          style={{ background: PURPLE }}
        >
          {allChecked ? "전체 동의 후 계속" : "전체 동의가 필요합니다"}
        </button>
        <p className="mt-4 text-center text-xs text-muted-foreground">
          본 안내는 일반 정보이며 진단·처방을 대체하지 않습니다.<br />담당 의료진 상담을 권고합니다.
        </p>
      </div>
    </main>
  );
}
