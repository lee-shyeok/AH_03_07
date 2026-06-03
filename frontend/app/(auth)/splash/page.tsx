"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";

export default function SplashPage() {
  const router = useRouter();

  useEffect(() => {
    const t = setTimeout(() => router.replace("/onboarding"), 2000);
    return () => clearTimeout(t);
  }, [router]);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center">
      <Image src="/splash-logo.png" alt="MediGuide" width={400} height={400} priority />
    </main>
  );
}
