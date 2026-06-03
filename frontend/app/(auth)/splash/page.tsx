"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

// 스플래시: 알약+체크 일러스트 후 로그인으로
export default function SplashPage() {
  const router = useRouter();

  useEffect(() => {
    const t = setTimeout(() => router.replace("/onboarding"), 1500);
    return () => clearTimeout(t);
  }, [router]);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center" style={{ background: "#F4F9F4" }}>
      {/* 알약 + 체크 일러스트 (SVG) */}
      <svg width="140" height="200" viewBox="0 0 140 200" fill="none">
        <defs>
          <linearGradient id="capTop" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#EAF7EC" />
            <stop offset="1" stopColor="#C8EBCE" />
          </linearGradient>
          <linearGradient id="capBot" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#5BC46E" />
            <stop offset="1" stopColor="#3FA855" />
          </linearGradient>
        </defs>
        <g transform="rotate(20 70 100)">
          {/* 윗부분 */}
          <path d="M40 60a30 30 0 0 1 60 0v40H40z" fill="url(#capTop)" />
          {/* 아랫부분 */}
          <path d="M40 100h60v40a30 30 0 0 1-60 0z" fill="url(#capBot)" />
          {/* 체크 */}
          <path d="M52 120l12 12 24-26" stroke="#fff" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        </g>
      </svg>
      <p className="mt-6 text-2xl font-extrabold text-primary">MediGuide</p>
      <p className="mt-1 text-sm text-muted-foreground">복약을 한눈에</p>
    </main>
  );
}
