"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, AlertTriangle } from "lucide-react";

const SYMPTOMS = [
  "호흡곤란 또는 가슴 답답함",
  "가슴 통증 (지속적 또는 압박감)",
  "38℃ 이상 고열 (3일 이상 지속)",
  "코피·잇몸 출혈 등 출혈 증상",
  "잦은 멍 또는 자색반점",
  "심한 두통 또는 어지러움",
  "새로운 발진 또는 피부 변화",
  "팔다리 또는 얼굴 부어오름",
];

export default function SymptomCheckPage() {
  const router = useRouter();
  const [checked, setChecked] = useState<Set<number>>(new Set());

  function toggle(i: number) {
    setChecked((prev) => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });
  }

  function handleSubmit() {
    // 백엔드: POST /v1/symptoms/check
    alert("의료진에게 알림을 전송했습니다.");
    router.back();
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 pb-32 pt-6">
      <div className="flex items-center gap-2">
        <button onClick={() => router.back()} className="p-1 text-foreground">
          <ChevronLeft className="h-6 w-6" />
        </button>
        <h1 className="text-2xl font-bold">주의 증상 체크</h1>
      </div>

      <div className="mt-5 flex items-start gap-3 rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-destructive" />
        <div>
          <p className="text-sm font-semibold text-destructive">다음 증상이 있다면 즉시 확인하세요</p>
          <p className="mt-0.5 text-xs text-destructive/70">의료진 상담이 필요한 신호입니다</p>
        </div>
      </div>

      <p className="mt-6 text-sm font-semibold text-muted-foreground">최근 24시간 내 증상</p>
      <div className="mt-3 overflow-hidden rounded-2xl border border-border">
        {SYMPTOMS.map((symptom, i) => (
          <label
            key={i}
            className={"flex cursor-pointer items-center gap-3 px-4 py-3.5 " + (i > 0 ? "border-t border-border" : "")}
          >
            <input
              type="checkbox"
              checked={checked.has(i)}
              onChange={() => toggle(i)}
              className="h-5 w-5 accent-destructive"
            />
            <span className="text-sm">{symptom}</span>
          </label>
        ))}
      </div>

      <div className="fixed inset-x-0 bottom-16 mx-auto max-w-md space-y-2 px-5">
        <button
          onClick={handleSubmit}
          disabled={checked.size === 0}
          className="w-full rounded-2xl bg-destructive py-4 text-base font-bold text-white disabled:opacity-40"
        >
          의료진에게 알리기
        </button>
        <p className="text-center text-xs text-muted-foreground">
          ⚠ 응급 상황이라면 119에 즉시 전화하세요
        </p>
        <p className="text-center text-xs text-muted-foreground">
          본 화면은 의료적 진단을 대체하지 않습니다
        </p>
      </div>
    </main>
  );
}
