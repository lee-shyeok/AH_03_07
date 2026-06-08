"use client";

import { useState } from "react";
import { AlertTriangle, Check, ChevronLeft, Info } from "lucide-react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import {
  postSymptomCheck,
  type SymptomCode,
  type SymptomCheckResponse,
} from "@/features/symptom/api";

const RED = "#EF5B5B";
const AMBER = "#F59E0B";

const SYMPTOMS: { code: SymptomCode; label: string; redFlag: boolean; info: string }[] = [
  { code: "DYSPNEA", label: "호흡곤란", redFlag: true, info: "숨쉬기 힘들거나 가슴이 답답한 느낌이 들어요." },
  { code: "ALTERED_CONSCIOUSNESS", label: "의식 저하", redFlag: true, info: "정신이 흐려지거나 반응이 평소보다 둔해요." },
  { code: "JAUNDICE", label: "황달 (눈 흰자·피부 노란빛)", redFlag: true, info: "눈 흰자나 피부가 노랗게 보여요." },
  { code: "SEVERE_BLEEDING", label: "심한 멍 또는 비정상 출혈", redFlag: true, info: "멈추지 않는 출혈이나 원인 모를 멍이 있어요." },
  { code: "FEVER", label: "발열", redFlag: false, info: "평소보다 체온이 높게 느껴져요." },
  { code: "PERSISTENT_COUGH", label: "지속되는 기침", redFlag: false, info: "수일 이상 기침이 계속돼요." },
  { code: "SEVERE_ABDOMINAL_PAIN", label: "심한 복통", redFlag: false, info: "참기 어려운 배 통증이 있어요." },
  { code: "SHINGLES_SUSPECTED", label: "대상포진 의심 수포", redFlag: false, info: "띠 모양으로 번지는 물집이 보여요." },
  { code: "MOUTH_SORES", label: "입안 헐음·구내염", redFlag: false, info: "입안이 헐거나 아파요." },
  { code: "BLURRED_VISION", label: "시야 흐림", redFlag: false, info: "사물이 흐릿하게 보여요." },
];

export default function SymptomCheckPage() {
  const router = useRouter();
  const [checked, setChecked] = useState<SymptomCode[]>([]);
  const [openInfo, setOpenInfo] = useState<SymptomCode | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<SymptomCheckResponse | null>(null);
  const [modal, setModal] = useState(false);

  function toggle(code: SymptomCode) {
    setResult(null);
    setChecked((prev) => (prev.includes(code) ? prev.filter((x) => x !== code) : [...prev, code]));
  }

  async function handleSubmit() {
    setSubmitting(true);
    try {
      const res = await postSymptomCheck(checked);
      setResult(res);
      if (res.red_flag_triggered) setModal(true);
    } catch {
      setResult(null);
    } finally {
      setSubmitting(false);
    }
  }

  const triggeredLabels = (result?.red_flag_symptoms ?? [])
    .map((c) => SYMPTOMS.find((s) => s.code === c)?.label)
    .filter(Boolean)
    .join(", ");

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
          <p className="font-bold">지난 일주일 동안 다음 증상이 있었나요?</p>
          <p className="text-sm" style={{ color: RED }}>해당하는 항목을 체크해주세요</p>
        </div>
      </div>

      {/* 범례 (Red Flag / 일반) */}
      <div className="mt-6 flex items-center gap-4 px-1 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: RED }} /> 즉시 확인 신호
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: AMBER }} /> 일반 증상
        </span>
      </div>

      <Card className="mt-2 divide-y divide-border">
        {SYMPTOMS.map((s) => {
          const on = checked.includes(s.code);
          const dot = s.redFlag ? RED : AMBER;
          return (
            <div key={s.code} className="px-4 py-3.5">
              <div className="flex items-center gap-3">
                <button onClick={() => toggle(s.code)} className="flex flex-1 items-center gap-3 text-left">
                  <span
                    className="flex h-5 w-5 items-center justify-center rounded"
                    style={on ? { background: dot } : { border: "2px solid hsl(var(--border))" }}
                  >
                    {on && <Check className="h-3.5 w-3.5 text-white" />}
                  </span>
                  <span className="inline-block h-2 w-2 shrink-0 rounded-full" style={{ background: dot }} />
                  <span className="text-sm">{s.label}</span>
                </button>
                <button
                  onClick={() => setOpenInfo((p) => (p === s.code ? null : s.code))}
                  aria-label={`${s.label} 설명`}
                  className="p-1 text-muted-foreground"
                >
                  <Info className="h-4 w-4" />
                </button>
              </div>
              {openInfo === s.code && (
                <p className="mt-2 pl-8 text-xs text-muted-foreground">{s.info}</p>
              )}
            </div>
          );
        })}
      </Card>

      {/* 일반 항목 결과 — 의료진 상담 권고 (Red Flag 아닐 때) */}
      {result && !result.red_flag_triggered && result.risk_flag_ids.length > 0 && (
        <Card className="mt-4 p-4" style={{ borderColor: AMBER + "55", background: AMBER + "10" }}>
          <p className="text-sm font-semibold">의료진 상담을 권고해요</p>
          <p className="mt-1 text-sm text-muted-foreground">
            체크하신 증상은 다음 진료 때 담당 의료진과 상의해보시는 것이 좋아요.
          </p>
        </Card>
      )}
      {result && !result.red_flag_triggered && result.risk_flag_ids.length === 0 && (
        <p className="mt-4 text-center text-sm text-muted-foreground">기록되었습니다.</p>
      )}

      <div className="fixed inset-x-0 bottom-16 mx-auto max-w-md px-5">
        <button
          onClick={handleSubmit}
          disabled={submitting}
          className="w-full rounded-xl py-3.5 text-base font-bold text-white disabled:opacity-60"
          style={{ background: RED }}
        >
          {submitting ? "기록 중..." : "체크 완료"}
        </button>
        <p className="mt-3 text-center text-xs text-muted-foreground">
          ⚠️ 응급 상황이라면 119에 즉시 전화하세요<br />본 화면은 의료적 진단을 대체하지 않습니다
        </p>
      </div>

      {/* 모달 — 의료진 확인 안내 (REQ-SYMP-002 / 와이어프레임 20) */}
      {modal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-8" onClick={() => setModal(false)}>
          <Card className="w-full max-w-sm p-6 text-center" onClick={(e) => e.stopPropagation()}>
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full" style={{ background: RED + "20" }}>
              <AlertTriangle className="h-8 w-8" style={{ color: RED }} />
            </div>
            <h2 className="mt-4 text-xl font-bold">의료진 확인이<br />필요한 증상이에요</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              {triggeredLabels ? `'${triggeredLabels}' 증상은 ` : "체크하신 증상은 "}
              즉시 담당 의료진 상담 또는 응급실 방문이 권고됩니다
            </p>
            <div className="mt-4 rounded-xl bg-muted p-3 text-xs text-muted-foreground">
              본 앱은 진단을 수행하지 않으며 보조 안내만 제공합니다
            </div>
            <a
              href="https://www.e-gen.or.kr/"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-5 block w-full rounded-xl py-3.5 font-bold text-white"
              style={{ background: RED }}
            >
              응급의료기관 정보 보기
            </a>
            <button
              onClick={() => setModal(false)}
              className="mt-2 block w-full rounded-xl border-2 border-primary py-3.5 font-bold text-primary"
            >
              닫기
            </button>
            <p className="mt-4 text-xs text-muted-foreground">
              <a href="tel:119" className="font-semibold underline">119</a> 직접 호출을 권장합니다.
            </p>
            <p className="mt-1 text-[11px] text-muted-foreground">
              위치 기반 일반 정보이며 특정 의료기관 추천이 아닙니다.
            </p>
          </Card>
        </div>
      )}
    </main>
  );
}
