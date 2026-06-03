"use client";

import { Search, Store, Clock, Phone, CheckCircle2 } from "lucide-react";
import { Card } from "@/components/ui/card";

interface Pharmacy {
  id: number;
  name: string;
  distance: string;
  address: string;
  open: boolean;
  is24h?: boolean;
  phone: string;
}

const PHARMACIES: Pharmacy[] = [
  { id: 1, name: "서울온누리약국", distance: "120m", address: "관악구 봉천동 1530", open: true, phone: "02-000-0001" },
  { id: 2, name: "건강드림약국", distance: "350m", address: "관악구 봉천동 977", open: true, phone: "02-000-0002" },
  { id: 3, name: "24시 열린약국", distance: "580m", address: "관악구 신림동 1430", open: true, is24h: true, phone: "02-000-0003" },
  { id: 4, name: "행복한약국", distance: "1.2km", address: "관악구 신림동 240", open: false, phone: "02-000-0004" },
];

export default function PharmacyPage() {
  return (
    <main className="mx-auto w-full max-w-md px-5 py-8">
      <h1 className="text-2xl font-bold">약국 찾기</h1>

      {/* 검색바 */}
      <div className="mt-5 flex items-center gap-2 rounded-full border border-border bg-card px-4 py-3">
        <Search className="h-4 w-4 text-muted-foreground" />
        <input placeholder="약국 이름·지역 검색" className="flex-1 bg-transparent text-sm outline-none" />
      </div>

      {/* 지도 placeholder */}
      <div className="mt-4 flex h-44 flex-col items-center justify-center rounded-2xl bg-muted">
        <span className="h-4 w-4 rounded-full border-2 border-white bg-blue-500 shadow" />
        <p className="mt-3 text-sm text-muted-foreground">현재 위치 기준 지도</p>
      </div>

      {/* 내 주변 약국 */}
      <div className="mt-6 flex items-center justify-between">
        <p className="font-bold">
          내 주변 약국 <span className="text-primary">{PHARMACIES.length}</span>
        </p>
        <span className="flex items-center gap-1 text-sm text-primary">
          <CheckCircle2 className="h-4 w-4" /> 영업중인
        </span>
      </div>

      <div className="mt-3 space-y-3">
        {PHARMACIES.map((p) => (
          <Card key={p.id} className="flex items-center gap-3 p-4">
            <div className={"flex h-11 w-11 items-center justify-center rounded-xl " + (p.open ? "bg-secondary" : "bg-muted")}>
              {p.is24h ? (
                <Clock className={"h-6 w-6 " + (p.open ? "text-primary" : "text-muted-foreground")} />
              ) : (
                <Store className={"h-6 w-6 " + (p.open ? "text-primary" : "text-muted-foreground")} />
              )}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <p className="font-bold">{p.name}</p>
                <span
                  className={
                    "rounded-md px-1.5 py-0.5 text-[11px] font-semibold " +
                    (p.is24h ? "bg-blue-50 text-blue-500" : p.open ? "bg-secondary text-primary" : "bg-muted text-muted-foreground")
                  }
                >
                  {p.open ? "영업중" : "영업종료"}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">{p.distance} · {p.address}</p>
            </div>
            <a href={`tel:${p.phone}`} aria-label="전화">
              <Phone className={"h-5 w-5 " + (p.open ? "text-primary" : "text-muted-foreground/40")} />
            </a>
          </Card>
        ))}
      </div>
    </main>
  );
}
