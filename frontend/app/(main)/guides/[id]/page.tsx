"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { getGuide, regenerateGuide, feedbackGuide } from "@/features/guides/api";
import type { Guide } from "@/features/guides/api";

function Section({ title, content }: { title: string; content?: string | string[] }) {
  if (!content || (Array.isArray(content) && content.length === 0)) return null;
  const text = Array.isArray(content)
    ? content.map((c) => `• ${c}`).join("\n")
    : content;
  return (
    <Card className="p-4">
      <h2 className="text-sm font-bold">{title}</h2>
      <p className="mt-2 whitespace-pre-line text-sm leading-6 text-foreground">{text}</p>
    </Card>
  );
}

// 백엔드 미가동 시 보여줄 예시 안내문 상세(데모)
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

export default function GuideDetailPage() {
  const params = useParams();
  const id = Number(params.id);
  const [guide, setGuide] = useState<Guide | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [rating, setRating] = useState(0);

  function load() {
    setLoading(true);
    // 백엔드가 살아있으면 실데이터, 없으면 2초 후 예시 표시
    Promise.race([
      getGuide(id),
      new Promise<Guide>((_, reject) => setTimeout(() => reject(new Error("timeout")), 2000)),
    ])
      .then(setGuide)
      .catch(() => setGuide(dummyGuide(id)))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    if (!Number.isNaN(id)) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleRegenerate() {
    setBusy(true);
    try {
      await regenerateGuide(id);
      load();
    } catch {
      alert("재생성에 실패했습니다.");
    } finally {
      setBusy(false);
    }
  }

  async function handleFeedback(score: number) {
    setRating(score);
    try {
      await feedbackGuide(id, score);
    } catch {
      /* no-op */
    }
  }

  if (loading) {
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
              <Star
                className={
                  "h-7 w-7 " +
                  (s <= rating ? "fill-primary text-primary" : "text-muted-foreground/40")
                }
              />
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
