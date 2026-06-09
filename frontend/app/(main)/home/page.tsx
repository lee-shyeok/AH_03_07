"use client";

import { useEffect, useState } from "react";
import { getDashboard } from "@/features/dashboard/api";
import { getMe } from "@/features/auth/api";
import { getMode } from "@/features/auth/mode";
import type { DashboardData } from "@/features/dashboard/api";
import GeneralHome from "@/features/home/GeneralHome";
import AutoimmuneHome from "@/features/home/AutoimmuneHome";
import { listMyDiseases } from "@/features/disease/api";
import { getHealthMetrics, type HealthMetric } from "@/features/health-metrics/api";

export default function HomePage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [name, setName] = useState<string>("");
  const [userType, setUserType] = useState<"general" | "autoimmune">("general");
  const [isLupus, setIsLupus] = useState(false);
  const [recentMetrics, setRecentMetrics] = useState<HealthMetric[]>([]);

  useEffect(() => {
    setUserType(getMode());
    getMe().then((u) => { setName(u.name); if (u.user_type) setUserType(u.user_type); }).catch(() => {});
    getDashboard().then((d) => setData(d)).catch(() => setData(fallback));
    listMyDiseases()
      .then((ds) => setIsLupus(ds.some((d) => d.disease_code === "SLE")))
      .catch(() => {});
    getHealthMetrics().then((m) => setRecentMetrics(m.length > 0 ? m.slice(0, 4) : FALLBACK_METRICS)).catch(() => setRecentMetrics(FALLBACK_METRICS));
  }, []);

  const meds = (data?.today_medications ?? []).map((m) => ({
    label: [m.drug_name_user_input, m.dosage].filter(Boolean).join(" "),
    done: false,
  }));
  const displayName = name || "OOO";

  if (userType === "autoimmune") {
    return (
      <AutoimmuneHome
        name={displayName}
        medications={meds}
        recentActivity={data?.recent_activity ?? []}
        riskFlags={data?.active_risk_flags ?? []}
        pendingSchedules={data?.pending_schedules ?? []}
        isLupus={isLupus}
      />
    );
  }
  return <GeneralHome name={displayName} medications={meds} recentMetrics={recentMetrics} />;
}

const FALLBACK_METRICS: HealthMetric[] = [
  { id: "1", metric_type: "BLOOD_PRESSURE", user_recorded_value: "120.0", measured_at: new Date().toISOString(), created_at: new Date().toISOString() },
  { id: "2", metric_type: "BLOOD_SUGAR", user_recorded_value: "95.0", measured_at: new Date().toISOString(), created_at: new Date().toISOString() },
  { id: "3", metric_type: "WEIGHT", user_recorded_value: "68.5", measured_at: new Date().toISOString(), created_at: new Date().toISOString() },
  { id: "4", metric_type: "HEART_RATE", user_recorded_value: "72.0", measured_at: new Date().toISOString(), created_at: new Date().toISOString() },
];

const fallback: DashboardData = {
  today_medications: [],
  recent_activity: [],
  pending_schedules: [],
  active_risk_flags: [],
};
