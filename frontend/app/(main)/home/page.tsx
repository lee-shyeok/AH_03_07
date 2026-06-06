"use client";

import { useEffect, useState } from "react";
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
import GeneralHome from "@/features/home/GeneralHome";
import AutoimmuneHome from "@/features/home/AutoimmuneHome";

const FALLBACK_GUIDES: Guide[] = [
  { id: 1, symptom_summary: "위염 복약 가이드", created_at: "2026-05-20" },
  { id: 2, symptom_summary: "감기 생활습관 안내", created_at: "2026-05-15" },
  { id: 3, symptom_summary: "고혈압 관리 가이드", created_at: "2026-05-10" },
];

const FALLBACK_RECORDS: MedicalRecord[] = [
  { id: 1, hospital_name: "서울대학교병원 내과", diagnosis: "위염", visit_date: "2026-05-20" },
  { id: 2, hospital_name: "서울가정의학과의원", diagnosis: "상기도 감염", visit_date: "2026-05-10" },
  { id: 3, hospital_name: "건강한약국", diagnosis: "처방전 확인", visit_date: "2026-04-25" },
];

const FALLBACK_OCR: MedicalDocument[] = [
  { id: 1, file_name: "진료기록_2026-05.jpg", status: "processing" },
];

export default function HomePage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [name, setName] = useState<string>("");
  const [userType, setUserType] = useState<"general" | "autoimmune">("general");
  const [guides, setGuides] = useState<Guide[]>(FALLBACK_GUIDES);
  const [records, setRecords] = useState<MedicalRecord[]>(FALLBACK_RECORDS);
  const [ocrDocs, setOcrDocs] = useState<MedicalDocument[]>(FALLBACK_OCR);

  useEffect(() => {
    setUserType(getMode());
    getMe().then((u) => { setName(u.name); if (u.user_type) setUserType(u.user_type); }).catch(() => {});
    getDashboard().then((d) => { setData(d); if (d.user_type) setUserType(d.user_type); }).catch(() => setData(fallback));
    getGuides().then((g) => { if (g.length > 0) setGuides(g.slice(0, 3)); }).catch(() => {});
    getRecords().then((r) => { if (r.length > 0) setRecords(r.slice(0, 3)); }).catch(() => {});
    getDocuments().then((docs) => {
      const pending = docs.filter((d) => d.status === "processing" || d.status === "pending");
      if (pending.length > 0) setOcrDocs(pending);
    }).catch(() => {});
  }, []);

  const meds = data?.medications ?? fallback.medications!;
  const displayName = name || data?.user_name || "OOO";

  if (userType === "autoimmune") {
    return <AutoimmuneHome name={displayName} medications={meds} />;
  }
  return (
    <GeneralHome
      name={displayName}
      medications={meds}
      guides={guides}
      records={records}
      ocrDocs={ocrDocs}
    />
  );
}

const fallback: DashboardData = {
  user_type: "general",
  medications: [
    { label: "아침약 (오전 9시)", done: true },
    { label: "점심약 (오후 1시)", done: false },
    { label: "저녁약 (오후 7시)", done: false },
  ],
  health_tips: ["💧 수분 충분히 섭취하기", "🚶 30분 가벼운 산책", "😴 7시간 이상 수면"],
};
