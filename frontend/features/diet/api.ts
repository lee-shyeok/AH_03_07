import { apiFetch } from "@/lib/api/client";

export type DietCategory = "RECOMMEND" | "AVOID";
export type FoodCategory =
  | "MEAT"
  | "FISH"
  | "VEGETABLE"
  | "FRUIT"
  | "GRAIN"
  | "DAIRY"
  | "OTHER";

export interface DietInfoResponse {
  id: number;
  disease_code: string;
  category: DietCategory;
  food_category: FoodCategory | null;
  food_name: string;
  reason: string;
  terms?: string[] | null;
}

export async function getDietInfo(disease_code?: string): Promise<DietInfoResponse[]> {
  const url = disease_code
    ? `/v1/diet/info?disease_code=${encodeURIComponent(disease_code)}`
    : "/v1/diet/info";
  return apiFetch<DietInfoResponse[]>(url);
}
