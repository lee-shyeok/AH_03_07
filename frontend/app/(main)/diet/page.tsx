"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, Loader2, AlertCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { getDietInfo, type DietInfoResponse, type FoodCategory } from "@/features/diet/api";

// ─── 상수 ─────────────────────────────────────────────────────────────────────

type DiseaseCategory = "autoimmune" | "chronic";

const DISEASE_GROUPS: Record<DiseaseCategory, { code: string; label: string }[]> = {
  autoimmune: [
    { code: "RA",  label: "류마티스 관절염" },
    { code: "SLE", label: "루푸스" },
  ],
  chronic: [
    { code: "DM1",          label: "1형 당뇨" },
    { code: "DM2",          label: "2형 당뇨" },
    { code: "HTN",          label: "고혈압" },
    { code: "HYPERLIPIDEMIA", label: "고지혈증" },
    { code: "ASTHMA",       label: "천식" },
    { code: "COPD",         label: "만성폐쇄성폐질환" },
    { code: "PARKINSON",    label: "파킨슨병" },
    { code: "MS",           label: "다발성 경화증" },
    { code: "BREAST_CANCER", label: "유방암" },
    { code: "COLON_CANCER", label: "대장암" },
    { code: "LUNG_CANCER",  label: "폐암" },
  ],
};

const CODE_TO_LABEL: Record<string, string> = Object.fromEntries(
  Object.values(DISEASE_GROUPS)
    .flat()
    .map((d) => [d.code, d.label])
);

const FOOD_TABS: { key: FoodCategory; label: string; emoji: string }[] = [
  { key: "MEAT",      label: "고기류",   emoji: "🥩" },
  { key: "FISH",      label: "생선류",   emoji: "🐟" },
  { key: "VEGETABLE", label: "채소류",   emoji: "🥦" },
  { key: "FRUIT",     label: "과일류",   emoji: "🍎" },
  { key: "GRAIN",     label: "곡물류",   emoji: "🌾" },
  { key: "DAIRY",     label: "유제품류", emoji: "🥛" },
];

const HEALTH_TIPS: { title: string; items: string[] }[] = [
  {
    title: "GI 지수 (혈당 지수)",
    items: [
      "음식을 먹었을 때 혈당이 얼마나 빠르게 오르는지를 0~100으로 나타낸 수치예요.",
      "55 이하 → 저GI: 현미·귀리·콩류처럼 혈당을 천천히 올려요.",
      "56~69 → 중GI: 바나나·파인애플 등 적당한 속도로 올라요.",
      "70 이상 → 고GI: 흰쌀밥·흰식빵·떡처럼 혈당이 빠르게 올라가요.",
      "당뇨·비만 예방을 위해 저GI 식품 위주로 식단을 구성하는 게 좋아요.",
    ],
  },
  {
    title: "나트륨 vs 소금",
    items: [
      "소금(NaCl)은 나트륨과 염소로 이루어진 화합물이에요.",
      "소금 1g 속에 나트륨은 약 400mg 들어있어요.",
      "하루 나트륨 권장량은 2,000mg(소금 5g)이에요.",
      "나트륨이 과다하면 혈액 속 수분이 늘어나 혈압이 오르고 심장·신장에 부담이 커져요.",
      "가공식품·김치·젓갈에는 '숨은 나트륨'이 많아요 — 영양성분표를 확인하세요.",
    ],
  },
  {
    title: "오메가3 vs 오메가6",
    items: [
      "둘 다 우리 몸에서 스스로 만들 수 없어 음식으로 꼭 섭취해야 하는 필수 지방산이에요.",
      "오메가3 (EPA·DHA·ALA): 염증을 줄이고 혈중 중성지방을 낮춰줘요. 고등어·연어·아마씨에 풍부해요.",
      "오메가6 (리놀레산): 세포막 구성에 필요하지만 과다 섭취 시 염증 반응을 촉진할 수 있어요. 식용유·견과류에 많아요.",
      "이상적인 오메가3:6 섭취 비율은 1:4 이내예요. 현대 식단은 보통 1:15~20으로 오메가6가 훨씬 많아요.",
      "오메가3를 늘리고 오메가6(식용유·튀김)를 줄이는 방향으로 식단을 조정하세요.",
    ],
  },
  {
    title: "포화지방 vs 불포화지방",
    items: [
      "포화지방: 상온에서 고체. 버터·삼겹살·코코넛오일 등 동물성 식품에 많아요. 과다 섭취 시 LDL(나쁜 콜레스테롤)을 올려요.",
      "단일불포화지방: 올리브오일·아보카도에 풍부. LDL을 낮추고 HDL(좋은 콜레스테롤)을 유지해줘요.",
      "다가불포화지방: 오메가3·오메가6가 여기에 해당해요. 생선·견과류·씨앗류에 많아요.",
      "트랜스지방: 식물성 기름을 고온 가공할 때 생겨요. LDL은 올리고 HDL은 낮추는 가장 나쁜 지방이에요. 마가린·튀김류에 주의하세요.",
      "건강한 지방(불포화지방)으로 나쁜 지방(포화·트랜스)을 대체하는 게 핵심이에요.",
    ],
  },
];

// ─── 서브 컴포넌트 ─────────────────────────────────────────────────────────────

function FoodCard({
  item,
  variant,
}: {
  item: DietInfoResponse;
  variant: "recommend" | "avoid";
}) {
  const rec = variant === "recommend";
  const hasTerms = item.terms && item.terms.length > 0;
  return (
    <div
      className={
        "rounded-xl border p-4 " +
        (rec ? "border-emerald-200 bg-emerald-50" : "border-red-200 bg-red-50")
      }
    >
      <p className={"font-semibold " + (rec ? "text-emerald-800" : "text-red-800")}>
        {rec ? "✅" : "❌"} {item.food_name}
      </p>
      <p className={"mt-1 text-sm leading-relaxed " + (rec ? "text-emerald-700" : "text-red-700")}>
        {item.reason}
      </p>
      {hasTerms && (
        <div
          className={
            "mt-3 border-t border-dashed pt-2.5 " +
            (rec ? "border-emerald-200" : "border-red-200")
          }
        >
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            💡 관련 용어
          </p>
          <ul className="space-y-0.5">
            {item.terms!.map((term, i) => (
              <li key={i} className="text-[11px] leading-snug text-muted-foreground">
                {term}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function DiseaseCategoryButton({
  cat,
  active,
  onClick,
}: {
  cat: DiseaseCategory;
  active: boolean;
  onClick: () => void;
}) {
  const [showTooltip, setShowTooltip] = useState(false);
  const label = cat === "autoimmune" ? "자가면역 질환" : "만성 질환";

  return (
    <div
      className="relative"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <button
        onClick={onClick}
        className={
          "w-full rounded-2xl border-2 py-5 text-sm font-bold transition-colors " +
          (active
            ? "border-primary bg-primary text-primary-foreground"
            : "border-border bg-card text-foreground hover:border-primary/50")
        }
      >
        {label}
      </button>
      {showTooltip && (
        <div className="absolute left-1/2 top-full z-20 mt-2 w-44 -translate-x-1/2 rounded-xl border border-border bg-popover px-3 py-2.5 shadow-md">
          <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            포함 질환
          </p>
          <ul className="space-y-1">
            {DISEASE_GROUPS[cat].map((d) => (
              <li key={d.code} className="text-xs text-foreground">
                {d.label}
              </li>
            ))}
          </ul>
          {/* 말풍선 꼭지 */}
          <div className="absolute -top-1.5 left-1/2 h-3 w-3 -translate-x-1/2 rotate-45 border-l border-t border-border bg-popover" />
        </div>
      )}
    </div>
  );
}

const NUTRITION_BASICS: { label: string; desc: string }[] = [
  { label: "칼로리", desc: "몸이 쓰는 에너지 단위. 성인 기준 하루 2,000kcal 참고." },
  { label: "탄수화물", desc: "주 에너지원. 뇌·근육 연료. 정제 탄수화물은 줄이는 게 좋아요." },
  { label: "단백질", desc: "근육·효소·면역 물질을 만드는 재료. 체중 1kg당 0.8~1g 섭취 참고." },
  { label: "지방", desc: "호르몬·세포막 구성 재료. 포화·트랜스지방은 줄이고 불포화지방 위주로." },
  { label: "나트륨", desc: "혈압 조절에 관여. 하루 2,000mg 이하 참고. 가공식품에 주의." },
];

function HealthTipAccordion() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <div className="mt-8">
      <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        건강 상식
      </p>
      <div className="flex gap-3">
        {/* 왼쪽: 버튼 목록 */}
        <div className="flex shrink-0 flex-col gap-2" style={{ width: "42%" }}>
          {HEALTH_TIPS.map((tip, i) => {
            const isOpen = openIndex === i;
            return (
              <button
                key={tip.title}
                onClick={() => setOpenIndex((prev) => (prev === i ? null : i))}
                className={
                  "w-full rounded-2xl border-2 py-5 text-sm font-bold transition-colors " +
                  (isOpen
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border bg-card text-foreground hover:border-primary/50")
                }
              >
                {tip.title}
              </button>
            );
          })}
        </div>

        {/* 오른쪽: 내용 패널 */}
        <div className="min-w-0 flex-1">
          {openIndex === null ? (
            /* 기본 상태: 영양성분표 */
            <div className="rounded-2xl border-2 border-border bg-card px-4 py-3">
              <p className="mb-2.5 text-xs font-semibold text-muted-foreground">영양성분 기초</p>
              <ul className="space-y-2.5">
                {NUTRITION_BASICS.map((n) => (
                  <li key={n.label}>
                    <p className="text-xs font-semibold text-foreground">{n.label}</p>
                    <p className="mt-0.5 text-[11px] leading-snug text-muted-foreground">{n.desc}</p>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            /* 선택 상태: 해당 항목 설명 */
            <div className="rounded-2xl border-2 border-primary/30 bg-card px-4 py-3">
              <p className="mb-2.5 text-xs font-semibold text-primary">
                {HEALTH_TIPS[openIndex].title}
              </p>
              <ul className="space-y-2">
                {HEALTH_TIPS[openIndex].items.map((item, j) => (
                  <li key={j} className="flex gap-1.5">
                    <span className="mt-0.5 shrink-0 text-[10px] text-primary">—</span>
                    <span className="text-[11px] leading-snug text-muted-foreground">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── 메인 페이지 ───────────────────────────────────────────────────────────────

export default function DietPage() {
  const router = useRouter();

  const [diseaseCategory, setDiseaseCategory] = useState<DiseaseCategory | null>(null);
  const [diseaseCode, setDiseaseCode] = useState<string | null>(null);
  const [foodTab, setFoodTab] = useState<FoodCategory>("MEAT");

  function handleDiseaseCategory(cat: DiseaseCategory) {
    setDiseaseCategory(cat);
    setDiseaseCode(null);
    setFoodTab("MEAT");
  }

  function handleDiseaseCode(code: string) {
    setDiseaseCode(code);
    setFoodTab("MEAT");
  }

  const { data, isLoading, isError } = useQuery({
    queryKey: ["diet-info", diseaseCode],
    queryFn: () => getDietInfo(diseaseCode ?? undefined),
    enabled: diseaseCode !== null,
    staleTime: 5 * 60 * 1000,
  });

  const inTab = (data ?? []).filter((d) => d.food_category === foodTab);
  const recommended = inTab.filter((d) => d.category === "RECOMMEND");
  const avoided = inTab.filter((d) => d.category === "AVOID");

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8 pb-10">
      {/* ── 헤더 ── */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => router.back()}
          className="rounded-full p-1 text-foreground hover:bg-muted"
        >
          <ChevronLeft className="h-6 w-6" />
        </button>
        <h1 className="text-2xl font-bold">식이 정보</h1>
      </div>

      {/* ── 1단계: 질환 유형 버튼 ── */}
      <div className="mt-6 grid grid-cols-2 gap-3">
        {(["autoimmune", "chronic"] as DiseaseCategory[]).map((cat) => (
          <DiseaseCategoryButton
            key={cat}
            cat={cat}
            active={diseaseCategory === cat}
            onClick={() => handleDiseaseCategory(cat)}
          />
        ))}
      </div>

      {/* ── 2단계: 질환 목록 ── */}
      {diseaseCategory && (
        <div className="mt-5">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            질환 선택
          </p>
          <div className="flex flex-wrap gap-2">
            {DISEASE_GROUPS[diseaseCategory].map((d) => (
              <button
                key={d.code}
                onClick={() => handleDiseaseCode(d.code)}
                className={
                  "rounded-full border px-4 py-2 text-sm font-medium transition-colors " +
                  (diseaseCode === d.code
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border text-foreground hover:border-primary hover:text-primary")
                }
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── 3단계: 식품 카테고리별 식이 정보 ── */}
      {diseaseCode && (
        <>
          {/* 질환명 소제목 */}
          <div className="mt-6 flex items-center justify-between">
            <p className="text-base font-bold">
              {CODE_TO_LABEL[diseaseCode]} 식이 안내
            </p>
          </div>

          {/* 식품 카테고리 탭 */}
          <div className="mt-3 flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
            {FOOD_TABS.map((fc) => (
              <button
                key={fc.key}
                onClick={() => setFoodTab(fc.key)}
                className={
                  "shrink-0 rounded-full px-3 py-2 text-sm font-medium transition-colors " +
                  (foodTab === fc.key
                    ? "bg-primary text-primary-foreground"
                    : "border border-border text-foreground hover:border-primary/50")
                }
              >
                {fc.emoji} {fc.label}
              </button>
            ))}
          </div>

          {/* 로딩 */}
          {isLoading && (
            <div className="mt-12 flex justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          )}

          {/* 에러 */}
          {isError && (
            <Card className="mt-5">
              <CardContent className="flex items-center gap-3 py-5">
                <AlertCircle className="h-5 w-5 shrink-0 text-destructive" />
                <p className="text-sm text-muted-foreground">
                  식이 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.
                </p>
              </CardContent>
            </Card>
          )}

          {/* 추천·제한 카드 */}
          {!isLoading && !isError && (
            <div className="mt-4 flex flex-col gap-3">
              {recommended.length === 0 && avoided.length === 0 ? (
                <p className="py-8 text-center text-sm text-muted-foreground">
                  해당 카테고리의 식이 정보가 없습니다.
                </p>
              ) : (
                <>
                  {recommended.map((item) => (
                    <FoodCard key={item.id} item={item} variant="recommend" />
                  ))}
                  {avoided.map((item) => (
                    <FoodCard key={item.id} item={item} variant="avoid" />
                  ))}
                </>
              )}
            </div>
          )}
        </>
      )}

      {/* ── 건강 상식 아코디언 ── */}
      <HealthTipAccordion />

      {/* ── 면책 문구 ── */}
      <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
        <p className="text-sm text-amber-800">
          ⚠ 본 정보는 참고용입니다. 담당 의료진과 상담하세요.
        </p>
      </div>
    </main>
  );
}
