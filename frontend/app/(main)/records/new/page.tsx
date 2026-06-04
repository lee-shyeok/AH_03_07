"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field } from "@/components/form/Field";
import { recordSchema, type RecordInput } from "@/features/medical-records/schema";
import { useCreateRecord } from "@/features/medical-records/queries";

export default function NewRecordPage() {
  const router = useRouter();
  const create = useCreateRecord();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RecordInput>({
    resolver: zodResolver(recordSchema),
    defaultValues: { hospital_name: "", department: "", visit_date: "", diagnosis: "", memo: "" },
  });

  async function onSubmit(values: RecordInput) {
    await create.mutateAsync(values);
    router.replace("/records");
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8">
      <h1 className="text-2xl font-bold">진료기록 입력</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4" noValidate>
        <Field label="병원명" htmlFor="hospital" required error={errors.hospital_name?.message}>
          <Input id="hospital" {...register("hospital_name")} />
        </Field>
        <Field label="진료과" htmlFor="dept" error={errors.department?.message}>
          <Input id="dept" placeholder="예: 류마티스내과" {...register("department")} />
        </Field>
        <Field label="방문일" htmlFor="date" required error={errors.visit_date?.message}>
          <Input id="date" type="date" {...register("visit_date")} />
        </Field>
        <Field label="진단" htmlFor="diag" error={errors.diagnosis?.message}>
          <Input id="diag" {...register("diagnosis")} />
        </Field>
        <Field label="메모" htmlFor="memo" error={errors.memo?.message}>
          <textarea
            id="memo"
            rows={3}
            className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            {...register("memo")}
          />
        </Field>

        <div className="flex gap-2 pt-2">
          <Button type="button" variant="outline" className="flex-1" onClick={() => router.back()}>
            취소
          </Button>
          <Button type="submit" className="flex-1" disabled={create.isPending}>
            {create.isPending ? "저장 중..." : "저장"}
          </Button>
        </div>
      </form>
    </main>
  );
}
