import { z } from "zod";

const labItem = z.object({
  key: z.string(),
  name: z.string().min(1, "항목명을 입력하세요"),
  description: z.string().optional(),
  unit: z.string().optional(),
  reference: z.string().optional(),
  max: z.number(),
  value: z
    .string()
    .refine((v) => v === "" || !Number.isNaN(parseFloat(v)), { message: "숫자를 입력하세요" }),
});

export const labSchema = z.object({
  test_date: z.string().min(1, "검사 일자를 선택하세요"),
  items: z.array(labItem).min(1, "검사 항목을 추가하세요"),
  memo: z.string().max(300).optional(),
});

export type LabInput = z.infer<typeof labSchema>;
