"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field } from "@/components/form/Field";
import { ApiError } from "@/lib/api/client";
import {
  emailStepSchema, type EmailStepInput,
  codeStepSchema, type CodeStepInput,
  signupInfoSchema, type SignupInfoInput,
} from "@/features/auth/schema";
import { useSendEmailCode, useConfirmEmailCode, useSignup } from "@/features/auth/queries";

type Step = "email" | "verify" | "info";
const msg = (err: unknown) => (err instanceof ApiError ? err.message : "네트워크 오류가 발생했습니다.");

export default function SignupVerifyPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");

  const sendCode = useSendEmailCode();
  const confirmCode = useConfirmEmailCode();
  const signupMut = useSignup();

  const emailForm = useForm<EmailStepInput>({ resolver: zodResolver(emailStepSchema), defaultValues: { email: "" } });
  const codeForm = useForm<CodeStepInput>({ resolver: zodResolver(codeStepSchema), defaultValues: { code: "" } });
  const infoForm = useForm<SignupInfoInput>({
    resolver: zodResolver(signupInfoSchema),
    defaultValues: { password: "", name: "", gender: "MALE", birthDate: "", phone: "" },
  });

  async function onEmail(v: EmailStepInput) {
    try {
      await sendCode.mutateAsync(v.email);
      setEmail(v.email);
      setStep("verify");
    } catch (e) {
      emailForm.setError("root", { message: msg(e) });
    }
  }
  async function onCode(v: CodeStepInput) {
    try {
      await confirmCode.mutateAsync({ email, code: v.code });
      setStep("info");
    } catch (e) {
      codeForm.setError("root", { message: msg(e) });
    }
  }
  async function onInfo(v: SignupInfoInput) {
    try {
      await signupMut.mutateAsync({
        email,
        password: v.password,
        name: v.name,
        gender: v.gender,
        birth_date: v.birthDate,
        phone_number: v.phone,
      });
      router.replace("/login?signup=success");
    } catch (e) {
      infoForm.setError("root", { message: msg(e) });
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
        <form onSubmit={emailForm.handleSubmit(onEmail)} className="mt-8 space-y-5" noValidate>
          <Field label="이메일" htmlFor="email" error={emailForm.formState.errors.email?.message}>
            <Input id="email" type="email" placeholder="example@email.com" {...emailForm.register("email")} />
          </Field>
          {emailForm.formState.errors.root && <p className="text-sm text-destructive">{emailForm.formState.errors.root.message}</p>}
          <Button type="submit" className="w-full" size="lg" disabled={sendCode.isPending}>
            {sendCode.isPending ? "발송 중..." : "인증코드 발송"}
          </Button>
        </form>
      )}

      {step === "verify" && (
        <form onSubmit={codeForm.handleSubmit(onCode)} className="mt-8 space-y-5" noValidate>
          <Field label="인증코드" htmlFor="code" error={codeForm.formState.errors.code?.message}>
            <Input id="code" inputMode="numeric" maxLength={6} placeholder="6자리 코드" {...codeForm.register("code")} />
          </Field>
          {codeForm.formState.errors.root && <p className="text-sm text-destructive">{codeForm.formState.errors.root.message}</p>}
          <Button type="submit" className="w-full" size="lg" disabled={confirmCode.isPending}>
            {confirmCode.isPending ? "확인 중..." : "인증 확인"}
          </Button>
          <button type="button" onClick={() => setStep("email")} className="w-full text-sm text-muted-foreground hover:text-foreground">
            이메일 다시 입력
          </button>
        </form>
      )}

      {step === "info" && (
        <form onSubmit={infoForm.handleSubmit(onInfo)} className="mt-8 space-y-4" noValidate>
          <Field label="비밀번호" htmlFor="password" error={infoForm.formState.errors.password?.message} hint="영문·숫자·특수문자 포함 8자 이상">
            <Input id="password" type="password" placeholder="비밀번호 입력" {...infoForm.register("password")} />
          </Field>
          <Field label="이름" htmlFor="name" error={infoForm.formState.errors.name?.message}>
            <Input id="name" {...infoForm.register("name")} />
          </Field>
          <Controller
            control={infoForm.control}
            name="gender"
            render={({ field }) => (
              <Field label="성별">
                <div className="flex gap-2">
                  {(["MALE", "FEMALE"] as const).map((g) => (
                    <button
                      key={g}
                      type="button"
                      onClick={() => field.onChange(g)}
                      className={"flex-1 rounded-md border py-2.5 text-sm font-medium transition-colors " + (field.value === g ? "border-primary bg-primary text-primary-foreground" : "border-input bg-background text-foreground")}
                    >
                      {g === "MALE" ? "남성" : "여성"}
                    </button>
                  ))}
                </div>
              </Field>
            )}
          />
          <Field label="생년월일" htmlFor="birth" error={infoForm.formState.errors.birthDate?.message}>
            <Input id="birth" type="date" {...infoForm.register("birthDate")} />
          </Field>
          <Field label="전화번호" htmlFor="phone" error={infoForm.formState.errors.phone?.message}>
            <Input id="phone" placeholder="010-0000-0000" {...infoForm.register("phone")} />
          </Field>
          {infoForm.formState.errors.root && <p className="text-sm text-destructive">{infoForm.formState.errors.root.message}</p>}
          <Button type="submit" className="w-full" size="lg" disabled={signupMut.isPending}>
            {signupMut.isPending ? "가입 중..." : "회원가입 완료"}
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
