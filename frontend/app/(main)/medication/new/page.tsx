"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Search, ChevronDown, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const CATEGORIES = ["면역억제제", "항염증제", "스테로이드", "항류마티스", "기타"];
const UNITS = ["정", "캡슐", "ml", "mg", "포"];
const TIMINGS = ["아침", "점심", "저녁", "취침 전"];

export default function MedicationNewPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [category, setCategory] = useState("면역억제제");
  const [dose, setDose] = useState("1");
  const [unit, setUnit] = useState("정");
  const [freq, setFreq] = useState(2);
  const [timings, setTimings] = useState<string[]>(["아침", "저녁"]);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [memo, setMemo] = useState("");
  const [loading, setLoading] = useState(false);

  function toggleTiming(t: string) {
    setTimings((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]));
  }

  async function handleSubmit() {
    if (!name.trim()) return alert("약품명을 입력해주세요.");
    setLoading(true);
    // 백엔드: POST /v1/medications
    setTimeout(() => {
      setLoading(false);
      router.replace("/medication");
    }, 600);
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8 pb-28">
      <h1 className="text-2xl font-bold">약 등록</h1>

      {/* 약품 정보 */}
      <p className="mt-6 text-sm font-semibold text-muted-foreground">약품 정보</p>
      <div className="mt-2 rounded-2xl border border-border p-4">
        <label className="text-sm">약품명 <span className="text-destructive">*</span></label>
        <div className="relative mt-1.5">
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="약품명 검색" className="pr-10" />
          <Search className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        </div>
        <label className="mt-4 block text-sm">약물 분류</label>
        <div className="relative mt-1.5">
          <select value={category} onChange={(e) => setCategory(e.target.value)} className="h-11 w-full appearance-none rounded-md border border-input bg-background px-3 text-sm">
            {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
          </select>
          <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        </div>
      </div>

      {/* 복용 정보 */}
      <p className="mt-6 text-sm font-semibold text-muted-foreground">복용 정보</p>
      <div className="mt-2 space-y-4 rounded-2xl border border-border p-4">
        <div>
          <label className="text-sm">1회 복용량 <span className="text-destructive">*</span></label>
          <div className="mt-1.5 flex gap-2">
            <Input value={dose} onChange={(e) => setDose(e.target.value)} inputMode="numeric" className="flex-[2] text-center" />
            <div className="relative flex-[3]">
              <select value={unit} onChange={(e) => setUnit(e.target.value)} className="h-11 w-full appearance-none rounded-md border border-input bg-background px-3 text-sm">
                {UNITS.map((u) => <option key={u}>{u}</option>)}
              </select>
              <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            </div>
          </div>
        </div>

        <div>
          <label className="text-sm">1일 복용 횟수 <span className="text-destructive">*</span></label>
          <div className="mt-2 flex gap-2">
            {[1, 2, 3, 4].map((n) => (
              <button
                key={n}
                onClick={() => setFreq(n)}
                className={"flex-1 rounded-full py-2.5 text-sm font-semibold " + (freq === n ? "bg-primary text-primary-foreground" : "border border-border")}
              >
                {n === 4 ? "4회 +" : `${n}회`}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="text-sm">복용 시점</label>
          <div className="mt-2 flex flex-wrap gap-2">
            {TIMINGS.map((t) => (
              <button
                key={t}
                onClick={() => toggleTiming(t)}
                className={"rounded-full px-4 py-2.5 text-sm font-semibold " + (timings.includes(t) ? "bg-primary text-primary-foreground" : "border border-border")}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="text-sm">복용 기간</label>
          <div className="mt-1.5 flex items-center gap-2">
            <div className="relative flex-1">
              <Calendar className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input type="date" value={start} onChange={(e) => setStart(e.target.value)} className="h-11 w-full rounded-md border border-input bg-background pl-9 pr-2 text-sm" />
            </div>
            <span className="text-muted-foreground">~</span>
            <div className="relative flex-1">
              <Calendar className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} className="h-11 w-full rounded-md border border-input bg-background pl-9 pr-2 text-sm" />
            </div>
          </div>
        </div>
      </div>

      {/* 추가 정보 */}
      <p className="mt-6 text-sm font-semibold text-muted-foreground">추가 정보</p>
      <div className="mt-2 rounded-2xl border border-border p-4">
        <label className="text-sm">메모 (선택)</label>
        <textarea value={memo} onChange={(e) => setMemo(e.target.value)} rows={2} placeholder="예: 식후 30분에 복용" className="mt-1.5 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
      </div>

      <div className="fixed inset-x-0 bottom-16 mx-auto max-w-md px-5">
        <Button className="w-full" size="lg" onClick={handleSubmit} disabled={loading}>
          {loading ? "등록 중..." : "등록하기"}
        </Button>
      </div>
    </main>
  );
}
