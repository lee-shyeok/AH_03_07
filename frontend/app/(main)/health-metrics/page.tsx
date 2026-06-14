"use client";

import { useState, useEffect } from "react";
import { ChevronLeft, Activity } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  getHealthMetrics,
  createHealthMetric,
  type HealthMetric,
} from "@/features/health-metrics/api";

type Tab = "BLOOD_PRESSURE" | "BLOOD_SUGAR" | "WEIGHT";
type Period = "1w" | "1m" | "3m" | "all";

const TABS: { key: Tab; label: string }[] = [
  { key: "BLOOD_PRESSURE", label: "혈압" },
  { key: "BLOOD_SUGAR", label: "혈당" },
  { key: "WEIGHT", label: "체중" },
];

const PERIODS: { key: Period; label: string }[] = [
  { key: "1w", label: "1주일" },
  { key: "1m", label: "1개월" },
  { key: "3m", label: "3개월" },
  { key: "all", label: "전체" },
];

const TAB_UNIT: Record<Tab, string> = {
  BLOOD_PRESSURE: "mmHg",
  BLOOD_SUGAR: "mg/dL",
  WEIGHT: "kg",
};

interface TabData {
  latest: string;
  unit: string;
  status: string;
  trend: number[];
  history: { date: string; value: string; status: string }[];
}

const EMPTY_TAB_DATA: TabData = { latest: "-", unit: "", status: "-", trend: [], history: [] };

const EMPTY_DATA: Record<Tab, TabData> = {
  BLOOD_PRESSURE: { ...EMPTY_TAB_DATA, unit: "mmHg" },
  BLOOD_SUGAR:    { ...EMPTY_TAB_DATA, unit: "mg/dL" },
  WEIGHT:         { ...EMPTY_TAB_DATA, unit: "kg" },
};

const DAY_KO = ["일", "월", "화", "수", "목", "금", "토"];

function formatDate(iso: string): string {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${mm}.${dd} (${DAY_KO[d.getDay()]})`;
}

function filterByPeriod(metrics: HealthMetric[], period: Period): HealthMetric[] {
  if (period === "all") return metrics;
  const days = period === "1w" ? 7 : period === "1m" ? 30 : 90;
  const cutoff = new Date(Date.now() - days * 86400 * 1000);
  return metrics.filter((m) => new Date(m.measured_at) >= cutoff);
}

function toTabData(items: HealthMetric[], unit: string): TabData {
  if (!items.length) return { latest: "-", unit, status: "-", trend: [], history: [] };
  const sorted = [...items].sort((a, b) => b.measured_at.localeCompare(a.measured_at));
  const latest = sorted[0];
  const trend = [...sorted].reverse().map((m) => {
    const raw = m.user_recorded_value ?? m.value ?? "0";
    const n = parseFloat(raw.split("/")[0]);
    return isNaN(n) ? 0 : n;
  });
  const history = sorted.map((m) => ({
    date: formatDate(m.measured_at),
    value: (m.user_recorded_value ?? m.value) ?? "0",
    status: m.status ?? "정상",
  }));
  const latestVal = (latest.user_recorded_value ?? latest.value) ?? "0";
  return { latest: latestVal, unit, status: latest.status ?? "정상", trend, history };
}

function Sparkline({ data }: { data: number[] }) {
  const w = 300, h = 90, pad = 10;
  const min = Math.min(...data), max = Math.max(...data);
  const range = max - min || 1;
  const pts = data.map((v, i) => {
    const x = data.length === 1 ? w / 2 : pad + (i * (w - 2 * pad)) / (data.length - 1);
    const y = h - pad - ((v - min) / range) * (h - 2 * pad);
    return { x, y };
  });
  const path = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full">
      <polyline points={path.replace(/[ML]/g, " ")} fill="none" stroke="hsl(var(--primary))" strokeWidth="2.5" />
      {pts.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r="3.5" fill="hsl(var(--primary))" />
      ))}
    </svg>
  );
}

export default function HealthMetricsPage() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("BLOOD_PRESSURE");
  const [period, setPeriod] = useState<Period>("1w");
  const [open, setOpen] = useState(false);
  const [val, setVal] = useState("");
  const [allMetrics, setAllMetrics] = useState<HealthMetric[]>([]);
  const [hasFetched, setHasFetched] = useState(false);
  const [saving, setSaving] = useState(false);

  function handleValChange(raw: string) {
    if (tab === "BLOOD_PRESSURE") {
      const filtered = raw.replace(/[^\d/]/g, "");
      const isDeleting = filtered.length < val.length;
      if (!isDeleting && !filtered.includes("/") && filtered.length === 3) {
        setVal(filtered + "/");
      } else {
        setVal(filtered);
      }
    } else {
      const filtered = raw.replace(/[^\d.]/g, "");
      const firstDot = filtered.indexOf(".");
      if (firstDot !== -1) {
        setVal(filtered.slice(0, firstDot + 1) + filtered.slice(firstDot + 1).replace(/\./g, ""));
      } else {
        setVal(filtered);
      }
    }
  }

  async function load() {
    try {
      const metrics = await getHealthMetrics();
      setAllMetrics(metrics);
      setHasFetched(true);
    } catch {
      // keep fallback
    }
  }

  useEffect(() => { load(); }, []);
  useEffect(() => { setVal(""); }, [tab]);

  const tabMetrics = allMetrics.filter((m) => m.metric_type === tab);
  const filteredMetrics = filterByPeriod(tabMetrics, period);
  const d = hasFetched
    ? (filteredMetrics.length
        ? toTabData(filteredMetrics, TAB_UNIT[tab])
        : { latest: "-", unit: TAB_UNIT[tab], status: "-", trend: [], history: [] })
    : EMPTY_DATA[tab];

  const periodLabel = PERIODS.find((p) => p.key === period)?.label ?? "";

  function formatSaveValue(raw: string): string {
    if (tab !== "WEIGHT") return raw;
    // 77 → 77.0 / 75. → 75.0 / 75.5 → 75.5
    if (!raw.includes(".")) return raw + ".0";
    const [int, dec] = raw.split(".");
    return `${int}.${dec || "0"}`;
  }

  async function save() {
    const v = val.trim();
    if (!v) return;
    const formatted = formatSaveValue(v);
    setSaving(true);
    try {
      const valueToSend = tab === "BLOOD_PRESSURE" ? v.split("/")[0] : v;
      await createHealthMetric({
        metric_type: tab,
        user_recorded_value: valueToSend,
        measured_at: new Date().toISOString(),
      });
      setAllMetrics((prev) => [
        { metric_type: tab, user_recorded_value: v, measured_at: new Date().toISOString(), status: "정상" },
        ...prev,
      ]);
      setVal("");
      setOpen(false);
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8 pb-28">
      <div className="flex items-center gap-2">
        <button onClick={() => router.back()} className="rounded-full p-1 hover:bg-accent" aria-label="뒤로가기">
          <ChevronLeft className="h-5 w-5" />
        </button>
        <h1 className="text-2xl font-bold">건강 수치</h1>
      </div>

      <div className="mt-5 flex items-center gap-3 rounded-2xl border border-primary/30 bg-secondary p-4">
        <Activity className="h-6 w-6 text-primary" />
        <div>
          <p className="font-bold">건강 수치 기록</p>
          <p className="text-sm text-secondary-foreground">혈압·혈당을 꾸준히 기록하세요</p>
        </div>
      </div>

      <div className="mt-5 flex gap-2">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={
              "flex-1 rounded-full py-2.5 text-sm font-bold transition-colors " +
              (tab === t.key ? "bg-primary text-primary-foreground" : "border border-border text-foreground")
            }
          >
            {t.label}
          </button>
        ))}
      </div>

      <Card className="mt-5 p-5">
        <p className="text-sm text-muted-foreground">최근 측정 · {d.history[0]?.date ?? "-"}</p>
        <div className="mt-1 flex items-end justify-between">
          <p className="text-3xl font-extrabold">
            {d.latest} <span className="text-base font-normal text-muted-foreground">{d.unit}</span>
          </p>
          <span className="rounded-md bg-secondary px-2.5 py-1 text-xs font-bold text-primary">{d.status}</span>
        </div>
      </Card>

      {d.trend.length >= 1 && (
        <Card className="mt-4 p-5">
          <p className="text-sm font-semibold text-muted-foreground">추이 ({periodLabel})</p>
          <div className="mt-3">
            <Sparkline data={d.trend} />
          </div>
        </Card>
      )}

      <div className="mt-6 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-muted-foreground">기록 내역</h2>
        <div className="flex gap-1">
          {PERIODS.map((p) => (
            <button
              key={p.key}
              onClick={() => setPeriod(p.key)}
              className={
                "rounded-full px-3 py-1 text-xs font-bold transition-colors " +
                (period === p.key
                  ? "bg-primary text-primary-foreground"
                  : "border border-border text-muted-foreground")
              }
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <Card className="mt-2 divide-y divide-border">
        {d.history.length === 0 ? (
          <p className="px-4 py-6 text-center text-sm text-muted-foreground">해당 기간 기록이 없습니다</p>
        ) : (
          d.history.map((h, i) => (
            <div key={i} className="flex items-center justify-between px-4 py-3.5">
              <span className="text-sm text-muted-foreground">{h.date}</span>
              <span className="font-bold">{h.value}</span>
              <span
                className={
                  "rounded-md px-2 py-0.5 text-xs font-bold " +
                  (h.status === "정상" ? "bg-secondary text-primary" : "bg-amber-100 text-amber-700")
                }
              >
                {h.status}
              </span>
            </div>
          ))
        )}
      </Card>

      <div className="fixed inset-x-0 bottom-6 mx-auto max-w-md px-5">
        <Button className="w-full" size="lg" onClick={() => setOpen(true)}>+ 수치 입력</Button>
      </div>

      {open && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40" onClick={() => setOpen(false)}>
          <div className="mx-auto w-full max-w-md rounded-t-2xl bg-card p-5" onClick={(e) => e.stopPropagation()}>
            <div className="mx-auto mb-3 h-1 w-10 rounded-full bg-muted-foreground/30" />
            <h2 className="font-bold">
              {TABS.find((t) => t.key === tab)?.label} 입력{" "}
              <span className="text-sm font-normal text-muted-foreground">({TAB_UNIT[tab]})</span>
            </h2>
            <input
              autoFocus
              value={val}
              onChange={(e) => handleValChange(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && save()}
              placeholder={tab === "BLOOD_PRESSURE" ? "예: 120/80" : tab === "BLOOD_SUGAR" ? "예: 98" : "예: 75.0"}
              className="mt-3 w-full rounded-xl border border-border bg-background px-4 py-3 text-center text-lg outline-none focus:border-primary"
            />
            <Button className="mt-4 w-full" size="lg" onClick={save} disabled={saving}>
              {saving ? "저장 중..." : "저장"}
            </Button>
          </div>
        </div>
      )}
    </main>
  );
}