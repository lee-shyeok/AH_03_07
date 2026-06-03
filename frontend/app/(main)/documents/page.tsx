"use client";

import { useState } from "react";
import Link from "next/link";
import { Search, FileText, FlaskConical, Pill } from "lucide-react";
import { Card } from "@/components/ui/card";

type Filter = "전체" | "진료기록" | "검사결과" | "처방전";
const FILTERS: Filter[] = ["전체", "진료기록", "검사결과", "처방전"];

interface Doc {
  type: Exclude<Filter, "전체">;
  title: string;
  detail: string;
  date: string;
  month: string;
}

const DOCS: Doc[] = [
  { type: "진료기록", title: "진료기록", detail: "서울대학교병원 내과 · 위염", date: "2026.5.20", month: "2026년 5월" },
  { type: "검사결과", title: "검사결과", detail: "서울대병원 류마티스 · CRP, ESR", date: "2026.5.12", month: "2026년 5월" },
  { type: "처방전", title: "처방전", detail: "서울가정의학과 · 아세트아미노펜", date: "2026.04.25", month: "2026년 4월" },
  { type: "진료기록", title: "진료기록", detail: "서울대병원 류마티스 · 류마티스 관절염", date: "2026.04.10", month: "2026년 4월" },
];

const ICONS = { 진료기록: FileText, 검사결과: FlaskConical, 처방전: Pill };
const ICON_BG = { 진료기록: "bg-secondary text-primary", 검사결과: "bg-[#F0E8FF] text-[#7C5CCF]", 처방전: "bg-secondary text-primary" };

export default function DocumentsPage() {
  const [filter, setFilter] = useState<Filter>("전체");

  const filtered = DOCS.filter((d) => filter === "전체" || d.type === filter);
  const months = Array.from(new Set(filtered.map((d) => d.month)));

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">의료문서</h1>
        <Link href="/search" aria-label="검색"><Search className="h-6 w-6" /></Link>
      </div>

      {/* 필터 */}
      <div className="mt-4 flex gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={"rounded-full px-4 py-2 text-sm font-semibold " + (filter === f ? "bg-primary text-primary-foreground" : "border border-border")}
          >
            {f}
          </button>
        ))}
      </div>

      {/* 월별 그룹 */}
      <div className="mt-6 space-y-6 pb-6">
        {months.map((month) => (
          <div key={month}>
            <p className="text-sm font-bold text-muted-foreground">{month}</p>
            <div className="mt-2 space-y-3">
              {filtered.filter((d) => d.month === month).map((d, i) => {
                const Icon = ICONS[d.type];
                return (
                  <Card key={i} className="flex items-center gap-3 p-4">
                    <div className={"flex h-12 w-12 items-center justify-center rounded-xl " + ICON_BG[d.type]}>
                      <Icon className="h-6 w-6" />
                    </div>
                    <div className="flex-1">
                      <p className="font-bold">{d.title}</p>
                      <p className="text-xs text-muted-foreground">{d.detail}</p>
                    </div>
                    <span className="text-xs text-muted-foreground">{d.date}</span>
                  </Card>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
