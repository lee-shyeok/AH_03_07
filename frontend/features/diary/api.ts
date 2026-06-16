import { apiFetch } from "@/lib/api/client";

export type Condition = "good" | "normal" | "bad";
export type BodyPart = "머리" | "목" | "어깨" | "가슴" | "배" | "등" | "허리" | "팔" | "다리";
export type Feeling = "콕콕" | "욱신" | "묵직" | "화끈" | "답답";
export type MealTime = "아침" | "점심" | "저녁" | "취침전";

export interface DiaryLog {
  id?: number;
  condition?: Condition;
  overall_condition?: string;
  body_parts?: BodyPart[];
  feelings?: Feeling[];
  note?: string;
  memo?: string;
  medications?: MealTime[];
  recorded_at?: string;
  log_date?: string;
}

export interface DiaryLogCreate {
  condition: Condition;
  body_parts?: BodyPart[];
  feelings?: Feeling[];
  note?: string;
  medications?: MealTime[];
  recorded_at?: string;
}

export async function getDiaryLogs(): Promise<DiaryLog[]> {
  const res = await apiFetch<{ logs?: DiaryLog[]; items?: DiaryLog[] } | DiaryLog[]>("/v1/diary/symptom-logs");
  return Array.isArray(res) ? res : (res.logs ?? res.items ?? []);
}

export async function deleteDiaryLog(id: number | string): Promise<void> {
  await apiFetch(`/v1/diary/symptom-logs/${id}`, { method: "DELETE" });
}

export async function createDiaryLog(data: DiaryLogCreate): Promise<void> {
  const payload: Record<string, unknown> = {
    overall_condition: ({ good: "GOOD", normal: "NORMAL", bad: "BAD" } as const)[data.condition],
    log_date: data.recorded_at,
    feeling: data.feelings?.length ? Object.fromEntries(data.feelings.map((f) => [f, true])) : null,
    memo: data.note,
    ...(data.body_parts !== undefined && { body_parts: data.body_parts }),
    ...(data.medications !== undefined && { medications: data.medications }),
  };
  await apiFetch("/v1/diary/symptom-logs", { method: "POST", body: payload });
}
