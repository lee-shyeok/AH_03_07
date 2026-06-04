"use client";

import { useState } from "react";
import { Pill, Link as LinkIcon, ArrowRight } from "lucide-react";
import { Card } from "@/components/ui/card";

const PURPLE = "#7C5CCF";
const TABS = ["복약", "생활습관", "주의사항", "자가면역"] as const;
type Tab = (typeof TABS)[number];

export default function MedicationDetailPage() {
  const [tab, setTab] = useState<Tab>("자가면역");

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-8">
      {/* 헤더 */}
      <h1 className="text-3xl font-extrabold">메토트렉세이트</h1>
      <p className="mt-1 text-muted-foreground">Methotrexate</p>
      <span className="mt-3 inline-block rounded-full px-3 py-1 text-xs font-bold text-white" style={{ background: PURPLE }}>
        자가면역
      </span>
      <p className="mt-2 flex items-center gap-1.5 text-sm text-muted-foreground">
        <Pill className="h-4 w-4" /> 매주 1회 복용
      </p>
      <a
        href={`https://nedrug.mfds.go.kr/searchDrug?searchYn=true&itemName=메토트렉세이트`}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-3 flex items-center gap-1.5 rounded-xl border border-border px-4 py-2.5 text-sm font-semibold text-primary hover:bg-accent"
      >
        <LinkIcon className="h-4 w-4" />
        공식 정보 보기 (식약처 의약품안전나라)
        <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground" />
      </a>

      {/* 탭 */}
      <div className="mt-6 flex border-b border-border">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={"flex-1 pb-3 text-sm font-semibold " + (tab === t ? "" : "text-muted-foreground")}
            style={tab === t ? { color: PURPLE, borderBottom: `2px solid ${PURPLE}` } : undefined}
          >
            {t}
          </button>
        ))}
      </div>

      {/* 콘텐츠 */}
      <div className="mt-6 space-y-6 pb-6">
        {tab === "자가면역" && (
          <>
            <section>
              <h2 className="text-lg font-bold">➕ 면역억제 효과</h2>
              <p className="mt-2 leading-7 text-foreground">
                메토트렉세이트는<br />면역억제 작용이 있어<br />감염 위험이 증가할 수 있어요.
              </p>
            </section>
            <section>
              <h2 className="text-lg font-bold">🦠 감염 주의</h2>
              <ul className="mt-2 space-y-1 text-foreground">
                <li>• 발열 시 즉시 의료진 상담</li>
                <li>• 생백신 접종 금지</li>
                <li>• 손씻기 등 위생 관리 강화</li>
              </ul>
            </section>
            {/* 출처 */}
            <Card className="p-4">
              <p className="text-sm">📚 출처</p>
              <p className="mt-1 font-bold">대한류마티스학회 진료 가이드라인</p>
              <p className="text-sm text-muted-foreground">대한류마티스학회</p>
              <p className="text-sm text-muted-foreground">업데이트: 2026.05.15</p>
              <button className="mt-2 flex items-center gap-1 text-sm" style={{ color: "#3B82F6" }}>
                <LinkIcon className="h-3.5 w-3.5" /> 원문 보기 <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </Card>
          </>
        )}
        {tab === "복약" && (
          <section>
            <h2 className="text-lg font-bold">복약 방법</h2>
            <p className="mt-2 leading-7 text-muted-foreground">매주 같은 요일에 1회 복용하세요. 정해진 용량을 지키는 것이 중요합니다.</p>
          </section>
        )}
        {tab === "생활습관" && (
          <section>
            <h2 className="text-lg font-bold">생활 습관</h2>
            <ul className="mt-2 space-y-1 text-muted-foreground">
              <li>• 충분한 수분 섭취</li>
              <li>• 음주 자제 (간 부담)</li>
              <li>• 규칙적인 수면</li>
            </ul>
          </section>
        )}
        {tab === "주의사항" && (
          <section>
            <h2 className="text-lg font-bold">주의사항</h2>
            <ul className="mt-2 space-y-1 text-muted-foreground">
              <li>• 임신 계획 시 반드시 의료진 상담</li>
              <li>• 정기 혈액검사 필수</li>
              <li>• 다른 약과 병용 시 확인</li>
            </ul>
          </section>
        )}
      </div>
    </main>
  );
}
