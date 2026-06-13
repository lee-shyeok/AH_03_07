"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ChevronDown, ChevronLeft, Calendar, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { TimePicker } from "@/components/ui/TimePicker";
import {
  medicationSchema, type MedicationInput,
  MED_CATEGORIES, MED_UNITS, MED_TIMINGS, CATEGORY_TO_DRUG_CLASS,
  GENERAL_DRUG_SUGGESTIONS, AUTOIMMUNE_DRUG_SUGGESTIONS,
} from "@/features/medication/schema";
import { useCreateMedication } from "@/features/medication/queries";
import { searchDrugReferences, type DrugReference } from "@/features/medication/api";
import { getMode } from "@/features/auth/mode";

const TIMING_KEY: Record<string, "morning" | "afternoon" | "evening" | "bedtime"> = {
  "아침": "morning",
  "점심": "afternoon",
  "저녁": "evening",
  "취침 전": "bedtime",
};

interface TimingTimes {
  morning: string;
  afternoon: string;
  evening: string;
  bedtime: string;
}

export default function MedicationNewPage() {
  const router = useRouter();
  const create = useCreateMedication();

  // SSR 하이드레이션 불일치 방지: useEffect에서만 localStorage 접근
  const [isAutoimmune, setIsAutoimmune] = useState(false);
  useEffect(() => {
    setIsAutoimmune(getMode() === "autoimmune");
  }, []);

  const localSuggestions = isAutoimmune ? AUTOIMMUNE_DRUG_SUGGESTIONS : GENERAL_DRUG_SUGGESTIONS;

  // drug-references 검색
  const [drugRefs, setDrugRefs] = useState<DrugReference[]>([]);
  const [showDrop, setShowDrop] = useState(false);
  const [searching, setSearching] = useState(false);

  // 시간대별 시간
  const [timingTimes, setTimingTimes] = useState<TimingTimes>({
    morning: "08:00",
    afternoon: "12:00",
    evening: "18:00",
    bedtime: "22:00",
  });

  // 저장 에러
  const [saveError, setSaveError] = useState<string | null>(null);

  const {
    handleSubmit,
    control,
    register,
    watch,
    formState: { errors },
  } = useForm<MedicationInput>({
    resolver: zodResolver(medicationSchema),
    defaultValues: {
      name: "", category: "스테로이드", dose: "1", unit: "정",
      freq: 2, timings: ["아침", "저녁"], start: "", end: "", memo: "",
    },
  });

  const nameValue = watch("name");
  const selectedTimings = watch("timings");

  // 약품명 입력 시 drug-references 검색 (300ms debounce)
  useEffect(() => {
    if (!nameValue || nameValue.length < 1) {
      setDrugRefs([]);
      setShowDrop(false);
      return;
    }
    const t = setTimeout(async () => {
      setSearching(true);
      const apiRefs = await searchDrugReferences(nameValue);
      if (apiRefs.length > 0) {
        setDrugRefs(apiRefs.slice(0, 6));
      } else {
        const filtered = (localSuggestions as readonly string[])
          .filter((s) => s.toLowerCase().includes(nameValue.toLowerCase()))
          .slice(0, 6)
          .map((s) => ({ drug_name: s } as DrugReference));
        setDrugRefs(filtered);
      }
      setSearching(false);
      setShowDrop(true);
    }, 300);
    return () => clearTimeout(t);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nameValue]);

  async function onSubmit(v: MedicationInput) {
    setSaveError(null);
    const times: Record<string, string> = {};
    for (const t of v.timings) {
      const key = TIMING_KEY[t];
      if (key) times[key] = timingTimes[key]; // 영문 키로 저장
    }
    try {
      await create.mutateAsync({
        name: v.name,
        drug_class: isAutoimmune
          ? (CATEGORY_TO_DRUG_CLASS[v.category] ?? "IMMUNOSUPPRESSANT")
          : undefined,
        note: v.memo || undefined,
        timings: v.timings,
        timing_times: Object.keys(times).length ? times : undefined,
        start_date: v.start || undefined,
        end_date: v.end || undefined,
      });
      router.replace("/medication");
    } catch {
      setSaveError("등록 중 오류가 발생했습니다. 다시 시도해주세요.");
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="mx-auto w-full max-w-md px-5 py-6 pb-28" noValidate>
      <div className="flex items-center gap-2">
        <button type="button" onClick={() => router.back()} className="p-1 text-foreground">
          <ChevronLeft className="h-6 w-6" />
        </button>
        <h1 className="text-2xl font-bold">약 등록</h1>
      </div>

      {/* 약품 정보 */}
      <p className="mt-6 text-lg font-bold">약품 정보</p>
      <div className="mt-3 rounded-3xl border border-border p-5 space-y-4">

        {/* 약품명 — drug-references 검색 */}
        <div>
          <label className="text-sm text-muted-foreground" htmlFor="name">
            약품명 <span className="text-destructive">*</span>
          </label>
          <Controller
            control={control}
            name="name"
            render={({ field }) => (
              <div className="relative mt-2">
                <Input
                  id="name"
                  placeholder="약품명 검색"
                  className="rounded-2xl h-12"
                  value={field.value}
                  ref={field.ref}
                  name={field.name}
                  autoComplete="off"
                  onChange={(e) => {
                    field.onChange(e.target.value);
                    setShowDrop(true);
                  }}
                  onBlur={() => {
                    field.onBlur();
                    setTimeout(() => setShowDrop(false), 150);
                  }}
                />
                {showDrop && (drugRefs.length > 0 || searching) && (
                  <div className="absolute left-0 right-0 top-full z-20 mt-1 overflow-hidden rounded-2xl border border-border bg-card shadow-lg">
                    {searching && (
                      <p className="px-4 py-3 text-sm text-muted-foreground">검색 중...</p>
                    )}
                    {!searching && drugRefs.map((ref) => (
                      <button
                        key={ref.drug_name}
                        type="button"
                        className="flex w-full flex-col px-4 py-3 text-left hover:bg-accent border-b border-border last:border-0"
                        onMouseDown={() => {
                          field.onChange(ref.drug_name);
                          setShowDrop(false);
                        }}
                      >
                        <span className="text-sm font-semibold">{ref.drug_name}</span>
                        <div className="mt-0.5 flex flex-wrap gap-2 text-xs text-muted-foreground">
                          {ref.ingredient && <span>{ref.ingredient}</span>}
                          {ref.manufacturer && <span>· {ref.manufacturer}</span>}
                          {ref.source && <span className="text-primary">· {ref.source}</span>}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          />
          <div className="mt-2 flex items-start gap-1.5 rounded-xl bg-muted px-3 py-2">
            <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            <p className="text-xs text-muted-foreground">
              정보 조회용입니다. 자동 매칭·추천이 아닙니다.
            </p>
          </div>
          {errors.name && (
            <p className="mt-1 text-sm text-destructive">{errors.name.message}</p>
          )}
        </div>

        {/* 약물 분류 — 자가면역 모드에서만 */}
        {isAutoimmune && (
          <div>
            <label className="text-sm text-muted-foreground" htmlFor="category">약물 분류</label>
            <div className="relative mt-2">
              <select
                id="category"
                className="h-12 w-full appearance-none rounded-2xl border border-input bg-background px-4 text-sm"
                {...register("category")}
              >
                {MED_CATEGORIES.map((c) => <option key={c}>{c}</option>)}
              </select>
              <ChevronDown className="pointer-events-none absolute right-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
            </div>
          </div>
        )}
      </div>

      {/* 복용 정보 */}
      <p className="mt-6 text-lg font-bold">복용 정보</p>
      <div className="mt-3 rounded-3xl border border-border p-5 space-y-5">

        {/* 1회 복용량 */}
        <div>
          <label className="text-sm text-muted-foreground" htmlFor="dose">
            1회 복용량 <span className="text-destructive">*</span>
          </label>
          <div className="mt-2 flex gap-3">
            <Input
              id="dose"
              inputMode="numeric"
              className="flex-[2] rounded-2xl h-12 text-center text-base"
              {...register("dose")}
            />
            <div className="relative flex-[3]">
              <select
                className="h-12 w-full appearance-none rounded-2xl border border-input bg-background px-4 text-sm"
                {...register("unit")}
              >
                {MED_UNITS.map((u) => <option key={u}>{u}</option>)}
              </select>
              <ChevronDown className="pointer-events-none absolute right-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
            </div>
          </div>
          {errors.dose && (
            <p className="mt-1 text-sm text-destructive">{errors.dose.message}</p>
          )}
        </div>

        {/* 복용 시점 선택 */}
        <Controller
          control={control}
          name="timings"
          render={({ field }) => (
            <div>
              <label className="text-sm text-muted-foreground">복용 시점</label>
              <div className="mt-2 flex gap-2">
                {MED_TIMINGS.map((t) => {
                  const on = field.value.includes(t);
                  return (
                    <button
                      key={t}
                      type="button"
                      onClick={() =>
                        field.onChange(
                          on ? field.value.filter((x) => x !== t) : [...field.value, t]
                        )
                      }
                      className={
                        "flex-1 rounded-full py-3 text-sm font-semibold " +
                        (on ? "bg-primary text-primary-foreground" : "border border-border bg-card")
                      }
                    >
                      {t}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        />

        {/* 시간대별 알림 시간 — 커스텀 TimePicker */}
        {selectedTimings.length > 0 && (
          <div>
            <label className="text-sm text-muted-foreground">시간대별 알림 시간</label>
            <div className="mt-2 space-y-2">
              {MED_TIMINGS.filter((t) => selectedTimings.includes(t)).map((t) => {
                const key = TIMING_KEY[t];
                return (
                  <div key={t} className="flex items-center justify-between rounded-2xl border border-input bg-background px-4 py-2 min-h-[52px]">
                    <span className="text-sm font-medium">{t}</span>
                    <TimePicker
                      value={timingTimes[key]}
                      onChange={(v) => setTimingTimes((prev) => ({ ...prev, [key]: v }))}
                    />
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 복용 기간 */}
        <div>
          <label className="text-sm text-muted-foreground">복용 기간</label>
          <div className="mt-2 flex items-center gap-2">
            <div className="relative flex-1">
              <Calendar className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="date"
                className="h-12 w-full rounded-2xl border border-input bg-background pl-9 pr-3 text-sm"
                {...register("start")}
              />
            </div>
            <span className="text-muted-foreground">~</span>
            <div className="relative flex-1">
              <Calendar className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="date"
                className="h-12 w-full rounded-2xl border border-input bg-background pl-9 pr-3 text-sm"
                {...register("end")}
              />
            </div>
          </div>
        </div>
      </div>

      {/* 추가 정보 */}
      <p className="mt-6 text-lg font-bold">추가 정보</p>
      <div className="mt-3 rounded-3xl border border-border p-5">
        <label className="text-sm text-muted-foreground" htmlFor="memo">메모 (선택)</label>
        <textarea
          id="memo"
          rows={2}
          placeholder="예: 식후 30분에 복용"
          className="mt-2 w-full rounded-2xl border border-input bg-background px-4 py-3 text-sm"
          {...register("memo")}
        />
      </div>

      {/* 저장 에러 */}
      {saveError && (
        <p className="mt-3 rounded-xl bg-destructive/10 px-4 py-2 text-sm text-destructive">
          {saveError}
        </p>
      )}

      <div className="fixed inset-x-0 bottom-16 mx-auto max-w-md px-5">
        <Button
          type="submit"
          className="w-full rounded-2xl h-14 text-base font-bold"
          size="lg"
          disabled={create.isPending}
        >
          {create.isPending ? "등록 중..." : "등록하기"}
        </Button>
      </div>
    </form>
  );
}
