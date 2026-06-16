"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, User, Plus, X, Link as LinkIcon, Trash2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import {
  getGuardians,
  createGuardian,
  deleteGuardian,
  getShareLinks,
  createShareLink,
  deleteShareLink,
} from "@/features/guardian/api";
import type { Guardian, ShareLink, SharePeriod, ShareCategory, ShareDetail } from "@/features/guardian/api";

const COLORS = ["#7C5CCF", "#60A5FA", "#F97316"];

const SHARE_ITEMS: { category: ShareCategory; label: string }[] = [
  { category: "activity", label: "활성도 기록" },
  { category: "health_metrics", label: "검사 결과" },
  { category: "medication", label: "복약 현황" },
  { category: "side_effect", label: "주의 증상 알림" },
  { category: "schedule", label: "진료 일정" },
];

const PERIODS: { value: SharePeriod; label: string }[] = [
  { value: "1d", label: "1일" },
  { value: "1w", label: "1주" },
  { value: "1m", label: "1개월" },
  { value: "unlimited", label: "철회 시까지" },
];

const RELATIONS = ["어머니", "아버지", "배우자", "자녀", "형제/자매", "기타"];

const DEFAULT_ADD_FORM = { name: "", contact: "", contactType: "phone" as "phone" | "email", relationship: "" };

function Toggle({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      role="switch"
      aria-checked={on}
      onClick={() => onChange(!on)}
      className={"relative h-6 w-11 rounded-full transition-colors " + (on ? "bg-primary" : "bg-muted")}
    >
      {!on && (
        <span className="absolute top-0.5 left-1 h-5 w-5 rounded-full bg-white shadow transition-transform" />
      )}
    </button>
  );
}

export default function GuardianPage() {
  const router = useRouter();
  const [guardians, setGuardians] = useState<Guardian[]>([]);
  const [shareLinks, setShareLinks] = useState<ShareLink[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [addForm, setAddForm] = useState(DEFAULT_ADD_FORM);
  const [shareToggles, setShareToggles] = useState([true, true, true, true, false]);
  const [sharePeriod, setSharePeriod] = useState<SharePeriod>("1w");
  const [shareDetail, setShareDetail] = useState<ShareDetail>("summary");
  const [creating, setCreating] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  useEffect(() => {
    getGuardians()
      .then(setGuardians)
      .catch(() => {});
    getShareLinks()
      .then(setShareLinks)
      .catch(() => {});
  }, []);

  function scopeLabel() {
    const count = shareToggles.filter(Boolean).length;
    if (count === SHARE_ITEMS.length) return "전체 공개";
    if (count > 0) return "일부 공개";
    return "비공개";
  }

  async function handleAddGuardian() {
    if (!addForm.name || !addForm.contact || !addForm.relationship) return;
    const payload: Parameters<typeof createGuardian>[0] = {
      name: addForm.name,
      phone_number: addForm.contactType === "phone" ? addForm.contact : null,
      email: addForm.contactType === "email" ? addForm.contact : null,
      relationship: addForm.relationship,
    };
    try {
      const g = await createGuardian(payload);
      setGuardians((prev) => [...prev, g]);
    } catch {
      // 등록 실패 시 모달만 닫음
    }
    setAddForm(DEFAULT_ADD_FORM);
    setShowModal(false);
  }

  async function handleDeleteGuardian(id: string) {
    await deleteGuardian(id).catch(() => {});
    setGuardians((prev) => prev.filter((g) => g.id !== id));
    setConfirmDeleteId(null);
  }

  async function handleCreateShareLink() {
    const categories = SHARE_ITEMS.filter((_, i) => shareToggles[i]).map((s) => s.category);
    if (categories.length === 0) return;
    setCreating(true);
    try {
      const link = await createShareLink({ period: sharePeriod, categories, detail: shareDetail });
      setShareLinks((prev) => [link, ...prev]);
    } finally {
      setCreating(false);
    }
  }

  async function handleDeleteShareLink(id: string) {
    await deleteShareLink(id).catch(() => {});
    setShareLinks((prev) => prev.filter((l) => l.id !== id));
  }

  return (
    <>
      <header className="sticky top-0 z-40 flex items-center gap-3 border-b border-border bg-background px-4 py-3">
        <button onClick={() => router.push("/home")} aria-label="뒤로가기">
          <ArrowLeft className="h-6 w-6" />
        </button>
        <h1 className="text-lg font-bold">보호자 공유</h1>
      </header>

      <main className="mx-auto w-full max-w-md px-5 py-6">
        {/* 배너 */}
        <div className="flex items-center gap-3 rounded-2xl border border-primary/30 bg-orange-50 p-4">
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-primary/10">
            <User className="h-5 w-5 text-primary" />
          </div>
          <div>
            <p className="font-bold">보호자와 건강정보 공유</p>
            <p className="text-sm text-muted-foreground">가족이 내 상태를 함께 확인할 수 있어요</p>
          </div>
        </div>

        {/* 보호자 목록 */}
        <p className="mt-6 text-sm font-semibold">
          등록된 보호자 <span className="text-primary">{guardians.length}</span>/3
        </p>
        <div className="mt-2 space-y-3">
          {guardians.map((g, i) =>
            confirmDeleteId === g.id ? (
              <Card key={g.id} className="flex items-center justify-between gap-3 p-4 border-red-200 bg-red-50">
                <p className="text-sm font-medium text-red-600">
                  {g.name}을(를) 삭제할까요?
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setConfirmDeleteId(null)}
                    className="rounded-lg border border-border bg-white px-3 py-1.5 text-xs font-medium"
                  >
                    취소
                  </button>
                  <button
                    onClick={() => handleDeleteGuardian(g.id)}
                    className="rounded-lg bg-red-500 px-3 py-1.5 text-xs font-medium text-white"
                  >
                    삭제
                  </button>
                </div>
              </Card>
            ) : (
              <Card
                key={g.id}
                className="flex cursor-pointer items-center gap-3 p-4 hover:bg-muted/40 transition-colors"
                onClick={() => router.push(`/guardian/${g.id}`)}
              >
                <div
                  className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-full"
                  style={{ background: COLORS[i % COLORS.length] + "22" }}
                >
                  <User className="h-5 w-5" style={{ color: COLORS[i % COLORS.length] }} />
                </div>
                <div className="flex-1">
                  <p className="font-bold">{g.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {g.relationship} · {scopeLabel()}
                  </p>
                </div>
                <button
                  aria-label="삭제"
                  onClick={(e) => { e.stopPropagation(); setConfirmDeleteId(g.id); }}
                  className="flex-shrink-0 rounded-lg p-1.5 text-muted-foreground hover:bg-red-50 hover:text-red-500 transition-colors"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </Card>
            )
          )}
        </div>

        {/* 보호자 추가 버튼 */}
        {guardians.length < 3 && (
          <button
            onClick={() => setShowModal(true)}
            className="mt-3 flex w-full items-center justify-center gap-1 rounded-2xl border-2 border-dashed border-primary py-4 text-sm font-semibold text-primary"
          >
            <Plus className="h-4 w-4" /> 보호자 추가
          </button>
        )}

        {/* 공유 항목 설정 */}
        <p className="mt-6 text-sm font-semibold text-muted-foreground">공유 항목 설정</p>
        <Card className="mt-2 divide-y divide-border">
          {SHARE_ITEMS.map((item, i) => (
            <div key={item.category} className="flex items-center justify-between px-4 py-3.5">
              <span className="text-sm">{item.label}</span>
              <Toggle
                on={shareToggles[i]}
                onChange={(v) => setShareToggles((prev) => prev.map((x, j) => (j === i ? v : x)))}
              />
            </div>
          ))}
        </Card>

        {/* 공유 기간 */}
        <p className="mt-5 text-sm font-semibold">공유 기간</p>
        <div className="mt-2 grid grid-cols-4 gap-2">
          {PERIODS.map((p) => (
            <button
              key={p.value}
              onClick={() => setSharePeriod(p.value)}
              className={
                "rounded-xl border py-2.5 text-xs font-medium transition-colors " +
                (sharePeriod === p.value
                  ? "border-primary bg-primary text-white"
                  : "border-border bg-card text-foreground")
              }
            >
              {p.label}
            </button>
          ))}
        </div>

        {/* 세부 공개 수준 */}
        <p className="mt-5 text-sm font-semibold">세부 공개 수준</p>
        <div className="mt-2 space-y-2">
          {(["summary", "full"] as const).map((d) => {
            const label = d === "summary" ? "요약만" : "전체 데이터";
            const desc = d === "summary" ? "주요 수치와 요약 정보만 공유" : "모든 기록을 상세히 공유";
            return (
              <button
                key={d}
                onClick={() => setShareDetail(d)}
                className={
                  "flex w-full items-center gap-3 rounded-xl border p-3.5 text-left transition-colors " +
                  (shareDetail === d ? "border-primary bg-primary/5" : "border-border bg-card")
                }
              >
                <div
                  className={
                    "h-4 w-4 flex-shrink-0 rounded-full border-2 " +
                    (shareDetail === d ? "border-primary bg-primary" : "border-muted-foreground")
                  }
                />
                <div>
                  <p className="text-sm font-medium">{label}</p>
                  <p className="text-xs text-muted-foreground">{desc}</p>
                </div>
              </button>
            );
          })}
        </div>

        {/* 공유 링크 생성 */}
        <button
          onClick={handleCreateShareLink}
          disabled={shareToggles.every((v) => !v) || creating}
          className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl bg-primary py-3.5 text-sm font-semibold text-white disabled:opacity-50"
        >
          <LinkIcon className="h-4 w-4" />
          {creating ? "생성 중..." : "공유 링크 생성"}
        </button>

        {/* 활성 공유 링크 */}
        {shareLinks.length > 0 && (
          <div className="mt-5">
            <p className="text-sm font-semibold">활성 공유 링크</p>
            <div className="mt-2 space-y-2">
              {shareLinks.map((link) => (
                <Card key={link.id} className="p-4">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-xs font-medium text-primary">{link.url}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {PERIODS.find((p) => p.value === link.period)?.label} ·{" "}
                        {link.categories
                          .map((c) => SHARE_ITEMS.find((s) => s.category === c)?.label)
                          .join(", ")}
                      </p>
                    </div>
                    <button
                      onClick={() => handleDeleteShareLink(link.id)}
                      aria-label="공유 철회"
                      className="flex-shrink-0 rounded-lg bg-red-50 p-1.5 text-red-500"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* 안내 문구 */}
        <p className="mt-6 text-center text-xs text-muted-foreground">
          보호자는 정보 열람만 가능하며<br />회원님의 데이터를 수정할 수 없습니다
        </p>
      </main>

      {/* 보호자 추가 모달 */}
      {showModal && (
        <div
          className="fixed inset-0 z-50 flex items-end bg-black/40"
          onClick={() => setShowModal(false)}
        >
          <div
            className="mx-auto w-full max-w-md rounded-t-3xl bg-background p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-bold">보호자 추가</h2>
              <button onClick={() => setShowModal(false)}>
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground">이름</label>
                <input
                  value={addForm.name}
                  onChange={(e) => setAddForm((f) => ({ ...f, name: e.target.value }))}
                  placeholder="보호자 이름"
                  className="mt-1 w-full rounded-xl border border-border bg-card px-3 py-2.5 text-sm outline-none focus:border-primary"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">연락처 유형</label>
                <div className="mt-1 flex gap-2">
                  {(["phone", "email"] as const).map((t) => (
                    <button
                      key={t}
                      onClick={() => setAddForm((f) => ({ ...f, contactType: t }))}
                      className={
                        "flex-1 rounded-xl border py-2 text-xs font-medium transition-colors " +
                        (addForm.contactType === t
                          ? "border-primary bg-primary text-white"
                          : "border-border bg-card")
                      }
                    >
                      {t === "phone" ? "전화번호" : "이메일"}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  {addForm.contactType === "phone" ? "전화번호" : "이메일"}
                </label>
                <input
                  value={addForm.contact}
                  onChange={(e) => setAddForm((f) => ({ ...f, contact: e.target.value }))}
                  placeholder={addForm.contactType === "phone" ? "010-0000-0000" : "example@email.com"}
                  type={addForm.contactType === "email" ? "email" : "tel"}
                  className="mt-1 w-full rounded-xl border border-border bg-card px-3 py-2.5 text-sm outline-none focus:border-primary"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">관계</label>
                <div className="mt-1 flex flex-wrap gap-2">
                  {RELATIONS.map((r) => (
                    <button
                      key={r}
                      onClick={() => setAddForm((f) => ({ ...f, relationship: r }))}
                      className={
                        "rounded-full border px-3 py-1 text-xs font-medium transition-colors " +
                        (addForm.relationship === r
                          ? "border-primary bg-primary text-white"
                          : "border-border bg-card")
                      }
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <button
              onClick={handleAddGuardian}
              disabled={!addForm.name || !addForm.contact || !addForm.relationship}
              className="mt-5 w-full rounded-2xl bg-primary py-3.5 text-sm font-semibold text-white disabled:opacity-50"
            >
              추가하기
            </button>
          </div>
        </div>
      )}
    </>
  );
}
