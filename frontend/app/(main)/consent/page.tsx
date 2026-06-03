"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { getConsents, updateConsent } from "@/features/consent/api";
import { CONSENT_META } from "@/features/consent/types";
import type { ConsentItem, ConsentType } from "@/features/consent/types";

export default function ConsentPage() {
  const [items, setItems] = useState<ConsentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setItems(await getConsents());
    } catch {
      setError("동의 이력을 불러오지 못했습니다.\n잠시 후 다시 시도해주세요.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function isAgreed(type: ConsentType) {
    return items.some((i) => i.consent_type === type && i.agreed);
  }

  async function handleToggle(type: ConsentType, required: boolean) {
    const current = isAgreed(type);
    if (required && current) {
      alert("필수 동의 항목은 철회할 수 없습니다.");
      return;
    }
    try {
      await updateConsent(type, !current);
      load();
    } catch {
      alert("변경에 실패했습니다.");
    }
  }

  return (
    <main className="mx-auto w-full max-w-md px-6 py-8">
      <h1 className="text-2xl font-bold">동의 관리</h1>

      {/* 민감정보 안내 (NFR-COMPLI-001) */}
      <div className="mt-4 rounded-xl border border-primary/30 bg-secondary p-4 text-sm leading-6 text-secondary-foreground">
        <p className="font-semibold">민감정보 처리 안내</p>
        <ul className="mt-1 list-disc pl-4 text-xs">
          <li>의료·건강 정보는 암호화되어 안전하게 저장됩니다</li>
          <li>수집된 정보는 서비스 제공 목적으로만 사용됩니다</li>
          <li>회원탈퇴 시 의료 데이터는 즉시 삭제됩니다</li>
        </ul>
      </div>

      {loading ? (
        <p className="mt-6 text-sm text-muted-foreground">불러오는 중...</p>
      ) : error ? (
        <div className="mt-6">
          <p className="whitespace-pre-line text-sm text-destructive">{error}</p>
          <button onClick={load} className="mt-2 text-sm text-primary hover:underline">
            다시 시도
          </button>
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {CONSENT_META.map((meta) => {
            const agreed = isAgreed(meta.type);
            return (
              <Card key={meta.type} className="flex items-center justify-between p-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold">{meta.label}</span>
                    <span
                      className={
                        "rounded px-1.5 py-0.5 text-[10px] font-bold " +
                        (meta.required
                          ? "bg-destructive/10 text-destructive"
                          : "bg-muted text-muted-foreground")
                      }
                    >
                      {meta.required ? "필수" : "선택"}
                    </span>
                  </div>
                  <p
                    className={
                      "mt-1 text-xs " +
                      (agreed ? "text-primary" : "text-destructive")
                    }
                  >
                    {agreed ? "✅ 동의 완료" : "❌ 미동의"}
                  </p>
                </div>
                <button
                  role="switch"
                  aria-checked={agreed}
                  onClick={() => handleToggle(meta.type, meta.required)}
                  className={
                    "relative h-6 w-11 rounded-full transition-colors " +
                    (agreed ? "bg-primary" : "bg-muted")
                  }
                >
                  <span
                    className={
                      "absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform " +
                      (agreed ? "translate-x-5" : "translate-x-0.5")
                    }
                  />
                </button>
              </Card>
            );
          })}
        </div>
      )}
    </main>
  );
}
