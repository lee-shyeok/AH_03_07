"use client";

import { useRouter } from "next/navigation";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ChevronLeft, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field } from "@/components/form/Field";
import { signupSchema, type SignupInput } from "@/features/auth/schema";

export default function SignupPage() {
  const router = useRouter();
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<SignupInput>({
    resolver: zodResolver(signupSchema),
    defaultValues: { name: "", email: "", password: "", passwordConfirm: "", agree: false },
  });

  function onSubmit(values: SignupInput) {
    // 이메일 인증 단계로 이동 (백엔드 email-verify)
    router.push(`/signup/verify?email=${encodeURIComponent(values.email)}`);
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col px-6 pb-8 pt-12">
      <button onClick={() => router.back()} aria-label="뒤로" className="-ml-2 w-fit">
        <ChevronLeft className="h-7 w-7" />
      </button>

      <h1 className="mt-6 text-4xl font-extrabold">처음이시군요!</h1>
      <p className="mt-2 text-sm text-muted-foreground">계정을 만들어주세요</p>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-10 flex flex-1 flex-col" noValidate>
        <div className="space-y-5">
          <Field label="이름" htmlFor="name" error={errors.name?.message}>
            <Input id="name" placeholder="홍길동" {...register("name")} />
          </Field>
          <Field label="이메일" htmlFor="email" error={errors.email?.message}>
            <Input id="email" type="email" placeholder="example@email.com" {...register("email")} />
          </Field>
          <Field
            label="비밀번호"
            htmlFor="password"
            error={errors.password?.message}
            hint="영문·숫자 포함 8자 이상"
          >
            <Input id="password" type="password" placeholder="비밀번호 입력" {...register("password")} />
          </Field>
          <Field label="비밀번호 확인" htmlFor="confirm" error={errors.passwordConfirm?.message}>
            <Input id="confirm" type="password" placeholder="다시 한번 입력" {...register("passwordConfirm")} />
          </Field>

          <Controller
            control={control}
            name="agree"
            render={({ field }) => (
              <div>
                <button
                  type="button"
                  onClick={() => field.onChange(!field.value)}
                  className="flex items-center gap-3 pt-2"
                >
                  <span className={"flex h-5 w-5 items-center justify-center rounded " + (field.value ? "bg-primary" : "border-2 border-border")}>
                    {field.value && <Check className="h-3.5 w-3.5 text-white" />}
                  </span>
                  <span className="text-sm">이용약관에 동의합니다</span>
                </button>
                {errors.agree && <p className="mt-1 text-sm text-destructive">{errors.agree.message}</p>}
              </div>
            )}
          />
        </div>

        <div className="mt-auto pt-8">
          <Button type="submit" className="w-full" size="lg">회원가입</Button>
        </div>
      </form>
    </main>
  );
}
