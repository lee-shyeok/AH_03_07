"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck, Check, X, ChevronLeft } from "lucide-react";
import {
  upsertAutoimmuneProfile,
  type PregnancyStatus,
} from "@/features/autoimmune/api";

const PURPLE = "#7C5CCF";

const RISK_FACTORS = [
  { code: "liver_impairment", label: "간 기능 이상" },
  { code: "kidney_impairment", label: "신장 기능 이상" },
  { code: "tb_history", label: "결핵 이력" },
  { code: "hepatitis_history", label: "간염 이력" },
  { code: "immunosuppressant_history", label: "면역억제제 복용 이력" },
  { code: "other", label: "기타" },
] as const;

type RiskCode = (typeof RISK_FACTORS)[number]["code"];

const COMORBIDITIES = [
  { code: "diabetes", label: "당뇨" },
  { code: "hypertension", label: "고혈압" },
  { code: "thyroid", label: "갑상선 질환" },
  { code: "cardiovascular", label: "심혈관 질환" },
] as const;

type ComorbidCode = (typeof COMORBIDITIES)[number]["code"];

const PREGNANCY_OPTIONS: { label: string; value: PregnancyStatus }[] = [
  { label: "해당 없음", value: "none" },
  { label: "임신 계획", value: "planning" },
  { label: "임신 중", value: "pregnant" },
  { label: "수유 중", value: "breastfeeding" },
];

function CheckItem({
  label,
  checked,
  onClick,
}: {
  label: string;
  checked: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm"
    >
      <span
        className="flex h-5 w-5 shrink-0 items-center justify-center rounded"
        style={
          checked
            ? { background: PURPLE }
            : { border: "2px solid hsl(var(--border))" }
        }
      >
        {checked && <Check className="h-3.5 w-3.5 text-white" />}
      </span>
      {label}
    </button>
  );
}

export default function RiskProfilePage() {
  const router = useRouter();

  const [selectedFactors, setSelectedFactors] = useState<RiskCode[]>([]);
  const [otherText, setOtherText] = useState("");
  const [pregnancy, setPregnancy] = useState<PregnancyStatus>("none");
  const [vaccineInput, setVaccineInput] = useState("");
  const [vaccines, setVaccines] = useState<string[]>([]);
  const [age, setAge] = useState("");
  const [drugAllergy, setDrugAllergy] = useState("");
  const [comorbidities, setComorbidities] = useState<ComorbidCode[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [advisoryMessage, setAdvisoryMessage] = useState<string | null>(null);

  function toggleFactor(code: RiskCode) {
    setSelectedFactors((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code],
    );
  }

  function toggleComorbid(code: ComorbidCode) {
    setComorbidities((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code],
    );
  }

  function addVaccine() {
    const trimmed = vaccineInput.trim();
    if (!trimmed) return;
    setVaccines((prev) => [...prev, trimmed]);
    setVaccineInput("");
  }

  function removeVaccine(index: number) {
    setVaccines((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSave() {
    setIsSubmitting(true);
    setApiError(null);
    try {
      const factors = selectedFactors.filter((c) => c !== "other");
      const payload = {
        pregnancy_status: pregnancy,
        risk_factors: {
          factors,
          other: selectedFactors.includes("other") ? otherText : "",
          age: age ? Number(age) : null,
          drug_allergy: drugAllergy || "",
          comorbidities,
        },
        vaccination_history: vaccines,
      };
      const res = await upsertAutoimmuneProfile(payload);
      if (res.advisory_message) {
        setAdvisoryMessage(res.advisory_message);
      } else {
        router.replace("/home");
      }
    } catch (err) {
      setApiError(
        err instanceof Error ? err.message : "저장 중 오류가 발생했습니다.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  if (advisoryMessage) {
    return (
      <main className="mx-auto flex min-h-screen w-full max-w-md flex-col items-center justify-center px-6">
        <div
          className="w-full rounded-2xl p-6"
          style={{ background: PURPLE + "15" }}
        >
          <ShieldCheck className="mx-auto mb-3 h-8 w-8" style={{ color: PURPLE }} />
          <p className="text-center text-sm leading-relaxed" style={{ color: PURPLE }}>
            {advisoryMessage}
          </p>
        </div>
        <button
          onClick={() => router.replace("/home")}
          className="mt-6 w-full rounded-xl py-4 text-base font-bold text-white"
          style={{ background: PURPLE }}
        >
          확인
        </button>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8 pb-40">
      <div className="flex items-center gap-2">
        <button onClick={() => router.back()} aria-label="뒤로" className="-ml-1"><ChevronLeft className="h-6 w-6" /></button>
        <h1 className="text-xl font-bold">위험요인 프로필</h1>
      </div>

      <div
        className="mt-4 flex items-center justify-center gap-3 rounded-2xl p-4"
        style={{ background: PURPLE + "15", border: `1px solid ${PURPLE}` }}
      >
        <ShieldCheck className="h-6 w-6 shrink-0" style={{ color: PURPLE }} />
        <p className="text-sm text-center" style={{ color: PURPLE }}>
          안전한 의료 관리를 위해
          <br />
          정확한 정보를 입력해주세요
        </p>
      </div>

      {/* 나이 */}
      <p className="mt-6 font-bold">나이</p>
      <input
        type="number"
        inputMode="numeric"
        value={age}
        onChange={(e) => setAge(e.target.value)}
        placeholder="예: 45"
        className="mt-2 h-11 w-full rounded-xl border border-input bg-white px-4 text-sm"
      />

      {/* 위험 요인 자가 신고 */}
      <p className="mt-6 font-bold">
        위험 요인 자가 신고{" "}
        <span className="text-sm font-normal text-muted-foreground">
          (다중 선택)
        </span>
      </p>
      <div className="mt-2 divide-y divide-border rounded-2xl border border-border bg-white">
        {RISK_FACTORS.map(({ code, label }) => (
          <CheckItem
            key={code}
            label={label}
            checked={selectedFactors.includes(code)}
            onClick={() => toggleFactor(code)}
          />
        ))}
      </div>
      {selectedFactors.includes("other") && (
        <input
          value={otherText}
          onChange={(e) => setOtherText(e.target.value)}
          placeholder="기타 위험 요인을 입력하세요"
          className="mt-2 h-11 w-full rounded-xl border border-input bg-white px-4 text-sm"
        />
      )}

      {/* 동반 질환 */}
      <p className="mt-6 font-bold">
        동반 질환{" "}
        <span className="text-sm font-normal text-muted-foreground">(다중 선택)</span>
      </p>
      <div className="mt-2 divide-y divide-border rounded-2xl border border-border bg-white">
        {COMORBIDITIES.map(({ code, label }) => (
          <CheckItem
            key={code}
            label={label}
            checked={comorbidities.includes(code)}
            onClick={() => toggleComorbid(code)}
          />
        ))}
      </div>

      {/* 약물 알레르기 */}
      <p className="mt-6 font-bold">약물 알레르기</p>
      <textarea
        value={drugAllergy}
        onChange={(e) => setDrugAllergy(e.target.value)}
        rows={2}
        placeholder="예: 페니실린, 아스피린"
        className="mt-2 w-full rounded-2xl border border-input bg-white px-4 py-3 text-sm"
      />

      {/* 임신·수유 상태 */}
      <p className="mt-6 font-bold">임신·수유 상태</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {PREGNANCY_OPTIONS.map(({ label, value }) => (
          <button
            key={value}
            type="button"
            onClick={() => setPregnancy(value)}
            className="rounded-full px-4 py-2 text-sm font-semibold transition-colors"
            style={
              pregnancy === value
                ? { background: PURPLE, color: "#fff" }
                : { border: "1px solid hsl(var(--border))", background: "#fff" }
            }
          >
            {label}
          </button>
        ))}
      </div>

      {/* 백신 이력 */}
      <p className="mt-6 font-bold">백신 이력</p>
      <div className="mt-2 flex gap-2">
        <input
          value={vaccineInput}
          onChange={(e) => setVaccineInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addVaccine())}
          placeholder="백신명 입력"
          className="h-11 flex-1 rounded-xl border border-input bg-white px-4 text-sm"
        />
        <button
          type="button"
          onClick={addVaccine}
          className="h-11 rounded-xl px-4 text-sm font-semibold text-white"
          style={{ background: PURPLE }}
        >
          추가
        </button>
      </div>
      {vaccines.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-2">
          {vaccines.map((v, i) => (
            <span
              key={i}
              className="flex items-center gap-1 rounded-full px-3 py-1 text-sm font-medium text-white"
              style={{ background: PURPLE }}
            >
              {v}
              <button
                type="button"
                onClick={() => removeVaccine(i)}
                aria-label={`${v} 삭제`}
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </span>
          ))}
        </div>
      )}

      {apiError && (
        <p className="mt-4 text-sm text-destructive">{apiError}</p>
      )}

      <div className="fixed inset-x-0 bottom-16 mx-auto max-w-md px-5">
        <button
          type="button"
          onClick={handleSave}
          disabled={isSubmitting}
          className="w-full rounded-xl py-3.5 text-base font-bold text-white disabled:opacity-50"
          style={{ background: PURPLE }}
        >
          {isSubmitting ? "저장 중…" : "저장"}
        </button>
      </div>
    </main>
  );
}
