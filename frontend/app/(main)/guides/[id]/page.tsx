"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import {
  Download,
  Newspaper,
  Share2,
  Star,
  ThumbsDown,
  ThumbsUp,
  Volume2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { regenerateGuide, feedbackGuide, generateCardNews, generateTTS } from "@/features/guides/api";
import { useGuide, guideKeys } from "@/features/guides/queries";
import { withTimeout } from "@/lib/query/util";

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
  const qc = useQueryClient();
  const { data: guide, isLoading } = useGuide(id);

  // HEAD: 재생성 + 별점 상태
  const [busy, setBusy] = useState(false);
  const [rating, setRating] = useState(0);

  // b06d67b: 카드뉴스/TTS + 👍👎 상태
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [cardNewsLoading, setCardNewsLoading] = useState(false);
  const [ttsLoading, setTtsLoading] = useState(false);
  const [contentMessage, setContentMessage] = useState<{ text: string; ok: boolean } | null>(null);

  // HEAD: 안내문 재생성
  async function handleRegenerate() {
    setBusy(true);
    try {
      await withTimeout(regenerateGuide(id));
      await qc.invalidateQueries({ queryKey: guideKeys.detail(id) });
    } catch {
      /* 백엔드 미가동(데모) */
    } finally {
      setBusy(false);
    }
  }

  // HEAD: 별점 피드백
  async function handleStarFeedback(score: number) {
    setRating(score);
    try {
      await withTimeout(feedbackGuide(id, score));
    } catch {
      /* no-op */
    }
  }

  // b06d67b: 카드뉴스 생성
  async function handleCardNews() {
    setCardNewsLoading(true);
    setContentMessage(null);
    try {
      await withTimeout(generateCardNews(id));
      setContentMessage({ text: "카드뉴스 생성이 완료됐어요.", ok: true });
    } catch {
      setContentMessage({ text: "카드뉴스 생성에 실패했어요.", ok: false });
    } finally {
      setCardNewsLoading(false);
    }
  }

  // b06d67b: TTS 변환
  async function handleTTS() {
    setTtsLoading(true);
    setContentMessage(null);
    try {
      await withTimeout(generateTTS(id));
      setContentMessage({ text: "음성 변환이 완료됐어요.", ok: true });
    } catch {
      setContentMessage({ text: "음성 변환에 실패했어요.", ok: false });
    } finally {
      setTtsLoading(false);
    }
  }

  // b06d67b: 👍👎 피드백
  async function handleThumbFeedback(vote: "up" | "down") {
    setFeedback(vote);
    setFeedbackSent(true);
    try {
      await withTimeout(feedbackGuide(id, vote === "up" ? 1 : 0));
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

      {/* HEAD: 별점 평가 (REQ-GUIDE-006) */}
      <Card className="p-4">
        <h2 className="text-sm font-bold">이 안내문이 도움이 됐나요?</h2>
        <div className="mt-2 flex gap-1">
          {[1, 2, 3, 4, 5].map((s) => (
            <button key={s} onClick={() => handleStarFeedback(s)} aria-label={`${s}점`}>
              <Star className={"h-7 w-7 " + (s <= rating ? "fill-primary text-primary" : "text-muted-foreground/40")} />
            </button>
          ))}
        </div>
      </Card>

      {/* HEAD: 재생성 (REQ-GUIDE-005) */}
      <Button variant="outline" className="w-full" onClick={handleRegenerate} disabled={busy}>
        {busy ? "재생성 중..." : "안내문 재생성"}
      </Button>

      {/* HEAD: 면책 조항 고정 노출 (NFR-SAFE-001) */}
      <p className="rounded-xl bg-muted/60 px-4 py-3 text-xs leading-5 text-muted-foreground">
        ⚠️ 본 안내문은 정보 제공 목적이며 의료 진단·처방·용량 조절을 대체하지 않습니다. 증상이 심각하거나 응급 상황이면 즉시 의료진에게 상담하세요.
        {guide.disclaimer && ` ${guide.disclaimer}`}
      </p>

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

      {/* b06d67b: REQ-CONT-001 카드뉴스 / REQ-CONT-002 음성 */}
      <div className="grid grid-cols-2 gap-3">
        <Button
          variant="outline"
          className="h-14 flex-col gap-1 text-xs"
          onClick={handleCardNews}
          disabled={cardNewsLoading || ttsLoading}
        >
          <Newspaper className="h-4 w-4" />
          {cardNewsLoading ? "생성 중..." : "카드뉴스로 보기"}
        </Button>
        <Button
          variant="outline"
          className="h-14 flex-col gap-1 text-xs"
          onClick={handleTTS}
          disabled={ttsLoading || cardNewsLoading}
        >
          <Volume2 className="h-4 w-4" />
          {ttsLoading ? "변환 중..." : "음성으로 듣기"}
        </Button>
      </div>
      {contentMessage && (
        <p className={`px-1 text-center text-xs ${contentMessage.ok ? "text-[#7C5CCF]" : "text-destructive"}`}>
          {contentMessage.text}
        </p>
      )}

      {/* b06d67b: PDF 저장 / 공유하기 */}
      <div className="grid grid-cols-2 gap-3">
        <Button variant="outline" className="gap-2" onClick={() => {}}>
          <Download className="h-4 w-4" />
          PDF 저장
        </Button>
        <Button variant="outline" className="gap-2" onClick={() => {}}>
          <Share2 className="h-4 w-4" />
          공유하기
        </Button>
      </div>

      {/* b06d67b: REQ-FEED-001 👍👎 피드백 */}
      <Card className="p-4">
        <h2 className="mb-3 text-center text-sm font-bold">이 요약이 도움이 됐나요?</h2>
        <div className="flex justify-center gap-6">
          <button
            onClick={() => handleThumbFeedback("up")}
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
            onClick={() => handleThumbFeedback("down")}
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
