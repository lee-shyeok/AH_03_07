"use client";

import { Phone, User, Stethoscope, AlertTriangle } from "lucide-react";
import { Card } from "@/components/ui/card";

const RED = "#EF5B5B";

const INFO = [
  { label: "혈액형", value: "A형 Rh+", danger: false },
  { label: "기저 질환", value: "류마티스 관절염", danger: false },
  { label: "복용 약물", value: "메토트렉세이트", danger: false },
  { label: "알레르기", value: "페니실린", danger: true },
];

export default function EmergencyPage() {
  return (
    <main className="mx-auto w-full max-w-md px-5 py-8">
      <h1 className="text-2xl font-bold">응급 SOS</h1>

      {/* 119 전화 */}
      <a
        href="tel:119"
        className="mt-6 flex flex-col items-center gap-1 rounded-2xl py-8 text-white"
        style={{ background: RED }}
      >
        <Phone className="h-9 w-9" />
        <span className="mt-2 text-2xl font-bold">119 전화하기</span>
        <span className="text-sm text-white/80">길게 눌러 바로 연결</span>
      </a>

      {/* 응급 의료정보 */}
      <p className="mt-7 text-sm text-muted-foreground">내 응급 의료정보</p>
      <Card className="mt-2 divide-y divide-border">
        {INFO.map((it) => (
          <div key={it.label} className="flex items-center justify-between px-4 py-3.5">
            <span className="text-sm text-muted-foreground">{it.label}</span>
            <span className={"font-bold " + (it.danger ? "text-destructive" : "")}>{it.value}</span>
          </div>
        ))}
      </Card>

      {/* 긴급 연락처 */}
      <p className="mt-7 text-sm text-muted-foreground">긴급 연락처</p>
      <div className="mt-2 space-y-3">
        <Card className="flex items-center gap-3 p-4">
          <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#F0E8FF]">
            <User className="h-5 w-5 text-[#7C5CCF]" />
          </div>
          <div className="flex-1">
            <p className="font-bold">김영희</p>
            <p className="text-xs text-muted-foreground">어머니</p>
          </div>
          <a href="tel:01012345678" aria-label="전화"><Phone className="h-5 w-5 text-primary" /></a>
        </Card>
        <Card className="flex items-center gap-3 p-4">
          <div className="flex h-11 w-11 items-center justify-center rounded-full bg-secondary">
            <Stethoscope className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1">
            <p className="font-bold">서울대병원 류마티스내과</p>
            <p className="text-xs text-muted-foreground">담당 의료진</p>
          </div>
          <a href="tel:020000000" aria-label="전화"><Phone className="h-5 w-5 text-primary" /></a>
        </Card>
      </div>

      {/* 안내 */}
      <div className="mt-6 flex items-center gap-2 rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm font-semibold text-destructive">
        <AlertTriangle className="h-5 w-5 shrink-0" />
        의식이 없을 때 이 화면을 구급대원에게 보여주세요
      </div>
    </main>
  );
}
