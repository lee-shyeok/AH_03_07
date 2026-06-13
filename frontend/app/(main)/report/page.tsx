"use client";

import { FileText, Download, Share2 } from "lucide-react";
import { Card } from "@/components/ui/card";

const PURPLE = "#7C5CCF";
const BARS: number[] = [];
const LABS: { name: string; value: string; high: boolean }[] = [];
const SYMPTOMS: { name: string; date: string }[] = [];

export default function ReportPage() {
  return (
    <main className="mx-auto w-full max-w-md px-5 py-8 pb-28">
      <h1 className="text-xl font-bold">진료 전 요약</h1>

      {/* 배너 */}
      <div className="mt-4 flex items-center gap-3 rounded-2xl border p-4" style={{ borderColor: PURPLE + "44", background: PURPLE + "12" }}>
        <FileText className="h-6 w-6" style={{ color: PURPLE }} />
        <div>
          <p className="font-bold">진료 전 요약 리포트</p>
          <p className="text-sm" style={{ color: PURPLE }}>의료진에게 보여주세요</p>
        </div>
      </div>

      {/* 리포트 헤더 */}
      <div className="mt-4 rounded-2xl p-5 text-center text-white" style={{ background: PURPLE }}>
        <p className="text-lg font-bold">MediGuide 요약 리포트</p>
        <p className="mt-1 text-sm text-white/85">2026.04.20 ~ 05.20 (4주간)</p>
        <p className="text-sm text-white/85">자가면역 모드 · 류마티스 관절염</p>
      </div>

      {/* 활성도 추이 */}
      <p className="mt-6 text-sm font-bold text-muted-foreground">활성도 추이</p>
      <Card className="mt-2 p-5">
        {BARS.length === 0 ? (
          <p className="py-4 text-center text-sm text-muted-foreground">데이터가 없습니다.</p>
        ) : (
          <>
            <div className="flex items-end justify-between">
              <p className="text-3xl font-extrabold" style={{ color: PURPLE }}>
                - <span className="text-base font-normal text-muted-foreground">/ 10 평균</span>
              </p>
            </div>
            <div className="mt-4 flex h-28 items-end justify-between gap-2">
              {BARS.map((v, i) => (
                <div
                  key={i}
                  className="flex-1 rounded-t-md"
                  style={{ height: `${v * 10}%`, background: i % 2 ? PURPLE : PURPLE + "55" }}
                />
              ))}
            </div>
          </>
        )}
      </Card>

      {/* 검사 결과 */}
      <p className="mt-6 text-sm font-bold text-muted-foreground">검사 결과</p>
      <Card className="mt-2 divide-y divide-border">
        {LABS.length === 0 ? (
          <p className="px-4 py-4 text-center text-sm text-muted-foreground">데이터가 없습니다.</p>
        ) : (
          LABS.map((l) => (
            <div key={l.name} className="flex items-center justify-between px-4 py-3.5">
              <span>{l.name}</span>
              <span className={"font-bold " + (l.high ? "text-destructive" : "text-primary")}>
                {l.value} {l.high ? "↑" : ""}
              </span>
            </div>
          ))
        )}
      </Card>

      {/* 복약 현황 */}
      <p className="mt-6 text-sm font-bold text-muted-foreground">복약 현황</p>
      <Card className="mt-2 p-4">
        <p className="text-center text-sm text-muted-foreground">데이터가 없습니다.</p>
      </Card>

      {/* 주의 증상 */}
      <p className="mt-6 text-sm font-bold text-muted-foreground">주의 증상 기록</p>
      <Card className="mt-2 divide-y divide-border">
        {SYMPTOMS.length === 0 ? (
          <p className="px-4 py-4 text-center text-sm text-muted-foreground">데이터가 없습니다.</p>
        ) : (
          SYMPTOMS.map((s) => (
            <div key={s.name} className="flex items-center justify-between px-4 py-3.5">
              <span>{s.name}</span>
              <span className="text-xs text-muted-foreground">{s.date}</span>
            </div>
          ))
        )}
      </Card>

      {/* 버튼 */}
      <div className="fixed inset-x-0 bottom-16 mx-auto flex max-w-md gap-2 px-5">
        <button className="flex flex-1 items-center justify-center gap-1.5 rounded-xl border-2 py-3.5 font-bold" style={{ borderColor: PURPLE, color: PURPLE }}>
          <Download className="h-4 w-4" /> PDF 저장
        </button>
        <button className="flex flex-1 items-center justify-center gap-1.5 rounded-xl py-3.5 font-bold text-white" style={{ background: PURPLE }}>
          <Share2 className="h-4 w-4" /> 공유하기
        </button>
      </div>
    </main>
  );
}
