"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  sendEmailVerifyCode,
  confirmEmailVerifyCode,
  signup,
} from "@/features/auth/api";
import { ApiError } from "@/lib/api/client";
import type { Gender } from "@/features/auth/types";

type Step = "email" | "verify" | "info";

export default function SignupPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("email");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [gender, setGender] = useState<Gender>("MALE");
  const [birthDate, setBirthDate] = useState("");
  const [phone, setPhone] = useState("");

  function handleError(err: unknown) {
    if (err instanceof ApiError) setError(err.message);
    else setError("네트워크 오류가 발생했습니다.");
  }

  async function handleSendCode(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await sendEmailVerifyCode(email);
      setStep("verify");
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await confirmEmailVerifyCode(email, code);
      setStep("info");
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await signup({
        email,
        password,
        name,
        gender,
        birth_date: birthDate,
        phone_number: phone,
      });
      router.replace("/login?signup=success");
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-6 py-10">
      <h1 className="text-2xl font-bold">회원가입</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        {step === "email" && "이메일 인증부터 시작해요"}
        {step === "verify" && "메일로 받은 인증코드를 입력하세요"}
        {step === "info" && "마지막으로 정보를 입력해주세요"}
      </p>

      {step === "email" && (
        <form onSubmit={handleSendCode} className="mt-8 space-y-5">
          <div className="space-y-2">
            <Label htmlFor="email">이메일</Label>
            <Input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="example@email.com"
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" className="w-full" size="lg" disabled={loading}>
            {loading ? "발송 중..." : "인증코드 발송"}
          </Button>
        </form>
      )}

      {step === "verify" && (
        <form onSubmit={handleVerify} className="mt-8 space-y-5">
          <div className="space-y-2">
            <Label htmlFor="code">인증코드</Label>
            <Input
              id="code"
              inputMode="numeric"
              required
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="6자리 코드"
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" className="w-full" size="lg" disabled={loading}>
            {loading ? "확인 중..." : "인증 확인"}
          </Button>
          <button
            type="button"
            onClick={() => setStep("email")}
            className="w-full text-sm text-muted-foreground hover:text-foreground"
          >
            이메일 다시 입력
          </button>
        </form>
      )}

      {step === "info" && (
        <form onSubmit={handleSignup} className="mt-8 space-y-4">
          <div className="space-y-2">
            <Label htmlFor="password">비밀번호</Label>
            <Input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="대/소문자·숫자·특수문자 포함 8자 이상"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="name">이름</Label>
            <Input
              id="name"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>성별</Label>
            <div className="flex gap-2">
              {(["MALE", "FEMALE"] as Gender[]).map((g) => (
                <button
                  key={g}
                  type="button"
                  onClick={() => setGender(g)}
                  className={
                    "flex-1 rounded-md border py-2.5 text-sm font-medium transition-colors " +
                    (gender === g
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-input bg-background text-foreground")
                  }
                >
                  {g === "MALE" ? "남성" : "여성"}
                </button>
              ))}
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="birth">생년월일</Label>
            <Input
              id="birth"
              type="date"
              required
              value={birthDate}
              onChange={(e) => setBirthDate(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="phone">전화번호</Label>
            <Input
              id="phone"
              required
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="010-0000-0000"
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" className="w-full" size="lg" disabled={loading}>
            {loading ? "가입 중..." : "회원가입 완료"}
          </Button>
        </form>
      )}

      <div className="mt-6 text-center text-sm text-muted-foreground">
        이미 계정이 있나요?{" "}
        <Link href="/login" className="text-primary hover:underline">
          로그인
        </Link>
      </div>
    </main>
  );
}
