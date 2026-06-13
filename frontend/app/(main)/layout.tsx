"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";
import { getMode } from "@/features/auth/mode";
import RecordsIcon from "@/components/icons/nav/RecordsIcon";
import ChatIcon from "@/components/icons/nav/ChatIcon";
import HomeIcon from "@/components/icons/nav/HomeIcon";
import BellIcon from "@/components/icons/nav/BellIcon";
import MyIcon from "@/components/icons/nav/MyIcon";

const PURPLE = "#7C5CCF";

const HIDE_NAV_PATHS = [
  "/documents/ocr-review", "/notifications/settings", "/health-metrics",
  "/diary", "/emergency", "/pharmacy", "/guardian", "/schedule",
  "/medication/alarm", "/medication/checklist", "/medication/new",
  "/activity/new", "/records/new", "/settings", "/guides/",
];

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [isAuto, setIsAuto] = useState(false);

  useEffect(() => {
    setIsAuto(getMode() === "autoimmune");
  }, []);

  const activeColor = isAuto ? PURPLE : "hsl(var(--primary))";
  const hideNav = HIDE_NAV_PATHS.some((p) => pathname.startsWith(p));

  const tabs = [
    { href: isAuto ? "/lab-results/list" : "/records"
      , label: "기록", icon: RecordsIcon },
    { href: "/chat", label: "챗봇", icon: ChatIcon },
    { href: "/home", label: "홈", icon: HomeIcon },
    { href: "/notifications", label: "알림", icon: BellIcon },
    { href: "/mypage", label: "마이", icon: MyIcon },
  ];

  return (
    <div className={cn("min-h-screen bg-background", !hideNav && "pb-16")}>
      {children}
      <nav className={cn("fixed inset-x-0 bottom-0 z-50 mx-auto flex max-w-md items-center justify-around border-t border-border bg-card py-2", hideNav && "hidden")}>
        {tabs.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          const tabActiveColor = activeColor;
          return (
            <Link
              key={href}
              href={href}
              className={cn("flex flex-1 flex-col items-center gap-0.5 py-1 text-xs", active ? "" : "text-muted-foreground")}
              style={active ? { color: tabActiveColor } : undefined}
            >
              <Icon className="h-5 w-5" strokeWidth={active ? 2.5 : 2} />
              {label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
