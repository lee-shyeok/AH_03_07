"use client";

import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Link as LinkIcon, ArrowRight, Pill } from "lucide-react";
import { useState } from "react";
import { Card } from "@/components/ui/card";
import { useMedications } from "@/features/medication/queries";
import { DRUG_CLASS_LABEL, DRUG_CLASS_COLOR } from "@/features/medication/schema";

const PRIMARY_GREEN = "#22C55E";
const AUTOIMMUNE_PURPLE = "#7C5CCF";
const ALL_TABS = ["복약", "생활습관", "주의사항", "자가면역"] as const;
type Tab = (typeof ALL_TABS)[number];

interface TabContent {
  복약: string[];
  생활습관: string[];
  주의사항: string[];
  자가면역: { title: string; items: string[] }[];
}

const CONTENT: Record<string, TabContent> = {
  STEROID: {
    복약: [
      "반드시 식후에 복용하세요.",
      "의사 지시 없이 갑자기 중단하지 마세요 (부신부전 위험).",
      "정해진 시간에 규칙적으로 복용하세요.",
    ],
    생활습관: [
      "저염·저당 식단을 유지하세요.",
      "체중 증가에 주의하고 규칙적으로 운동하세요.",
      "골다공증 예방을 위해 칼슘·비타민D를 보충하세요.",
      "혈압·혈당을 정기적으로 측정하세요.",
    ],
    주의사항: [
      "혈당·혈압 이상 시 즉시 의료진에게 알리세요.",
      "생백신 접종 전 반드시 의료진과 상담하세요.",
      "감염 증상(발열, 오한)이 있으면 즉시 연락하세요.",
      "임신 계획 시 반드시 의료진과 상의하세요.",
    ],
    자가면역: [
      { title: "항염증 효과", items: ["강력한 항염증·면역억제 작용으로 자가면역 증상을 빠르게 억제합니다."] },
      { title: "감염 주의", items: ["면역 저하로 감염 위험이 높아집니다.", "발열 시 즉시 의료진에게 연락하세요."] },
      { title: "장기 부작용 모니터링", items: ["골다공증, 고혈압, 당뇨 위험을 정기 검사로 관리하세요."] },
    ],
  },
  IMMUNOSUPPRESSANT: {
    복약: [
      "정해진 용량과 시간을 반드시 지키세요.",
      "구역감이 있으면 식후에 복용하세요.",
      "정기 혈액검사(CBC, 간 기능)가 필수입니다.",
    ],
    생활습관: [
      "음주를 자제하세요 (간 부담).",
      "충분한 수분을 섭취하세요.",
      "규칙적인 수면과 스트레스 관리를 유지하세요.",
      "손 씻기 등 개인위생을 철저히 하세요.",
    ],
    주의사항: [
      "생백신 접종 금지.",
      "임신 계획 시 반드시 의료진 상담 (최소 3개월 전).",
      "발열·기침·상처 악화 등 감염 징후 즉시 보고.",
      "다른 약 복용 전 반드시 의사·약사에게 알리세요.",
    ],
    자가면역: [
      { title: "면역억제 작용", items: ["과활성화된 면역 반응을 억제하여 관절·장기 손상을 예방합니다."] },
      { title: "감염 주의", items: ["면역 기능 저하로 일반 감염도 중증화될 수 있습니다.", "발열 시 즉시 의료진 상담."] },
      { title: "정기 모니터링", items: ["혈액검사로 혈구 수치와 간·신장 기능을 정기 확인하세요."] },
    ],
  },
  ANTIMALARIAL: {
    복약: [
      "식사와 함께 또는 식후에 복용하세요 (위 자극 감소).",
      "효과가 나타나기까지 수 주~수 개월이 걸릴 수 있습니다.",
      "임의로 중단하지 마세요.",
    ],
    생활습관: [
      "자외선 차단제를 꼭 사용하세요 (광과민성 증가 가능).",
      "정기 안과 검진을 받으세요 (연 1회 권장).",
      "규칙적인 생활 리듬을 유지하세요.",
    ],
    주의사항: [
      "시야 이상, 색감 변화가 생기면 즉시 중단 후 의료진에게 연락하세요.",
      "심장 질환이 있는 경우 주기적인 심전도 검사를 받으세요.",
      "임신 중에도 의사 지시에 따라 복용 가능하나 반드시 상담하세요.",
    ],
    자가면역: [
      { title: "질환 활성도 조절", items: ["루푸스·류마티스 관절염의 재발을 줄이고 질환 활성도를 낮추는 데 도움을 줍니다."] },
      { title: "장기 보호", items: ["장기적으로 심혈관·신장 합병증 위험을 줄이는 효과가 보고되어 있습니다."] },
      { title: "망막 독성 주의", items: ["고용량 장기 복용 시 망막 독성이 발생할 수 있으므로 안과 검진이 필요합니다."] },
    ],
  },
  BIOLOGIC: {
    복약: [
      "처방된 일정(주사 또는 주입)에 맞춰 투여받으세요.",
      "자가 주사 방법을 의료진에게 충분히 교육받으세요.",
      "냉장 보관이 필요한 경우 보관 방법을 준수하세요.",
    ],
    생활습관: [
      "감염 예방을 위해 위생 관리를 철저히 하세요.",
      "주사 부위를 매번 바꿔 가며 투여하세요.",
      "정기적인 검사 일정을 반드시 지키세요.",
    ],
    주의사항: [
      "투여 전 결핵 검사(TB)를 완료하세요.",
      "심부전, 탈수초 질환 병력이 있는 경우 의사에게 알리세요.",
      "생백신 접종 금지.",
      "수술 전 의사와 투여 중단 여부를 반드시 상의하세요.",
    ],
    자가면역: [
      { title: "표적 면역 조절", items: ["특정 사이토카인(TNF, IL-6 등)을 표적으로 차단해 관절 손상과 염증을 억제합니다."] },
      { title: "결핵 재활성 위험", items: ["잠복 결핵이 있으면 재활성화될 수 있으므로 치료 전 검사가 필수입니다."] },
      { title: "감염 주의", items: ["중증 감염이 발생하면 투여를 즉시 중단하고 의료진에게 연락하세요."] },
    ],
  },
  NSAID: {
    복약: [
      "반드시 식후에 복용하세요 (위 점막 보호).",
      "필요 시 위장 보호제를 함께 복용하세요.",
      "증상이 완화되면 의사와 상의 후 용량을 조절하세요.",
    ],
    생활습관: [
      "충분한 수분을 섭취하세요 (신장 보호).",
      "알코올 섭취를 자제하세요.",
      "위장 불편감이 지속되면 즉시 의료진과 상담하세요.",
    ],
    주의사항: [
      "신장 기능 저하, 심혈관 질환 병력이 있는 경우 의사에게 알리세요.",
      "다른 소염진통제와 중복 복용하지 마세요.",
      "위장 출혈 증상(흑색 변, 토혈)이 있으면 즉시 응급실을 방문하세요.",
    ],
    자가면역: [
      { title: "항염·진통 효과", items: ["프로스타글란딘 생성을 억제해 통증과 염증을 완화합니다."] },
      { title: "면역억제 효과 없음", items: ["NSAID는 면역을 억제하지 않으므로 자가면역 질환의 근본 치료제는 아닙니다.", "보조적 통증 관리에 사용됩니다."] },
    ],
  },
};

const DEFAULT_CONTENT: TabContent = {
  복약: ["처방된 용법·용량을 준수하세요.", "임의로 중단하지 마세요."],
  생활습관: ["규칙적인 생활을 유지하세요.", "충분한 수면과 수분 섭취를 권장합니다."],
  주의사항: ["다른 약 복용 전 의사·약사와 상담하세요.", "부작용 발생 시 즉시 의료진에게 알리세요."],
  자가면역: [{ title: "주의사항", items: ["담당 의료진의 지시를 따르세요."] }],
};

export default function MedicationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);
  const [tab, setTab] = useState<Tab>("복약");

  // 목록 캐시(DUMMY 포함)에서 가져와 API 인코딩 오류 방지
  const { data: meds = [], isLoading } = useMedications();
  const med = meds.find((m) => m.id === id) ?? null;

  const drugClass = med?.drug_class ?? "";
  const content = CONTENT[drugClass] ?? DEFAULT_CONTENT;
  const label = DRUG_CLASS_LABEL[drugClass];
  const isAutoimmuneDrug = !!drugClass;
  const tabs = isAutoimmuneDrug ? ALL_TABS : (ALL_TABS.filter((t) => t !== "자가면역") as Tab[]);
  const color = DRUG_CLASS_COLOR[drugClass] ?? (isAutoimmuneDrug ? AUTOIMMUNE_PURPLE : PRIMARY_GREEN);
  const nedrugsUrl = `https://nedrug.mfds.go.kr/searchDrug?searchYn=true&itemName=${encodeURIComponent(med?.name ?? "")}`;

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-8 pb-10">
      {/* 헤더 */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => router.push("/medication")}
          className="flex items-center justify-center rounded-full p-1.5 hover:bg-muted"
          aria-label="뒤로가기"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
      </div>

      {isLoading ? (
        <div className="mt-4 space-y-2 animate-pulse">
          <div className="h-8 w-48 rounded bg-muted" />
          <div className="h-6 w-20 rounded-full bg-muted mt-3" />
        </div>
      ) : !med ? (
        <p className="mt-4 text-muted-foreground">약물 정보를 찾을 수 없습니다.</p>
      ) : (
        <>
          <div className="mt-3 flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
              <Pill className="h-5 w-5 text-primary" />
            </div>
            <h1 className="text-2xl font-bold leading-tight">{med.name}</h1>
          </div>

          {/* 뱃지 */}
          <div className="mt-3 flex flex-wrap gap-2">
            {label && (
              <span
                className="inline-block rounded-full px-3 py-1 text-xs font-bold"
                style={{ background: color + "1A", color }}
              >
                {label}
              </span>
            )}
            {med.is_injection && (
              <span
                className="inline-block rounded-full px-3 py-1 text-xs font-bold"
                style={{ background: "#EF444420", color: "#EF4444" }}
              >
                주사제
              </span>
            )}
          </div>

          {med.note && (
            <p className="mt-2 text-sm text-muted-foreground">{med.note}</p>
          )}

          {/* 식약처 의약품안전나라 링크 */}
          <a
            href={nedrugsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 flex items-center gap-1.5 rounded-xl border border-border px-4 py-2.5 text-sm font-semibold text-primary hover:bg-accent"
          >
            <LinkIcon className="h-4 w-4 shrink-0" />
            공식 정보 보기 (식약처 의약품안전나라)
            <ArrowRight className="ml-auto h-4 w-4 shrink-0 text-muted-foreground" />
          </a>

          {/* 탭 */}
          <div className="mt-6 flex border-b border-border">
            {tabs.map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={"flex-1 pb-3 text-sm font-semibold " + (tab === t ? "" : "text-muted-foreground")}
                style={tab === t ? { color, borderBottom: `2px solid ${color}` } : undefined}
              >
                {t}
              </button>
            ))}
          </div>

          {/* 탭 콘텐츠 */}
          <div className="mt-6 space-y-4 pb-6">
            {tab === "자가면역" ? (
              <>
                {content.자가면역.map((section) => (
                  <section key={section.title}>
                    <h2 className="text-base font-bold">{section.title}</h2>
                    <ul className="mt-2 space-y-1">
                      {section.items.map((item, i) => (
                        <li key={i} className="flex gap-2 text-sm leading-relaxed">
                          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: color }} />
                          {item}
                        </li>
                      ))}
                    </ul>
                  </section>
                ))}
                <Card className="p-4">
                  <p className="text-xs text-muted-foreground">📚 출처</p>
                  <p className="mt-1 text-sm font-bold">대한류마티스학회 진료 가이드라인</p>
                  <p className="text-xs text-muted-foreground">업데이트: 2026.05.15</p>
                </Card>
              </>
            ) : (
              <ul className="space-y-2">
                {(content[tab] as string[]).map((item, i) => (
                  <li key={i} className="flex gap-2 rounded-xl border border-border p-3 text-sm leading-relaxed">
                    <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: color }} />
                    {item}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <p className="text-center text-xs text-muted-foreground leading-relaxed">
            본 정보는 일반 안내용이며 의료적 진단·처방을 대체하지 않습니다.
          </p>
        </>
      )}
    </main>
  );
}
