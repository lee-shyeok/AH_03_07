import { apiFetch } from "@/lib/api/client";

export type SymptomCode =
  | "FEVER"
  | "PERSISTENT_COUGH"
  | "DYSPNEA"
  | "SEVERE_ABDOMINAL_PAIN"
  | "JAUNDICE"
  | "SEVERE_BLEEDING"
  | "ALTERED_CONSCIOUSNESS"
  | "SHINGLES_SUSPECTED"
  | "MOUTH_SORES"
  | "BLURRED_VISION";

export interface SymptomCheckResponse {
  id: number;
  checked_symptoms: SymptomCode[];
  red_flag_triggered: boolean;
  red_flag_symptoms: SymptomCode[];
  risk_flag_ids: number[];
}

export async function postSymptomCheck(
  checked: SymptomCode[]
): Promise<SymptomCheckResponse> {
  return apiFetch<SymptomCheckResponse>("/v1/symptom-checks", {
    method: "POST",
    body: { checked_symptoms: checked },
  });
}
