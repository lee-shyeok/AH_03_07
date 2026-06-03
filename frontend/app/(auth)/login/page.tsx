"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field } from "@/components/form/Field";
import { loginSchema, type LoginInput } from "@/features/auth/schema";
import { useLogin } from "@/features/auth/queries";
import { ApiError } from "@/lib/api/client";

export default function LoginPage() {
  const router = useRouter();
  const login = useLogin();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  async function onSubmit(values: LoginInput) {
    try {
      await login.mutateAsync(values);
      router.replace("/mode-select");
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "네트워크 오류가 발생했습니다.";
      setError("root", { message });
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col px-6 pb-8 pt-24">
      <h1 className="text-4xl font-extrabold">반가워요!</h1>
      <p className="mt-2 text-sm text-muted-foreground">로그인해주세요</p>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-12 flex flex-1 flex-col" noValidate>
        <div className="space-y-5">
          <Field label="이메일" htmlFor="email" error={errors.email?.message}>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="example@email.com"
              {...register("email")}
            />
          </Field>
          <Field label="비밀번호" htmlFor="password" error={errors.password?.message}>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              placeholder="비밀번호 입력"
              {...register("password")}
            />
          </Field>
          {errors.root && <p className="text-sm text-destructive">{errors.root.message}</p>}
        </div>

        {/* 하단 고정 영역 */}
        <div className="mt-auto">
          <Button type="submit" className="w-full" size="lg" disabled={login.isPending}>
            {login.isPending ? "로그인 중..." : "로그인"}
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
