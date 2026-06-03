"use client";

import { useState } from "react";
import { Activity, User, Settings, Plus } from "lucide-react";
import { Card } from "@/components/ui/card";

interface Guardian {
  id: number;
  name: string;
  relation: string;
  scope: string;
  color: string;
}

const GUARDIANS: Guardian[] = [
  { id: 1, name: "김영희", relation: "어머니", scope: "전체 공개", color: "#7C5CCF" },
  { id: 2, name: "김철수", relation: "배우자", scope: "일부 공개", color: "#60A5FA" },
];

const SHARE_ITEMS = ["활성도 기록", "검사 결과", "복약 현황", "주의 증상 알림", "진료 일정"];

function Toggle({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      role="switch"
      aria-checked={on}
      onClick={() => onChange(!on)}
      className={"relative h-6 w-11 rounded-full transition-colors " + (on ? "bg-primary" : "bg-muted")}
    >
      <span className={"absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform " + (on ? "translate-x-5" : "translate-x-0.5")} />
    </button>
  );
}

export default function GuardianPage() {
  const [shares, setShares] = useState<boolean[]>([true, true, true, true, false]);

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8">
      <h1 className="text-2xl font-bold">보호자 공유</h1>

      {/* 배너 */}
      <div className="mt-5 flex items-center gap-3 rounded-2xl border border-primary/30 bg-secondary p-4">
        <Activity className="h-6 w-6 text-primary" />
        <div>
          <p className="font-bold">보호자와 건강정보 공유</p>
          <p className="text-sm text-secondary-foreground">가족이 내 상태를 함께 확인할 수 있어요</p>
        </div>
      </div>

      {/* 보호자 목록 */}
      <p className="mt-6 text-sm font-semibold">
        등록된 보호자 <span className="text-primary">{GUARDIANS.length}</span>
      </p>
      <div className="mt-2 space-y-3">
        {GUARDIANS.map((g) => (
          <Card key={g.id} className="flex items-center gap-3 p-4">
            <div className="flex h-11 w-11 items-center justify-center rounded-full" style={{ background: g.color + "22" }}>
              <User className="h-5 w-5" style={{ color: g.color }} />
            </div>
            <div className="flex-1">
              <p className="font-bold">{g.name}</p>
              <p className="text-xs text-muted-foreground">{g.relation} · {g.scope}</p>
            </div>
            <button aria-label="설정"><Settings className="h-5 w-5 text-muted-foreground" /></button>
          </Card>
        ))}
      </div>

      {/* 보호자 추가 */}
      <button className="mt-3 flex w-full items-center justify-center gap-1 rounded-2xl border-2 border-dashed border-primary py-4 text-sm font-semibold text-primary">
        <Plus className="h-4 w-4" /> 보호자 추가
      </button>

      {/* 공유 항목 설정 */}
      <p className="mt-6 text-sm font-semibold text-muted-foreground">공유 항목 설정</p>
      <Card className="mt-2 divide-y divide-border">
        {SHARE_ITEMS.map((label, i) => (
          <div key={label} className="flex items-center justify-between px-4 py-3.5">
            <span className="text-sm">{label}</span>
            <Toggle on={shares[i]} onChange={(v) => setShares((prev) => prev.map((x, j) => (j === i ? v : x)))} />
          </div>
        ))}
      </Card>

      <p className="mt-4 text-center text-xs text-muted-foreground">
        보호자는 정보 열람만 가능하며<br />회원님의 데이터를 수정할 수 없습니다
      </p>
    </main>
  );
}
