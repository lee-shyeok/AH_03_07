// 알림 서버 상태 (TanStack Query) — 데모 폴백 유지
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getNotifications, markRead, type AppNotification } from "./api";
import { withTimeout } from "@/lib/query/util";

export const notificationKeys = { all: ["notifications"] as const };

// 백엔드 미가동 시 보여줄 예시 알림(데모)
const DUMMY: AppNotification[] = [
  { id: 1, title: "복약 시간이에요 💊", body: "오후 약(MTX) 복용할 시간입니다.", notification_type: "medication", is_read: false },
  { id: 2, title: "활성도 점검 알림", body: "이번 주 활성도를 기록해주세요.", notification_type: "activity", is_read: false },
  { id: 3, title: "고위험 신호 감지", body: "최근 CRP 수치가 참고 범위를 초과했어요. 의료진 상담을 권장합니다.", notification_type: "risk", is_read: false },
  { id: 4, title: "새 맞춤 안내문 도착", body: "여름철 자외선 관리 가이드가 도착했어요.", notification_type: "guide", is_read: true },
  { id: 5, title: "출석체크 완료", body: "오늘도 건강 관리 성공! +10P 적립되었습니다.", notification_type: "done", is_read: true },
];

export function useNotifications() {
  return useQuery({
    queryKey: notificationKeys.all,
    queryFn: async () => {
      try {
        const data = await withTimeout(getNotifications());
        return data.length ? data : DUMMY;
      } catch {
        return DUMMY;
      }
    },
  });
}

export function useMarkRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      try {
        await withTimeout(markRead(id));
      } catch {
        /* 데모 */
      }
    },
    // 낙관적 업데이트: 즉시 읽음 처리
    onMutate: async (id: number) => {
      await qc.cancelQueries({ queryKey: notificationKeys.all });
      const prev = qc.getQueryData<AppNotification[]>(notificationKeys.all);
      qc.setQueryData<AppNotification[]>(notificationKeys.all, (old) =>
        (old ?? []).map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      return { prev };
    },
    onError: (_e, _id, ctx) => {
      if (ctx?.prev) qc.setQueryData(notificationKeys.all, ctx.prev);
    },
  });
}
