import { apiFetch } from "@/lib/api/client";

type DiseaseItem = {
  disease_code: "RA" | "SLE";
  diagnosed_date?: string | null;
  note?: string | null;
};

export async function createDiseases(diseases: DiseaseItem[]) {
  return apiFetch("/v1/diseases", {
    method: "POST",
    body: { diseases },
  });
}
