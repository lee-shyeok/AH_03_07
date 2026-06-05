"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, ChevronDown, Pill, Check } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  getNotificationSettings,
  updateNotificationSettings,
  type NotificationSettings,
} from "@/features/notifications/api";

const DRUG = { name: "메토트렉세이트 7.5mg", type: "자가면역" };

const REPEAT_OPTIONS = [
  { value: "daily", label: "매일" },
  { value: "weekly_mon", label: "매주 월요일" },
  { value: "weekly_tue", label: "매주 화요일" },
  { value: "weekly_wed", label: "매주 수요일" },
  { value: "weekly_thu", label: "매주 목요일" },
  { value: "weekly_fri", label: "매주 금요일" },
  { value: "weekly_sat", label: "매주 토요일" },
  { value: "weekly_sun", label: "매주 일요일" },
];

function formatTime(value: string | null | undefined): string {
  if (!value) return formatTime("09:00");
  const [h, m] = value.split(":").map(Number);
  const ampm = h < 12 ? "오전" : "오후";
  const h12 = h === 0 ? 12 : h > 12 ? h - 12 : h;
  return `${ampm} ${String(h12).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

// --- sub-components ---

function Toggle({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      role="switch"
      aria-checked={on}
      onClick={() => onChange(!on)}
      className={"relative h-6 w-11 flex-shrink-0 rounded-full transition-colors " + (on ? "bg-primary" : "bg-muted")}
    >
      <span
        className={
          "absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform " +
          (on ? "translate-x-5" : "translate-x-0.5")
        }
      />
    </button>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return <p className="mt-6 mb-2 text-sm font-semibold text-muted-foreground">{children}</p>;
}

function ToggleRow({
  label,
  description,
  on,
  onChange,
}: {
  label: string;
  description?: string;
  on: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-start justify-between gap-3 px-4 py-3">
      <div className="min-w-0">
        <p className="text-sm font-medium leading-snug">{label}</p>
        {description && <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>}
      </div>
      <Toggle on={on} onChange={onChange} />
    </div>
  );
}

function CheckRow({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className="flex w-full items-center gap-3 px-4 py-3 text-left"
    >
      <span
        className={
          "flex h-5 w-5 flex-shrink-0 items-center justify-center rounded border-2 transition-colors " +
          (checked ? "border-primary bg-primary" : "border-border bg-background")
        }
      >
        {checked && <Check className="h-3 w-3 text-white" strokeWidth={3} />}
      </span>
      <span className="text-sm font-medium">{label}</span>
    </button>
  );
}

const FALLBACK_SETTINGS: NotificationSettings = {
  enabled: true,
  time: "09:00",
  repeat: "weekly_fri",
  early_reminder: true,
  missed_reminder: true,
  location_record: false,
  channels: { app: true, kakao: true, email: false },
};

// --- page ---

export default function NotificationSettingsPage() {
  const router = useRouter();
  const timeInputRef = useRef<HTMLInputElement>(null);

  const [alertOn, setAlertOn] = useState(FALLBACK_SETTINGS.enabled);
  const [alertTime, setAlertTime] = useState(FALLBACK_SETTINGS.time);
  const [repeat, setRepeat] = useState(FALLBACK_SETTINGS.repeat);
  const [repeatOpen, setRepeatOpen] = useState(false);
  const [earlyReminder, setEarlyReminder] = useState(FALLBACK_SETTINGS.early_reminder);
  const [missedReminder, setMissedReminder] = useState(FALLBACK_SETTINGS.missed_reminder);
  const [locationRecord, setLocationRecord] = useState(FALLBACK_SETTINGS.location_record);
  const [channels, setChannels] = useState<{ app: boolean; kakao: boolean; email: boolean }>(
    FALLBACK_SETTINGS.channels
  );
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getNotificationSettings()
      .then((s) => {
        setAlertOn(s.enabled);
        setAlertTime(s.time);
        setRepeat(s.repeat);
        setEarlyReminder(s.early_reminder);
        setMissedReminder(s.missed_reminder);
        setLocationRecord(s.location_record);
        setChannels(s.channels ?? FALLBACK_SETTINGS.channels);
      })
      .catch(() => {
        // API 실패 시 fallback 유지
      })
      .finally(() => setLoading(false));
  }, []);

  const repeatLabel = REPEAT_OPTIONS.find((o) => o.value === repeat)?.label ?? "매주 금요일";

  function toggleChannel(key: keyof typeof channels) {
    setChannels((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  async function handleSave() {
    setSaving(true);
    try {
      await updateNotificationSettings({
        enabled: alertOn,
        time: alertTime,
        repeat,
        early_reminder: earlyReminder,
        missed_reminder: missedReminder,
        location_record: locationRecord,
        channels,
      });
    } catch {
      // API 실패 시 무시하고 뒤로 이동
    } finally {
      setSaving(false);
      router.back();
    }
  }

  if (loading) {
    return (
      <main className="mx-auto flex w-full max-w-md items-center justify-center py-20">
        <p className="text-sm text-muted-foreground">설정을 불러오는 중...</p>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-6 pb-28">
      {/* 헤더 */}
      <div className="flex items-center gap-2">
        <button onClick={() => router.back()} className="p-1 text-foreground">
          <ChevronLeft className="h-6 w-6" />
        </button>
        <h1 className="text-lg font-bold">복약 알림 설정</h1>
      </div>

      {/* 약품 카드 */}
      <Card className="mt-5 flex items-center gap-3 p-4">
        <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-full bg-[#F0E8FF]">
          <Pill className="h-5 w-5 text-[#7C5CCF]" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold leading-snug">{DRUG.name}</p>
          <span className="mt-1 inline-block rounded-full bg-[#F0E8FF] px-2 py-0.5 text-xs font-medium text-[#7C5CCF]">
            {DRUG.type}
          </span>
        </div>
      </Card>

      {/* 알림 설정 */}
      <SectionLabel>알림 설정</SectionLabel>
      <Card className="divide-y divide-border">
        <ToggleRow label="알림 받기" on={alertOn} onChange={setAlertOn} />

        {/* 알림 시간 */}
        <div className="flex items-center justify-between px-4 py-3">
          <p className="text-sm font-medium">알림 시간</p>
          <div className="relative flex items-center">
            <button
              onClick={() => timeInputRef.current?.showPicker?.()}
              className="text-sm font-semibold text-primary"
            >
              {formatTime(alertTime)}
            </button>
            <input
              ref={timeInputRef}
              type="time"
              value={alertTime}
              onChange={(e) => setAlertTime(e.target.value)}
              className="absolute right-0 h-0 w-0 overflow-hidden opacity-0"
            />
          </div>
        </div>

        {/* 반복 */}
        <div className="relative px-4 py-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">반복</p>
            <button
              onClick={() => setRepeatOpen((v) => !v)}
              className="flex items-center gap-0.5 text-sm font-semibold text-primary"
            >
              {repeatLabel}
              <ChevronDown className={"h-4 w-4 transition-transform " + (repeatOpen ? "rotate-180" : "")} />
            </button>
          </div>
          {repeatOpen && (
            <div className="absolute right-4 top-full z-10 mt-1 w-44 overflow-hidden rounded-xl border border-border bg-card shadow-lg">
              {REPEAT_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => { setRepeat(opt.value); setRepeatOpen(false); }}
                  className={
                    "flex w-full items-center justify-between px-4 py-2.5 text-sm " +
                    (opt.value === repeat ? "font-semibold text-primary" : "text-foreground hover:bg-muted")
                  }
                >
                  {opt.label}
                  {opt.value === repeat && <Check className="h-4 w-4" />}
                </button>
              ))}
            </div>
          )}
        </div>
      </Card>

      {/* 알림 옵션 */}
      <SectionLabel>알림 옵션</SectionLabel>
      <Card className="divide-y divide-border">
        <ToggleRow
          label="5분 전 미리 알림"
          description="복용 시간 5분 전 추가 알림"
          on={earlyReminder}
          onChange={setEarlyReminder}
        />
        <ToggleRow
          label="미복용 시 재알림"
          description="30분 후 재알림"
          on={missedReminder}
          onChange={setMissedReminder}
        />
      </Card>

      {/* 알림 채널 */}
      <SectionLabel>알림 채널</SectionLabel>
      <Card className="divide-y divide-border">
        <CheckRow label="앱 푸시" checked={channels.app} onChange={() => toggleChannel("app")} />
        <CheckRow label="카카오톡" checked={channels.kakao} onChange={() => toggleChannel("kakao")} />
        <CheckRow label="이메일" checked={channels.email} onChange={() => toggleChannel("email")} />
      </Card>

      {/* REQ-NOTI-008: 위치 기록 */}
      <SectionLabel>위치 기록</SectionLabel>
      <Card className="divide-y divide-border">
        <ToggleRow
          label="복약 위치 기록"
          description="복용 완료 시 현재 위치를 함께 기록합니다"
          on={locationRecord}
          onChange={setLocationRecord}
        />
      </Card>

      {/* 저장 버튼 */}
      <div className="fixed bottom-0 left-1/2 w-full max-w-md -translate-x-1/2 bg-background px-5 py-4">
        <Button
          onClick={handleSave}
          disabled={saving}
          className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
        >
          {saving ? "저장 중..." : "저장하기"}
        </Button>
      </div>
    </main>
  );
}
