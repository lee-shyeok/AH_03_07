"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Phone, User, Stethoscope, AlertTriangle, ArrowLeft, Info } from "lucide-react";
import { Card } from "@/components/ui/card";
import { getEmergencyCard, type EmergencyCard } from "@/features/emergency/api";

const RED = "#EF5B5B";

const MOCK_CARD: EmergencyCard = {
  blood_type: "A형 Rh+",
  conditions: "류마티스 관절염",
  medications: "메토트렉세이트",
  allergies: "페니실린",
  emergency_contacts: [
    { name: "김영희", relationship: "어머니", phone: "01012345678" },
    { name: "서울대병원 류마티스내과", relationship: "담당 의료진", phone: "020000000", is_doctor: true },
  ],
  show_on_lock_screen: true,
  send_location: true,
};

export default function EmergencyPage() {
  const router = useRouter();
  const [card, setCard] = useState<EmergencyCard>(MOCK_CARD);

  useEffect(() => {
    getEmergencyCard()
      .then((data) => setCard(data))
      .catch(() => setCard(MOCK_CARD));
  }, []);

  const info = [
    { label: "혈액형", value: card.blood_type ?? "—", danger: false },
    { label: "기저 질환", value: card.conditions ?? "—", danger: false },
    { label: "복용 약물", value: card.medications ?? "—", danger: false },
    { label: "알레르기", value: card.allergies ?? "—", danger: true },
  ];

  const contacts = card.emergency_contacts ?? [];

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8">
      {/* 뒤로가기 */}
      <button
        onClick={() => router.push("/home")}
        className="mb-4 flex items-center gap-1 text-sm text-muted-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        홈으로
      </button>

      <h1 className="text-2xl font-bold">응급 SOS</h1>

      {/* 보조 수단 디스클레이머 */}
      <div className="mt-4 flex items-start gap-2 rounded-xl bg-muted/60 px-4 py-3 text-xs text-muted-foreground">
        <Info className="mt-0.5 h-4 w-4 shrink-0" />
        본 앱은 보조 수단이며 119 직접 호출을 권장합니다
      </div>

      {/* 119 전화 */}
      <a
        href="tel:119"
        className="mt-5 flex flex-col items-center gap-1 rounded-2xl py-8 text-white"
        style={{ background: RED }}
      >
        <Phone className="h-9 w-9" />
        <span className="mt-2 text-2xl font-bold">119 전화하기</span>
        <span className="text-sm text-white/80">길게 눌러 바로 연결</span>
      </a>

      {/* 응급 의료정보 */}
      <p className="mt-7 text-sm text-muted-foreground">내 응급 의료정보</p>
      <Card className="mt-2 divide-y divide-border">
        {info.map((it) => (
          <div key={it.label} className="flex items-center justify-between px-4 py-3.5">
            <span className="text-sm text-muted-foreground">{it.label}</span>
            <span className={"font-bold " + (it.danger ? "text-destructive" : "")}>{it.value}</span>
          </div>
        ))}
      </Card>

      {/* 긴급 연락처 */}
      {contacts.length > 0 && (
        <>
          <p className="mt-7 text-sm text-muted-foreground">긴급 연락처</p>
          <div className="mt-2 space-y-3">
            {contacts.map((c) => (
              <Card key={c.phone} className="flex items-center gap-3 p-4">
                <div className={
                  "flex h-11 w-11 items-center justify-center rounded-full " +
                  (c.is_doctor ? "bg-secondary" : "bg-[#F0E8FF]")
                }>
                  {c.is_doctor
                    ? <Stethoscope className="h-5 w-5 text-primary" />
                    : <User className="h-5 w-5 text-[#7C5CCF]" />}
                </div>
                <div className="flex-1">
                  <p className="font-bold">{c.name}</p>
                  <p className="text-xs text-muted-foreground">{c.relationship}</p>
                </div>
                <a href={`tel:${c.phone}`} aria-label="전화">
                  <Phone className="h-5 w-5 text-primary" />
                </a>
              </Card>
            ))}
          </div>
        </>
      )}

      {/* 안내 */}
      <div className="mt-6 flex items-center gap-2 rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm font-semibold text-destructive">
        <AlertTriangle className="h-5 w-5 shrink-0" />
        의식이 없을 때 이 화면을 구급대원에게 보여주세요
      </div>
    </main>
  );
}
