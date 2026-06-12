"use client";

import { useState, useEffect } from "react";
import { Activity, ChevronLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  getHealthMetrics,
  createHealthMetric,
  type HealthMetric,
} from "@/features/health-metrics/api";

type Tab = "BLOOD_PRESSURE" | "BLOOD_SUGAR" | "WEIGHT";

const TABS: { key: Tab; label: string }[] = [
  { key: "BLOOD_PRESSURE", label: "혈압" },
  { key: "BLOOD_SUGAR", label: "혈당" },
  { key: "WEIGHT", label: "체중" },
];

interface TabData {
  latest: string;
  unit: string;
  status: string;
  trend: number[];
  history: { date: string; value: string; status: string }[];
}

const FALLBACK_DATA: Record<Tab, TabData> = {
  BLOOD_PRESSURE: {
    latest: "128/82",
    unit: "mmHg",
    status: "정상",
    trend: [120, 124, 119, 138, 130, 133, 128],
    history: [
      { date: "05.20 (화)", value: "128/82", status: "정상" },
      { date: "05.19 (월)", value: "135/88", status: "주의" },
      { date: "05.18 (일)", value: "126/80", status: "정상" },
    ],
  },
  BLOOD_SUGAR: {
    latest: "98",
    unit: "mg/dL",
    status: "정상",
    trend: [95, 102, 98, 110, 100, 97, 98],
    history: [{ date: "05.20 (화)", value: "98", status: "정상" }],
  },
  WEIGHT: {
    latest: "75.0",
    unit: "kg",
    status: "정상",
    trend: [76, 75.5, 75.2, 75, 74.8, 75, 75],
    history: [{ date: "05.20 (화)", value: "75.0", status: "정상" }],
  },
};

const DAY_KO = ["일", "월", "화", "수", "목", "금", "토"];

function formatDate(iso: string): string {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${mm}.${dd} (${DAY_KO[d.getDay()]})`;
}

function toTabData(items: HealthMetric[], unit: string): TabData {
  if (!items.length) return { latest: "-", unit, status: "-", trend: [], history: [] };
  const sorted = [...items].sort((a, b) => b.measured_at.localeCompare(a.measured_at));
  const latest = sorted[0];
  const trend = sorted
    .slice(0, 7)
    .reverse()
    .map((m) => {
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

function buildData(metrics: HealthMetric[]): Record<Tab, TabData> {
  return {
    BLOOD_PRESSURE: toTabData(metrics.filter((m) => m.metric_type === "BLOOD_PRESSURE"), "mmHg"),
    BLOOD_SUGAR: toTabData(metrics.filter((m) => m.metric_type === "BLOOD_SUGAR"), "mg/dL"),
    WEIGHT: toTabData(metrics.filter((m) => m.metric_type === "WEIGHT"), "kg"),
  };
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
  const [open, setOpen] = useState(false);
  const [val, setVal] = useState("");
  const [data, setData] = useState<Record<Tab, TabData>>(FALLBACK_DATA);
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
      // glucose / weight: digits + user-typed dot only, no auto-insert
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
      const built = buildData(metrics);
      setData((prev) => ({
        BLOOD_PRESSURE: built.BLOOD_PRESSURE.history.length ? built.BLOOD_PRESSURE : prev.BLOOD_PRESSURE,
        BLOOD_SUGAR: built.BLOOD_SUGAR.history.length ? built.BLOOD_SUGAR : prev.BLOOD_SUGAR,
        WEIGHT: built.WEIGHT.history.length ? built.WEIGHT : prev.WEIGHT,
      }));
    } catch {
      // keep fallback data
    }
  }

  useEffect(() => { load(); }, []);
  useEffect(() => { setVal(""); }, [tab]);

  const d = data[tab];

  async function save() {
    const v = val.trim();
    if (!v) return;
    setSaving(true);
    try {
      await createHealthMetric({ metric_type: tab, value: v });
      setVal("");
      setOpen(false);
      await load();
    } catch {
      setData((prev) => ({
        ...prev,
        [tab]: {
          ...prev[tab],
          latest: v,
          history: [{ date: "오늘", value: v, status: "정상" }, ...prev[tab].history],
        },
      }));
      setVal("");
      setOpen(false);
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8 pb-8">
      <div className="flex items-center gap-2">
        <button onClick={() => router.push("/home")} className="rounded-full p-1 text-foreground hover:bg-muted">
          <ChevronLeft className="h-6 w-6" />
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
          <p className="text-sm font-semibold text-muted-foreground">추이 (최근 7일)</p>
          <div className="mt-3">
            <Sparkline data={d.trend} />
          </div>
        </Card>
      )}

      <h2 className="mt-6 text-sm font-semibold text-muted-foreground">기록 내역</h2>
      <Card className="mt-2 divide-y divide-border">
        {d.history.map((h, i) => (
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
        ))}
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
              <span className="text-sm font-normal text-muted-foreground">({d.unit})</span>
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
