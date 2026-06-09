import { useMutation, useQuery } from "@tanstack/react-query";
import { getGuides, getGuide, getSources, getSections, createGuide, getGuideJob, type GuideJob } from "./api";

export const guideKeys = {
  all: ["guides"] as const,
  detail: (id: number) => ["guides", id] as const,
  sources: (id: number) => ["guides", id, "sources"] as const,
  sections: (id: number) => ["guides", id, "sections"] as const,
  job: (jobId: number) => ["guides", "job", jobId] as const,
};


export function useGuides() {
  return useQuery({
    queryKey: guideKeys.all,
    queryFn: () => getGuides(),
  });
}

export function useGuide(id: number) {
  return useQuery({
    queryKey: guideKeys.detail(id),
    queryFn: () => getGuide(id),
    enabled: Number.isFinite(id),
  });
}

export function useGuideSources(guideId: number) {
  return useQuery({
    queryKey: guideKeys.sources(guideId),
    queryFn: () => getSources(guideId),
    enabled: !!guideId,
  });
}

export function useGuideSections(guideId: number) {
  return useQuery({
    queryKey: guideKeys.sections(guideId),
    queryFn: () => getSections(guideId),
    enabled: !!guideId,
  });
}

export function useGuideJob(jobId: number | null) {
  return useQuery<GuideJob>({
    queryKey: guideKeys.job(jobId!),
    queryFn: () => getGuideJob(jobId!),
    enabled: jobId != null,
    refetchInterval: (query) => {
      const s = query.state.data?.status;
      return s === "COMPLETED" || s === "BLOCKED" || s === "FAILED" ? false : 2000;
    },
  });
}

export function useGenerateGuide() {
  return useMutation({ mutationFn: createGuide });
}
