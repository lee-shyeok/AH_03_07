"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  User, FileText, Pill, Activity, FolderOpen,
  Bell, Settings, HelpCircle, Megaphone, LogOut, ChevronRight,
  ShieldCheck, BarChart3, FlaskConical, CalendarDays, AlertTriangle,
  NotebookPen, Store, Siren, IdCard, Users, ClipboardList, Gift, Home, Gamepad2,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { getMe, logout } from "@/features/auth/api";
import { getMode, type UserMode } from "@/features/auth/mode";
import type { UserProfile } from "@/features/auth/types";

const PURPLE = "#7C5CCF";

export default function MyPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [mode, setModeState] = useState<UserMode>("general");

  useEffect(() => {
    setModeState(getMode());
    getMe().then(setUser).catch(() => {});
  }, []);

  const isAuto = (user?.user_type ?? mode) === "autoimmune";
  const accent = isAuto ? PURPLE : undefined; // 일반=초록(기본), 자가면역=보라

  async function handleLogout() {
    await logout();
    router.replace("/login");
  }

  // 모드별 건강정보 메뉴
  const healthMenus = isAuto
    ? [
        { href: "/disease/new", label: "질환 정보", icon: FileText },
        { href: "/medication", label: "약물 목록", icon: Pill },
        { href: "/risk-profile", label: "위험요인 프로필", icon: ShieldCheck },
        { href: "/activity-trend", label: "활성도 추이", icon: BarChart3 },
        { href: "/lab", label: "검사 결과", icon: FlaskConical },
        { href: "/schedule", label: "검사·진료 일정", icon: CalendarDays },
        { href: "/risk-flags", label: "의료진 확인 신호", icon: AlertTriangle },
        { href: "/documents", label: "문서 보관함", icon: FolderOpen },
      ]
    : [
        { href: "/records", label: "진료 기록", icon: FileText },
        { href: "/medication", label: "약물 목록", icon: Pill },
        { href: "/health-metrics", label: "건강 수치 기록", icon: Activity },
        { href: "/diary", label: "건강 일기", icon: NotebookPen },
        { href: "/documents", label: "문서 보관함", icon: FolderOpen },
      ];

  // 편의 기능 (공통)
  const convMenus = [
    { href: "/pharmacy", label: "약국 찾기", icon: Store },
    { href: "/emergency", label: "응급 SOS", icon: Siren },
    { href: "/emergency/card", label: "응급 카드 설정", icon: IdCard },
    { href: "/guardian", label: "보호자 공유", icon: Users },
    { href: "/report", label: "진료 전 요약", icon: ClipboardList },
    { href: "/rewards", label: "포인트 · 보상", icon: Gift },
    { href: "/room", label: "방 꾸미기", icon: Home },
    { href: "/games", label: "건강 미니게임", icon: Gamepad2 },
  ];

  const appMenus = [
    { href: "/mode-select", label: "모드 변경 (일반 / 자가면역)", icon: User },
    { href: "/notifications", label: "알림 설정", icon: Bell },
    { href: "/consent", label: "동의 관리", icon: ShieldCheck },
    { href: "/settings", label: "설정", icon: Settings },
  ];

  const heightWeight =
    user?.height && user?.weight ? `${user.height}cm / ${user.weight}kg` : "-";
  const birth = user?.birth_date ? user.birth_date.replaceAll("-", ".") : "-";

  return (
    <main className="mx-auto w-full max-w-md px-5 pb-6 pt-8">
      <h1 className="text-2xl font-extrabold">마이페이지</h1>

      {/* 프로필 */}
      <Card className="mt-5 p-5">
        <div className="flex items-center gap-4">
          <div
            className="flex h-13 w-13 items-center justify-center rounded-full p-3"
            style={{ background: isAuto ? PURPLE + "20" : "hsl(var(--secondary))" }}
          >
            <User className="h-7 w-7" style={{ color: accent }} />
          </div>
          <div className="flex-1">
            <p className="text-lg font-bold">{user?.name ?? "-"}</p>
            <p className="text-sm text-muted-foreground">{user?.email ?? "-"}</p>
          </div>
          <ChevronRight className="h-5 w-5 text-muted-foreground" />
        </div>
        <div className="mt-4 grid grid-cols-2 gap-2.5">
          <StatBox label="키 / 몸무게" value={heightWeight} auto={isAuto} />
          <StatBox label="생년월일" value={birth} auto={isAuto} />
        </div>
      </Card>

      {/* 모드 배지 */}
      <span
        className="mt-3 inline-block rounded-full px-3 py-1 text-xs font-bold text-white"
        style={{ background: isAuto ? PURPLE : "hsl(var(--primary))" }}
      >
        {isAuto ? "자가면역" : "일반"}
      </span>

      <Section title="내 건강 정보" menus={healthMenus} />
      <Section title="편의 기능" menus={convMenus} />
      <Section title="앱 설정" menus={appMenus} />

      {/* 지원 */}
      <h2 className="mt-6 text-sm font-semibold text-muted-foreground">지원</h2>
      <div className="mt-2 overflow-hidden rounded-2xl border border-border">
        <Row icon={HelpCircle} label="도움말" onClick={() => alert("준비 중입니다.")} />
        <Row icon={Megaphone} label="문의하기" onClick={() => alert("준비 중입니다.")} border />
        <Row icon={LogOut} label="로그아웃" danger onClick={handleLogout} border />
      </div>
    </main>
  );
}

function StatBox({ label, value, auto }: { label: string; value: string; auto: boolean }) {
  return (
    <div
      className="rounded-xl px-4 py-3 text-center"
      style={{ background: auto ? PURPLE + "12" : "hsl(var(--secondary))" }}
    >
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-0.5 font-bold">{value}</p>
    </div>
  );
}

function Section({
  title,
  menus,
}: {
  title: string;
  menus: { href: string; label: string; icon: typeof FileText }[];
}) {
  return (
    <>
      <h2 className="mt-6 text-sm font-semibold text-muted-foreground">{title}</h2>
      <div className="mt-2 overflow-hidden rounded-2xl border border-border">
        {menus.map(({ href, label, icon: Icon }, i) => (
          <Link
            key={href + label}
            href={href}
            className={"flex items-center gap-3 bg-card px-4 py-3.5 hover:bg-accent " + (i > 0 ? "border-t border-border" : "")}
          >
            <Icon className="h-5 w-5 text-muted-foreground" />
            <span className="flex-1 text-sm font-medium">{label}</span>
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          </Link>
        ))}
      </div>
    </>
  );
}

function Row({
  icon: Icon, label, onClick, danger, border,
}: {
  icon: typeof FileText; label: string; onClick: () => void; danger?: boolean; border?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={"flex w-full items-center gap-3 bg-card px-4 py-3.5 hover:bg-accent " + (border ? "border-t border-border " : "")}
    >
      <Icon className={"h-5 w-5 " + (danger ? "text-destructive" : "text-muted-foreground")} />
      <span className={"flex-1 text-left text-sm font-medium " + (danger ? "text-destructive" : "")}>{label}</span>
      <ChevronRight className="h-4 w-4 text-muted-foreground" />
    </button>
  );
}
