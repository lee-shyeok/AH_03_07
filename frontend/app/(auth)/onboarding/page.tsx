"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const SLIDES = [
  {
    title: "복약을 한눈에",
    desc: "매일 먹는 약을 등록하고\n복약 시간을 알려드려요",
  },
  {
    title: "증상을 매일 기록",
    desc: "컨디션과 검사 결과를\n시간순으로 관리해요",
  },
  {
    title: "의료진과 함께 관리",
    desc: "진료 시 데이터를 의료진과 공유해\n정확한 진단을 받으세요",
  },
];

function PillIllustration() {
  return (
    <svg width="160" height="160" viewBox="0 0 160 160" fill="none">
      <defs>
        <linearGradient id="p1" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#86EFAC" />
          <stop offset="1" stopColor="#22C55E" />
        </linearGradient>
        <linearGradient id="p2" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#BBF7D0" />
          <stop offset="1" stopColor="#86EFAC" />
        </linearGradient>
      </defs>
      {/* 뒤 알약 */}
      <g transform="rotate(-30 80 80)">
        <rect x="38" y="55" width="84" height="50" rx="25" fill="url(#p1)" />
        <rect x="38" y="55" width="42" height="50" rx="25" fill="url(#p2)" />
      </g>
      {/* 앞 알약 */}
      <g transform="rotate(35 80 90)">
        <rect x="50" y="70" width="74" height="44" rx="22" fill="url(#p2)" />
        <rect x="87" y="70" width="37" height="44" rx="22" fill="url(#p1)" />
        <rect x="100" y="80" width="6" height="24" rx="3" fill="#fff" opacity="0.7" />
      </g>
    </svg>
  );
}

export default function OnboardingPage() {
  const router = useRouter();
  const [page, setPage] = useState(0);

  function next() {
    if (page < SLIDES.length - 1) setPage(page + 1);
    else router.replace("/login");
  }

  const slide = SLIDES[page];

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col px-6 pb-8 pt-6">
      <button onClick={() => router.replace("/login")} className="ml-auto text-sm text-muted-foreground">
        건너뛰기
      </button>

      <div className="flex flex-1 flex-col items-center justify-center text-center">
        <PillIllustration />
        <h1 className="mt-8 text-3xl font-extrabold">{slide.title}</h1>
        <p className="mt-4 whitespace-pre-line leading-7 text-muted-foreground">{slide.desc}</p>
      </div>

      {/* 인디케이터 */}
      <div className="mb-8 flex justify-center gap-2">
        {SLIDES.map((_, i) => (
          <span
            key={i}
            className={"h-2 rounded-full transition-all " + (i === page ? "w-6 bg-primary" : "w-2 bg-muted")}
          />
        ))}
      </div>

      <button onClick={next} className="w-full rounded-xl bg-primary py-4 text-base font-bold text-primary-foreground">
        {page < SLIDES.length - 1 ? "다음" : "시작하기"}
      </button>
    </main>
  );
}
