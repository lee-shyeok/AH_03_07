"use client";

import { useState } from "react";
import { FileText, User, Settings, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const RED = "#EF5B5B";

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

export default function EmergencyCardPage() {
  const [lockScreen, setLockScreen] = useState(true);
  const [sendLocation, setSendLocation] = useState(true);

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8 pb-28">
      <h1 className="text-xl font-bold">응급 카드 설정</h1>

      {/* 배너 */}
      <div className="mt-4 flex items-center gap-3 rounded-2xl border p-4" style={{ borderColor: RED + "55", background: RED + "12" }}>
        <FileText className="h-6 w-6" style={{ color: RED }} />
        <div>
          <p className="font-bold" style={{ color: RED }}>응급 카드 정보 관리</p>
          <p className="text-sm" style={{ color: RED }}>응급 시 구급대원에게 표시될 정보입니다</p>
        </div>
      </div>

      {/* 기본 의료정보 */}
      <p className="mt-6 text-sm text-muted-foreground">기본 의료정보</p>
      <Card className="mt-2 divide-y divide-border">
        <div className="flex items-center justify-between px-4 py-3">
          <div>
            <p className="text-xs text-muted-foreground">혈액형</p>
            <p className="font-semibold">A형 Rh+</p>
          </div>
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        </div>
        {[["기저 질환", "류마티스 관절염"], ["복용 약물", "메토트렉세이트 7.5mg"], ["알레르기", "페니실린"]].map(([l, v]) => (
          <div key={l} className="px-4 py-3">
            <p className="text-xs text-muted-foreground">{l}</p>
            <p className="font-semibold">{v}</p>
          </div>
        ))}
      </Card>

      {/* 긴급 연락처 */}
      <p className="mt-6 text-sm text-muted-foreground">긴급 연락처</p>
      <Card className="mt-2 flex items-center gap-3 p-4">
        <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#F0E8FF]">
          <User className="h-5 w-5 text-[#7C5CCF]" />
        </div>
        <div className="flex-1">
          <p className="font-bold">김영희</p>
          <p className="text-xs text-muted-foreground">어머니 010-1234-5678</p>
        </div>
        <Settings className="h-5 w-5 text-muted-foreground" />
      </Card>
      <button className="mt-3 w-full rounded-2xl border-2 border-dashed py-4 text-sm font-semibold" style={{ borderColor: RED + "66", color: RED }}>
        + 보호자 추가
      </button>

      {/* 표시 설정 */}
      <p className="mt-6 text-sm text-muted-foreground">표시 설정</p>
      <Card className="mt-2 divide-y divide-border">
        <div className="flex items-center justify-between px-4 py-3.5">
          <div>
            <p className="text-sm">잠금화면에 표시</p>
            <p className="text-xs text-muted-foreground">잠금 상태에서도 응급 카드 접근</p>
          </div>
          <Toggle on={lockScreen} onChange={setLockScreen} />
        </div>
        <div className="flex items-center justify-between px-4 py-3.5">
          <div>
            <p className="text-sm">위치정보 함께 전송</p>
            <p className="text-xs text-muted-foreground">119 신고 시 현재 위치 자동 전송</p>
          </div>
          <Toggle on={sendLocation} onChange={setSendLocation} />
        </div>
      </Card>

      <div className="fixed inset-x-0 bottom-16 mx-auto max-w-md px-5">
        <Button className="w-full" size="lg">저장하기</Button>
      </div>
    </main>
  );
}
