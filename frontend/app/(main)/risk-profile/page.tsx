"use client";

import { useState } from "react";
import { ShieldCheck, Check } from "lucide-react";

const PURPLE = "#7C5CCF";

function Chip({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="rounded-full px-4 py-2 text-sm font-semibold transition-colors"
      style={active ? { background: PURPLE, color: "#fff" } : { border: "1px solid hsl(var(--border))" }}
    >
      {label}
    </button>
  );
}

function CheckItem({ label, checked, onClick }: { label: string; checked: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm">
      <span
        className="flex h-5 w-5 items-center justify-center rounded"
        style={checked ? { background: PURPLE } : { border: "2px solid hsl(var(--border))" }}
      >
        {checked && <Check className="h-3.5 w-3.5 text-white" />}
      </span>
      {label}
    </button>
  );
}

export default function RiskProfilePage() {
  const [pregnancy, setPregnancy] = useState("해당없음");
  const [kidney, setKidney] = useState("없음");
  const [liver, setLiver] = useState("없음");
  const [infections, setInfections] = useState<string[]>(["결핵(TB)"]);
  const [allergy, setAllergy] = useState("페니실린, 아스피린");
  const [comorbid, setComorbid] = useState<string[]>(["갑상선 질환"]);

  function toggle(list: string[], setList: (v: string[]) => void, item: string) {
    setList(list.includes(item) ? list.filter((x) => x !== item) : [...list, item]);
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8 pb-28">
      <h1 className="text-xl font-bold">위험요인 프로필</h1>

      {/* 배너 */}
      <div className="mt-4 flex items-center gap-3 rounded-2xl p-4" style={{ background: PURPLE + "15" }}>
        <ShieldCheck className="h-5 w-5" style={{ color: PURPLE }} />
        <p className="text-sm" style={{ color: PURPLE }}>안전한 의료 관리를 위해<br />정확한 정보를 입력해주세요</p>
      </div>

      {/* 임신 관련 */}
      <p className="mt-6 font-bold">임신 관련 정보 <span className="text-destructive">*</span></p>
      <div className="mt-2 rounded-2xl border border-border p-4">
        <p className="text-sm text-muted-foreground">임신·수유 상태</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {["임신중", "수유중", "임신계획", "해당없음"].map((o) => (
            <Chip key={o} label={o} active={pregnancy === o} onClick={() => setPregnancy(o)} />
          ))}
        </div>
      </div>

      {/* 장기 기능 */}
      <p className="mt-6 font-bold">장기 기능</p>
      <div className="mt-2 space-y-4 rounded-2xl border border-border p-4">
        {[["신장 기능 이상", kidney, setKidney], ["간 기능 이상", liver, setLiver]].map(([label, val, set]) => (
          <div key={label as string}>
            <p className="text-sm text-muted-foreground">{label as string}</p>
            <div className="mt-2 flex gap-2">
              {["있음", "없음", "모름"].map((o) => (
                <Chip key={o} label={o} active={val === o} onClick={() => (set as (v: string) => void)(o)} />
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* 감염 이력 */}
      <p className="mt-6 font-bold">감염 이력 <span className="text-sm font-normal text-muted-foreground">(다중 선택)</span></p>
      <div className="mt-2 divide-y divide-border rounded-2xl border border-border">
        {["결핵(TB)", "B형 간염", "대상포진", "코로나19", "해당없음"].map((o) => (
          <CheckItem key={o} label={o} checked={infections.includes(o)} onClick={() => toggle(infections, setInfections, o)} />
        ))}
      </div>

      {/* 약물 알레르기 */}
      <p className="mt-6 font-bold">약물 알레르기</p>
      <textarea
        value={allergy}
        onChange={(e) => setAllergy(e.target.value)}
        rows={2}
        className="mt-2 w-full rounded-2xl border border-border px-4 py-3 text-sm"
      />

      {/* 동반 질환 */}
      <p className="mt-6 font-bold">동반 질환 <span className="text-sm font-normal text-muted-foreground">(다중 선택)</span></p>
      <div className="mt-2 divide-y divide-border rounded-2xl border border-border">
        {["당뇨", "고혈압", "갑상선 질환", "심혈관 질환", "해당없음"].map((o) => (
          <CheckItem key={o} label={o} checked={comorbid.includes(o)} onClick={() => toggle(comorbid, setComorbid, o)} />
        ))}
      </div>

      <div className="fixed inset-x-0 bottom-16 mx-auto max-w-md px-5">
        <button className="w-full rounded-xl py-3.5 text-base font-bold text-white" style={{ background: PURPLE }}>
          저장하기
        </button>
      </div>
    </main>
  );
}
