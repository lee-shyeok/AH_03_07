"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [agree, setAgree] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password !== confirm) {
      setError("비밀번호가 일치하지 않습니다.");
      return;
    }
    if (!agree) {
      setError("이용약관에 동의해주세요.");
      return;
    }
    // 이메일 인증 단계로 이동 (백엔드 email-verify)
    router.push(`/signup/verify?email=${encodeURIComponent(email)}`);
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col px-6 pb-8 pt-12">
      <button onClick={() => router.back()} aria-label="뒤로" className="-ml-2 w-fit">
        <ChevronLeft className="h-7 w-7" />
      </button>

      <h1 className="mt-6 text-4xl font-extrabold">처음이시군요!</h1>
      <p className="mt-2 text-sm text-muted-foreground">계정을 만들어주세요</p>

      <form onSubmit={handleSubmit} className="mt-10 flex flex-1 flex-col">
        <div className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="name">이름</Label>
            <Input id="name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="홍길동" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">이메일</Label>
            <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="example@email.com" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">비밀번호</Label>
            <Input id="password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="비밀번호 입력" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirm">비밀번호 확인</Label>
            <Input id="confirm" type="password" required value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="다시 한번 입력" />
          </div>

          <button type="button" onClick={() => setAgree(!agree)} className="flex items-center gap-3 pt-2">
            <span className={"flex h-5 w-5 items-center justify-center rounded " + (agree ? "bg-primary" : "border-2 border-border")}>
              {agree && <Check className="h-3.5 w-3.5 text-white" />}
            </span>
            <span className="text-sm">이용약관에 동의합니다</span>
          </button>

          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>

        <div className="mt-auto pt-8">
          <Button type="submit" className="w-full" size="lg">회원가입</Button>
        </div>
      </form>
    </main>
  );
}
