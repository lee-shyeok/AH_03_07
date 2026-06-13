"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, ChevronDown, Pill, Check, PlusCircle } from "lucide-react";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { TimePicker } from "@/components/ui/TimePicker";
import {
  getNotificationSettings,
  updateNotificationSettings,
  type NotificationSettings,
} from "@/features/notifications/api";
import { useMedications } from "@/features/medication/queries";
import { DRUG_CLASS_LABEL } from "@/features/medication/schema";
import { getMode } from "@/features/auth/mode";

const GREEN = "#03C85F";
const PURPLE = "#7C5CCF";

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

// ── Sub-components ──────────────────────────────────────────

function Toggle({
  on,
  onChange,
  accent,
}: {
  on: boolean;
  onChange: (v: boolean) => void;
  accent: string;
}) {
  return (
    <button
      role="switch"
      aria-checked={on}
      onClick={() => onChange(!on)}
      className="relative h-6 w-11 flex-shrink-0 rounded-full transition-colors"
      style={{ background: on ? accent : "hsl(var(--muted))" }}
    >
      <span
        className="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform"
        style={{ transform: on ? "translateX(20px)" : "translateX(2px)" }}
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
  accent,
}: {
  label: string;
  description?: string;
  on: boolean;
  onChange: (v: boolean) => void;
  accent: string;
}) {
  return (
    <div className="flex items-start justify-between gap-3 px-4 py-3">
      <div className="min-w-0">
        <p className="text-sm font-medium leading-snug">{label}</p>
        {description && (
          <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
        )}
      </div>
      <Toggle on={on} onChange={onChange} accent={accent} />
    </div>
  );
}

function CheckRow({
  label,
  checked,
  onChange,
  accent,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  accent: string;
}) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className="flex w-full items-center gap-3 px-4 py-3 text-left"
    >
      <span
        className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded border-2 transition-colors"
        style={
          checked
            ? { borderColor: accent, background: accent }
            : { borderColor: "hsl(var(--border))", background: "hsl(var(--background))" }
        }
      >
        {checked && <Check className="h-3 w-3 text-white" strokeWidth={3} />}
      </span>
      <span className="text-sm font-medium">{label}</span>
    </button>
  );
}

const DEFAULT_TIMING_TIMES = { morning: "08:00", afternoon: "12:00", evening: "18:00", bedtime: "22:00" };
const DEFAULT_QUIET_HOURS = { enabled: false, start: "22:00", end: "07:00" };
const DEFAULT_CHANNELS = { app: false, kakao: false, email: false };

// ── Page ─────────────────────────────────────────────────────

export default function NotificationSettingsPage() {
  const router = useRouter();

  // SSR 하이드레이션 불일치 방지
  const [accent, setAccent] = useState(GREEN);
  useEffect(() => {
    setAccent(getMode() === "autoimmune" ? PURPLE : GREEN);
  }, []);
  const isAutoimmune = accent === PURPLE;

  // 약물 목록
  const { data: meds = [], isLoading: medsLoading } = useMedications();
  const [selectedMedId, setSelectedMedId] = useState<number | null>(null);

  useEffect(() => {
    if (meds.length > 0 && selectedMedId === null) {
      setSelectedMedId(meds[0].id);
    }
  }, [meds, selectedMedId]);

  const selectedMed = meds.find((m) => m.id === selectedMedId) ?? meds[0] ?? null;

  // 알림 설정 상태
  const [alertOn, setAlertOn] = useState(false);
  const [alertTime, setAlertTime] = useState("09:00");
  const [repeat, setRepeat] = useState("daily");
  const [repeatOpen, setRepeatOpen] = useState(false);
  const [earlyReminder, setEarlyReminder] = useState(false);
  const [missedReminder, setMissedReminder] = useState(false);
  const [locationRecord, setLocationRecord] = useState(false);
  const [channels, setChannels] = useState<{ app: boolean; kakao: boolean; email: boolean }>(
    DEFAULT_CHANNELS
  );
  const [timingTimes, setTimingTimes] = useState(DEFAULT_TIMING_TIMES);
  const [quietHours, setQuietHours] = useState(DEFAULT_QUIET_HOURS);
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
        setChannels(s.channels ?? DEFAULT_CHANNELS);
        if (s.timing_times) setTimingTimes({ ...DEFAULT_TIMING_TIMES, ...s.timing_times });
        if (s.quiet_hours) setQuietHours(s.quiet_hours);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const repeatLabel =
    REPEAT_OPTIONS.find((o) => o.value === repeat)?.label ?? "매주 금요일";

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
        timing_times: timingTimes,
        quiet_hours: quietHours,
      });
    } catch {
      // API 실패 시 무시
    } finally {
      setSaving(false);
      router.back();
    }
  }

  if (loading || medsLoading) {
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

      {/* 약물 없음 상태 */}
      {meds.length === 0 ? (
        <div className="mt-12 flex flex-col items-center gap-4 text-center">
          <Pill className="h-12 w-12 opacity-20" style={{ color: accent }} />
          <p className="text-sm text-muted-foreground">등록된 약물이 없습니다.</p>
          <Link
            href="/medication/new"
            className="flex items-center gap-1.5 rounded-xl px-5 py-2.5 text-sm font-bold text-white"
            style={{ background: accent }}
          >
            <PlusCircle className="h-4 w-4" />
            약물 등록하기
          </Link>
        </div>
      ) : (
        <>
          {/* 약물 탭 (2개 이상) */}
          {meds.length > 1 && (
            <div className="mt-5 flex gap-2 overflow-x-auto pb-1 scrollbar-none">
              {meds.map((m) => {
                const active = m.id === selectedMedId;
                return (
                  <button
                    key={m.id}
                    onClick={() => setSelectedMedId(m.id)}
                    className="flex-shrink-0 rounded-full px-4 py-2 text-sm font-semibold transition-colors"
                    style={
                      active
                        ? { background: accent, color: "#fff" }
                        : { background: accent + "18", color: accent }
                    }
                  >
                    {m.name}
                  </button>
                );
              })}
            </div>
          )}

          {/* 선택된 약물 카드 */}
          {selectedMed && (
            <Card className="mt-4 flex items-center gap-3 p-4">
              <div
                className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-full"
                style={{ background: accent + "20" }}
              >
                <Pill className="h-5 w-5" style={{ color: accent }} />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold leading-snug">{selectedMed.name}</p>
                <span
                  className="mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-medium"
                  style={{ background: accent + "20", color: accent }}
                >
                  {selectedMed.drug_class
                    ? (DRUG_CLASS_LABEL[selectedMed.drug_class] ?? selectedMed.drug_class)
                    : isAutoimmune ? "자가면역" : "일반"}
                </span>
              </div>
            </Card>
          )}

          {/* 알림 설정 */}
          <SectionLabel>알림 설정</SectionLabel>
          <Card className="divide-y divide-border">
            <ToggleRow label="알림 받기" on={alertOn} onChange={setAlertOn} accent={accent} />

            {/* 알림 시간 */}
            <div className="flex items-center justify-between px-4 py-2 min-h-[52px]">
              <p className="text-sm font-medium">알림 시간</p>
              <TimePicker value={alertTime} onChange={setAlertTime} accentColor={accent} />
            </div>

            {/* 반복 */}
            <div className="relative px-4 py-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">반복</p>
                <button
                  onClick={() => setRepeatOpen((v) => !v)}
                  className="flex items-center gap-0.5 text-sm font-semibold"
                  style={{ color: accent }}
                >
                  {repeatLabel}
                  <ChevronDown
                    className={"h-4 w-4 transition-transform " + (repeatOpen ? "rotate-180" : "")}
                  />
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
                        (opt.value === repeat ? "font-semibold" : "text-foreground hover:bg-muted")
                      }
                      style={opt.value === repeat ? { color: accent } : undefined}
                    >
                      {opt.label}
                      {opt.value === repeat && (
                        <Check className="h-4 w-4" style={{ color: accent }} />
                      )}
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
              accent={accent}
            />
            <ToggleRow
              label="미복용 시 재알림"
              description="30분 후 재알림"
              on={missedReminder}
              onChange={setMissedReminder}
              accent={accent}
            />
          </Card>

          {/* 알림 채널 */}
          <SectionLabel>알림 채널</SectionLabel>
          <Card className="divide-y divide-border">
            <CheckRow
              label="앱 푸시"
              checked={channels.app}
              onChange={() => toggleChannel("app")}
              accent={accent}
            />
            <CheckRow
              label="카카오톡"
              checked={channels.kakao}
              onChange={() => toggleChannel("kakao")}
              accent={accent}
            />
            <CheckRow
              label="이메일"
              checked={channels.email}
              onChange={() => toggleChannel("email")}
              accent={accent}
            />
          </Card>

          {/* 시간대별 알림 시간 */}
          <SectionLabel>시간대별 알림 시간</SectionLabel>
          <Card className="divide-y divide-border">
            {(
              [
                { key: "morning" as const, label: "아침" },
                { key: "afternoon" as const, label: "점심" },
                { key: "evening" as const, label: "저녁" },
                { key: "bedtime" as const, label: "취침 전" },
              ] as const
            ).map(({ key, label }) => (
              <div key={key} className="flex items-center justify-between px-4 py-2 min-h-[52px]">
                <p className="text-sm font-medium">{label}</p>
                <TimePicker
                  value={timingTimes[key] ?? "08:00"}
                  onChange={(v) => setTimingTimes((prev) => ({ ...prev, [key]: v }))}
                  accentColor={accent}
                />
              </div>
            ))}
          </Card>

          {/* 알림 본문 미리보기 */}
          <SectionLabel>알림 본문 미리보기</SectionLabel>
          <Card className="p-4 space-y-2">
            <div className="rounded-xl bg-muted p-3 text-sm leading-relaxed">
              <p className="font-semibold" style={{ color: accent }}>
                {selectedMed?.name ?? "약품명"}님, [아침] 복약 시간입니다.
              </p>
              <p className="mt-1 text-muted-foreground">
                등록하신 약품: {selectedMed?.name ?? "메토트렉세이트 10mg"} 1정
              </p>
            </div>
            <p className="text-xs text-muted-foreground">
              본 알림은 사용자가 등록한 정보를 그대로 표시합니다 (앱 복약지도 아님)
            </p>
          </Card>

          {/* 방해 금지 시간 */}
          <SectionLabel>방해 금지 시간 (Quiet Hours)</SectionLabel>
          <Card className="divide-y divide-border">
            <ToggleRow
              label="방해 금지 시간 사용"
              description="해당 시간대에는 알림을 보내지 않습니다"
              on={quietHours.enabled}
              onChange={(v) => setQuietHours((prev) => ({ ...prev, enabled: v }))}
              accent={accent}
            />
            {quietHours.enabled && (
              <div className="px-4 py-3 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium">시작 시간</p>
                  <TimePicker
                    value={quietHours.start}
                    onChange={(v) => setQuietHours((prev) => ({ ...prev, start: v }))}
                    accentColor={accent}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium">종료 시간</p>
                  <TimePicker
                    value={quietHours.end}
                    onChange={(v) => setQuietHours((prev) => ({ ...prev, end: v }))}
                    accentColor={accent}
                  />
                </div>
              </div>
            )}
          </Card>

          {/* 위치 기록 */}
          <SectionLabel>위치 기록</SectionLabel>
          <Card className="divide-y divide-border">
            <ToggleRow
              label="복약 위치 기록"
              description="복용 완료 시 현재 위치를 함께 기록합니다"
              on={locationRecord}
              onChange={setLocationRecord}
              accent={accent}
            />
          </Card>
        </>
      )}

      {/* 저장 버튼 */}
      {meds.length > 0 && (
        <div className="fixed bottom-0 left-1/2 w-full max-w-md -translate-x-1/2 bg-background px-5 py-4">
          <button
            onClick={handleSave}
            disabled={saving}
            className="w-full rounded-xl py-4 text-sm font-bold text-white transition-opacity disabled:opacity-60"
            style={{ background: accent }}
          >
            {saving ? "저장 중..." : "저장하기"}
          </button>
        </div>
      )}
    </main>
  );
}
