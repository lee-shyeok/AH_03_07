"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, ChevronDown, Calendar } from "lucide-react";

const DISEASES = ["류마티스 관절염", "루푸스", "강직성 척추염", "쇼그렌 증후군", "기타"];

export default function DiseaseNewPage() {
  const router = useRouter();
  const [disease, setDisease] = useState("");
  const [date, setDate] = useState("");
  const [hospital, setHospital] = useState("");
  const [memo, setMemo] = useState("");

  function done() {
    // 백엔드: POST /v1/diseases 등
    router.replace("/home");
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col px-6 pb-8 pt-10">
      <button onClick={() => router.back()} aria-label="뒤로" className="-ml-2 w-fit">
        <ChevronLeft className="h-7 w-7" />
      </button>

      <h1 className="mt-6 text-3xl font-extrabold leading-tight">진단 정보를<br />입력해주세요</h1>
      <p className="mt-2 text-sm text-muted-foreground">맞춤형 가이드 제공을 위해 필요해요</p>

      <div className="mt-10 flex-1 space-y-6">
        <div>
          <label className="text-sm font-medium">진단명 <span className="text-destructive">*</span></label>
          <div className="relative mt-2">
            <select
              value={disease}
              onChange={(e) => setDisease(e.target.value)}
              className="h-12 w-full appearance-none rounded-xl border border-input bg-background px-4 text-sm"
            >
              <option value="">진단명 선택</option>
              {DISEASES.map((d) => <option key={d}>{d}</option>)}
            </select>
            <ChevronDown className="pointer-events-none absolute right-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          </div>
        </div>

        <div>
          <label className="text-sm font-medium">진단일 <span className="text-destructive">*</span></label>
          <div className="relative mt-2">
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="h-12 w-full rounded-xl border border-input bg-background px-4 text-sm"
            />
            <Calendar className="pointer-events-none absolute right-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          </div>
        </div>

        <div>
          <label className="text-sm font-medium">진료 받은 병원 (선택)</label>
          <input
            value={hospital}
            onChange={(e) => setHospital(e.target.value)}
            placeholder="예: OO대학교병원"
            className="mt-2 h-12 w-full rounded-xl border border-input bg-background px-4 text-sm"
          />
        </div>

        <div>
          <label className="text-sm font-medium">추가 메모 (선택)</label>
          <input
            value={memo}
            onChange={(e) => setMemo(e.target.value)}
            placeholder="입력하세요"
            className="mt-2 h-12 w-full rounded-xl border border-input bg-background px-4 text-sm"
          />
        </div>
      </div>

      <button
        onClick={done}
        disabled={!disease || !date}
        className="w-full rounded-xl bg-primary py-4 text-base font-bold text-primary-foreground disabled:opacity-50"
      >
        완료
      </button>
    </main>
  );
}
