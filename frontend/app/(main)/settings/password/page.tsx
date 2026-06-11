"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { changePassword } from "@/features/auth/api";

export default function PasswordChangePage() {
  const router = useRouter();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNext, setShowNext] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const mismatch = next && confirm && next !== confirm;
  const weak = next && next.length < 8;

  async function handleSave() {
    if (!current || !next || !confirm) return;
    if (mismatch || weak) return;
    setSaving(true);
    setError(null);
    try {
      await changePassword(current, next, confirm);
      setSaved(true);
      setTimeout(() => router.back(), 800);
    } catch (err) {
      setError(err instanceof Error ? err.message : "비밀번호 변경에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-6 pb-32">
      <div className="flex items-center gap-2">
        <button onClick={() => router.back()} className="p-1 text-foreground">
          <ChevronLeft className="h-6 w-6" />
        </button>
        <h1 className="text-2xl font-bold">비밀번호 변경</h1>
      </div>

      <div className="mt-6 space-y-5">
        <PasswordField
          label="현재 비밀번호"
          value={current}
          onChange={setCurrent}
          show={showCurrent}
          onToggle={() => setShowCurrent((v) => !v)}
          placeholder="현재 비밀번호 입력"
        />
        <PasswordField
          label="새 비밀번호"
          value={next}
          onChange={setNext}
          show={showNext}
          onToggle={() => setShowNext((v) => !v)}
          placeholder="영문·숫자·특수문자 8자 이상"
          hint={weak ? "8자 이상 입력해주세요" : undefined}
        />
        <PasswordField
          label="새 비밀번호 확인"
          value={confirm}
          onChange={setConfirm}
          show={showNext}
          onToggle={() => setShowNext((v) => !v)}
          placeholder="새 비밀번호 재입력"
          hint={mismatch ? "비밀번호가 일치하지 않습니다" : undefined}
        />
      </div>

      {error && <p className="mt-4 text-sm text-destructive">{error}</p>}

      <div className="fixed inset-x-0 bottom-6 mx-auto max-w-md px-5">
        <Button
          className="w-full"
          size="lg"
          onClick={handleSave}
          disabled={saving || saved || !current || !next || !confirm || !!mismatch || !!weak}
        >
          {saved ? "변경됨 ✓" : saving ? "변경 중..." : "변경하기"}
        </Button>
      </div>
    </main>
  );
}

function PasswordField({
  label, value, onChange, show, onToggle, placeholder, hint,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  show: boolean;
  onToggle: () => void;
  placeholder?: string;
  hint?: string;
}) {
  return (
    <div>
      <label className="text-sm font-medium">{label}</label>
      <div className="relative mt-2">
        <input
          type={show ? "text" : "password"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="h-11 w-full rounded-xl border border-input bg-background px-4 pr-11 text-sm outline-none focus:border-primary"
        />
        <button
          type="button"
          onClick={onToggle}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
        >
          {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </button>
      </div>
      {hint && <p className="mt-1 text-xs text-destructive">{hint}</p>}
    </div>
  );
}
