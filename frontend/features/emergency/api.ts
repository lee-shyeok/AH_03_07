// 응급 카드 API (REQ-EMRG)
import { apiFetch } from "@/lib/api/client";

export interface EmergencyContact {
  name: string;
  relationship: string;
  phone: string;
  is_doctor?: boolean;
}

export interface EmergencyCard {
  blood_type?: string;
  chronic_conditions?: string;
  medications?: string;
  allergies?: string;
  emergency_contacts?: EmergencyContact[];
  show_on_lock_screen?: boolean;
  send_location?: boolean;
}

export interface SOSTriggerResult {
  triggered: boolean;
  message?: string;
}

export async function getEmergencyCard(): Promise<EmergencyCard> {
  return apiFetch<EmergencyCard>("/v1/emergency/card");
}

export async function updateEmergencyCard(
  data: Partial<EmergencyCard>
): Promise<EmergencyCard> {
  return apiFetch<EmergencyCard>("/v1/emergency/card", {
    method: "PUT",
    body: data,
  });
}

export async function triggerEmergencySOS(): Promise<SOSTriggerResult> {
  return apiFetch<SOSTriggerResult>("/v1/emergency/trigger", {
    method: "POST",
  });
}
