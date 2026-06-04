"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Check, Circle, AlertTriangle, ClipboardCheck } from "lucide-react";
import { Card } from "@/components/ui/card";
import { getDashboard } from "@/features/dashboard/api";
import { getMe } from "@/features/auth/api";
import { getMode } from "@/features/auth/mode";
import type { DashboardData } from "@/features/dashboard/api";

const PURPLE = "#7C5CCF";
const ACTIVITY = [
  { label: "통증", value: 5 },
  { label: "피로", value: 6 },
  { label: "강직", value: 4 },
  { label: "불편도", value: 7 },
];

export default function HomePage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [name, setName] = useState<string>("");
  const [userType, setUserType] = useState<"general" | "autoimmune">("general");

  useEffect(() => {
    // 로컬에 저장된 모드 선택을 우선 반영 (백엔드 없이도 동작)
    setUserType(getMode());
    getMe()
      .then((u) => {
        setName(u.name);
        if (u.user_type) setUserType(u.user_type);
      })
      .catch(() => {});
    getDashboard()
      .then((d) => {
        setData(d);
        if (d.user_type) setUserType(d.user_type);
      })
      .catch(() => setData(fallback));
  }, []);

  const meds = data?.medications ?? fallback.medications!;
  const tips = data?.health_tips ?? fallback.health_tips!;
  const isAuto = userType === "autoimmune";

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-10">
      {/* 인사말 */}
      <h1 className="text-3xl font-bold leading-tight">
        안녕하세요!
        <br />
        {name || data?.user_name || "OOO"}님{" "}
        {!isAuto && (
          <span className="text-base font-semibold text-primary">일반 환자</span>
        )}
      </h1>

      {/* 자가면역: 오늘의 활성도 */}
      {isAuto && (
        <Card className="mt-6 p-5">
          <h2 className="text-base font-bold">오늘의 활성도</h2>
          <p className="mt-1 text-3xl font-extrabold" style={{ color: PURPLE }}>
            5.5 <span className="text-base font-normal text-muted-foreground">/ 10</span>
          </p>
          <div className="mt-3 grid grid-cols-2 gap-2.5">
            {ACTIVITY.map((a) => (
              <div key={a.label} className="rounded-xl bg-muted/60 px-4 py-3">
                <span className="text-xs text-muted-foreground">{a.label} </span>
                <span className="font-bold">{a.value}</span>
              </div>
            ))}
          </div>
          <Link
            href="/activity/new"
            className="mt-4 block w-full rounded-xl py-3 text-center font-bold text-white"
            style={{ background: PURPLE }}
          >
            활성도 기록하기
          </Link>
        </Card>
      )}

      {/* 오늘 복약 */}
      <Card className="mt-6 p-5">
        <h2 className="text-base font-bold">오늘 복약</h2>
        <ul className="mt-3 space-y-2">
          {meds.map((m, i) => (
            <li key={i} className="flex items-center gap-2.5 text-sm">
              {m.done ? (
                <Check className="h-4 w-4 text-primary" />
              ) : (
                <Circle className="h-4 w-4 text-muted-foreground/40" />
              )}
              <span className={m.done ? "text-foreground" : "text-muted-foreground"}>
                {m.label}
              </span>
            </li>
          ))}
        </ul>
        <Link
          href="/medication/checklist"
          className="mt-3 flex items-center justify-end gap-1 text-sm text-primary"
        >
          전체 보기 <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </Card>

      {/* 일반: 건강 팁 / 자가면역: 위험신호 배너 */}
      {isAuto ? (
        <div className="mt-4 space-y-2">
          <Link
            href="/risk-flags"
            className="flex items-center justify-between rounded-2xl border-2 px-4 py-3.5"
            style={{ borderColor: "#F5C518", background: "#FEF9E7" }}
          >
            <span className="flex items-center gap-2 text-sm font-semibold">
              <AlertTriangle className="h-4 w-4" style={{ color: "#B7950B" }} />
              의료진 확인 필요 신호 1건
            </span>
            <ArrowRight className="h-4 w-4 text-muted-foreground" />
          </Link>
          <Link href="/symptom-check" className="flex items-center justify-between rounded-2xl border border-border bg-card px-4 py-3.5">
            <span className="flex items-center gap-2 text-sm font-semibold">
              <ClipboardCheck className="h-4 w-4 text-destructive" />
              주의 증상 체크하기
            </span>
            <ArrowRight className="h-4 w-4 text-muted-foreground" />
          </Link>
        </div>
      ) : (
        <Card className="mt-4 p-5">
          <h2 className="text-base font-bold">오늘의 건강 팁</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {tips.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
          <Link
            href="/guides"
            className="mt-3 flex items-center justify-end gap-1 text-sm text-primary"
          >
            전체 보기 <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </Card>
      )}
    </main>
  );
}

const fallback: DashboardData = {
  user_type: "general",
  medications: [
    { label: "아침약 (오전 9시)", done: true },
    { label: "점심약 (오후 1시)", done: false },
    { label: "저녁약 (오후 7시)", done: false },
  ],
  health_tips: ["💧 수분 충분히 섭취하기", "🚶 30분 가벼운 산책", "😴 7시간 이상 수면"],
};
