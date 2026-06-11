"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ChevronLeft } from "lucide-react";
import { diseaseSchema, type DiseaseInput, DISEASES } from "@/features/disease/schema";
import { createDiseases } from "@/features/disease/api";

export default function DiseaseNewPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const fromMypage = searchParams.get("from") === "mypage";
  const [apiError, setApiError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isValid, isSubmitting },
  } = useForm<DiseaseInput>({
    resolver: zodResolver(diseaseSchema),
    mode: "onChange",
    defaultValues: { codes: [], diagnosed_date: "", note: "" },
  });

  const selectedCodes = watch("codes") ?? [];

  function toggleCode(code: "RA" | "SLE") {
    const next = selectedCodes.includes(code)
      ? selectedCodes.filter((c) => c !== code)
      : [...selectedCodes, code];
    setValue("codes", next, { shouldValidate: true });
  }

  async function onSubmit(data: DiseaseInput) {
    setApiError(null);
    try {
      const diseases = data.codes.map((code) => ({
        disease_code: code,
        diagnosed_date: data.diagnosed_date || null,
        note: data.note || null,
      }));
      await createDiseases(diseases);
      router.replace(fromMypage ? "/mypage" : "/risk-profile");
    } catch (err) {
      setApiError(err instanceof Error ? err.message : "등록 중 오류가 발생했습니다.");
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col px-6 pb-8 pt-10">
      <button onClick={() => router.back()} aria-label="뒤로" className="-ml-2 w-fit">
        <ChevronLeft className="h-7 w-7" />
      </button>

      <h1 className="mt-6 text-3xl font-extrabold leading-tight">진단 정보를<br />입력해주세요</h1>
      <p className="mt-2 text-sm text-muted-foreground">어떤 자가면역질환을 가지고 계신가요?</p>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-10 flex flex-1 flex-col" noValidate>
        <div className="flex-1 space-y-6">
          <div>
            <p className="text-sm font-medium">
              진단명 <span className="text-destructive">*</span>
            </p>
            <div className="mt-2 space-y-2">
              {DISEASES.map(({ code, label }) => (
                <button
                  key={code}
                  type="button"
                  onClick={() => toggleCode(code)}
                  className={`flex h-12 w-full items-center gap-3 rounded-xl border px-4 text-sm transition-colors ${
                    selectedCodes.includes(code)
                      ? "border-[#7C5CCF] bg-[#7C5CCF]/10 font-medium"
                      : "border-input bg-white"
                  }`}
                >
                  <span
                    className={`flex h-5 w-5 shrink-0 items-center justify-center rounded border-2 ${
                      selectedCodes.includes(code)
                        ? "border-[#7C5CCF] bg-[#7C5CCF]"
                        : "border-muted-foreground"
                    }`}
                  >
                    {selectedCodes.includes(code) && (
                      <svg viewBox="0 0 12 10" className="h-3 w-3 text-white" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="1,5 4,8 11,1" />
                      </svg>
                    )}
                  </span>
                  {label}
                </button>
              ))}
            </div>
            {errors.codes && <p className="mt-1 text-sm text-destructive">{errors.codes.message}</p>}
          </div>

          <div>
            <label className="text-sm font-medium" htmlFor="diagnosed_date">
              진단일 (선택)
            </label>
            <input
              id="diagnosed_date"
              type="date"
              className="mt-2 h-12 w-full rounded-xl border border-input bg-white px-4 text-sm"
              {...register("diagnosed_date")}
            />
          </div>

          <div>
            <label className="text-sm font-medium" htmlFor="note">추가 메모 (선택)</label>
            <input
              id="note"
              placeholder="입력하세요"
              className="mt-2 h-12 w-full rounded-xl border border-input bg-white px-4 text-sm"
              {...register("note")}
            />
          </div>
        </div>

        {apiError && <p className="mt-4 text-sm text-destructive">{apiError}</p>}

        <button
          type="submit"
          disabled={!isValid || isSubmitting}
          className="mt-6 w-full rounded-xl bg-[#7C5CCF] py-4 text-base font-bold text-white disabled:opacity-50"
        >
          {isSubmitting ? "등록 중…" : "등록"}
        </button>
      </form>
    </main>
  );
}
