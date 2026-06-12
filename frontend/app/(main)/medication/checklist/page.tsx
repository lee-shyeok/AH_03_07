"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Camera, Check, Clock } from "lucide-react";
import { Card } from "@/components/ui/card";
import {
  getMedicationLogs,
  checkMedicationLog,
  createMedication,
  type MedicationLog,
} from "@/features/medication/api";
import { uploadDocument, startOcrJob, getOcrJob } from "@/features/documents/api";

interface Slot {
  time: string;
  items: MedicationLog[];
}

const DAYS = ["일", "월", "화", "수", "목", "금", "토"];

function todayLabel() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}.${m}.${day} (${DAYS[d.getDay()]})`;
}

function todayISO() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function formatSlotTime(t: string) {
  const [hStr, mStr] = t.split(":");
  const h = Number(hStr);
  const ampm = h < 12 ? "오전" : "오후";
  const h12 = h % 12 || 12;
  return `${ampm} ${h12}:${mStr}`;
}

function groupByTime(logs: MedicationLog[]): Slot[] {
  const map = new Map<string, MedicationLog[]>();
  for (const log of logs) {
    const t = log.scheduled_time ?? "09:00";
    if (!map.has(t)) map.set(t, []);
    map.get(t)!.push(log);
  }
  return [...map.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([time, items]) => ({ time: formatSlotTime(time), items }));
}

// 백엔드 미가동 시 폴백 더미
const DUMMY: MedicationLog[] = [
  { id: 1, medication_id: 1, medication_name: "메토트렉세이트 7.5mg", scheduled_time: "09:00", taken: true, taken_at: "09:05", is_autoimmune_drug: true },
  { id: 2, medication_id: 2, medication_name: "폴산 5mg", scheduled_time: "09:00", taken: true, taken_at: "09:05", is_autoimmune_drug: true },
  { id: 3, medication_id: 3, medication_name: "아세트아미노펜 500mg", scheduled_time: "13:00", taken: false, dosage: "해열·진통 · 1정" },
  { id: 4, medication_id: 3, medication_name: "아세트아미노펜 500mg", scheduled_time: "18:00", taken: false, dosage: "해열·진통 · 1정" },
];

export default function ChecklistPage() {
  const router = useRouter();
  const [slots, setSlots] = useState<Slot[]>([]);
  const [loading, setLoading] = useState(true);
  const scanRef = useRef<HTMLInputElement>(null);
  const [scanStatus, setScanStatus] = useState<"idle" | "working" | "done">("idle");
  const [scanMsg, setScanMsg] = useState<string | null>(null);

  async function loadLogs() {
    try {
      const logs = await getMedicationLogs(todayISO());
      setSlots(groupByTime(logs.length ? logs : DUMMY));
    } catch {
      setSlots(groupByTime(DUMMY));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadLogs(); }, []);

  async function take(logId: number) {
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, "0");
    const mm = String(now.getMinutes()).padStart(2, "0");
    setSlots((prev) =>
      prev.map((s) => ({
        ...s,
        items: s.items.map((it) =>
          it.id === logId ? { ...it, taken: true, taken_at: `${hh}:${mm}` } : it
        ),
      }))
    );
    try { await checkMedicationLog(logId); } catch {}
  }

  async function handleScan(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = "";
    setScanStatus("working");
    setScanMsg("약 봉투 인식 중...");
    try {
      const doc = await uploadDocument(file, "pill_bag");
      const job = await startOcrJob(doc.id);
      let result = job;
      for (let i = 0; i < 30; i++) {
        await new Promise<void>((r) => setTimeout(r, 1000));
        result = await getOcrJob(job.job_id);
        if (result.status === "completed" || result.status === "failed") break;
      }
      if (result.status === "completed" && result.structured_data) {
        const meds = (result.structured_data.medications ?? []) as Array<{
          drug_name?: string;
          name?: string;
          dosage?: string;
        }>;
        for (const med of meds) {
          const name = med.drug_name ?? med.name;
          if (name) {
            try { await createMedication({ name, note: med.dosage }); } catch {}
          }
        }
        setScanMsg(meds.length > 0 ? `${meds.length}개 약이 목록에 추가됐어요` : "인식된 약이 없어요. 직접 입력해주세요.");
        await loadLogs();
      } else {
        setScanMsg("인식 실패. 직접 입력해주세요.");
      }
    } catch {
      setScanMsg("인식 중 오류가 발생했어요.");
    } finally {
      setScanStatus("done");
      setTimeout(() => { setScanMsg(null); setScanStatus("idle"); }, 4000);
    }
  }

  const all = slots.flatMap((s) => s.items);
  const total = all.length;
  const done = all.filter((i) => i.taken).length;

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-8">
      {/* 헤더 */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => router.back()}
          className="flex items-center justify-center rounded-full p-1.5 hover:bg-muted"
          aria-label="뒤로가기"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <h1 className="flex-1 text-xl font-bold">복약 체크리스트</h1>
        <button
          onClick={() => scanRef.current?.click()}
          disabled={scanStatus === "working"}
          className="flex items-center gap-1.5 rounded-xl bg-orange-50 px-3 py-2 text-xs font-semibold text-orange-600 hover:bg-orange-100 disabled:opacity-50"
          aria-label="약봉투 촬영"
        >
          {scanStatus === "working" ? (
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-orange-400 border-t-transparent inline-block" />
          ) : (
            <Camera className="h-4 w-4" />
          )}
          약봉투 스캔
        </button>
        <input
          ref={scanRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={handleScan}
        />
      </div>

      {/* 스캔 결과 메시지 */}
      {scanMsg && (
        <div className="mt-2 rounded-lg bg-orange-50 px-4 py-2 text-sm text-orange-700">
          {scanMsg}
        </div>
      )}

      {/* 날짜 + 진행률 카드 */}
      <Card className="mt-5 p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xl font-bold">{todayLabel()}</p>
            <p className="mt-0.5 text-sm text-muted-foreground">오늘의 복약 일정</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-muted-foreground">완료</p>
            <p className="text-2xl font-extrabold text-primary">
              {done}
              <span className="text-base text-muted-foreground">/{total}</span>
            </p>
          </div>
        </div>
        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-primary transition-all"
            style={{ width: total ? `${(done / total) * 100}%` : "0%" }}
          />
        </div>
      </Card>

      {/* 시간대별 목록 */}
      {loading ? (
        <p className="mt-8 text-sm text-muted-foreground">불러오는 중...</p>
      ) : (
        <div className="mt-6 space-y-5 pb-10">
          {slots.map((slot) => (
            <div key={slot.time}>
              <p className="flex items-center gap-1.5 text-sm font-semibold text-primary">
                <Clock className="h-4 w-4" /> {slot.time}
              </p>
              <div className="mt-2 space-y-2">
                {slot.items.map((it) => (
                  <Card
                    key={it.id}
                    className={"flex items-center gap-3 p-4 " + (it.taken ? "border-primary/20 bg-secondary" : "")}
                  >
                    {it.taken ? (
                      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary">
                        <Check className="h-5 w-5 text-primary-foreground" />
                      </span>
                    ) : (
                      <span className="h-8 w-8 shrink-0 rounded-full border-2 border-muted-foreground/30" />
                    )}

                    {/* 약 이름 클릭 → 상세 페이지 */}
                    <Link href={`/medication/${it.medication_id}`} className="min-w-0 flex-1">
                      <p className={"truncate font-semibold " + (it.taken ? "text-muted-foreground line-through" : "")}>
                        {it.medication_name}
                      </p>
                      <div className="mt-0.5 flex items-center gap-1.5">
                        {it.is_autoimmune_drug && (
                          <span className="rounded bg-[#F0E8FF] px-1.5 py-0.5 text-[11px] font-semibold text-[#7C5CCF]">
                            자가면역
                          </span>
                        )}
                        <span className="text-xs text-muted-foreground">
                          {it.taken
                            ? `복용 ${it.taken_at ?? ""}`
                            : (it.dosage ?? "")}
                        </span>
                      </div>
                    </Link>

                    {!it.taken && (
                      <button
                        onClick={() => take(it.id)}
                        className="shrink-0 rounded-lg bg-primary px-4 py-2 text-sm font-bold text-primary-foreground"
                      >
                        복용
                      </button>
                    )}
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
