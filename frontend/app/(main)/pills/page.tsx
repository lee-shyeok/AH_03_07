"use client";

import { useState } from "react";
import Link from "next/link";
import { Camera, Pill, Search } from "lucide-react";
import { Card } from "@/components/ui/card";

interface Candidate {
  name: string;
  ingredient: string;
  category: string;
  confidence: number;
}

const CANDIDATES: Candidate[] = [
  { name: "타이레놀 500mg", ingredient: "아세트아미노펜", category: "해열진통제", confidence: 98 },
  { name: "게보린", ingredient: "아세트아미노펜 복합", category: "진통제", confidence: 85 },
  { name: "펜잘큐", ingredient: "아세트아미노펜 복합", category: "진통제", confidence: 72 },
];

export default function PillsRecognizePage() {
  const [recognized, setRecognized] = useState(false);

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8">
      <h1 className="text-2xl font-bold">약품 카메라 인식</h1>

      {/* 안내 배너 */}
      <div className="mt-5 flex items-center gap-3 rounded-2xl border border-primary/40 bg-secondary p-4">
        <Camera className="h-6 w-6 text-primary" />
        <div>
          <p className="font-bold">약품을 촬영해주세요</p>
          <p className="text-sm text-secondary-foreground">인식 후보 중 직접 선택하세요</p>
        </div>
      </div>

      {/* 카메라 프레임 */}
      <div className="mt-5 flex h-64 flex-col items-center justify-center rounded-2xl bg-[#2A2D34]">
        <div className="flex h-28 w-44 items-center justify-center rounded-xl border-2 border-dashed border-white/40">
          <Pill className="h-12 w-12 text-white/50" />
        </div>
        <p className="mt-5 text-sm text-white/70">알약을 가이드 안에 맞춰주세요</p>
      </div>

      {/* 카메라 버튼 */}
      <div className="mt-4 flex justify-center">
        <button
          onClick={() => setRecognized(true)}
          className="flex h-16 w-16 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg shadow-primary/40"
          aria-label="촬영"
        >
          <Camera className="h-7 w-7" />
        </button>
      </div>

      {/* 인식 결과 */}
      {recognized && (
        <>
          <p className="mt-7 text-sm font-semibold text-muted-foreground">인식 결과(후보)</p>
          <div className="mt-2 space-y-3">
            {CANDIDATES.map((c) => {
              const high = c.confidence >= 90;
              return (
                <Card key={c.name} className="flex items-center gap-3 p-4">
                  <div className={"flex h-12 w-12 items-center justify-center rounded-xl " + (high ? "bg-secondary" : "bg-muted")}>
                    <Pill className={"h-6 w-6 " + (high ? "text-primary" : "text-muted-foreground")} />
                  </div>
                  <div className="flex-1">
                    <p className="font-bold">{c.name}</p>
                    <p className="text-sm text-muted-foreground">{c.ingredient} · {c.category}</p>
                  </div>
                  <span
                    className={
                      "rounded-full px-2.5 py-1 text-xs font-bold " +
                      (high ? "bg-secondary text-primary" : "bg-amber-50 text-amber-700")
                    }
                  >
                    {c.confidence}%
                  </span>
                </Card>
              );
            })}
          </div>

          <Link href="/search" className="mt-3 flex items-center justify-center gap-2 rounded-2xl border border-border py-4 text-sm text-muted-foreground">
            <Search className="h-4 w-4" /> 찾는 약품이 없어요 · 직접 검색
          </Link>

          <p className="mt-4 text-center text-xs text-muted-foreground">
            AI 인식 결과는 참고용입니다<br />정확한 약품은 직접 확인 후 선택하세요
          </p>
        </>
      )}

      {!recognized && (
        <div className="mt-6 text-center">
          <Link href="/pills/history" className="text-sm text-primary hover:underline">
            인식 내역 보기
          </Link>
        </div>
      )}
    </main>
  );
}
