"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Camera, Activity } from "lucide-react";
import HomeHeader from "./components/HomeHeader";
import MedicationCard from "./components/MedicationCard";
import SectionCard from "./components/SectionCard";
import type { MedicationStatus } from "@/features/dashboard/api";
import { getHealthMetrics, METRIC_LABEL, METRIC_UNIT, type HealthMetric, type MetricType } from "@/features/health-metrics/api";

interface GeneralHomeProps {
  name: string;
  medications: MedicationStatus[];
  recentMetrics?: HealthMetric[];
}

export default function GeneralHome({ name, medications, recentMetrics }: GeneralHomeProps) {
  return (
    <main className="mx-auto w-full max-w-md px-5 pb-24 pt-10">
      <HomeHeader name={name} mode="general" />

      <div className="mt-10 flex flex-col gap-8">
        {/* 오늘 컨디션 */}
        <SectionCard title="오늘 컨디션" moreHref="/diary" moreLabel="기록하기">
          <p className="mt-2 text-sm text-muted-foreground">
            오늘 몸 상태를 일기로 기록해보세요.
          </p>
        </SectionCard>

        {/* 최근 건강 수치 */}
        {recentMetrics && recentMetrics.length > 0 && (
          <SectionCard title="최근 건강 수치" moreHref="/health-metrics" moreLabel="전체 보기">
            <div className="mt-3 grid grid-cols-2 gap-2.5">
              {recentMetrics.slice(0, 4).map((m) => (
                <div key={m.id} className="rounded-xl bg-muted/60 px-3 py-2.5">
                  <p className="text-xs text-muted-foreground">{METRIC_LABEL[m.metric_type as MetricType]}</p>
                  <p className="mt-0.5 text-sm font-bold">
                    {Number(m.user_recorded_value).toFixed(1)}
                    <span className="ml-0.5 text-xs font-normal text-muted-foreground">
                      {METRIC_UNIT[m.metric_type as MetricType]}
                    </span>
                  </p>
                </div>
              ))}
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

        {/* 식단 가이드 */}
        <SectionCard title="식단 가이드" moreHref="#" moreLabel="전체 보기">
          <p className="mt-2 text-sm text-muted-foreground">
            증상 관리에 참고할 권장·주의 식품 정보를 한눈에 확인하세요.
          </p>
        </SectionCard>

        {/* 약품 카메라 빠른 진입 */}
        <Link href="/documents">
          <SectionCard>
            <div className="flex items-center gap-3">
              <Camera className="h-5 w-5 text-primary" />
              <span className="flex-1 text-sm font-medium">약품 카메라로 빠르게 등록</span>
              <ArrowRight className="h-4 w-4 text-primary" />
            </div>
          </SectionCard>
        </Link>
      </div>
    </main>
  );
}
