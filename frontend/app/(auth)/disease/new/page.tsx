"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ChevronLeft, ChevronDown } from "lucide-react";
import { diseaseSchema, type DiseaseInput, DISEASES } from "@/features/disease/schema";

export default function DiseaseNewPage() {
  const router = useRouter();
  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
  } = useForm<DiseaseInput>({
    resolver: zodResolver(diseaseSchema),
    mode: "onChange",
    defaultValues: { disease: "", date: "", hospital: "", memo: "" },
  });

  function onSubmit() {
    // 백엔드: POST /v1/diseases 등 (온보딩 완료 → 홈)
    router.replace("/home");
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col px-6 pb-8 pt-10">
      <button onClick={() => router.back()} aria-label="뒤로" className="-ml-2 w-fit">
        <ChevronLeft className="h-7 w-7" />
      </button>

      <h1 className="mt-6 text-3xl font-extrabold leading-tight">진단 정보를<br />입력해주세요</h1>
      <p className="mt-2 text-sm text-muted-foreground">맞춤형 가이드 제공을 위해 필요해요</p>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-10 flex flex-1 flex-col" noValidate>
        <div className="flex-1 space-y-6">
          <div>
            <label className="text-sm font-medium" htmlFor="disease">
              진단명 <span className="text-destructive">*</span>
            </label>
            <div className="relative mt-2">
              <select
                id="disease"
                className="h-12 w-full appearance-none rounded-xl border border-input bg-background px-4 text-sm"
                {...register("disease")}
              >
                <option value="">진단명 선택</option>
                {DISEASES.map((d) => <option key={d}>{d}</option>)}
              </select>
              <ChevronDown className="pointer-events-none absolute right-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            </div>
            {errors.disease && <p className="mt-1 text-sm text-destructive">{errors.disease.message}</p>}
          </div>

          <div>
            <label className="text-sm font-medium" htmlFor="date">
              진단일 <span className="text-destructive">*</span>
            </label>
            <input
              id="date"
              type="date"
              className="mt-2 h-12 w-full rounded-xl border border-input bg-background px-4 text-sm"
              {...register("date")}
            />
            {errors.date && <p className="mt-1 text-sm text-destructive">{errors.date.message}</p>}
          </div>

          <div>
            <label className="text-sm font-medium" htmlFor="hospital">진료 받은 병원 (선택)</label>
            <input
              id="hospital"
              placeholder="예: OO대학교병원"
              className="mt-2 h-12 w-full rounded-xl border border-input bg-background px-4 text-sm"
              {...register("hospital")}
            />
          </div>

          <div>
            <label className="text-sm font-medium" htmlFor="memo">추가 메모 (선택)</label>
            <input
              id="memo"
              placeholder="입력하세요"
              className="mt-2 h-12 w-full rounded-xl border border-input bg-background px-4 text-sm"
              {...register("memo")}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={!isValid}
          className="w-full rounded-xl bg-primary py-4 text-base font-bold text-primary-foreground disabled:opacity-50"
        >
          완료
        </button>
      </form>
    </main>
  );
}
