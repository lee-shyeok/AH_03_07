"use client";

import { useEffect, useState, useMemo, useRef } from "react";
import Link from "next/link";
import { ArrowRight, Volume2, Loader2, X, Plus } from "lucide-react";
import HomeHeader from "./components/HomeHeader";
import MedicationCard from "./components/MedicationCard";
import SectionCard from "./components/SectionCard";
import type { MedicationStatus } from "@/features/dashboard/api";
import { METRIC_LABEL, METRIC_UNIT, type HealthMetric, type MetricType } from "@/features/health-metrics/api";
import { getDiaryLogs, type DiaryLog } from "@/features/diary/api";
import { apiFetch } from "@/lib/api/client";

interface GeneralHomeProps {
  name: string;
  medications: MedicationStatus[];
  recentMetrics?: HealthMetric[];
}

const DAYS = ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"];

const CONDITION_EMOJI: Record<string, string> = {
  good: "😊", GOOD: "😊",
  normal: "😐", NORMAL: "😐",
  bad: "😟", BAD: "😟",
};

const CONDITION_LABEL: Record<string, string> = {
  good: "좋음", GOOD: "좋음",
  normal: "보통", NORMAL: "보통",
  bad: "나쁨", BAD: "나쁨",
};

function getMetricValueColor(type: MetricType, value: number): string {
  if (type === "BLOOD_PRESSURE") {
    if (value <= 120) return "text-green-600";
    if (value <= 139) return "text-yellow-500";
    return "text-red-500";
  }
  if (type === "BLOOD_SUGAR") {
    if (value <= 100) return "text-green-600";
    if (value <= 125) return "text-yellow-500";
    return "text-red-500";
  }
  return "";
}

interface TtsData {
  audioUrl: string;
  summaryText: string;
}

export default function GeneralHome({ name, medications, recentMetrics }: GeneralHomeProps) {
  const [todayLog, setTodayLog] = useState<DiaryLog | null>(null);
  const [ttsLoading, setTtsLoading] = useState(false);
  const [ttsData, setTtsData] = useState<TtsData | null>(null);
  const [ttsError, setTtsError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const todayLabel = useMemo(() => {
    const now = new Date();
    return `${now.getMonth() + 1}월 ${now.getDate()}일 ${DAYS[now.getDay()]}`;
  }, []);

  const todayStr = useMemo(() => new Date().toISOString().slice(0, 10), []);

  useEffect(() => {
    getDiaryLogs()
      .then((logs) => {
        const today = logs.find((l) => {
          const date = l.log_date ?? l.recorded_at;
          return date?.startsWith(todayStr);
        });
        setTodayLog(today ?? null);
      })
      .catch(() => {});
  }, [todayStr]);

  const handleTts = async () => {
    if (ttsLoading) return;
    setTtsLoading(true);
    setTtsError(null);
    try {
      const res = await apiFetch<{ audio_url: string; summary_text: string }>(
        "/v1/contents/health-summary-tts",
        { method: "POST" }
      );
      const data: TtsData = { audioUrl: res.audio_url, summaryText: res.summary_text };
      setTtsData(data);
      if (audioRef.current) {
        audioRef.current.pause();
      }
      const audio = new Audio(data.audioUrl);
      audioRef.current = audio;
      audio.play().catch(() => {});
    } catch {
      setTtsError("음성 생성에 실패했습니다.");
    } finally {
      setTtsLoading(false);
    }
  };

  const condition = todayLog?.condition ?? todayLog?.overall_condition;

  return (
    <main className="mx-auto w-full max-w-md px-5 pb-24 pt-10">
      <HomeHeader name={name} mode="general" />
      <div className="mt-1 flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{todayLabel}</p>
        <button
          onClick={handleTts}
          disabled={ttsLoading}
          className="flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1.5 text-primary active:bg-primary/20 disabled:opacity-50"
          aria-label="건강 요약 음성 듣기"
        >
          {ttsLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Volume2 className="h-4 w-4" />
          )}
          <span className="text-xs font-medium">요약 듣기</span>
        </button>
      </div>

      {/* TTS 요약 카드 */}
      {ttsError && (
        <div className="mt-3 flex items-start justify-between gap-2 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">
          <span>{ttsError}</span>
          <button onClick={() => setTtsError(null)} className="shrink-0">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
      {ttsData && (
        <div className="mt-3 flex items-start justify-between gap-2 rounded-xl bg-primary/5 px-4 py-3">
          <div className="flex items-start gap-2">
            <Volume2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
            <p className="text-sm leading-relaxed text-foreground">{ttsData.summaryText}</p>
          </div>
          <button
            onClick={() => {
              audioRef.current?.pause();
              setTtsData(null);
            }}
            className="shrink-0 text-muted-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <div className="mt-8 flex flex-col gap-8">
        {/* 오늘 컨디션 */}
        <SectionCard
          title="오늘 컨디션"
          moreHref="/diary"
          moreLabel="자세히 보기"
        >
          {condition ? (
            <div className="mt-2 flex items-center gap-3">
              <span className="text-4xl">{CONDITION_EMOJI[condition] ?? "😐"}</span>
              <div>
                <p className="text-base font-semibold">{CONDITION_LABEL[condition] ?? condition}</p>
                <p className="text-xs text-muted-foreground">오늘 상태를 기록했어요</p>
              </div>
            </div>
          ) : (
            <p className="mt-2 text-sm text-muted-foreground">
              오늘 몸 상태를 기록해보세요.
            </p>
          )}
        </SectionCard>

        {/* 최근 건강 수치 */}
        {recentMetrics && recentMetrics.length > 0 && (
          <SectionCard title="최근 건강 수치" moreHref="/health-metrics" moreLabel="전체 보기">
            <div className="mt-3 grid grid-cols-2 gap-2.5">
              {(["BLOOD_PRESSURE", "BLOOD_SUGAR", "WEIGHT", "HEART_RATE"] as MetricType[])
                .map((type) =>
                  recentMetrics
                    .filter((m) => m.metric_type === type)
                    .sort((a, b) => b.measured_at.localeCompare(a.measured_at))[0]
                )
                .filter(Boolean)
                .map((m) => {
                  const systolic = Math.round(Number(m!.user_recorded_value));
                  const colorClass = getMetricValueColor(m!.metric_type as MetricType, systolic);
                  const displayVal =
                    m!.metric_type === "BLOOD_PRESSURE" && m!.diastolic_value
                      ? `${systolic}/${Math.round(Number(m!.diastolic_value))}`
                      : String(systolic);
                  return (
                    <Link
                      key={m!.metric_type}
                      href="/health-metrics"
                      className="rounded-xl bg-muted/60 px-3 py-2.5 active:bg-muted"
                    >
                      <p className="text-xs text-muted-foreground">
                        {METRIC_LABEL[m!.metric_type as MetricType]}
                      </p>
                      <p className={`mt-0.5 text-sm font-bold ${colorClass}`}>
                        {displayVal}
                        <span className="ml-0.5 text-xs font-normal text-muted-foreground">
                          {METRIC_UNIT[m!.metric_type as MetricType]}
                        </span>
                      </p>
                    </Link>
                  );
                })}
            </div>
          </SectionCard>
        )}

        {/* 오늘 복용약 */}
        <MedicationCard medications={medications} />

        {/* 통합 캘린더 */}
        <SectionCard title="통합 캘린더" moreHref="/schedule" moreLabel="전체 보기">
          <p className="mt-2 text-sm text-muted-foreground">
            복약·일정을 한눈에 확인하세요.
          </p>
        </SectionCard>

        {/* 빠른 진입점 */}
        <div className="grid grid-cols-4 gap-2">
          <Link
            href="/pharmacy"
            className="flex flex-col items-center gap-1.5 rounded-2xl bg-muted/60 py-4 active:bg-muted"
          >
            <span className="text-2xl">🗺️</span>
            <span className="text-xs font-medium">약국 찾기</span>
          </Link>
          <Link
            href="/guardian"
            className="flex flex-col items-center gap-1.5 rounded-2xl bg-muted/60 py-4 active:bg-muted"
          >
            <span className="text-2xl">👨‍👩‍👧</span>
            <span className="text-xs font-medium">보호자 공유</span>
          </Link>
          <Link
            href="/diet"
            className="flex flex-col items-center gap-1.5 rounded-2xl bg-muted/60 py-4 active:bg-muted"
          >
            <span className="text-2xl">📚</span>
            <span className="text-xs font-medium">건강 가이드</span>
          </Link>
          <Link
            href="/documents"
            className="flex flex-col items-center gap-1.5 rounded-2xl bg-muted/60 py-4 active:bg-muted"
          >
            <span className="text-2xl">📄</span>
            <span className="text-xs font-medium">처방전</span>
          </Link>
        </div>

        {/* SOS 응급 버튼 + 응급카드 */}
        <div className="flex gap-3">
          <Link href="/emergency" className="flex-1">
            <div className="flex items-center justify-center gap-2 rounded-2xl bg-red-500 px-4 py-4 text-white shadow-md active:bg-red-600">
              <span className="text-base font-bold">🚨 SOS 응급</span>
              <ArrowRight className="h-4 w-4" />
            </div>
          </Link>
          <Link href="/emergency/card" className="flex-1">
            <div className="flex items-center justify-center gap-2 rounded-2xl border border-red-300 bg-red-50 px-4 py-4 text-red-600 shadow-sm active:bg-red-100">
              <span className="text-base font-bold">🪪 응급카드 +</span>
            </div>
          </Link>
        </div>
      </div>
    </main>
  );
}
