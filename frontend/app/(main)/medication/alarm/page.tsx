"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Pill, Check, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useMedications } from "@/features/medication/queries";
import { DRUG_CLASS_LABEL } from "@/features/medication/schema";
import { getMode } from "@/features/auth/mode";

const GREEN = "#03C85F";
const PURPLE = "#7C5CCF";

function Toggle({ on, onChange, accent }: { on: boolean; onChange: (v: boolean) => void; accent: string }) {
  return (
    <button
      role="switch"
      aria-checked={on}
      onClick={() => onChange(!on)}
      className="relative h-6 w-11 rounded-full transition-colors"
      style={{ background: on ? accent : "hsl(var(--muted))" }}
    >
      <span className={"absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform " + (on ? "translate-x-5" : "translate-x-0.5")} />
    </button>
  );
}

export default function MedicationAlarmPage() {
  const router = useRouter();
  const { data: meds = [] } = useMedications();
  const med = meds[0] ?? null;

  const isAutoimmune = getMode() === "autoimmune";
  const accent = isAutoimmune ? PURPLE : GREEN;

  const [enabled, setEnabled] = useState(true);
  const [preAlert, setPreAlert] = useState(true);
  const [reAlert, setReAlert] = useState(true);
  const [channels, setChannels] = useState({ push: true, kakao: true, email: false });
  const [saved, setSaved] = useState(false);

  function save() {
    setSaved(true);
    setTimeout(() => router.back(), 800);
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8 pb-28">
      <h1 className="text-2xl font-bold">복약 알림 설정</h1>

      {/* 약품 헤더 */}
      <Card className="mt-5 flex items-center gap-3 p-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl" style={{ background: accent + "20" }}>
          <Pill className="h-6 w-6" style={{ color: accent }} />
        </div>
        <div>
          <p className="font-bold">{med?.name ?? "등록된 약물 없음"}</p>
          {(med?.drug_class || isAutoimmune) && (
            <span className="mt-1 inline-block rounded-full px-2 py-0.5 text-[11px] font-bold text-white" style={{ background: accent }}>
              {med?.drug_class ? (DRUG_CLASS_LABEL[med.drug_class] ?? med.drug_class) : isAutoimmune ? "자가면역" : "일반"}
            </span>
          )}
        </div>
      </Card>

      {/* 알림 설정 */}
      <p className="mt-6 text-sm text-muted-foreground">알림 설정</p>
      <Card className="mt-2 divide-y divide-border">
        <div className="flex items-center justify-between px-4 py-3.5">
          <span className="text-sm">알림 받기</span>
          <Toggle on={enabled} onChange={setEnabled} accent={accent} />
        </div>
        <div className="flex items-center justify-between px-4 py-3.5">
          <span className="text-sm">알림 시간</span>
          <span className="text-sm font-semibold text-primary">오전 09:00</span>
        </div>
        <div className="flex items-center justify-between px-4 py-3.5">
          <span className="text-sm">반복</span>
          <span className="flex items-center gap-1 text-sm font-semibold text-primary">
            매주 금요일 <ChevronDown className="h-4 w-4" />
          </span>
        </div>
      </Card>

      {/* 알림 옵션 */}
      <p className="mt-6 text-sm text-muted-foreground">알림 옵션</p>
      <Card className="mt-2 divide-y divide-border">
        <div className="flex items-center justify-between px-4 py-3.5">
          <div>
            <p className="text-sm">5분 전 미리 알림</p>
            <p className="text-xs text-muted-foreground">복용 시간 5분 전 추가 알림</p>
          </div>
          <Toggle on={preAlert} onChange={setPreAlert} accent={accent} />
        </div>
        <div className="flex items-center justify-between px-4 py-3.5">
          <div>
            <p className="text-sm">미복용 시 재알림</p>
            <p className="text-xs text-muted-foreground">30분 후 재알림</p>
          </div>
          <Toggle on={reAlert} onChange={setReAlert} accent={accent} />
        </div>
      </Card>

      {/* 알림 채널 */}
      <p className="mt-6 text-sm text-muted-foreground">알림 채널</p>
      <Card className="mt-2 divide-y divide-border">
        {([
          ["push", "앱 푸시"],
          ["kakao", "카카오톡"],
          ["email", "이메일"],
        ] as const).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setChannels((c) => ({ ...c, [key]: !c[key] }))}
            className="flex w-full items-center justify-between px-4 py-3.5"
          >
            <span className="text-sm">{label}</span>
            {channels[key] ? (
              <Check className="h-5 w-5 text-primary" />
            ) : (
              <span className="h-5 w-5 rounded border-2 border-muted-foreground/30" />
            )}
          </button>
        ))}
      </Card>

      <div className="fixed inset-x-0 bottom-16 mx-auto max-w-md px-5">
        <Button className="w-full" size="lg" disabled={saved} onClick={save}>{saved ? "저장됨 ✓" : "저장하기"}</Button>
      </div>
    </main>
  );
}
