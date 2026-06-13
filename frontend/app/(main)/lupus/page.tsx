"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft } from "lucide-react";
import { Card } from "@/components/ui/card";
import {
  upsertLupusDailyContext,
  getLupusDailyContext,
  listLupusSkinLogs,
  createLupusSkinLog,
  deleteLupusSkinLog,
  type StressLevel,
  type LupusSkinSymptomType,
  type LupusSkinLogResponse,
} from "@/features/lupus/api";

const PURPLE = "#7C5CCF";

const SKIN_SYMPTOMS: { type: LupusSkinSymptomType; label: string }[] = [
  { type: "RASH", label: "발진" },
  { type: "ORAL_ULCER", label: "구강 궤양" },
  { type: "HAIR_LOSS", label: "탈모" },
  { type: "RAYNAUD", label: "레이노 현상" },
];

const STRESS_OPTIONS: { value: StressLevel; label: string }[] = [
  { value: "LOW", label: "하" },
  { value: "MID", label: "중" },
  { value: "HIGH", label: "상" },
];

function todayStr(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function formatDisplay(dateStr: string): string {
  return dateStr.replace(/-/g, ".");
}

function addDays(dateStr: string, delta: number): string {
  const d = new Date(dateStr);
  d.setDate(d.getDate() + delta);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

interface SliderFieldProps {
  label: string;
  min: number;
  max: number;
  step?: number;
  value: number;
  leftLabel: string;
  rightLabel: string;
  unit?: string;
  onChange: (v: number) => void;
}

function SliderField({ label, min, max, step = 1, value, leftLabel, rightLabel, unit, onChange }: SliderFieldProps) {
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between">
        <span className="font-semibold">{label}</span>
        <span className="text-xl font-extrabold" style={{ color: PURPLE }}>
          {value}
          {unit && <span className="text-sm font-normal text-muted-foreground">{unit}</span>}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="mt-3 w-full"
        style={{ accentColor: PURPLE }}
      />
      <div className="mt-1 flex justify-between text-xs text-muted-foreground">
        <span>{leftLabel}</span>
        <span>{rightLabel}</span>
      </div>
    </Card>
  );
}

export default function LupusPage() {
  const router = useRouter();
  const [logDate, setLogDate] = useState(todayStr());
  const [uvMinutes, setUvMinutes] = useState(0);
  const [sleepHours, setSleepHours] = useState(7);
  const [stress, setStress] = useState<StressLevel | null>(null);
  const [medTaken, setMedTaken] = useState(false);
  const [selectedSkin, setSelectedSkin] = useState<LupusSkinSymptomType[]>([]);
  const [skinLogs, setSkinLogs] = useState<LupusSkinLogResponse[]>([]);
  const [memo, setMemo] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [kidneySign, setKidneySign] = useState<boolean | null>(null);

  useEffect(() => {
    const d = new URLSearchParams(window.location.search).get("date");
    if (d) setLogDate(d);
  }, []);

  useEffect(() => {
    let active = true;
    setKidneySign(null);
    getLupusDailyContext(logDate).then((ctx) => {
      if (!active) return;
      if (!ctx) {
        setUvMinutes(0);
        setSleepHours(7);
        setStress(null);
        setMedTaken(false);
        setMemo("");
        return;
      }
      setUvMinutes(ctx.uv_exposure_minutes ?? 0);
      setSleepHours(ctx.sleep_hours ?? 7);
      setStress(ctx.stress_level);
      setMedTaken(ctx.med_taken ?? false);
      setMemo(ctx.note ?? "");
    });
    listLupusSkinLogs().then((logs) => {
      if (!active) return;
      const today = logs.filter((l) => l.log_date === logDate);
      setSkinLogs(today);
      setSelectedSkin([...new Set(today.map((l) => l.symptom_type))]);
    });
    return () => {
      active = false;
    };
  }, [logDate]);

  function toggleSkin(type: LupusSkinSymptomType) {
    setSelectedSkin((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  }

  async function handleSave() {
    setIsSubmitting(true);
    setApiError(null);
    try {
      await upsertLupusDailyContext({
        log_date: logDate,
        uv_exposure_minutes: uvMinutes,
        sleep_hours: sleepHours,
        stress_level: stress,
        med_taken: medTaken,
        note: memo.trim() || null,
      });

      const toCreate = selectedSkin.filter(
        (s) => !skinLogs.some((l) => l.symptom_type === s)
      );
      const toDelete = skinLogs.filter((l) => !selectedSkin.includes(l.symptom_type));
      await Promise.all([
        ...toCreate.map((s) => createLupusSkinLog({ symptom_type: s, log_date: logDate })),
        ...toDelete.map((l) => deleteLupusSkinLog(l.id)),
      ]);

      const logs = await listLupusSkinLogs();
      const today = logs.filter((l) => l.log_date === logDate);
      setSkinLogs(today);
      setSelectedSkin([...new Set(today.map((l) => l.symptom_type))]);

      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      setApiError("저장에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 pb-32 pt-6">
      <div className="flex items-center gap-2">
        <button onClick={() => router.back()} className="rounded-full p-1 hover:bg-accent" aria-label="뒤로가기">
          <ChevronLeft className="h-5 w-5" />
        </button>
        <h1 className="text-xl font-bold">루푸스 기록</h1>
      </div>

      <div className="mt-4 flex items-center justify-center gap-6">
        <button aria-label="이전" className="text-muted-foreground" onClick={() => setLogDate((d) => addDays(d, -1))}>
          ‹
        </button>
        <span className="font-bold" style={{ color: PURPLE }}>
          {formatDisplay(logDate)}
        </span>
        <button
          aria-label="다음"
          className="text-muted-foreground"
          onClick={() => setLogDate((d) => addDays(d, 1))}
          disabled={logDate >= todayStr()}
        >
          ›
        </button>
      </div>

      <div className="mt-6 flex flex-col gap-4">
        <SliderField label="햇빛(UV) 노출" min={0} max={240} step={10} value={uvMinutes} leftLabel="0분" rightLabel="240분+" unit="분" onChange={setUvMinutes} />
        <SliderField label="수면 시간" min={0} max={12} step={0.5} value={sleepHours} leftLabel="0시간" rightLabel="12시간" unit="시간" onChange={setSleepHours} />

        <Card className="p-4">
          <span className="font-semibold">스트레스</span>
          <div className="mt-3 flex gap-2">
            {STRESS_OPTIONS.map((opt) => {
              const on = stress === opt.value;
              return (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setStress(on ? null : opt.value)}
                  className="flex-1 rounded-lg border py-2 text-sm font-medium"
                  style={on ? { background: PURPLE, borderColor: PURPLE, color: "#fff" } : { borderColor: "#d4d4d8", color: "#52525b" }}
                >
                  {opt.label}
                </button>
              );
            })}
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <span className="font-semibold">오늘 약 복용</span>
            <button
              type="button"
              onClick={() => setMedTaken((v) => !v)}
              aria-pressed={medTaken}
              className="rounded-full border px-4 py-1.5 text-sm font-medium"
              style={medTaken ? { background: PURPLE, borderColor: PURPLE, color: "#fff" } : { borderColor: "#d4d4d8", color: "#52525b" }}
            >
              {medTaken ? "복용함" : "복용 안 함"}
            </button>
          </div>
        </Card>

        <Card className="p-4">
          <span className="font-semibold">피부·점막 증상</span>
          <p className="mt-1 text-xs text-muted-foreground">오늘 나타난 증상을 선택하세요.</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {SKIN_SYMPTOMS.map(({ type, label }) => {
              const on = selectedSkin.includes(type);
              return (
                <button
                  key={type}
                  type="button"
                  onClick={() => toggleSkin(type)}
                  className="rounded-full border px-3 py-1.5 text-sm"
                  style={on ? { background: PURPLE, borderColor: PURPLE, color: "#fff" } : { borderColor: "#d4d4d8", color: "#52525b" }}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </Card>

        <Card className="p-4">
          <p className="mb-2 font-semibold">메모 (선택)</p>
          <textarea
            value={memo}
            onChange={(e) => setMemo(e.target.value)}
            placeholder="오늘 상태를 자유롭게 기록해보세요."
            maxLength={500}
            rows={3}
            className="w-full resize-none rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:border-[#7C5CCF]"
          />
          <p className="mt-1 text-right text-xs text-muted-foreground">{memo.length}/500</p>
        </Card>

        {/* 신장 관련 신호 (인라인 자가 인지 + 안내, 저장 없음) */}
        <Card className="p-4" style={{ background: "#fff" }}>
          <span className="font-semibold" style={{ color: "#000" }}>신장 관련 신호</span>
          <p className="mt-1 text-sm" style={{ color: "#000" }}>
            소변에 거품이 많거나 피가 비치나요?
          </p>
          <div className="mt-3 flex gap-2">
            {[
              { v: true, label: "있음" },
              { v: false, label: "없음" },
            ].map((opt) => {
              const on = kidneySign === opt.v;
              return (
                <button
                  key={opt.label}
                  type="button"
                  onClick={() => setKidneySign(on ? null : opt.v)}
                  className="flex-1 rounded-lg border py-2 text-sm font-medium"
                  style={
                    on
                      ? { background: PURPLE, borderColor: PURPLE, color: "#fff" }
                      : { borderColor: "#d4d4d8", color: "#000" }
                  }
                >
                  {opt.label}
                </button>
              );
            })}
          </div>
          {kidneySign === true && (
            <p className="mt-3 text-sm" style={{ color: "#EF5B5B" }}>
              지속되면 의료진 확인이 필요할 수 있어요.
            </p>
          )}
        </Card>

        <p className="px-1 text-xs leading-relaxed text-muted-foreground">
          본 기록은 사용자 자가 기록입니다. 앱은 의학적 평가를 수행하지 않습니다.
        </p>
      </div>

      {apiError && <p className="mt-4 text-center text-sm text-destructive">{apiError}</p>}
      {saved && <p className="mt-4 text-center text-sm font-medium" style={{ color: PURPLE }}>저장되었습니다.</p>}

      <div className="fixed inset-x-0 bottom-16 mx-auto max-w-md px-5">
        <button
          onClick={handleSave}
          disabled={isSubmitting}
          className="w-full rounded-xl py-3.5 text-base font-bold text-white disabled:opacity-60"
          style={{ background: PURPLE }}
        >
          {isSubmitting ? "저장 중..." : "저장하기"}
        </button>
      </div>
    </main>
  );
}
