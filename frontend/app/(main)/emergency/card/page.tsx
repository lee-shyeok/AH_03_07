"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { FileText, ArrowLeft, Plus, X, User, Phone, Heart } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  getEmergencyCard,
  updateEmergencyCard,
  type EmergencyCard,
  type EmergencyContact,
} from "@/features/emergency/api";

const RED = "#EF5B5B";

const BLOOD_TYPE_OPTIONS = [
  "A형 Rh+",
  "A형 Rh-",
  "B형 Rh+",
  "B형 Rh-",
  "O형 Rh+",
  "O형 Rh-",
  "AB형 Rh+",
  "AB형 Rh-",
];

const MOCK_CARD: EmergencyCard = {
  blood_type: "A형 Rh+",
  chronic_conditions: "류마티스 관절염",
  medications: "메토트렉세이트 7.5mg",
  allergies: "페니실린",
  emergency_contacts: [],
  show_on_lock_screen: true,
  send_location: true,
};

/* ── 전화번호 자동 포맷 ─────────────────────────────────── */
function formatPhone(raw: string): string {
  const digits = raw.replace(/\D/g, "").slice(0, 11);
  if (digits.startsWith("02")) {
    if (digits.length <= 2) return digits;
    if (digits.length <= 5) return `${digits.slice(0, 2)}-${digits.slice(2)}`;
    if (digits.length <= 9) return `${digits.slice(0, 2)}-${digits.slice(2, 5)}-${digits.slice(5)}`;
    return `${digits.slice(0, 2)}-${digits.slice(2, 6)}-${digits.slice(6)}`;
  }
  if (digits.length <= 3) return digits;
  if (digits.length <= 7) return `${digits.slice(0, 3)}-${digits.slice(3)}`;
  if (digits.length <= 10) return `${digits.slice(0, 3)}-${digits.slice(3, 6)}-${digits.slice(6)}`;
  return `${digits.slice(0, 3)}-${digits.slice(3, 7)}-${digits.slice(7)}`;
}

/* ── 혈액형 초기화 ──────────────────────────────────────── */
function initBloodTypeMode(value: string): { select: string; custom: string } {
  if (!value) return { select: "", custom: "" };
  if (BLOOD_TYPE_OPTIONS.includes(value)) return { select: value, custom: "" };
  return { select: "직접입력", custom: value };
}

/* ── 토글 ───────────────────────────────────────────────── */
function Toggle({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      role="switch"
      aria-checked={on}
      onClick={() => onChange(!on)}
      className={"relative h-6 w-11 rounded-full transition-colors " + (on ? "bg-primary" : "bg-muted")}
    >
      <span className={"absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform " + (on ? "translate-x-5" : "translate-x-0.5")} />
    </button>
  );
}

/* ── 등록된 보호자 카드 ─────────────────────────────────── */
function GuardianCard({
  guardian,
  index,
  onRemove,
}: {
  guardian: EmergencyContact;
  index: number;
  onRemove: () => void;
}) {
  return (
    <Card className="px-4 py-3">
      <div className="flex items-start justify-between">
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-1.5">
            <span
              className="rounded-full px-2 py-0.5 text-[11px] font-semibold"
              style={{ background: RED + "18", color: RED }}
            >
              보호자 {index + 1}
            </span>
            {guardian.relationship && (
              <span className="text-xs text-muted-foreground">{guardian.relationship}</span>
            )}
          </div>
          <p className="text-sm font-semibold">{guardian.name || "이름 없음"}</p>
          {guardian.phone && (
            <p className="text-xs text-muted-foreground">{guardian.phone}</p>
          )}
        </div>
        <button
          onClick={onRemove}
          className="mt-0.5 rounded-full p-1 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </Card>
  );
}

/* ── 보호자 입력 폼 ─────────────────────────────────────── */
function GuardianForm({
  onAdd,
  onCancel,
}: {
  onAdd: (g: EmergencyContact) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [relationship, setRelationship] = useState("");

  const nameRef = useRef<HTMLInputElement>(null);
  const phoneRef = useRef<HTMLInputElement>(null);
  const relationRef = useRef<HTMLInputElement>(null);

  // 폼이 마운트되면 이름 필드에 자동 포커스
  useEffect(() => {
    nameRef.current?.focus();
  }, []);

  function handlePhoneChange(value: string) {
    setPhone(formatPhone(value));
  }

  function handleAdd() {
    if (!name.trim()) {
      nameRef.current?.focus();
      return;
    }
    onAdd({ name: name.trim(), phone, relationship: relationship.trim() });
  }

  return (
    <Card className="mt-2 divide-y divide-border overflow-hidden">
      {/* 이름 */}
      <div className="flex items-center gap-3 px-4 py-3">
        <User className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
        <div className="flex-1">
          <Label className="text-xs text-muted-foreground">이름</Label>
          <Input
            ref={nameRef}
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && phoneRef.current?.focus()}
            placeholder="홍길동"
            className="mt-0.5 border-0 p-0 text-sm font-semibold shadow-none focus-visible:ring-0"
          />
        </div>
      </div>

      {/* 전화번호 */}
      <div className="flex items-center gap-3 px-4 py-3">
        <Phone className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
        <div className="flex-1">
          <Label className="text-xs text-muted-foreground">전화번호</Label>
          <Input
            ref={phoneRef}
            value={phone}
            onChange={(e) => handlePhoneChange(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && relationRef.current?.focus()}
            placeholder="010-0000-0000"
            inputMode="tel"
            className="mt-0.5 border-0 p-0 text-sm font-semibold shadow-none focus-visible:ring-0"
          />
        </div>
      </div>

      {/* 관계 */}
      <div className="flex items-center gap-3 px-4 py-3">
        <Heart className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
        <div className="flex-1">
          <Label className="text-xs text-muted-foreground">관계</Label>
          <Input
            ref={relationRef}
            value={relationship}
            onChange={(e) => setRelationship(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
            placeholder="어머니, 아버지, 배우자 …"
            className="mt-0.5 border-0 p-0 text-sm font-semibold shadow-none focus-visible:ring-0"
          />
        </div>
      </div>

      {/* 버튼 */}
      <div className="flex gap-2 px-4 py-3">
        <button
          onClick={onCancel}
          className="flex-1 rounded-xl border py-2 text-sm font-medium text-muted-foreground"
        >
          취소
        </button>
        <button
          onClick={handleAdd}
          className="flex-1 rounded-xl py-2 text-sm font-semibold text-white"
          style={{ background: RED }}
        >
          추가
        </button>
      </div>
    </Card>
  );
}

/* ── 메인 페이지 ────────────────────────────────────────── */
export default function EmergencyCardPage() {
  const router = useRouter();

  const [bloodTypeSelect, setBloodTypeSelect] = useState("");
  const [bloodTypeCustom, setBloodTypeCustom] = useState("");
  const [chronicConditions, setChronicConditions] = useState("");
  const [medications, setMedications] = useState("");
  const [allergies, setAllergies] = useState("");
  const [guardians, setGuardians] = useState<EmergencyContact[]>([]);
  const [showGuardianForm, setShowGuardianForm] = useState(false);
  const [lockScreen, setLockScreen] = useState(true);
  const [sendLocation, setSendLocation] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getEmergencyCard()
      .then((data) => applyCard(data))
      .catch(() => applyCard(MOCK_CARD));
  }, []);

  function applyCard(data: EmergencyCard) {
    const { select, custom } = initBloodTypeMode(data.blood_type ?? MOCK_CARD.blood_type ?? "");
    setBloodTypeSelect(select);
    setBloodTypeCustom(custom);
    setChronicConditions(data.chronic_conditions ?? MOCK_CARD.chronic_conditions ?? "");
    setMedications(data.medications ?? MOCK_CARD.medications ?? "");
    setAllergies(data.allergies ?? MOCK_CARD.allergies ?? "");
    setGuardians((data.emergency_contacts ?? MOCK_CARD.emergency_contacts ?? []).slice(0, 3));
    setLockScreen(data.show_on_lock_screen ?? true);
    setSendLocation(data.send_location ?? true);
  }

  function getBloodType(): string {
    return bloodTypeSelect === "직접입력" ? bloodTypeCustom : bloodTypeSelect;
  }

  function handleGuardianAdd(g: EmergencyContact) {
    setGuardians((prev) => [...prev, g].slice(0, 3));
    setShowGuardianForm(false);
  }

  function removeGuardian(index: number) {
    setGuardians((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSave() {
    setSaving(true);
    setError("");
    try {
      await updateEmergencyCard({
        blood_type: getBloodType(),
        chronic_conditions: chronicConditions,
        medications,
        allergies,
        emergency_contacts: guardians,
        show_on_lock_screen: lockScreen,
        send_location: sendLocation,
      });
      setSaved(true);
      setTimeout(() => router.push("/emergency"), 800);
    } catch {
      setError("저장에 실패했습니다. 다시 시도해 주세요.");
      setSaving(false);
    }
  }

  const canAddMore = guardians.length < 3 && !showGuardianForm;

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8 pb-28">
      {/* 뒤로가기 */}
      <button
        onClick={() => router.push("/emergency")}
        className="mb-4 flex items-center gap-1 text-sm text-muted-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        응급 SOS
      </button>

      <h1 className="text-xl font-bold">응급 카드 설정</h1>

      {/* 배너 */}
      <div
        className="mt-4 flex items-center gap-3 rounded-2xl border p-4"
        style={{ borderColor: RED + "55", background: RED + "12" }}
      >
        <FileText className="h-6 w-6" style={{ color: RED }} />
        <div>
          <p className="font-bold" style={{ color: RED }}>응급 카드 정보 관리</p>
          <p className="text-sm" style={{ color: RED }}>응급 시 구급대원에게 표시될 정보입니다</p>
        </div>
      </div>

      {/* 기본 의료정보 */}
      <p className="mt-6 text-sm text-muted-foreground">기본 의료정보</p>
      <Card className="mt-2 divide-y divide-border">
        {/* 혈액형 */}
        <div className="px-4 py-3">
          <Label className="text-xs text-muted-foreground">혈액형</Label>
          <select
            value={bloodTypeSelect}
            onChange={(e) => {
              setBloodTypeSelect(e.target.value);
              if (e.target.value !== "직접입력") setBloodTypeCustom("");
            }}
            className="mt-1 w-full border-0 bg-transparent p-0 text-sm font-semibold focus:outline-none"
          >
            <option value="">선택하세요</option>
            {BLOOD_TYPE_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
            <option value="직접입력">직접 입력</option>
          </select>
          {bloodTypeSelect === "직접입력" && (
            <Input
              value={bloodTypeCustom}
              onChange={(e) => setBloodTypeCustom(e.target.value)}
              placeholder="혈액형을 직접 입력하세요"
              className="mt-2 border-0 border-t p-0 pt-2 text-sm font-semibold shadow-none focus-visible:ring-0"
            />
          )}
        </div>

        {/* 기저 질환 */}
        <div className="px-4 py-3">
          <Label htmlFor="chronic_conditions" className="text-xs text-muted-foreground">기저 질환</Label>
          <Input
            id="chronic_conditions"
            value={chronicConditions}
            onChange={(e) => setChronicConditions(e.target.value)}
            placeholder="예: 류마티스 관절염"
            className="mt-1 border-0 p-0 text-sm font-semibold shadow-none focus-visible:ring-0"
          />
        </div>

        {/* 복용 약물 */}
        <div className="px-4 py-3">
          <Label htmlFor="medications" className="text-xs text-muted-foreground">복용 약물</Label>
          <Input
            id="medications"
            value={medications}
            onChange={(e) => setMedications(e.target.value)}
            placeholder="예: 메토트렉세이트 7.5mg"
            className="mt-1 border-0 p-0 text-sm font-semibold shadow-none focus-visible:ring-0"
          />
        </div>

        {/* 알레르기 */}
        <div className="px-4 py-3">
          <Label htmlFor="allergies" className="text-xs text-muted-foreground">알레르기</Label>
          <Input
            id="allergies"
            value={allergies}
            onChange={(e) => setAllergies(e.target.value)}
            placeholder="예: 페니실린"
            className="mt-1 border-0 p-0 text-sm font-semibold shadow-none focus-visible:ring-0"
          />
        </div>
      </Card>

      {/* 보호자 정보 */}
      {guardians.length > 0 && (
        <div className="mt-6 flex flex-col gap-2">
          {guardians.map((g, i) => (
            <GuardianCard
              key={i}
              guardian={g}
              index={i}
              onRemove={() => removeGuardian(i)}
            />
          ))}
        </div>
      )}

      {showGuardianForm && (
        <GuardianForm
          onAdd={handleGuardianAdd}
          onCancel={() => setShowGuardianForm(false)}
        />
      )}

      {canAddMore && (
        <button
          onClick={() => setShowGuardianForm(true)}
          className={
            "flex w-full items-center justify-center gap-1.5 rounded-2xl border border-dashed py-3 text-sm font-medium transition-colors " +
            (guardians.length > 0 ? "mt-2" : "mt-6")
          }
          style={{ borderColor: RED + "55", color: RED }}
        >
          <Plus className="h-4 w-4" />
          보호자 추가
        </button>
      )}

      {/* 표시 설정 */}
      <p className="mt-6 text-sm text-muted-foreground">표시 설정</p>
      <Card className="mt-2 divide-y divide-border">
        <div className="flex items-center justify-between px-4 py-3.5">
          <div>
            <p className="text-sm">잠금화면에 표시</p>
            <p className="text-xs text-muted-foreground">잠금 상태에서도 응급 카드 접근</p>
          </div>
          <Toggle on={lockScreen} onChange={setLockScreen} />
        </div>
        <div className="flex items-center justify-between px-4 py-3.5">
          <div>
            <p className="text-sm">위치정보 함께 전송</p>
            <p className="text-xs text-muted-foreground">119 신고 시 현재 위치 자동 전송</p>
          </div>
          <Toggle on={sendLocation} onChange={setSendLocation} />
        </div>
      </Card>

      {error && (
        <p className="mt-3 text-center text-sm text-destructive">{error}</p>
      )}

      <div className="fixed inset-x-0 bottom-0 mx-auto max-w-md bg-background px-5 pb-6 pt-3">
        <Button
          className="w-full"
          size="lg"
          disabled={saving || saved}
          onClick={handleSave}
        >
          {saved ? "저장됨 ✓" : saving ? "저장 중…" : "저장하기"}
        </Button>
      </div>
    </main>
  );
}
