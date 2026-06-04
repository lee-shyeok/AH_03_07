import { z } from "zod";

export const recordSchema = z.object({
  hospital_name: z.string().min(1, "병원명을 입력하세요").max(60, "60자 이내로 입력하세요"),
  department: z.string().max(40).optional(),
  visit_date: z.string().min(1, "방문일을 선택하세요"),
  diagnosis: z.string().max(200).optional(),
  memo: z.string().max(500).optional(),
});

export type RecordInput = z.infer<typeof recordSchema>;
