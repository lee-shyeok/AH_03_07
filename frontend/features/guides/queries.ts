// 맞춤 안내문 서버 상태 (TanStack Query) — 데모 폴백 유지
import { useQuery } from "@tanstack/react-query";
import { getGuides, getGuide, type Guide } from "./api";
import { withTimeout } from "@/lib/query/util";

export const guideKeys = {
  all: ["guides"] as const,
  detail: (id: number) => ["guides", id] as const,
};

const DUMMY_LIST: Guide[] = [
  { id: 1, status: "완료", symptom_summary: "최근 관절 통증·아침 강직 30분 이상 지속. 활성도 중등도로 평가됨.", created_at: "2026-05-20" },
  { id: 2, status: "완료", symptom_summary: "혈압 130/85, 가벼운 두통 동반. 저염식·규칙적 복약 안내 포함.", created_at: "2026-05-10" },
];

function dummyGuide(id: number): Guide {
  return {
    id,
    status: "완료",
    medication_general:
      "처방받은 약은 정해진 시간에 복용하세요.\n메토트렉세이트는 주 1회 같은 요일에 복용하며, 다음 날 엽산을 복용합니다.\n복용을 잊었다면 임의로 두 배 용량을 먹지 말고 의료진에 문의하세요.",
    symptom_summary:
      "최근 관절 통증과 아침 강직이 30분 이상 지속되었습니다. 전반적 활성도는 중등도로 평가됩니다.",
    lifestyle_info:
      "규칙적인 저강도 운동(걷기·수영)으로 관절 기능을 유지하세요.\n충분한 수면과 수분 섭취, 금연이 증상 관리에 도움이 됩니다.",
    side_effect_monitoring:
      "구내염, 메스꺼움, 발열, 심한 피로가 나타나면 복약을 중단하고 의료진과 상담하세요.\n정기적인 혈액검사(간기능·혈구수)가 필요합니다.",
    disclaimer:
      "본 안내문은 일반 정보이며 진단·처방을 대체하지 않습니다. 증상 변화 시 담당 의료진과 상담하세요.",
  } as Guide;
}

export function useGuides() {
  return useQuery({
    queryKey: guideKeys.all,
    queryFn: async () => {
      try {
        const data = await withTimeout(getGuides());
        return data.length ? data : DUMMY_LIST;
      } catch {
        return DUMMY_LIST;
      }
    },
  });
}

export function useGuide(id: number) {
  return useQuery({
    queryKey: guideKeys.detail(id),
    queryFn: async () => {
      try {
        return await withTimeout(getGuide(id));
      } catch {
        return dummyGuide(id);
      }
    },
    enabled: Number.isFinite(id),
  });
}
