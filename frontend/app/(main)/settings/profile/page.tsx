"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { getMe, updateMe } from "@/features/auth/api";

const CHRONIC_OPTIONS = ["당뇨", "고혈압", "고지혈증", "심혈관 질환", "갑상선 질환", "기타"];

export default function ProfileEditPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [chronicList, setChronicList] = useState<string[]>([]);
  const [allergy, setAllergy] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getMe().then((u) => {
      setName(u.name ?? "");
      setPhone(u.phone_number ?? "");
      setAllergy(u.allergy_info ?? "");
      if (u.chronic_diseases) {
        setChronicList(u.chronic_diseases.split(",").map((s) => s.trim()).filter(Boolean));
      }
    }).catch(() => {});
  }, []);

  function toggleChronic(item: string) {
    setChronicList((prev) =>
      prev.includes(item) ? prev.filter((c) => c !== item) : [...prev, item]
    );
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await updateMe({
        name: name.trim() || undefined,
        phone_number: phone.trim() || undefined,
        chronic_diseases: chronicList.join(",") || undefined,
        allergy_info: allergy.trim() || undefined,
      });
      setSaved(true);
      setTimeout(() => router.back(), 800);
    } catch (err) {
      setError(err instanceof Error ? err.message : "저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-6 pb-32">
      <div className="flex items-center gap-2">
        <button onClick={() => router.back()} className="flex items-center justify-center rounded-full p-1.5 hover:bg-muted text-lg font-semibold" aria-label="뒤로가기">
          &lt;
        </button>
        <h1 className="text-2xl font-bold">회원 정보 수정</h1>
      </div>

      <div className="mt-6 space-y-5">
        <div>
          <label className="text-sm font-medium">이름</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="이름 입력"
            className="mt-2 h-11 w-full rounded-xl border border-input bg-background px-4 text-sm outline-none focus:border-primary"
          />
        </div>

        <div>
          <label className="text-sm font-medium">휴대폰 번호</label>
          <input
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="010-0000-0000"
            className="mt-2 h-11 w-full rounded-xl border border-input bg-background px-4 text-sm outline-none focus:border-primary"
          />
        </div>

        <div>
          <label className="text-sm font-medium">만성질환 정보</label>
          <div className="mt-2 flex flex-wrap gap-2">
            {CHRONIC_OPTIONS.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => toggleChronic(item)}
                className="rounded-full px-4 py-1.5 text-sm font-medium transition-colors"
                style={
                  chronicList.includes(item)
                    ? { background: "hsl(var(--primary))", color: "#fff" }
                    : { border: "1px solid hsl(var(--border))", background: "hsl(var(--background))" }
                }
              >
                {item}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="text-sm font-medium">알레르기 정보</label>
          <textarea
            value={allergy}
            onChange={(e) => setAllergy(e.target.value)}
            rows={3}
            placeholder="예: 페니실린, 땅콩"
            className="mt-2 w-full rounded-xl border border-input bg-background px-4 py-3 text-sm outline-none focus:border-primary"
          />
        </div>
      </div>

      {error && <p className="mt-4 text-sm text-destructive">{error}</p>}

      <div className="fixed inset-x-0 bottom-6 mx-auto max-w-md px-5">
        <Button className="w-full" size="lg" onClick={handleSave} disabled={saving || saved}>
          {saved ? "저장됨 ✓" : saving ? "저장 중..." : "저장하기"}
        </Button>
      </div>
    </main>
  );
}
