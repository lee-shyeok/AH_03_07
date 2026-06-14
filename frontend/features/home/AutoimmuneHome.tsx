"use client";

import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  FileText,
  ClipboardList,
  FlaskConical,
  MessageCircle,
  Phone,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import HomeHeader from "./components/HomeHeader";
import MedicationCard, { type Medication } from "./components/MedicationCard";
import SectionCard from "./components/SectionCard";
import { useGuides } from "@/features/guides/queries";

const PURPLE = "#7C5CCF";
const RED = "#EF5B5B";

interface AutoimmuneHomeProps {
  name: string;
  medications: Medication[];
  recentActivity: unknown[];
  riskFlags: unknown[];
  pendingSchedules: unknown[];
  isLupus?: boolean;
}

// ⑥ 빠른 진입점 — TODO(라우트): /lab-results, /chat 실제 경로 확정 필요
const QUICK_LINKS = [
  { href: "/activity/new", label: "활성도 기록", Icon: Activity },
  { href: "/diary", label: "증상 일기", Icon: ClipboardList },
  { href: "/lab-results", label: "검사 결과", Icon: FlaskConical },
  { href: "/guides", label: "맞춤 안내문", Icon: FileText },
  { href: "/chat", label: "챗봇 상담", Icon: MessageCircle },
];

export default function AutoimmuneHome({
  name,
  medications,
  recentActivity,
  riskFlags,
  pendingSchedules,
  isLupus,
}: AutoimmuneHomeProps) {
  const hasActivity = recentActivity.length > 0;
  const riskCount = riskFlags.length;
  const hasSchedule = pendingSchedules.length > 0;
  const { data: guides = [] } = useGuides();
  const latestGuideHref = guides[0]?.id ? `/guides/${guides[0].id}` : "/guides";

  return (
    <main className="mx-auto w-full max-w-md px-5 pb-32 pt-10">
      <HomeHeader name={name} mode="autoimmune" />


      <div className="mt-12 flex flex-col gap-6">
        {/* ① 오늘의 활성도 (미작성 시 보라 테두리 강조) */}
        <Card className="p-5" style={hasActivity ? undefined : { borderColor: PURPLE }}>
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4" style={{ color: PURPLE }} />
            <h2 className="text-base font-bold">오늘의 활성도</h2>
          </div>
          <p className="mt-2 text-sm text-muted-foreground">
            {hasActivity
              ? "오늘 활성도 기록이 등록되어 있어요."
              : "아직 오늘 활성도를 기록하지 않았어요."}
          </p>
          <Link
            href="/activity/new"
            className="mt-4 block w-full rounded-xl py-3 text-center font-bold text-white"
            style={{ background: PURPLE }}
          >
            활성도 기록하기
          </Link>
        </Card>

        {/* ①-B 루푸스 기록 (SLE 환자만) */}
        {isLupus && (
          <Card className="p-5">
            <div className="flex items-center gap-2">
              <ClipboardList className="h-4 w-4" style={{ color: PURPLE }} />
              <h2 className="text-base font-bold">루푸스 기록</h2>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              햇빛 노출·수면·피부 증상 등 오늘의 루푸스 상태를 기록해요.
            </p>
            <Link
              href="/lupus"
              className="mt-4 block w-full rounded-xl py-3 text-center font-bold text-white"
              style={{ background: PURPLE }}
            >
              루푸스 기록하기
            </Link>
          </Card>
        )}

        {/* ② 의료진 확인 필요 신호 (v2) */}
        {riskCount > 0 ? (
          <Link
            href="/risk-flags"
            className="flex items-center justify-between rounded-2xl border-2 px-4 py-4"
            style={{ borderColor: "#F39C12", background: "#FEF9E7" }}
          >
            <span className="flex items-center gap-2 text-sm font-semibold">
              <AlertTriangle className="h-4 w-4" style={{ color: "#F39C12" }} />
              의료진 확인 필요 신호 {riskCount}건
            </span>
            <ArrowRight className="h-4 w-4 text-muted-foreground" />
          </Link>
        ) : (
          <div
            className="flex items-center gap-2 rounded-2xl border px-4 py-3.5"
            style={{ borderColor: "#F39C12", background: "#FEF9E7" }}
          >
            <AlertTriangle className="h-4 w-4" style={{ color: "#F39C12" }} />
            <span className="text-sm text-muted-foreground">
              현재 확인이 필요한 신호가 없어요.
            </span>
          </div>
        )}

        {/* ③ 오늘 복용약 (공통 컴포넌트 재사용) */}
        <MedicationCard medications={medications} accentClassName="text-[#7C5CCF]" />

        {/* ④ 다가오는 일정 */}
        <SectionCard title="다가오는 일정" moreHref="/schedule" accentClassName="text-[#7C5CCF]">
          <p className="text-sm text-muted-foreground">
            {hasSchedule ? "예정된 일정이 있어요." : "예정된 일정이 없어요."}
          </p>
        </SectionCard>

        {/* ⑤ 최신 맞춤 안내문 */}
        <SectionCard title="최신 맞춤 안내문" moreHref={latestGuideHref} accentClassName="text-[#7C5CCF]">
          <p className="text-sm text-muted-foreground">
            내 질환에 맞춘 안내문을 확인해 보세요.
          </p>
        </SectionCard>

        {/* SOS 버튼 + 응급카드 바로가기 */}
      <div className="mt-5 flex gap-3">
        <Link
          href="/emergency"
          className="flex flex-1 flex-col items-center gap-1 rounded-2xl py-5 text-white"
          style={{ background: RED }}
        >
          <Phone className="h-6 w-6" />
          <span className="mt-1 text-base font-bold">SOS</span>
          <span className="text-xs text-white/80">응급 도움 받기</span>
        </Link>
        <Link
          href="/emergency/card"
          className="flex flex-1 flex-col items-center gap-1 rounded-2xl border py-5"
          style={{ borderColor: RED + "55", background: RED + "0d" }}
        >
          <FileText className="h-6 w-6" style={{ color: RED }} />
          <span className="mt-1 text-sm font-bold" style={{ color: RED }}>응급카드</span>
          <span className="text-xs text-muted-foreground">정보 관리</span>
        </Link>
      </div>


        {/* ⑥ 빠른 진입점 (가로 스크롤) */}
        <section>
          <h2 className="mb-2 text-sm font-bold text-muted-foreground">빠른 진입점</h2>
          <div className="-mx-1 flex gap-3 overflow-x-auto px-1 pb-1">
            {QUICK_LINKS.map(({ href, label, Icon }) => (
              <Link
                key={href}
                href={href}
                className="flex min-w-[76px] shrink-0 flex-col items-center gap-2 rounded-2xl bg-muted/50 px-3 py-3"
              >
                <Icon className="h-5 w-5" style={{ color: PURPLE }} />
                <span className="text-center text-xs font-medium">{label}</span>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
