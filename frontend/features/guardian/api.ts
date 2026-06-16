import { apiFetch } from "@/lib/api/client";

export interface Guardian {
  id: string;
  name: string;
  phone_number: string | null;
  email: string | null;
  relationship: string | null;
  is_active: boolean;
}

export interface CreateGuardianData {
  name: string;
  phone_number?: string | null;
  email?: string | null;
  relationship?: string | null;
}

export type SharePeriod = "1d" | "1w" | "1m" | "unlimited";
export type ShareCategory = "medication" | "activity" | "schedule" | "side_effect" | "health_metrics";
export type ShareDetail = "summary" | "full";

export interface ShareLink {
  id: string;
  period: SharePeriod;
  categories: ShareCategory[];
  detail: ShareDetail;
  url: string;
  expires_at?: string;
  created_at: string;
}

export interface CreateShareLinkData {
  period: SharePeriod;
  categories: ShareCategory[];
  detail: ShareDetail;
}

export async function getGuardians(): Promise<Guardian[]> {
  const res = await apiFetch<Guardian[] | { items?: Guardian[] } | { guardians?: Guardian[] }>("/v1/guardians");
  if (Array.isArray(res)) return res;
  if (res && "items" in res && Array.isArray(res.items)) return res.items;
  if (res && "guardians" in res && Array.isArray(res.guardians)) return res.guardians;
  return [];
}

export async function createGuardian(data: CreateGuardianData): Promise<Guardian> {
  return apiFetch<Guardian>("/v1/guardians", { method: "POST", body: data });
}

export async function getShareLinks(): Promise<ShareLink[]> {
  return apiFetch<ShareLink[]>("/v1/guardians/shares");
}

export async function createShareLink(data: CreateShareLinkData): Promise<ShareLink> {
  return apiFetch<ShareLink>("/v1/guardians/shares", { method: "POST", body: data });
}

export async function deleteGuardian(id: string): Promise<void> {
  await apiFetch<void>(`/v1/guardians/${id}`, { method: "DELETE" });
}

export async function updateGuardian(id: string, data: CreateGuardianData): Promise<Guardian> {
  return apiFetch<Guardian>(`/v1/guardians/${id}`, { method: "PUT", body: data });
}

export async function deleteShareLink(id: string): Promise<void> {
  await apiFetch<void>(`/v1/guardians/shares/${id}`, { method: "DELETE" });
}
