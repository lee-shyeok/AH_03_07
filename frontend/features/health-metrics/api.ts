// 건강 수치 API
import { apiFetch } from "@/lib/api/client";

export type MetricType = "BLOOD_PRESSURE" | "BLOOD_SUGAR" | "WEIGHT" | "HEART_RATE";

export interface HealthMetric {
  id: string;
  metric_type: MetricType;
  user_recorded_value: string;
  measured_at: string;
  notes?: string | null;
  created_at: string;
}

export const METRIC_LABEL: Record<MetricType, string> = {
  BLOOD_PRESSURE: "혈압",
  BLOOD_SUGAR: "혈당",
  WEIGHT: "체중",
  HEART_RATE: "심박수",
};

export const METRIC_UNIT: Record<MetricType, string> = {
  BLOOD_PRESSURE: "mmHg",
  BLOOD_SUGAR: "mg/dL",
  WEIGHT: "kg",
  HEART_RATE: "bpm",
};

export async function getHealthMetrics(metricType?: MetricType): Promise<HealthMetric[]> {
  const params = new URLSearchParams();
  if (metricType) params.set("metric_type", metricType);
  const qs = params.toString();
  const res = await apiFetch<{ metrics?: HealthMetric[] } | HealthMetric[]>(
    `/v1/health-metrics${qs ? `?${qs}` : ""}`
  );
  if (Array.isArray(res)) return res;
  return res.metrics ?? [];
}
