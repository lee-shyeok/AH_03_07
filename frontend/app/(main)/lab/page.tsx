"use client";

import { useRouter } from "next/navigation";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { FlaskConical, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { labSchema, type LabInput } from "@/features/lab/schema";
import { useCreateLab } from "@/features/lab/queries";

const PURPLE = "#7C5CCF";

const INITIAL: LabInput["items"] = [
  { key: "crp", name: "CRP", description: "C-반응성 단백 · 염증 지표", unit: "mg/L", reference: "<0.5 mg/L (정상)", max: 0.5, value: "3.5" },
  { key: "esr", name: "ESR", description: "적혈구 침강 속도", unit: "mm/hr", reference: "<20 mm/hr (정상)", max: 20, value: "45" },
  { key: "ra", name: "RA Factor", description: "류마티스 인자", unit: "IU/mL", reference: "<14 IU/mL (정상)", max: 14, value: "12" },
];

export default function LabPage() {
  const router = useRouter();
  const create = useCreateLab();
  const {
    register,
    handleSubmit,
    control,
    watch,
    formState: { errors },
  } = useForm<LabInput>({
    resolver: zodResolver(labSchema),
    defaultValues: { test_date: "2026-05-20", items: INITIAL, memo: "" },
  });
  const { fields, append } = useFieldArray({ control, name: "items" });
  const watchedItems = watch("items");

  function isNormal(value: string, max: number) {
    const v = parseFloat(value);
    if (Number.isNaN(v)) return true;
    return v < max;
  }

  async function onSubmit(values: LabInput) {
    await create.mutateAsync({
      test_date: values.test_date,
      items: values.items.map((it) => ({ key: it.key, value: parseFloat(it.value) || 0 })),
      memo: values.memo,
    });
    router.back();
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="mx-auto w-full max-w-md px-5 py-8 pb-28" noValidate>
      <h1 className="text-2xl font-bold">검사 결과 입력</h1>

      {/* 자가면역 배너 */}
      <div className="mt-5 flex items-center gap-3 rounded-2xl border p-4" style={{ borderColor: PURPLE + "55", background: PURPLE + "12" }}>
        <FlaskConical className="h-6 w-6" style={{ color: PURPLE }} />
        <div>
          <p className="font-bold">자가면역 검사 결과 추적</p>
          <p className="text-sm" style={{ color: PURPLE }}>시간순 변화를 의료진과 공유</p>
        </div>
      </div>

      {/* 검사 일자 */}
      <div className="mt-6">
        <label className="text-sm text-muted-foreground" htmlFor="test_date">검사 일자</label>
        <input
          id="test_date"
          type="date"
          className="mt-1.5 w-full rounded-xl border border-input bg-background px-4 py-3 text-center text-base font-bold"
          {...register("test_date")}
        />
        {errors.test_date && <p className="mt-1 text-sm text-destructive">{errors.test_date.message}</p>}
      </div>

      {/* 검사 항목 */}
      <div className="mt-6">
        <label className="text-sm text-muted-foreground">검사 항목</label>
        <div className="mt-2 space-y-3">
          {fields.map((field, i) => {
            const normal = isNormal(watchedItems?.[i]?.value ?? "", field.max);
            const valErr = errors.items?.[i]?.value?.message;
            return (
              <Card key={field.id} className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-lg font-bold">{field.name}</p>
                    {field.description && <p className="text-xs text-muted-foreground">{field.description}</p>}
                  </div>
                  <span className={"rounded-md px-2 py-1 text-xs font-bold " + (normal ? "bg-secondary text-primary" : "bg-destructive/10 text-destructive")}>
                    {normal ? "정상" : "초과"}
                  </span>
                </div>
                <div className="mt-3 flex items-center gap-2 rounded-lg border border-input px-4 py-3">
                  <input
                    inputMode="decimal"
                    className={"flex-1 bg-transparent text-lg font-bold outline-none " + (normal ? "text-primary" : "text-destructive")}
                    {...register(`items.${i}.value`)}
                  />
                  {field.unit && <span className="text-sm text-muted-foreground">{field.unit}</span>}
                </div>
                {field.reference && <p className="mt-2 text-xs text-muted-foreground">참고 범위: {field.reference}</p>}
                {valErr && <p className="mt-1 text-xs text-destructive">{valErr}</p>}
              </Card>
            );
          })}
        </div>
      </div>

      {/* 항목 추가 */}
      <button
        type="button"
        className="mt-3 w-full rounded-xl border-2 border-dashed py-3.5 text-sm font-semibold"
        style={{ borderColor: PURPLE + "66", color: PURPLE }}
        onClick={() =>
          append({ key: `custom-${fields.length}`, name: "새 항목", description: "", unit: "", reference: "-", max: Number.MAX_SAFE_INTEGER, value: "" })
        }
      >
        <Plus className="mr-1 inline h-4 w-4" /> 검사 항목 추가
      </button>

      {/* 메모 */}
      <div className="mt-6">
        <label className="text-sm text-muted-foreground" htmlFor="memo">메모 (선택)</label>
        <textarea
          id="memo"
          rows={2}
          placeholder="예: 다음 진료 시 의료진과 상의"
          className="mt-1.5 w-full rounded-xl border border-input bg-background px-4 py-3 text-sm"
          {...register("memo")}
        />
      </div>

      {/* 저장 */}
      <div className="fixed inset-x-0 bottom-16 mx-auto max-w-md px-5">
        <Button type="submit" className="w-full text-base" size="lg" style={{ background: PURPLE }} disabled={create.isPending}>
          {create.isPending ? "저장 중..." : "저장하기"}
        </Button>
      </div>
    </form>
  );
}
