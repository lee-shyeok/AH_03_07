"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, BookOpen, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useGuides, useGuideJob, useGenerateGuide, useDeleteGuide, guideKeys } from "@/features/guides/queries";
import { getMode } from "@/features/auth/mode";

const PURPLE = "#7C5CCF";

export default function GuidesPage() {
  const router = useRouter();
  const qc = useQueryClient();
  const [isAutoimmune, setIsAutoimmune] = useState(false);
  const { data: guides = [], isLoading } = useGuides();
  const gen = useGenerateGuide();
  const del = useDeleteGuide();

  useEffect(() => { setIsAutoimmune(getMode() === "autoimmune"); }, []);

  const [jobId, setJobId] = useState<number | null>(null);
  const [emergency, setEmergency] = useState(false);

  const { data: jobData } = useGuideJob(jobId);

  const isGenerating =
    gen.isPending ||
    jobData?.status === "PENDING" ||
    jobData?.status === "PROCESSING";

  useEffect(() => {
    if (!jobData) return;
    // 우선순위: 응급 > 차단 > 완료
    if (jobData.trigger_emergency_modal) {
      setEmergency(true);
      return;
    }
    if (jobData.status === "BLOCKED") return;
    if (jobData.status === "COMPLETED" && jobData.guide_id) {
      router.push(`/guides/${jobData.guide_id}`);
      qc.invalidateQueries({ queryKey: guideKeys.all });
      setJobId(null);
    }
  }, [jobData, router, qc]);

  async function handleGenerate() {
    try {
      const res = await gen.mutateAsync();
      setJobId(res.job_id);
    } catch {
      /* gen.isError 로 처리 */
    }
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-10">
      {/* 헤더 + 생성 버튼 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button onClick={() => router.back()} className="rounded-full p-1 hover:bg-accent" aria-label="뒤로가기">
            <ChevronLeft className="h-5 w-5" />
          </button>
          <h1 className="text-2xl font-bold">맞춤 안내문</h1>
        </div>
        {isAutoimmune && (
          <Button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="gap-2 text-white"
            style={{ background: PURPLE }}
          >
            {isGenerating && <Loader2 className="h-4 w-4 animate-spin" />}
            안내문 생성
          </Button>
        )}
      </div>

      {/* 일반 모드 안내 */}
      {!isAutoimmune && (
        <div className="mt-4 rounded-lg bg-muted/60 px-4 py-3 text-sm text-muted-foreground">
          맞춤 안내문은 자가면역 질환 모드에서 사용할 수 있습니다.
        </div>
      )}

      {/* 생성 진행 중 */}
      {isAutoimmune && isGenerating && (
        <div className="mt-4 flex items-center gap-2 rounded-lg bg-muted/60 px-4 py-3 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" style={{ color: PURPLE }} />
          안내문을 생성하고 있어요
        </div>
      )}

      {/* 재체크 요청 — stale 증상 체크만으로 LOCKED된 경우 */}
      {jobData?.status === "BLOCKED" && jobData.blocked_reason === "NEEDS_RECHECK" && !emergency && (
        <div className="mt-4 rounded-lg bg-blue-50 px-4 py-3">
          <p className="text-sm font-semibold text-blue-800">증상 체크를 다시 해주세요</p>
          <p className="mt-1 text-xs text-blue-700">
            마지막 증상 체크가 14일을 초과했습니다. 최신 상태를 반영하려면 증상 체크를 새로 진행해 주세요.
          </p>
          <Button
            variant="outline"
            className="mt-3 w-full border-blue-400 text-blue-800 hover:bg-blue-100"
            onClick={() => router.push("/symptom-check")}
          >
            증상 체크하러 가기
          </Button>
        </div>
      )}

      {/* 차단(BLOCKED) 안내 — active 소스로 LOCKED된 경우 REQ-AUTO-006 */}
      {jobData?.status === "BLOCKED" && jobData.blocked_reason !== "NEEDS_RECHECK" && !emergency && (
        <div className="mt-4 rounded-lg bg-yellow-50 px-4 py-3">
          <p className="text-sm text-yellow-800">
            현재 입력하신 상태는 의료진 검토가 권고됩니다. 담당 의료진 상담을 권고합니다.
          </p>
          <Button
            variant="outline"
            className="mt-3 w-full border-yellow-400 text-yellow-800 hover:bg-yellow-100"
            onClick={() => router.push("/risk-flags")}
          >
            의료진 확인 필요 신호 보기
          </Button>
        </div>
      )}

      {/* API 호출 자체 실패 (401 등) */}
      {isAutoimmune && gen.isError && !jobId && (
        <div className="mt-4 rounded-lg bg-muted/60 px-4 py-3 text-sm text-muted-foreground">
          안내문 생성 요청에 실패했어요. 로그인 상태를 확인하거나 잠시 후 다시 시도해 주세요.
        </div>
      )}

      {/* 생성 실패 */}
      {jobData?.status === "FAILED" && (() => {
        const raw = jobData.error_message ?? "";
        if (raw) console.warn("[guide generation] failed:", raw);
        const msg = raw.includes("TRIGGER_NOT_MET")
          ? "안내문을 생성하려면 먼저 자가면역 모드 설정과 증상·약물·검사 기록 중 하나 이상을 입력해 주세요."
          : "안내문 생성에 실패했어요. 잠시 후 다시 시도해 주세요.";
        return (
          <div className="mt-4 rounded-lg bg-muted/60 px-4 py-3 text-sm text-muted-foreground">
            {msg}
          </div>
        );
      })()}

      {/* 목록 */}
      {isLoading ? (
        <p className="mt-8 text-sm text-muted-foreground">불러오는 중...</p>
      ) : guides.length === 0 ? (
        <div className="mt-16 flex flex-col items-center text-muted-foreground">
          <BookOpen className="h-12 w-12 opacity-30" />
          <p className="mt-3 text-sm">생성된 안내문이 없습니다.</p>
          <p className="mt-1 text-xs">진료기록에서 안내문을 생성해보세요.</p>
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {guides.map((g) => (
            <Card key={g.id} className="p-4">
              <Link href={`/guides/${g.id}`} className="block hover:opacity-80">
                <div className="flex items-center justify-between">
                  <span className="font-bold">맞춤 건강 안내문</span>
                  {g.status && (
                    <span className="rounded bg-secondary px-2 py-0.5 text-[11px] font-bold text-secondary-foreground">
                      {g.status}
                    </span>
                  )}
                </div>
                {g.symptom_summary && (
                  <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">
                    {g.symptom_summary}
                  </p>
                )}
                {g.created_at && (
                  <p className="mt-2 text-xs text-muted-foreground">
                    {g.created_at.slice(0, 10)}
                  </p>
                )}
              </Link>
              <div className="mt-3 flex justify-end">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs text-destructive hover:bg-destructive/10"
                  disabled={del.isPending}
                  onClick={() => {
                    if (confirm("이 안내문을 삭제할까요?")) del.mutate(g.id);
                  }}
                >
                  삭제
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* 응급 모달 (trigger_emergency_modal) — NFR-SAFE-003 */}
      {emergency && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-6">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6">
            <h2 className="text-base font-bold text-yellow-700">
              의료진 확인이 필요한 위험 신호가 있어요
            </h2>
            <p className="mt-3 text-sm leading-6 text-foreground">
              즉시 담당 의료진 상담 또는 응급실 방문을 권고합니다.
            </p>
            <p className="mt-2 text-xs text-muted-foreground">
              119 직접 호출을 권장합니다.
            </p>
            <Button
              variant="outline"
              className="mt-5 w-full"
              onClick={() => setEmergency(false)}
            >
              닫기
            </Button>
          </div>
        </div>
      )}
    </main>
  );
}
