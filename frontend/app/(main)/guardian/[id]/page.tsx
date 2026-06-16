"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft, User, Phone, Mail, Pencil, X } from "lucide-react";
import { Card } from "@/components/ui/card";
import { getGuardians, updateGuardian } from "@/features/guardian/api";
import type { Guardian, CreateGuardianData } from "@/features/guardian/api";

const MOCK_GUARDIANS: Guardian[] = [
  { id: "mock-1", name: "김영희", phone_number: "010-1234-5678", email: null, relationship: "어머니", is_active: true },
  { id: "mock-2", name: "김철수", phone_number: "010-9876-5432", email: null, relationship: "배우자", is_active: true },
];

const RELATIONS = ["어머니", "아버지", "배우자", "자녀", "형제/자매", "기타"];

const DEFAULT_EDIT_FORM = { name: "", contact: "", contactType: "phone" as "phone" | "email", relationship: "" };

export default function GuardianDetailPage() {
  const router = useRouter();
  const params = useParams();
  const [guardian, setGuardian] = useState<Guardian | null>(null);
  const [showEdit, setShowEdit] = useState(false);
  const [editForm, setEditForm] = useState(DEFAULT_EDIT_FORM);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const id = String(params.id);
    getGuardians()
      .catch(() => MOCK_GUARDIANS)
      .then((list) => {
        const found = list.find((g) => g.id === id) ?? null;
        setGuardian(found);
      });
  }, [params.id]);

  function openEdit() {
    if (!guardian) return;
    setEditForm({
      name: guardian.name,
      contact: guardian.phone_number ?? guardian.email ?? "",
      contactType: guardian.phone_number ? "phone" : "email",
      relationship: guardian.relationship ?? "",
    });
    setShowEdit(true);
  }

  async function handleSave() {
    if (!guardian || !editForm.name || !editForm.contact) return;
    setSaving(true);
    const payload: CreateGuardianData = {
      name: editForm.name,
      phone_number: editForm.contactType === "phone" ? editForm.contact : null,
      email: editForm.contactType === "email" ? editForm.contact : null,
      relationship: editForm.relationship || null,
    };
    try {
      const updated = await updateGuardian(guardian.id, payload);
      setGuardian(updated);
    } catch {
      setGuardian((prev) =>
        prev
          ? { ...prev, ...payload, phone_number: payload.phone_number ?? null, email: payload.email ?? null, relationship: payload.relationship ?? null }
          : prev
      );
    } finally {
      setSaving(false);
      setShowEdit(false);
    }
  }

  if (!guardian) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">
        불러오는 중...
      </div>
    );
  }

  const hasEmail = !guardian.phone_number && !!guardian.email;
  const ContactIcon = hasEmail ? Mail : Phone;
  const contactLabel = hasEmail ? "이메일" : "전화번호";
  const contactValue = guardian.phone_number ?? guardian.email ?? "-";

  return (
    <>
      <header className="sticky top-0 z-40 flex items-center gap-3 border-b border-border bg-background px-4 py-3">
        <button onClick={() => router.push("/guardian")} aria-label="뒤로가기">
          <ArrowLeft className="h-6 w-6" />
        </button>
        <h1 className="flex-1 text-lg font-bold">보호자 정보</h1>
        <button onClick={openEdit} aria-label="수정" className="rounded-lg p-1.5 hover:bg-muted transition-colors">
          <Pencil className="h-5 w-5 text-muted-foreground" />
        </button>
      </header>

      <main className="mx-auto w-full max-w-md px-5 py-6 space-y-4">
        <div className="flex flex-col items-center gap-3 py-6">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/10">
            <User className="h-10 w-10 text-primary" />
          </div>
          <p className="text-xl font-bold">{guardian.name}</p>
          <span className="rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary">
            {guardian.relationship ?? "-"}
          </span>
        </div>

        <Card className="divide-y divide-border">
          <div className="flex items-center gap-3 px-4 py-4">
            <ContactIcon className="h-5 w-5 flex-shrink-0 text-muted-foreground" />
            <div className="flex-1">
              <p className="text-xs text-muted-foreground">{contactLabel}</p>
              <p className="text-sm font-medium">{contactValue}</p>
            </div>
            {guardian.phone_number && (
              <a
                href={`tel:${guardian.phone_number}`}
                aria-label="전화 연결"
                className="flex items-center gap-1.5 rounded-xl bg-primary/10 px-3 py-1.5 text-xs font-medium text-primary"
              >
                <Phone className="h-3.5 w-3.5" />
                전화
              </a>
            )}
          </div>
          <div className="flex items-center gap-3 px-4 py-4">
            <User className="h-5 w-5 flex-shrink-0 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">관계</p>
              <p className="text-sm font-medium">{guardian.relationship ?? "-"}</p>
            </div>
          </div>
        </Card>

        <button
          onClick={openEdit}
          className="mt-2 w-full rounded-2xl border border-primary py-3.5 text-sm font-semibold text-primary transition-colors hover:bg-primary/5"
        >
          수정하기
        </button>
      </main>

      {/* 수정 모달 */}
      {showEdit && (
        <div
          className="fixed inset-0 z-50 flex items-end bg-black/40"
          onClick={() => setShowEdit(false)}
        >
          <div
            className="mx-auto w-full max-w-md rounded-t-3xl bg-background p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-bold">보호자 수정</h2>
              <button onClick={() => setShowEdit(false)}>
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground">이름</label>
                <input
                  value={editForm.name}
                  onChange={(e) => setEditForm((f) => ({ ...f, name: e.target.value }))}
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
                      onClick={() => setEditForm((f) => ({ ...f, contactType: t }))}
                      className={
                        "flex-1 rounded-xl border py-2 text-xs font-medium transition-colors " +
                        (editForm.contactType === t
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
                  {editForm.contactType === "phone" ? "전화번호" : "이메일"}
                </label>
                <input
                  value={editForm.contact}
                  onChange={(e) => setEditForm((f) => ({ ...f, contact: e.target.value }))}
                  placeholder={editForm.contactType === "phone" ? "010-0000-0000" : "example@email.com"}
                  type={editForm.contactType === "email" ? "email" : "tel"}
                  className="mt-1 w-full rounded-xl border border-border bg-card px-3 py-2.5 text-sm outline-none focus:border-primary"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">관계</label>
                <div className="mt-1 flex flex-wrap gap-2">
                  {RELATIONS.map((r) => (
                    <button
                      key={r}
                      onClick={() => setEditForm((f) => ({ ...f, relationship: r }))}
                      className={
                        "rounded-full border px-3 py-1 text-xs font-medium transition-colors " +
                        (editForm.relationship === r
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
              onClick={handleSave}
              disabled={!editForm.name || !editForm.contact || saving}
              className="mt-5 w-full rounded-2xl bg-primary py-3.5 text-sm font-semibold text-white disabled:opacity-50"
            >
              {saving ? "저장 중..." : "저장하기"}
            </button>
          </div>
        </div>
      )}
    </>
  );
}