"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft } from "lucide-react";
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card } from "@/components/ui/card";
import { listActivityLogs, type ActivityLogResponse } from "@/features/activity/api";

const PURPLE = "#7C5CCF";

// 지표 정의 (와이어프레임 색상: 통증 빨강 / 피로도 노랑 / 일상 불편도 보라 / 아침 강직 파랑)
const METRICS = [
  { key: "pain", label: "통증", color: "#EF4444", axis: "left", type: "line" },
  { key: "fatigue", label: "피로도", color: "#F59E0B", axis: "left", type: "line" },
  { key: "difficulty", label: "일상 불편도", color: PURPLE, axis: "left", type: "line" },
  { key: "stiffness", label: "아침 강직(분)", color: "#3B82F6", axis: "right", type: "bar" },
] as const;

type MetricKey = (typeof METRICS)[number]["key"];

const PERIODS = [
  { key: "1w", label: "1주", days: 7 },
  { key: "1m", label: "1개월", days: 30 },
  { key: "3m", label: "3개월", days: 90 },
  { key: "6m", label: "6개월", days: 180 },
] as const;

function todayStr(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
function addDays(dateStr: string, delta: number): string {
  const d = new Date(dateStr);
  d.setDate(d.getDate() + delta);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
function shortLabel(dateStr: string): string {
  const [, m, d] = dateStr.split("-");
  return `${Number(m)}/${Number(d)}`;
}

interface Point {
  date: string;
  label: string;
  pain: number;
  fatigue: number;
  difficulty: number;
  stiffness: number | null;
}

function stat(values: number[]) {
  if (values.length === 0) return null;
  const sum = values.reduce((a, b) => a + b, 0);
  return {
    avg: (sum / values.length).toFixed(1),
    max: Math.max(...values),
    min: Math.min(...values),
  };
}

export default function ActivityTrendPage() {
  const router = useRouter();
  const [periodKey, setPeriodKey] = useState<(typeof PERIODS)[number]["key"]>("1w");
  const [logs, setLogs] = useState<ActivityLogResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [visible, setVisible] = useState<Record<MetricKey, boolean>>({
    pain: true,
    fatigue: true,
    difficulty: true,
    stiffness: false,
  });

  useEffect(() => {
    const period = PERIODS.find((p) => p.key === periodKey)!;
    const to = todayStr();
    const from = addDays(to, -(period.days - 1));
    setLoading(true);
    listActivityLogs(from, to)
      .then((rows) => {
        setLogs(rows);
        // 강직 데이터가 있으면 토글 자동 노출
        if (rows.some((r) => r.morning_stiffness_minutes != null)) {
          setVisible((v) => ({ ...v, stiffness: true }));
        }
      })
      .catch(() => setLogs([]))
      .finally(() => setLoading(false));
  }, [periodKey]);

  const data: Point[] = useMemo(
    () =>
      [...logs]
        .sort((a, b) => a.log_date.localeCompare(b.log_date))
        .map((l) => ({
          date: l.log_date,
          label: shortLabel(l.log_date),
          pain: l.pain_vas,
          fatigue: l.fatigue,
          difficulty: l.daily_difficulty,
          stiffness: l.morning_stiffness_minutes,
        })),
    [logs]
  );

  const painStat = useMemo(() => stat(data.map((d) => d.pain)), [data]);
  const fatigueStat = useMemo(() => stat(data.map((d) => d.fatigue)), [data]);

  return (
    <main className="mx-auto w-full max-w-md px-5 pb-28 pt-6">
      {/* 헤더 */}
      <div className="flex items-center gap-6">
        <button onClick={() => router.back()} className="rounded-full p-1 hover:bg-accent" aria-label="뒤로가기">
          <ChevronLeft className="h-5 w-5" />
        </button>
        <h1 className="text-xl font-bold">활성도 추이</h1>
      </div>

      {/* 기간 선택 */}
      <div className="mt-12 flex gap-2">
        {PERIODS.map((p) => {
          const on = p.key === periodKey;
          return (
            <button
              key={p.key}
              onClick={() => setPeriodKey(p.key)}
              className="flex-1 rounded-xl py-2 text-sm font-semibold transition"
              style={
                on
                  ? { background: PURPLE, color: "#fff" }
                  : { background: PURPLE + "14", color: PURPLE }
              }
            >
              {p.label}
            </button>
          );
        })}
      </div>

      {/* 지표 토글 */}
      <div className="mt-3 flex flex-wrap gap-2">
        {METRICS.map((m) => {
          const on = visible[m.key];
          return (
            <button
              key={m.key}
              onClick={() => setVisible((v) => ({ ...v, [m.key]: !v[m.key] }))}
              className="flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition"
              style={{
                borderColor: on ? m.color : "#e5e7eb",
                color: on ? m.color : "#9ca3af",
                background: on ? m.color + "12" : "transparent",
              }}
            >
              <span
                className="inline-block h-2.5 w-2.5 rounded-full"
                style={{ background: on ? m.color : "#d1d5db" }}
              />
              {m.label}
            </button>
          );
        })}
      </div>

      {/* 차트 */}
      <Card className="mt-4 p-3">
        {loading ? (
          <p className="py-16 text-center text-sm text-muted-foreground">불러오는 중...</p>
        ) : data.length === 0 ? (
          <div className="py-14 text-center">
            <p className="text-sm text-muted-foreground">이 기간에 기록이 없어요.</p>
            <button
              onClick={() => router.push("/activity/new")}
              className="mt-4 rounded-xl px-5 py-2.5 text-sm font-bold text-white"
              style={{ background: PURPLE }}
            >
              기록하기
            </button>
          </div>
        ) : (
          <div style={{ width: "100%", height: 260 }}>
            <ResponsiveContainer>
              <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="label"
                  tick={{ fontSize: 11 }}
                  interval="preserveStartEnd"
                  minTickGap={20}
                />
                <YAxis yAxisId="left" domain={[0, 10]} tick={{ fontSize: 11 }} width={28} />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  tick={{ fontSize: 11 }}
                  width={32}
                  hide={!visible.stiffness}
                />
                <Tooltip />
                {METRICS.map((m) =>
                  !visible[m.key] ? null : m.type === "bar" ? (
                    <Bar
                      key={m.key}
                      yAxisId="right"
                      dataKey={m.key}
                      name={m.label}
                      fill={m.color}
                      barSize={10}
                      radius={[3, 3, 0, 0]}
                    />
                  ) : (
                    <Line
                      key={m.key}
                      yAxisId="left"
                      type="monotone"
                      dataKey={m.key}
                      name={m.label}
                      stroke={m.color}
                      strokeWidth={2}
                      dot={{ r: 2 }}
                      connectNulls
                    />
                  )
                )}
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>

      {/* 통계 (통증·피로도 평균/최고/최저) */}
      {!loading && data.length > 0 && (
        <div className="mt-4 grid grid-cols-2 gap-3">
          {[
            { label: "통증", s: painStat, color: "#EF4444" },
            { label: "피로도", s: fatigueStat, color: "#F59E0B" },
          ].map(({ label, s, color }) =>
            s ? (
              <Card key={label} className="p-4">
                <p className="text-sm font-semibold" style={{ color }}>
                  {label}
                </p>
                <div className="mt-2 flex justify-between text-sm">
                  <span className="text-muted-foreground">평균</span>
                  <span className="font-bold">{s.avg}</span>
                </div>
                <div className="mt-1 flex justify-between text-sm">
                  <span className="text-muted-foreground">최고 / 최저</span>
                  <span className="font-bold">
                    {s.max} / {s.min}
                  </span>
                </div>
              </Card>
            ) : null
          )}
        </div>
      )}

      {/* 안내 문구 (컴플라이언스) */}
      <p className="mt-5 text-center text-xs leading-relaxed text-muted-foreground">
        추이는 의료진과 공유할 때 참고하세요.
        <br />
        앱은 의학적 평가를 수행하지 않습니다.
      </p>

    </main>
  );
}
