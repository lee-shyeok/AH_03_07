"use client";

import { useState } from "react";

interface Flag {
  id: number;
  reason: string;
  recommend: string;
  source: string;
  resolved: boolean;
}

const INITIAL: Flag[] = [
  { id: 1, reason: "통증 점수가 5점 이상으로\n7일 동안 지속되었습니다.", recommend: "담당 의료진 상담을 권고드립니다.", source: "자가면역 진료 가이드라인", resolved: false },
  { id: 2, reason: "피로 점수가 8점 이상으로\n3일 연속 기록되었습니다.", recommend: "담당 의료진 상담을 권고드립니다.", source: "자가면역 진료 가이드라인", resolved: false },
  { id: 3, reason: "강직 점수가 일시적으로\n상승했습니다", recommend: "담당 의료진 상담을 권고드립니다.", source: "자가면역 진료 가이드라인", resolved: true },
];

export default function RiskFlagsPage() {
  const [flags, setFlags] = useState<Flag[]>(INITIAL);

  const active = flags.filter((f) => !f.resolved);
  const resolved = flags.filter((f) => f.resolved);

  function resolve(id: number) {
    setFlags((prev) => prev.map((f) => (f.id === id ? { ...f, resolved: true } : f)));
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-8">
      <h1 className="text-3xl font-extrabold leading-tight">의료진 확인이<br />필요한 신호</h1>
      <p className="mt-2 text-sm text-muted-foreground">최근 데이터에서 주의가 필요한<br />패턴을 감지했어요</p>

      {/* 활성 신호 */}
      <p className="mt-7 font-bold">활성 신호 {active.length}건</p>
      <div className="mt-2 space-y-3">
        {active.map((f) => (
          <div key={f.id} className="rounded-2xl border-2 p-5 text-center" style={{ borderColor: "#F5C518", background: "#FEF9E7" }}>
            <p className="font-bold">⚠️ 의료진 확인 필요 신호</p>
            <p className="mt-2 whitespace-pre-line font-medium">{f.reason}</p>
            <p className="mt-3 text-sm">💡 {f.recommend}</p>
            <p className="mt-2 text-xs text-muted-foreground">📚 출처: {f.source}</p>
            <button onClick={() => resolve(f.id)} className="mt-4 w-full rounded-xl bg-white py-3 font-bold shadow-sm">
              해소
            </button>
          </div>
        ))}
        {active.length === 0 && <p className="text-sm text-muted-foreground">활성 신호가 없습니다.</p>}
      </div>

      {/* 해소된 신호 */}
      {resolved.length > 0 && (
        <>
          <p className="mt-7 font-bold">해소된 신호 {resolved.length}건</p>
          <div className="mt-2 space-y-3 pb-6">
            {resolved.map((f) => (
              <div key={f.id} className="rounded-2xl border border-border bg-muted/40 p-5 text-center text-muted-foreground">
                <p className="font-bold">⚠️ 의료진 확인 필요 신호 ✓</p>
                <p className="mt-2 whitespace-pre-line">{f.reason}</p>
                <p className="mt-3 text-sm">💡 {f.recommend}</p>
                <p className="mt-2 text-xs">📚 출처: {f.source}</p>
                <div className="mt-4 w-full rounded-xl bg-muted py-3 font-bold">해소됨</div>
              </div>
            ))}
          </div>
        </>
      )}
    </main>
  );
}
