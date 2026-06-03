"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, MessageCircle, Home, Bell, User } from "lucide-react";
import { cn } from "@/lib/utils";

const tabs = [
  { href: "/records", label: "기록", icon: Activity },
  { href: "/chat", label: "챗봇", icon: MessageCircle },
  { href: "/home", label: "홈", icon: Home },
  { href: "/notifications", label: "알림", icon: Bell },
  { href: "/mypage", label: "마이", icon: User },
];

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-background pb-16">
      {children}
      <nav className="fixed inset-x-0 bottom-0 z-50 mx-auto flex max-w-md items-center justify-around border-t border-border bg-card py-2">
        {tabs.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex flex-1 flex-col items-center gap-0.5 py-1 text-xs",
                active ? "text-primary" : "text-muted-foreground"
              )}
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
