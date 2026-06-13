"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft } from "lucide-react";
import { Card } from "@/components/ui/card";
import {
  upsertActivityLog,
  getActivityLog,
} from "@/features/activity/api";
import JointPicker from "@/features/activity/JointPicker";
import { DIAGRAM_META, type DiagramKind } from "@/features/activity/jointDiagram";

const PURPLE = "#7C5CCF";

const SWELLING_AREAS = ["턱", "어깨", "팔꿈치", "손목", "손가락", "척추", "엉덩이", "무릎", "발목", "발가락"];

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
  onChange: (v: number) => void;
  unit?: string;
}

function SliderField({
  label,
  min,
  max,
  step = 1,
  value,
  leftLabel,
  rightLabel,
  onChange,
  unit,
}: SliderFieldProps) {
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

export default function ActivityNewPage() {
  const router = useRouter();
  const [logDate, setLogDate] = useState(todayStr());
  const [painVas, setPainVas] = useState(5);
  const [fatigue, setFatigue] = useState(5);
  const [stiffnessMin, setStiffnessMin] = useState(0);
  const [swellingAreas, setSwellingAreas] = useState<string[]>([]);
  const [dailyDifficulty, setDailyDifficulty] = useState(5);
  const [memo, setMemo] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [diagramOpen, setDiagramOpen] = useState<DiagramKind | null>(null);

  // 쿼리(?date=)로 진입 시 해당 날짜로 시작 (수정 모드)
  useEffect(() => {
    const d = new URLSearchParams(window.location.search).get("date");
    if (d) setLogDate(d);
  }, []);

  // 날짜 바뀌면 기존 기록 불러오기 (없으면 폼 초기화)
  useEffect(() => {
    getActivityLog(logDate).then((log) => {
      if (!log) {
        setPainVas(5);
        setFatigue(5);
        setStiffnessMin(0);
        setSwellingAreas([]);
        setDailyDifficulty(5);
        setMemo("");
        return;
      }
      setPainVas(log.pain_vas);
      setFatigue(log.fatigue);
      setStiffnessMin(log.morning_stiffness_minutes ?? 0);
      setSwellingAreas(log.joint_swelling_areas ?? []);
      setDailyDifficulty(log.daily_difficulty);
      setMemo(log.free_memo ?? "");
    });
  }, [logDate]);

  async function handleSave() {
    setIsSubmitting(true);
    setApiError(null);
    try {
      await upsertActivityLog({
        log_date: logDate,
        pain_vas: painVas,
        fatigue,
        morning_stiffness_minutes: stiffnessMin > 0 ? stiffnessMin : null,
        joint_swelling_areas: swellingAreas.length > 0 ? swellingAreas : null,
        daily_difficulty: dailyDifficulty,
        free_memo: memo.trim() || null,
      });
      router.replace("/activity");
    } catch {
      setApiError("저장에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setIsSubmitting(false);
    }
  }

  const diagramKindFor = (area: string): DiagramKind | null =>
    area === "손가락" ? "hand" : area === "발가락" ? "foot" : null;

  const jointCountFor = (area: string): number => {
    const k = diagramKindFor(area);
    if (!k) return 0;
    return swellingAreas.filter((s) => s.startsWith(DIAGRAM_META[k].prefix)).length;
  };

  const isChipSelected = (area: string): boolean => {
    const k = diagramKindFor(area);
    if (k) return swellingAreas.some((s) => s.startsWith(DIAGRAM_META[k].prefix));
    return swellingAreas.includes(area);
  };

  const onChipClick = (area: string) => {
    const k = diagramKindFor(area);
    if (k) {
      setDiagramOpen(k);
      return;
    }
    setSwellingAreas((prev) =>
      prev.includes(area) ? prev.filter((x) => x !== area) : [...prev, area]
    );
  };

  return (
    <main className="mx-auto w-full max-w-md px-5 pb-32 pt-6">
      {/* 헤더 */}
      <div className="flex items-center gap-2">
        <button onClick={() => router.back()} className="rounded-full p-1 hover:bg-accent" aria-label="뒤로가기">
          <ChevronLeft className="h-5 w-5" />
        </button>
        <h1 className="text-xl font-bold">활성도 기록</h1>
      </div>

      {/* 날짜 네비 */}
      <div className="mt-4 flex items-center justify-center gap-6">
        <button
          aria-label="이전"
          className="text-muted-foreground"
          onClick={() => setLogDate((d) => addDays(d, -1))}
        >
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
        <SliderField
          label="통증"
          min={0}
          max={10}
          value={painVas}
          leftLabel="좋음 0"
          rightLabel="나쁨 10"
          onChange={setPainVas}
        />
        <SliderField
          label="피로"
          min={0}
          max={10}
          value={fatigue}
          leftLabel="좋음 0"
          rightLabel="나쁨 10"
          onChange={setFatigue}
        />
        <SliderField
          label="아침 강직"
          min={0}
          max={120}
          step={5}
          value={stiffnessMin}
          leftLabel="0분"
          rightLabel="120분"
          unit="분"
          onChange={setStiffnessMin}
        />

            {/* 관절 부종 부위 (다중 선택) */}
            <Card className="p-4">
              <span className="font-semibold">관절 부종 부위</span>
              <div className="mt-3 flex flex-wrap gap-2">
                {SWELLING_AREAS.map((area) => {
                  const selected = isChipSelected(area);
                  const count = jointCountFor(area);
                  return (
                    <button
                      key={area}
                      type="button"
                      onClick={() => onChipClick(area)}
                      className="rounded-full border px-3 py-1.5 text-sm"
                      style={
                        selected
                          ? { background: PURPLE, borderColor: PURPLE, color: "#fff" }
                          : { borderColor: "#d4d4d8", color: "#52525b" }
                      }
                    >
                      {area}
                      {count > 0 && (
                        <span className="ml-1 text-xs font-semibold">{count}</span>
                      )}
                    </button>
                  );
                })}
              </div>
            </Card>
        <SliderField
          label="일상 불편도"
          min={0}
          max={10}
          value={dailyDifficulty}
          leftLabel="좋음 0"
          rightLabel="나쁨 10"
          onChange={setDailyDifficulty}
        />

        {/* 메모 */}
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

            {/* 안내 문구 (NFR-SAFE) */}
            <p className="px-1 text-xs leading-relaxed text-muted-foreground">
              본 기록은 사용자 자가 기록입니다. 앱은 의학적 평가를 수행하지 않습니다.
            </p>
          </div>

      {apiError && (
        <p className="mt-4 text-center text-sm text-destructive">{apiError}</p>
      )}

      {/* 저장 버튼 */}
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

      {diagramOpen && (
        <JointPicker
          kind={diagramOpen}
          selected={swellingAreas}
          onSave={setSwellingAreas}
          onClose={() => setDiagramOpen(null)}
        />
      )}
    </main>
  );
}
