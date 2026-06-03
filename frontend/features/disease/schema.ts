import { z } from "zod";

export const DISEASES = ["류마티스 관절염", "루푸스", "강직성 척추염", "쇼그렌 증후군", "기타"] as const;

export const diseaseSchema = z.object({
  disease: z.string().min(1, "진단명을 선택하세요"),
  date: z.string().min(1, "진단일을 선택하세요"),
  hospital: z.string().max(60).optional(),
  memo: z.string().max(300).optional(),
});

export type DiseaseInput = z.infer<typeof diseaseSchema>;
