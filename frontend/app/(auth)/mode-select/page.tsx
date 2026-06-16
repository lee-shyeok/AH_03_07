"use client";

import { useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight } from "lucide-react";
import Image from "next/image";
import { getAutoimmuneOnboarding, updateMode } from "@/features/auth/api";
import { updateConsent } from "@/features/consent/api";
import { setMode } from "@/features/auth/mode";
import { withTimeout } from "@/lib/query/util";

const GREEN = "#03C85F";
const PURPLE = "#A83AC1";

type Mode = "general" | "autoimmune";

export default function ModeSelectPage() {
  const router = useRouter();

  async function select(mode: Mode) {
    // 로컬 즉시 저장
    setMode(mode);
    // 백엔드 모드 동기화는 백그라운드 (실패·지연해도 이동 차단 없음)
    updateMode(mode).catch(() => {});

    if (mode === "autoimmune") {
      try {
        // 타임아웃 3초 — 응답 없으면 consent 화면으로 바로 이동
        const s = await withTimeout(getAutoimmuneOnboarding(), 3000);
        if (s.completed) {
          router.replace("/home");
        } else if (!s.consent_done) {
          router.replace("/mode-consent");
        } else if (!s.disease_done) {
          router.replace("/disease/new");
        } else if (!s.risk_profile_done) {
          router.replace("/risk-profile");
        } else {
          router.replace("/home");
        }
      } catch {
        router.replace("/mode-consent");
      }
      return;
    }
    // 일반 모드도 MEDICAL_DATA 동의 설정 (건강수치 등 API 403 방지)
    updateConsent("sensitive_medical", true).catch(() => {});
    router.replace("/home");
  }

  const cards: { key: Mode; title: string; lines: string[]; color: string; image: string }[] = [
    { key: "general", title: "일반 환자", lines: ["복약 관리", "일반 의료 정보"], color: GREEN, image: "/mode-select/person-general.png" },
    { key: "autoimmune", title: "자가면역환자", lines: ["활성도 추적", "면역약물 특화 정보"], color: PURPLE, image: "/mode-select/person-auto.png" },
  ];

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col px-6 pb-10 pt-12">
      <button onClick={() => router.back()} aria-label="뒤로" className="-ml-2 w-fit">
        <ChevronLeft className="h-7 w-7" />
      </button>

      <h1 className="mt-6 text-[32px] font-extrabold leading-tight">
        어떤 도움이<br />필요하신가요?
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">맞춤 가이드를 제공해드릴게요</p>

      <div className="mt-12 flex flex-col gap-[18px]">
        {cards.map((c) => (
          <button
            key={c.key}
            onClick={() => select(c.key)}
            className="flex w-full items-center gap-4 rounded-2xl border-2 bg-card p-5 text-left transition-colors"
            style={{ borderColor: c.color }}
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-full" style={{ background: c.color + "1f" }}>
              <Image src={c.image} alt={c.title} width={50} height={50} />
            </div>
            <div className="flex-1">
              <p className="text-[22px] font-semibold" style={{ color: c.color }}>{c.title}</p>
              {c.lines.map((l) => (
                <p key={l} className="text-base font-normal text-muted-foreground">{l}</p>
              ))}
            </div>
            <ChevronRight className="h-6 w-6 shrink-0" style={{ color: c.color }} />
          </button>
        ))}
      </div>

      <div className="mt-auto flex justify-center pt-8">
        <button onClick={() => select("general")} className="text-sm text-muted-foreground">
          나중에 선택할게요
        </button>
      </div>
    </main>
  );
}
