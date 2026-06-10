"use client";

import { useRouter } from "next/navigation";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Search, ChevronDown, ChevronLeft, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  medicationSchema, type MedicationInput,
  MED_CATEGORIES, MED_UNITS, MED_TIMINGS, CATEGORY_TO_DRUG_CLASS,
} from "@/features/medication/schema";
import { useCreateMedication } from "@/features/medication/queries";

export default function MedicationNewPage() {
  const router = useRouter();
  const create = useCreateMedication();
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<MedicationInput>({
    resolver: zodResolver(medicationSchema),
    defaultValues: {
      name: "", category: "스테로이드", dose: "1", unit: "정",
      freq: 2, timings: ["아침", "저녁"], start: "", end: "", memo: "",
    },
  });

  async function onSubmit(v: MedicationInput) {
    await create.mutateAsync({
      name: v.name,
      drug_class: CATEGORY_TO_DRUG_CLASS[v.category] ?? "IMMUNOSUPPRESSANT",
      note: v.memo || undefined,
    });
    router.replace("/medication");
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
        <div>
          <label className="text-sm text-muted-foreground" htmlFor="name">약품명 <span className="text-destructive">*</span></label>
          <div className="relative mt-2">
            <Input id="name" placeholder="약품명 검색" className="rounded-2xl pr-10 h-12" {...register("name")} />
            <Search className="absolute right-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
          </div>
          {errors.name && <p className="mt-1 text-sm text-destructive">{errors.name.message}</p>}
        </div>

        <div>
          <label className="text-sm text-muted-foreground" htmlFor="category">약물 분류</label>
          <div className="relative mt-2">
            <select id="category" className="h-12 w-full appearance-none rounded-2xl border border-input bg-background px-4 text-sm" {...register("category")}>
              {MED_CATEGORIES.map((c) => <option key={c}>{c}</option>)}
            </select>
            <ChevronDown className="pointer-events-none absolute right-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
          </div>
        </div>
      </div>

      {/* 복용 정보 */}
      <p className="mt-6 text-lg font-bold">복용 정보</p>
      <div className="mt-3 rounded-3xl border border-border p-5 space-y-5">
        <div>
          <label className="text-sm text-muted-foreground" htmlFor="dose">1회 복용량 <span className="text-destructive">*</span></label>
          <div className="mt-2 flex gap-3">
            <Input id="dose" inputMode="numeric" className="flex-[2] rounded-2xl h-12 text-center text-base" {...register("dose")} />
            <div className="relative flex-[3]">
              <select className="h-12 w-full appearance-none rounded-2xl border border-input bg-background px-4 text-sm" {...register("unit")}>
                {MED_UNITS.map((u) => <option key={u}>{u}</option>)}
              </select>
              <ChevronDown className="pointer-events-none absolute right-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
            </div>
          </div>
          {errors.dose && <p className="mt-1 text-sm text-destructive">{errors.dose.message}</p>}
        </div>

        <Controller
          control={control}
          name="freq"
          render={({ field }) => (
            <div>
              <label className="text-sm text-muted-foreground">1일 복용 횟수 <span className="text-destructive">*</span></label>
              <div className="mt-2 flex gap-2">
                {[1, 2, 3, 4].map((n) => (
                  <button
                    key={n}
                    type="button"
                    onClick={() => field.onChange(n)}
                    className={"flex-1 rounded-full py-3 text-sm font-semibold " + (field.value === n ? "bg-primary text-primary-foreground" : "border border-border bg-card")}
                  >
                    {n === 4 ? "4회 +" : `${n}회`}
                  </button>
                ))}
              </div>
            </div>
          )}
        />

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
                      onClick={() => field.onChange(on ? field.value.filter((x) => x !== t) : [...field.value, t])}
                      className={"flex-1 rounded-full py-3 text-sm font-semibold " + (on ? "bg-primary text-primary-foreground" : "border border-border bg-card")}
                    >
                      {t}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        />

        <div>
          <label className="text-sm text-muted-foreground">복용 기간</label>
          <div className="mt-2 flex items-center gap-2">
            <div className="relative flex-1">
              <Calendar className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input type="date" placeholder="시작일" className="h-12 w-full rounded-2xl border border-input bg-background pl-9 pr-3 text-sm" {...register("start")} />
            </div>
            <span className="text-muted-foreground">~</span>
            <div className="relative flex-1">
              <Calendar className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input type="date" placeholder="종료일" className="h-12 w-full rounded-2xl border border-input bg-background pl-9 pr-3 text-sm" {...register("end")} />
            </div>
          </div>
        </div>
      </div>

      {/* 추가 정보 */}
      <p className="mt-6 text-lg font-bold">추가 정보</p>
      <div className="mt-3 rounded-3xl border border-border p-5">
        <label className="text-sm text-muted-foreground" htmlFor="memo">메모 (선택)</label>
        <textarea id="memo" rows={2} placeholder="예: 식후 30분에 복용" className="mt-2 w-full rounded-2xl border border-input bg-background px-4 py-3 text-sm" {...register("memo")} />
      </div>

      <div className="fixed inset-x-0 bottom-16 mx-auto max-w-md px-5">
        <Button type="submit" className="w-full rounded-2xl h-14 text-base font-bold" size="lg" disabled={create.isPending}>
          {create.isPending ? "등록 중..." : "등록하기"}
        </Button>
      </div>
    </form>
  );
}
