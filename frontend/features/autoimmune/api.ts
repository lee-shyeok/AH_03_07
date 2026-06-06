import { apiFetch } from "@/lib/api/client";

export type PregnancyStatus = "none" | "pregnant" | "breastfeeding" | "planning";

export type AutoimmuneProfilePayload = {
  risk_factors: Record<string, unknown>;
  pregnancy_status: PregnancyStatus;
  vaccination_history: string[];
};

export type AutoimmuneProfileResponse = AutoimmuneProfilePayload & {
  advisory_message?: string | null;
};

export async function upsertAutoimmuneProfile(
  payload: AutoimmuneProfilePayload,
): Promise<AutoimmuneProfileResponse> {
  return apiFetch<AutoimmuneProfileResponse>("/v1/autoimmune/profile", {
    method: "PUT",
    body: payload,
  });
}
