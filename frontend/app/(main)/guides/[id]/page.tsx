"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { regenerateGuide, feedbackGuide } from "@/features/guides/api";
import { useGuide, guideKeys } from "@/features/guides/queries";
import { withTimeout } from "@/lib/query/util";

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
  const [busy, setBusy] = useState(false);
  const [rating, setRating] = useState(0);

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

  async function handleFeedback(score: number) {
    setRating(score);
    try {
      await withTimeout(feedbackGuide(id, score));
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

      {/* 평가 (REQ-GUIDE-006) */}
      <Card className="p-4">
        <h2 className="text-sm font-bold">이 안내문이 도움이 됐나요?</h2>
        <div className="mt-2 flex gap-1">
          {[1, 2, 3, 4, 5].map((s) => (
            <button key={s} onClick={() => handleFeedback(s)} aria-label={`${s}점`}>
              <Star className={"h-7 w-7 " + (s <= rating ? "fill-primary text-primary" : "text-muted-foreground/40")} />
            </button>
          ))}
        </div>
      </Card>

      {/* 재생성 (REQ-GUIDE-005) */}
      <Button variant="outline" className="w-full" onClick={handleRegenerate} disabled={busy}>
        {busy ? "재생성 중..." : "안내문 재생성"}
      </Button>

      {/* 면책 (NFR-SAFE) */}
      {guide.disclaimer && (
        <p className="px-1 text-xs leading-5 text-muted-foreground">{guide.disclaimer}</p>
      )}
    </main>
  );
}
