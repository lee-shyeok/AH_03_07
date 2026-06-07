"use client";

import { useEffect, useState } from "react";
import { getDashboard } from "@/features/dashboard/api";
import { getMe } from "@/features/auth/api";
import { getMode } from "@/features/auth/mode";
import type { DashboardData } from "@/features/dashboard/api";
import GeneralHome from "@/features/home/GeneralHome";
import AutoimmuneHome from "@/features/home/AutoimmuneHome";
import { listMyDiseases } from "@/features/disease/api";

export default function HomePage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [name, setName] = useState<string>("");
  const [userType, setUserType] = useState<"general" | "autoimmune">("general");
  const [isLupus, setIsLupus] = useState(false);

  useEffect(() => {
    setUserType(getMode());
    getMe().then((u) => { setName(u.name); if (u.user_type) setUserType(u.user_type); }).catch(() => {});
    getDashboard().then((d) => setData(d)).catch(() => setData(fallback));
    listMyDiseases()
      .then((ds) => setIsLupus(ds.some((d) => d.disease_code === "SLE")))
      .catch(() => {});
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
  return <GeneralHome name={displayName} medications={meds} />;
}

const fallback: DashboardData = {
  today_medications: [],
  recent_activity: [],
  pending_schedules: [],
  active_risk_flags: [],
};
