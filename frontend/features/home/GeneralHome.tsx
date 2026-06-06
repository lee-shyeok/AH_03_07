"use client";

import Link from "next/link";
import { FileText, Stethoscope } from "lucide-react";
import HomeHeader from "./components/HomeHeader";
import MedicationCard, { type Medication } from "./components/MedicationCard";
import SectionCard from "./components/SectionCard";
import type { Guide } from "@/features/guides/api";
import type { MedicalRecord } from "@/features/medical-records/api";
import type { MedicalDocument } from "@/features/documents/api";

const FALLBACK_OCR: MedicalDocument[] = [
  { id: 1, file_name: "진료기록_2026-05.jpg", status: "processing" },
];
const FALLBACK_RECORDS: MedicalRecord[] = [
  { id: 1, hospital_name: "서울대학교병원 내과", diagnosis: "위염", visit_date: "2026-05-20" },
  { id: 2, hospital_name: "서울가정의학과의원", diagnosis: "상기도 감염", visit_date: "2026-05-10" },
  { id: 3, hospital_name: "건강한약국", diagnosis: "처방전 확인", visit_date: "2026-04-25" },
];
const FALLBACK_GUIDES: Guide[] = [
  { id: 1, symptom_summary: "위염 복약 가이드", created_at: "2026-05-20" },
  { id: 2, symptom_summary: "감기 생활습관 안내", created_at: "2026-05-15" },
  { id: 3, symptom_summary: "고혈압 관리 가이드", created_at: "2026-05-10" },
];

function shortDate(dateStr?: string) {
  if (!dateStr) return "";
  return dateStr.slice(5, 10).replace("-", ".");
}

function formatDate(dateStr?: string) {
  if (!dateStr) return "";
  return dateStr.slice(0, 10).replace(/-/g, ".");
}

function isLatest(dateStr?: string) {
  if (!dateStr) return false;
  return Date.now() - new Date(dateStr).getTime() < 30 * 24 * 60 * 60 * 1000;
}

interface GeneralHomeProps {
  name: string;
  medications: Medication[];
  guides?: Guide[];
  records?: MedicalRecord[];
  ocrDocs?: MedicalDocument[];
}

export default function GeneralHome({
  name,
  medications,
  guides = FALLBACK_GUIDES,
  records = FALLBACK_RECORDS,
  ocrDocs = FALLBACK_OCR,
}: GeneralHomeProps) {
  return (
    <main className="mx-auto w-full max-w-md px-5 pb-24 pt-10">
      <HomeHeader name={name} mode="general" />

      <div className="mt-6">
        <MedicationCard medications={medications} />
      </div>

      {ocrDocs.length > 0 && (
        <>
          <h2 className="mb-3 mt-7 text-sm font-semibold text-muted-foreground">
            진행 중인 OCR 처리 작업
          </h2>
          <SectionCard>
            {ocrDocs.map((doc) => (
              <div key={doc.id} className="flex items-center gap-3">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-amber-50">
                  <FileText className="h-6 w-6 text-amber-500" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-foreground">
                    {doc.file_name ?? `문서 #${doc.id}`}
                  </p>
                  <p className="mb-2 text-xs text-muted-foreground">OCR 텍스트 추출중...</p>
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                    <div className="h-full w-3/4 rounded-full bg-amber-500" />
                  </div>
                </div>
              </div>
            ))}
          </SectionCard>
        </>
      )}

      <h2 className="mb-3 mt-7 text-sm font-semibold text-muted-foreground">최근 진료 기록</h2>
      <SectionCard moreHref="/records">
        <ul className="space-y-4">
          {records.map((r) => (
            <li key={r.id} className="flex items-center gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-sky-50">
                <Stethoscope className="h-5 w-5 text-sky-500" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-[15px] font-medium text-foreground">
                  {r.hospital_name ?? "병원명 없음"}
                </p>
                {r.diagnosis && (
                  <p className="text-sm text-muted-foreground">{r.diagnosis}</p>
                )}
              </div>
              <span className="shrink-0 text-xs text-muted-foreground">
                {shortDate(r.visit_date)}
              </span>
            </li>
          ))}
        </ul>
      </SectionCard>

      <h2 className="mb-3 mt-7 text-sm font-semibold text-muted-foreground">최근 가이드</h2>
      <SectionCard moreHref="/guides">
        <ul className="space-y-4">
          {guides.map((g) => {
            const title = g.symptom_summary ?? g.medication_general ?? `가이드 #${g.id}`;
            const date = formatDate(g.created_at);
            const latest = isLatest(g.created_at);
            return (
              <li key={g.id} className="flex items-center gap-3">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary/10">
                  <FileText className="h-5 w-5 text-primary" />
                </div>
                <Link href={`/guides/${g.id}`} className="min-w-0 flex-1">
                  <p className="text-[15px] font-medium text-foreground">{title}</p>
                  <p className="text-sm text-muted-foreground">
                    {date}
                    {latest && <span> · 최신</span>}
                  </p>
                </Link>
              </li>
            );
          })}
        </ul>
      </SectionCard>
    </main>
  );
}
