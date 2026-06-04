"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, Check, ChevronLeft } from "lucide-react";
import { Card } from "@/components/ui/card";

const RED = "#EF5B5B";

const SYMPTOMS = [
  "호흡곤란 또는 가슴 답답함",
  "가슴 통증 (지속적 또는 압박감)",
  "38°C 이상 고열 (3일 이상 지속)",
  "코피·잇몸 출혈 등 출혈 증상",
  "잦은 멍 또는 자색반점",
  "심한 두통 또는 어지러움",
  "새로운 발진 또는 피부 변화",
  "팔다리 또는 얼굴 부어오름",
];

export default function SymptomCheckPage() {
  const router = useRouter();
  const [checked, setChecked] = useState<number[]>([0, 2]);
  const [modal, setModal] = useState(false);

  function toggle(i: number) {
    setChecked((prev) => (prev.includes(i) ? prev.filter((x) => x !== i) : [...prev, i]));
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8 pb-28">
      <div className="flex items-center gap-2 mb-4">
        <button onClick={() => router.back()} className="p-1 text-foreground">
          <ChevronLeft className="h-6 w-6" />
        </button>
        <h1 className="text-xl font-bold">주의 증상 체크</h1>
      </div>

      {/* 빨강 안내 */}
      <div className="mt-4 flex items-center gap-3 rounded-2xl border p-4" style={{ borderColor: RED + "44", background: RED + "10" }}>
        <AlertTriangle className="h-6 w-6" style={{ color: RED }} />
        <div>
          <p className="font-bold">다음 증상이 있다면 즉시 확인하세요</p>
          <p className="text-sm" style={{ color: RED }}>의료진 상담이 필요한 신호입니다</p>
        </div>
      </div>

      <p className="mt-6 text-sm text-muted-foreground">최근 24시간 내 증상</p>
      <Card className="mt-2 divide-y divide-border">
        {SYMPTOMS.map((s, i) => {
          const on = checked.includes(i);
          return (
            <button key={i} onClick={() => toggle(i)} className="flex w-full items-center gap-3 px-4 py-3.5 text-left">
              <span
                className="flex h-5 w-5 items-center justify-center rounded"
                style={on ? { background: RED } : { border: "2px solid hsl(var(--border))" }}
              >
                {on && <Check className="h-3.5 w-3.5 text-white" />}
              </span>
              <span className="text-sm">{s}</span>
            </button>
          );
        })}
      </Card>

      <div className="fixed inset-x-0 bottom-16 mx-auto max-w-md px-5">
        <button
          onClick={() => setModal(true)}
          className="w-full rounded-xl py-3.5 text-base font-bold text-white"
          style={{ background: RED }}
        >
          의료진에게 알리기
        </button>
        <p className="mt-3 text-center text-xs text-muted-foreground">
          ⚠️ 응급 상황이라면 119에 즉시 전화하세요<br />본 화면은 의료적 진단을 대체하지 않습니다
        </p>
      </div>

      {/* 모달 */}
      {modal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-8" onClick={() => setModal(false)}>
          <Card className="w-full max-w-sm p-6 text-center" onClick={(e) => e.stopPropagation()}>
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full" style={{ background: RED + "20" }}>
              <AlertTriangle className="h-8 w-8" style={{ color: RED }} />
            </div>
            <h2 className="mt-4 text-xl font-bold">의료진 확인이<br />필요합니다</h2>
            <p className="mt-2 text-sm text-muted-foreground">선택하신 증상은 즉각적인<br />의료적 평가가 필요할 수 있습니다</p>
            <a href="tel:119" className="mt-5 block w-full rounded-xl py-3.5 font-bold text-white" style={{ background: RED }}>
              119 응급 전화
            </a>
            <a href="tel:020000000" className="mt-2 block w-full rounded-xl border-2 border-primary py-3.5 font-bold text-primary">
              담당 의료진 연락
            </a>
            <button onClick={() => setModal(false)} className="mt-4 text-sm text-muted-foreground">나중에 하기</button>
            <p className="mt-4 text-xs text-muted-foreground">본 알림은 진단·처방을 대체하지 않습니다</p>
          </Card>
        </div>
      )}
    </main>
  );
}
