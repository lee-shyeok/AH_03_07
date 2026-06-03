// 검사 결과 API (REQ-AUTO 자가면역 검사 추적)
import { apiFetch } from "@/lib/api/client";

export interface LabItem {
  key: string;
  name: string;
  description: string;
  unit: string;
  reference: string;
  // 정상 판정: value가 max 미만이면 정상
  max: number;
  value: string;
}

export interface LabResultCreate {
  test_date: string;
  items: { key: string; value: number }[];
  memo?: string;
}

export async function createLabResult(data: LabResultCreate): Promise<void> {
  await apiFetch("/v1/lab-results", { method: "POST", body: data });
}
