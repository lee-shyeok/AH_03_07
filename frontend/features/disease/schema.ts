import { z } from "zod";

export const DISEASES = [
  { code: "RA", label: "류마티스 관절염" },
  { code: "SLE", label: "전신홍반루푸스 (루푸스)" },
] as const;

export const diseaseSchema = z.object({
  codes: z.array(z.enum(["RA", "SLE"])).min(1, "질환을 1개 이상 선택하세요"),
  diagnosed_date: z.string().optional(),
  note: z.string().max(500).optional(),
});

export type DiseaseInput = z.infer<typeof diseaseSchema>;
