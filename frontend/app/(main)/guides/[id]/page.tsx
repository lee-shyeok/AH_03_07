"use client";

import { useState } from "react";
import { useParams } from "next/navigation";

import {
  ChevronDown,
  Download,
  Share2,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { feedbackGuide } from "@/features/guides/api";
import { useGuide, useGuideSources } from "@/features/guides/queries";
import { withTimeout } from "@/lib/query/util";

const PURPLE = "#7C5CCF";
const MOCK = {
  key_symptoms: ["관절 통증", "발열", "피로감", "피부 발진"],
};

function Section({ title, content }: { title: string; content?: string | string[] }) {
  if (!content || (Array.isArray(content) && content.length === 0)) return null;
  const text = Array.isArray(content) ? content.map((c) => `• ${c}`).join("\n") : content;
  return (
    <Card className="p-4">
      <h2 className="text-sm font-bold">{title}</h2>
      <p className="mt-2 whitespace-pre-line text-sm leading-6 text-foreground">{text}</p>
    </Card>
  );
}

export default function GuideDetailPage() {
  const params = useParams();
  const id = Number(params.id);
  const { data: guide, isLoading } = useGuide(id);
  const { data: sources } = useGuideSources(id);
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [shareMessage, setShareMessage] = useState<string | null>(null);

  async function handleShare() {
    const url = window.location.href;
    if (navigator.share) {
      try {
        await navigator.share({ title: "진료 전 요약", url });
      } catch {
        /* 사용자가 취소한 경우 무시 */
      }
      return;
    }
    try {
      await navigator.clipboard.writeText(url);
      setShareMessage("링크가 복사됐어요");
      setTimeout(() => setShareMessage(null), 2500);
    } catch {
      setShareMessage("복사에 실패했어요");
      setTimeout(() => setShareMessage(null), 2500);
    }
  }

  async function handleFeedback(type: "up" | "down") {
    if (feedbackSent) return;
    setFeedback(type);
    setFeedbackSent(true);
    try {
      await withTimeout(feedbackGuide(id, type === "up" ? 1 : 0));
    } catch {
      /* no-op */
    }
  }

  if (isLoading) {
    return <main className="mx-auto max-w-md px-5 py-10 text-sm text-muted-foreground">불러오는 중...</main>;
  }
  if (!guide) {
    return <main className="mx-auto max-w-md px-5 py-10 text-sm text-destructive">안내문을 찾을 수 없습니다.</main>;
  }

  return (
    <main className="mx-auto w-full max-w-md space-y-4 px-5 py-8">
      <h1 className="text-2xl font-bold">맞춤 건강 안내문</h1>

      <Section title="복약 안내" content={guide.medication_general} />
      <Section title="증상 요약" content={guide.symptom_summary} />
      <Section title="생활 습관" content={guide.lifestyle_info} />
      <Section title="부작용 모니터링" content={guide.side_effect_monitoring} />

      {/* 참고 자료 (REQ-KB-003) */}
      <Card className="p-4">
        <button
          className="flex w-full items-center justify-between"
          onClick={() => setSourcesOpen((v) => !v)}
          aria-expanded={sourcesOpen}
        >
          <span className="text-sm font-bold" style={{ color: PURPLE }}>참고 자료</span>
          <ChevronDown
            className="h-4 w-4 transition-transform"
            style={{ color: PURPLE, transform: sourcesOpen ? "rotate(180deg)" : "rotate(0deg)" }}
          />
        </button>

        {sourcesOpen && (
          <div className="mt-3 space-y-3">
            {!sources || sources.length === 0 ? (
              <p className="text-xs text-muted-foreground">출처 없는 일반 정보입니다</p>
            ) : (
              [...sources]
                .sort((a, b) => a.citation_order - b.citation_order)
                .map((src) => (
                  <div key={src.citation_order} className="rounded-lg border p-3 text-xs">
                    <div className="flex items-center gap-2">
                      <span
                        className="rounded px-1.5 py-0.5 text-[11px] font-bold text-white"
                        style={{ background: PURPLE }}
                      >
                        {src.source_org}
                      </span>
                      <span className="font-medium text-foreground">{src.source_title}</span>
                    </div>
                    {src.source_page != null && (
                      <p className="mt-1 text-muted-foreground">p.{src.source_page}</p>
                    )}
                    {src.used_for_section != null && (
                      <p className="mt-1 text-muted-foreground">참고 챕터: {src.used_for_section}</p>
                    )}
                    {src.source_url && (
                      <a
                        href={src.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-1 block underline"
                        style={{ color: PURPLE }}
                      >
                        공식 출처 보기
                      </a>
                    )}
                  </div>
                ))
            )}
          </div>
        )}
      </Card>

      {/* b06d67b: 주의 증상 기록 */}
      <Card className="p-4">
        <h2 className="mb-3 text-sm font-bold">주의 증상 기록</h2>
        <ul className="space-y-2">
          {MOCK.key_symptoms.map((sym) => (
            <li key={sym} className="flex items-center gap-2 text-sm">
              <span className="h-2 w-2 flex-shrink-0 rounded-full bg-[#7C5CCF]" />
              {sym}
            </li>
          ))}
        </ul>
      </Card>

      {/* b06d67b: PDF 저장 / 공유하기 */}
      <div className="grid grid-cols-2 gap-3">
        <Button variant="outline" className="gap-2" onClick={() => window.print()}>
          <Download className="h-4 w-4" />
          PDF 저장
        </Button>
        <Button variant="outline" className="gap-2" onClick={handleShare}>
          <Share2 className="h-4 w-4" />
          공유하기
        </Button>
      </div>
      {shareMessage && (
        <p className="text-center text-xs text-[#7C5CCF]">{shareMessage}</p>
      )}

      {/* b06d67b: REQ-FEED-001 👍👎 피드백 */}
      <Card className="p-4">
        <h2 className="mb-3 text-center text-sm font-bold">이 요약이 도움이 됐나요?</h2>
        <div className="flex justify-center gap-6">
          <button
            onClick={() => handleFeedback("up")}
            disabled={feedbackSent}
            className={`flex flex-col items-center gap-1.5 rounded-xl px-6 py-3 text-xs font-semibold transition-colors disabled:opacity-60 ${
              feedback === "up"
                ? "bg-[#EDE9FF] text-[#7C5CCF]"
                : "bg-gray-50 text-muted-foreground hover:bg-[#EDE9FF] hover:text-[#7C5CCF]"
            }`}
          >
            <ThumbsUp className="h-6 w-6" />
            도움됐어요
          </button>
          <button
            onClick={() => handleFeedback("down")}
            disabled={feedbackSent}
            className={`flex flex-col items-center gap-1.5 rounded-xl px-6 py-3 text-xs font-semibold transition-colors disabled:opacity-60 ${
              feedback === "down"
                ? "bg-red-50 text-red-500"
                : "bg-gray-50 text-muted-foreground hover:bg-red-50 hover:text-red-500"
            }`}
          >
            <ThumbsDown className="h-6 w-6" />
            아쉬워요
          </button>
        </div>
        {feedbackSent && (
          <p className="mt-3 text-center text-xs text-muted-foreground">피드백 감사합니다 :)</p>
        )}
      </Card>

      {guide.disclaimer && (
        <p className="px-1 text-xs leading-5 text-muted-foreground">{guide.disclaimer}</p>
      )}
    </main>
  );
}
