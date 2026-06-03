import { z } from "zod";

export const MED_CATEGORIES = ["면역억제제", "항염증제", "스테로이드", "항류마티스", "기타"] as const;
export const MED_UNITS = ["정", "캡슐", "ml", "mg", "포"] as const;
export const MED_TIMINGS = ["아침", "점심", "저녁", "취침 전"] as const;

export const medicationSchema = z.object({
  name: z.string().min(1, "약품명을 입력하세요").max(60),
  category: z.string(),
  dose: z.string().min(1, "복용량을 입력하세요"),
  unit: z.string(),
  freq: z.number().int().min(1).max(4),
  timings: z.array(z.string()),
  start: z.string().optional(),
  end: z.string().optional(),
  memo: z.string().max(300).optional(),
});

export type MedicationInput = z.infer<typeof medicationSchema>;
