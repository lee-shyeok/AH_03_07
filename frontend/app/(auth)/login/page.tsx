"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { login } from "@/features/auth/api";
import { ApiError } from "@/lib/api/client";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login({ email, password });
      router.replace("/mode-select");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("네트워크 오류가 발생했습니다.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col px-6 pb-8 pt-24">
      <h1 className="text-4xl font-extrabold">반가워요!</h1>
      <p className="mt-2 text-sm text-muted-foreground">로그인해주세요</p>

      <form onSubmit={handleSubmit} className="mt-12 flex flex-1 flex-col">
        <div className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="email">이메일</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="example@email.com"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">비밀번호</Label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="비밀번호 입력"
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>

        {/* 하단 고정 영역 */}
        <div className="mt-auto">
          <Button type="submit" className="w-full" size="lg" disabled={loading}>
            {loading ? "로그인 중..." : "로그인"}
          </Button>
          <Button
            type="button"
            variant="outline"
            className="mt-3 w-full"
            size="lg"
            onClick={() => router.replace("/mode-select")}
          >
            로그인 없이 둘러보기 (체험)
          </Button>
          <div className="mt-6 flex items-center justify-center gap-3 text-sm text-muted-foreground">
            <span className="cursor-pointer hover:text-foreground">비밀번호 찾기</span>
            <span className="text-border">|</span>
            <Link href="/signup" className="hover:text-foreground">
              회원가입
            </Link>
          </div>
        </div>
      </form>
    </main>
  );
}
