import Link from "next/link";
import { AlertTriangle, ArrowRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import HomeHeader from "./components/HomeHeader";
import MedicationCard, { type Medication } from "./components/MedicationCard";

const PURPLE = "#7C5CCF";

// TODO(데이터): 활성도 점수/지표 — REQ-ACTV 연동 전 placeholder
const ACTIVITY = [
  { label: "통증", value: 5 },
  { label: "피로", value: 6 },
  { label: "강직", value: 4 },
  { label: "불편도", value: 7 },
];

interface AutoimmuneHomeProps {
  name: string;
  medications: Medication[];
}

export default function AutoimmuneHome({ name, medications }: AutoimmuneHomeProps) {
  return (
    <main className="mx-auto w-full max-w-md px-5 pb-24 pt-10">
      <HomeHeader name={name} mode="autoimmune" />

      {/* 오늘의 활성도 */}
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

      {/* 오늘 복약 (공통 컴포넌트 재사용) */}
      <div className="mt-6">
        <MedicationCard medications={medications} accentClassName="text-[#7C5CCF]" />
      </div>

      {/* 위험신호 배너 */}
      <Link
        href="/risk-flags"
        className="mt-4 flex items-center justify-between rounded-2xl border-2 px-4 py-3.5"
        style={{ borderColor: "#F5C518", background: "#FEF9E7" }}
      >
        <span className="flex items-center gap-2 text-sm font-semibold">
          <AlertTriangle className="h-4 w-4" style={{ color: "#B7950B" }} />
          의료진 확인 필요 신호 1건
        </span>
        <ArrowRight className="h-4 w-4 text-muted-foreground" />
      </Link>
    </main>
  );
}