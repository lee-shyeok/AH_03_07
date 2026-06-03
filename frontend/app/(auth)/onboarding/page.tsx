"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";

const SLIDES = [
  {
    title: "복약을 한눈에",
    desc: "매일 먹는 약을 등록하고\n복약 시간을 알려드려요",
    image: "/onboarding/medication.png",
  },
  {
    title: "증상을 매일 기록",
    desc: "통증, 증상, 복약 상태를 기록하고\n건강 변화를 한눈에 확인해요",
    image: "/onboarding/symptom.png",
  },
  {
    title: "의료진과 함께 관리",
    desc: "진료 시 데이터를 의료진과 공유해\n정확한 진단을 받으세요",
    image: "/onboarding/doctor.png",
  },
];

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
        <Image src={slide.image} alt={slide.title} width={160} height={160} priority />
        <h1 className="mt-8 text-[32px] font-extrabold">{slide.title}</h1>
        <p className="mt-4 whitespace-pre-line text-base leading-[18px] text-[#6B7684]">{slide.desc}</p>
      </div>

      {/* 인디케이터 */}
      <div className="mb-8 flex justify-center gap-2">
        {SLIDES.map((_, i) => (
          <span
            key={i}
            className={"h-2 rounded-full transition-all " + (i === page ? "w-6 bg-primary" : "w-2 bg-[#7F8C8D]")}
          />
        ))}
      </div>

      <button onClick={next} className="w-full rounded-xl bg-primary py-4 text-base font-bold text-primary-foreground">
        {page < SLIDES.length - 1 ? "다음" : "시작하기"}
      </button>
    </main>
  );
}
