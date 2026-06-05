"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Check, Circle, AlertTriangle, ClipboardCheck, FileText } from "lucide-react";
import { Card } from "@/components/ui/card";
import { getDashboard } from "@/features/dashboard/api";
import { getMe } from "@/features/auth/api";
import { getMode } from "@/features/auth/mode";
import { getGuides } from "@/features/guides/api";
import { getRecords } from "@/features/medical-records/api";
import { getDocuments } from "@/features/documents/api";
import type { DashboardData } from "@/features/dashboard/api";
import type { Guide } from "@/features/guides/api";
import type { MedicalRecord } from "@/features/medical-records/api";
import type { MedicalDocument } from "@/features/documents/api";

const PURPLE = "#7C5CCF";
const ACTIVITY = [
  { label: "통증", value: 5 },
  { label: "피로", value: 6 },
  { label: "강직", value: 4 },
  { label: "불편도", value: 7 },
];

function formatDate(dateStr?: string) {
  if (!dateStr) return "";
  return dateStr.slice(0, 10).replace(/-/g, ".");
}

function shortDate(dateStr?: string) {
  if (!dateStr) return "";
  return dateStr.slice(5, 10).replace("-", ".");
}

function isLatest(dateStr?: string) {
  if (!dateStr) return false;
  return (Date.now() - new Date(dateStr).getTime()) < 7 * 24 * 60 * 60 * 1000;
}

export default function HomePage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [name, setName] = useState<string>("");
  const [userType, setUserType] = useState<"general" | "autoimmune">("general");
  const [guides, setGuides] = useState<Guide[]>([]);
  const [records, setRecords] = useState<MedicalRecord[]>([]);
  const [ocrDocs, setOcrDocs] = useState<MedicalDocument[]>([]);

  useEffect(() => {
    setUserType(getMode());
    getMe().then((u) => { setName(u.name); if (u.user_type) setUserType(u.user_type); }).catch(() => {});
    getDashboard().then((d) => { setData(d); if (d.user_type) setUserType(d.user_type); }).catch(() => setData(fallback));
    getGuides().then((g) => setGuides(g.slice(0, 3))).catch(() => setGuides(fallbackGuides));
    getRecords().then((r) => setRecords(r.slice(0, 3))).catch(() => setRecords(fallbackRecords));
    getDocuments().then((docs) => {
      const pending = docs.filter((d) => d.status === "processing" || d.status === "pending");
      setOcrDocs(pending.length > 0 ? pending : fallbackOcr);
    }).catch(() => setOcrDocs(fallbackOcr));
  }, []);

  const meds = data?.medications ?? fallback.medications!;
  const tips = data?.health_tips ?? fallback.health_tips!;
  const isAuto = userType === "autoimmune";

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-10 pb-6">
      {/* 인사말 */}
      <h1 className="text-3xl font-bold leading-tight">
        안녕하세요!<br />
        {name || data?.user_name || "OOO"}님{" "}
        {!isAuto && <span className="text-base font-semibold text-primary">일반 환자</span>}
      </h1>

      {/* 자가면역: 오늘의 활성도 */}
      {isAuto && (
        <Card className="mt-6 p-5">
          <h2 className="text-base font-bold">오늘의 활성도</h2>
          <p className="mt-1 text-3xl font-extrabold" style={{ color: PURPLE }}>
            5.5 <span className="text-base font-normal text-muted-foreground">/ 10</span>
          </p>
          <div className="mt-3 grid grid-cols-2 gap-2.5">
            {ACTIVITY.map((a) => (
              <div key={a.label} className="rounded-xl bg-muted/60 px-4 py-3">
                <span className="text-xs text-muted-foreground">{a.label} </span>
                <span className="font-bold">{a.value}</span>
              </div>
            ))}
          </div>
          <Link href="/activity/new" className="mt-4 block w-full rounded-xl py-3 text-center font-bold text-white" style={{ background: PURPLE }}>
            활성도 기록하기
          </Link>
        </Card>
      )}

      {/* 오늘 복약 */}
      <Card className="mt-6 p-5">
        <h2 className="text-base font-bold">오늘 복약</h2>
        <ul className="mt-3 space-y-2.5">
          {meds.map((m, i) => (
            <li key={i} className="flex items-center gap-2.5 text-sm">
              {m.done
                ? <Check className="h-4 w-4 shrink-0 text-primary" />
                : <Circle className="h-4 w-4 shrink-0 text-muted-foreground/40" />}
              <span className={m.done ? "font-semibold text-foreground" : "text-muted-foreground"}>{m.label}</span>
            </li>
          ))}
        </ul>
        <Link href="/medication/checklist" className="mt-3 flex items-center justify-end gap-1 text-sm font-semibold text-primary">
          전체 보기 <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </Card>

      {/* 진행 중인 OCR 처리 작업 */}
      {ocrDocs.length > 0 && (
        <div className="mt-6">
          <h2 className="text-base font-bold">진행 중인 OCR 처리 작업</h2>
          <div className="mt-3 space-y-3">
            {ocrDocs.map((doc) => (
              <Card key={doc.id} className="flex items-center gap-3 p-4">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-amber-100">
                  <FileText className="h-5 w-5 text-amber-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-foreground">{doc.file_name ?? `문서 #${doc.id}`}</p>
                  <p className="text-xs text-muted-foreground">OCR 텍스트 추출중...</p>
                  <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                    <div className="h-full w-3/4 rounded-full bg-amber-500" />
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* 최근 진료 기록 */}
      {records.length > 0 && (
        <div className="mt-6">
          <h2 className="text-base font-bold">최근 진료 기록</h2>
          <Card className="mt-3 divide-y divide-border overflow-hidden p-0">
            {records.map((r) => (
              <div key={r.id} className="flex items-center justify-between px-4 py-3.5">
                <div className="flex-1">
                  <p className="text-sm font-semibold text-foreground">{r.hospital_name ?? "병원명 없음"}</p>
                  {r.diagnosis && <p className="text-xs text-muted-foreground">{r.diagnosis}</p>}
                </div>
                <span className="ml-3 shrink-0 text-xs text-muted-foreground">{shortDate(r.visit_date)}</span>
              </div>
            ))}
            <div className="px-4 py-2.5 text-right">
              <Link href="/records" className="text-sm font-semibold text-primary">전체 보기 →</Link>
            </div>
          </Card>
        </div>
      )}

      {/* 최근 가이드 */}
      {guides.length > 0 && (
        <div className="mt-6">
          <h2 className="text-base font-bold">최근 가이드</h2>
          <Card className="mt-3 divide-y divide-border overflow-hidden p-0">
            {guides.map((g) => {
              const title = g.symptom_summary ?? g.medication_general ?? `가이드 #${g.id}`;
              const date = formatDate(g.created_at);
              const latest = isLatest(g.created_at);
              return (
                <Link key={g.id} href={`/guides/${g.id}`} className="flex items-center gap-3 px-4 py-3.5 hover:bg-accent">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10">
                    <FileText className="h-5 w-5 text-primary" strokeWidth={1.5} />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-foreground">{title}</p>
                    <p className="text-xs text-muted-foreground">
                      {date}{latest && <span> · 최신</span>}
                    </p>
                  </div>
                </Link>
              );
            })}
            <div className="px-4 py-2.5 text-right">
              <Link href="/guides" className="text-sm font-semibold text-primary">전체 보기 →</Link>
            </div>
          </Card>
        </div>
      )}

      {/* 위험신호 / 건강 팁 */}
      {isAuto ? (
        <div className="mt-6 space-y-2">
          <Link href="/risk-flags" className="flex items-center justify-between rounded-2xl border-2 px-4 py-3.5" style={{ borderColor: "#F5C518", background: "#FEF9E7" }}>
            <span className="flex items-center gap-2 text-sm font-semibold">
              <AlertTriangle className="h-4 w-4" style={{ color: "#B7950B" }} />
              의료진 확인 필요 신호 1건
            </span>
            <ArrowRight className="h-4 w-4 text-muted-foreground" />
          </Link>
          <Link href="/symptom-check" className="flex items-center justify-between rounded-2xl border border-border bg-card px-4 py-3.5">
            <span className="flex items-center gap-2 text-sm font-semibold">
              <ClipboardCheck className="h-4 w-4 text-destructive" />
              주의 증상 체크하기
            </span>
            <ArrowRight className="h-4 w-4 text-muted-foreground" />
          </Link>
        </div>
      ) : (
        <Card className="mt-6 p-5">
          <h2 className="text-base font-bold">오늘의 건강 팁</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {tips.map((t, i) => <li key={i} className="font-medium text-foreground">{t}</li>)}
          </ul>
          <Link href="/guides" className="mt-3 flex items-center justify-end gap-1 text-sm font-semibold text-primary">
            전체 보기 <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </Card>
      )}
    </main>
  );
}

const fallbackGuides: Guide[] = [
  { id: 1, symptom_summary: "위염 복약 가이드", created_at: "2026-05-20" },
  { id: 2, symptom_summary: "감기 생활습관 안내", created_at: "2026-05-15" },
  { id: 3, symptom_summary: "고혈압 관리 가이드", created_at: "2026-05-10" },
];

const fallbackRecords: MedicalRecord[] = [
  { id: 1, hospital_name: "서울대학교병원 내과", diagnosis: "위염", visit_date: "2026-05-20" },
  { id: 2, hospital_name: "서울가정의학과의원", diagnosis: "상기도 감염", visit_date: "2026-05-10" },
  { id: 3, hospital_name: "건강한약국", diagnosis: "처방전 확인", visit_date: "2026-04-25" },
];

const fallbackOcr: MedicalDocument[] = [
  { id: 1, file_name: "진료기록_2026-05.jpg", status: "processing" },
];

const fallback: DashboardData = {
  user_type: "general",
  medications: [
    { label: "아침약 (오전 9시)", done: true },
    { label: "점심약 (오후 1시)", done: false },
    { label: "저녁약 (오후 7시)", done: false },
  ],
  health_tips: ["💧 수분 충분히 섭취하기", "🚶 30분 가벼운 산책", "😴 7시간 이상 수면"],
};
