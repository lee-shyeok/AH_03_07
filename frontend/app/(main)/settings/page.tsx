"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { withdraw } from "@/features/auth/api";
import { ApiError } from "@/lib/api/client";

type FontSize = "small" | "medium" | "large";

const FONT_SIZE_CLASS: Record<FontSize, string> = {
  small: "text-sm",
  medium: "text-base",
  large: "text-lg",
};

const FONT_SIZE_LABEL: Record<FontSize, string> = {
  small: "작게",
  medium: "보통",
  large: "크게",
};

function applyFontSize(size: FontSize) {
  const html = document.documentElement;
  html.classList.remove("text-sm", "text-base", "text-lg");
  html.classList.add(FONT_SIZE_CLASS[size]);
}

function Toggle({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      role="switch"
      aria-checked={on}
      onClick={() => onChange(!on)}
      className={"relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors " + (on ? "bg-primary" : "bg-input")}
    >
      <span className={"inline-block h-4 w-4 rounded-full bg-white shadow-sm transition-transform " + (on ? "translate-x-6" : "translate-x-1")} />
    </button>
  );
}

export default function SettingsPage() {
  const router = useRouter();
  const [alerts, setAlerts] = useState({ med: true, guide: true, marketing: false, location: false });
  const [channels, setChannels] = useState({ app: true, email: false, kakao: true });
  const [fontSize, setFontSize] = useState<FontSize>("medium");
  const [confirming, setConfirming] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem("fontSize") as FontSize | null;
    if (saved && saved in FONT_SIZE_CLASS) {
      setFontSize(saved);
      applyFontSize(saved);
    }
  }, []);

  function handleFontSize(size: FontSize) {
    setFontSize(size);
    localStorage.setItem("fontSize", size);
    applyFontSize(size);
  }

  async function handleWithdraw() {
    setLoading(true);
    setError(null);
    try {
      await withdraw();
      router.replace("/login");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "탈퇴에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-6 pb-24">
      <div className="flex items-center gap-2">
        <button onClick={() => router.back()} className="flex items-center justify-center rounded-full p-1.5 hover:bg-muted text-lg font-semibold" aria-label="뒤로가기">
          &lt;
        </button>
        <h1 className="text-2xl font-bold">설정</h1>
      </div>

      {/* 알림 설정 */}
      <p className="mt-6 text-sm font-semibold text-muted-foreground">알림 설정</p>
      <Card className="mt-2 divide-y divide-border">
        <Row label="복약 알림" right={<Toggle on={alerts.med} onChange={(v) => setAlerts({ ...alerts, med: v })} />} />
        <Row label="가이드 확인 알림" right={<Toggle on={alerts.guide} onChange={(v) => setAlerts({ ...alerts, guide: v })} />} />
        <Row label="마케팅 알림" right={<Toggle on={alerts.marketing} onChange={(v) => setAlerts({ ...alerts, marketing: v })} />} />
        <Row label="복약 완료 시 위치 태깅 (선택)" right={<Toggle on={alerts.location} onChange={(v) => setAlerts({ ...alerts, location: v })} />} />
      </Card>

      {/* 알림 채널 */}
      <p className="mt-6 text-sm font-semibold text-muted-foreground">알림 채널</p>
      <Card className="mt-2 divide-y divide-border">
        <Row label="앱 알림" right={<Toggle on={channels.app} onChange={(v) => setChannels({ ...channels, app: v })} />} />
        <Row label="이메일" right={<Toggle on={channels.email} onChange={(v) => setChannels({ ...channels, email: v })} />} />
        <Row label="카카오톡" right={<Toggle on={channels.kakao} onChange={(v) => setChannels({ ...channels, kakao: v })} />} />
      </Card>

      {/* 접근성 */}
      <p className="mt-6 text-sm font-semibold text-muted-foreground">접근성</p>
      <Card className="mt-2 p-4">
        <p className="text-sm font-medium mb-3">글씨 크기</p>
        <div className="flex gap-2">
          {(["small", "medium", "large"] as FontSize[]).map((size) => (
            <button
              key={size}
              onClick={() => handleFontSize(size)}
              className={
                "flex-1 rounded-lg border py-2 text-sm font-medium transition-colors " +
                (fontSize === size
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border bg-background text-foreground")
              }
              aria-pressed={fontSize === size}
            >
              {FONT_SIZE_LABEL[size]}
            </button>
          ))}
        </div>
      </Card>

      {/* 계정 */}
      <p className="mt-6 text-sm font-semibold text-muted-foreground">계정</p>
      <Card className="mt-2 divide-y divide-border">
        <NavRow label="비밀번호 변경" onClick={() => router.push("/settings/password")} />
        <NavRow label="회원 정보 수정" onClick={() => router.push("/settings/profile")} />
        <NavRow label="회원 탈퇴" danger onClick={() => setConfirming(true)} />
      </Card>

      {confirming && (
        <Card className="mt-3 p-4">
          <p className="text-sm">탈퇴 시 모든 의료 기록·가이드·OCR 데이터가 즉시 삭제되며 복구할 수 없습니다.</p>
          {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
          <div className="mt-3 flex gap-2">
            <Button variant="outline" className="flex-1" onClick={() => setConfirming(false)} disabled={loading}>취소</Button>
            <Button variant="destructive" className="flex-1" onClick={handleWithdraw} disabled={loading}>
              {loading ? "처리 중..." : "탈퇴"}
            </Button>
          </div>
        </Card>
      )}

      {/* 정보 */}
      <p className="mt-6 text-sm font-semibold text-muted-foreground">정보</p>
      <Card className="mt-2 divide-y divide-border">
        <NavRow label="개인정보처리방침" onClick={() => alert("개인정보처리방침")} />
        <NavRow label="이용 약관" onClick={() => alert("이용 약관")} />
        <NavRow label="오픈소스 라이선스" onClick={() => alert("오픈소스 라이선스")} />
        <div className="flex items-center justify-between px-4 py-3.5">
          <span className="text-sm">버전</span>
          <span className="text-sm text-muted-foreground">v1.0</span>
        </div>
      </Card>
    </main>
  );
}

function Row({ label, right }: { label: string; right: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between px-4 py-3.5">
      <span className="text-sm">{label}</span>
      {right}
    </div>
  );
}

function NavRow({ label, onClick, danger }: { label: string; onClick: () => void; danger?: boolean }) {
  return (
    <button onClick={onClick} className="flex w-full items-center justify-between px-4 py-3.5">
      <span className={"text-sm " + (danger ? "text-destructive" : "")}>{label}</span>
      <span className="text-muted-foreground">›</span>
    </button>
  );
}
