"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Calendar as CalendarIcon,
  ChevronDown,
  Info,
  Pencil,
  Plus,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import {
  createLabResult,
  listLabReferences,
  type LabReferenceResponse,
} from "@/features/lab-results/api";

const PURPLE = "#7C5CCF";


const EXCLUDED_CODES = ["XRAY_HANDFOOT", "JOINT_US", "MRI"];

function pad(n: number) {
  return String(n).padStart(2, "0");
}
function todayStr() {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}
function fmtDot(iso: string) {
  const [y, m, d] = iso.split("-");
  return `${y}.${m}.${d}`;
}

// state에는 code(=test_type) + 사용자 직접입력값만. name_ko/unit 등은 렌더 시 labRefs에서 파생.
type Item = {
  test_type: string; // = code
  value: string;
  reference_range: string;
};
const EMPTY_ITEM: Item = {
  test_type: "",
  value: "",
  reference_range: "",
};

export default function LabResultsPage() {
  const router = useRouter();
  const dateRef = useRef<HTMLInputElement>(null);

  const [testDate, setTestDate] = useState<string>(todayStr());
  const [items, setItems] = useState<Item[]>([{ ...EMPTY_ITEM }]);
  const [memo, setMemo] = useState("");
  const [saving, setSaving] = useState(false);
  const [labRefs, setLabRefs] = useState<LabReferenceResponse[]>([]);

  useEffect(() => {
    listLabReferences().then(setLabRefs).catch(() => {});
  }, []);

  // 데스크톱 Chrome은 인풋 클릭만으론 달력이 안 열려 showPicker()로 직접 호출
  function openDatePicker() {
    const el = dateRef.current as (HTMLInputElement & { showPicker?: () => void }) | null;
    if (el?.showPicker) el.showPicker();
  }

  function patchItem(idx: number, patch: Partial<Item>) {
    setItems((arr) => arr.map((it, i) => (i === idx ? { ...it, ...patch } : it)));
  }
  function addItem() {
    setItems((arr) => [...arr, { ...EMPTY_ITEM }]);
  }
  function removeItem(idx: number) {
    setItems((arr) => (arr.length === 1 ? arr : arr.filter((_, i) => i !== idx)));
  }

  const validItems = items.filter((it) => it.test_type.trim() && it.value.trim());

  async function handleSave() {
    if (validItems.length === 0) return;
    setSaving(true);
    try {
      for (const it of validItems) {
        const ref = labRefs.find((r) => r.code === it.test_type.trim());
        const unit = ref?.unit ?? "";
        const value = unit ? `${it.value.trim()} ${unit}` : it.value.trim();
        await createLabResult({
          test_date: testDate,
          test_type: it.test_type.trim(),
          user_recorded_value: value,
          // reference_range는 사용자가 검사지 보고 직접 입력한 값만 저장
          // reference_range_general(마스터 예시값) 절대 자동기입 금지 (REQ-LAB-001)
          reference_range: it.reference_range.trim() || null,
          note: memo.trim() || null,
        });
      }
      router.push("/lab-results/list");
    } catch {
      /* 실패 시 입력값 유지 */
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="mx-auto min-h-screen w-full max-w-md px-5 py-8">
      {/* 헤더 */}
      <div className="flex items-center gap-3">
        <button type="button" onClick={() => router.back()} className="flex items-center justify-center rounded-full p-1.5 hover:bg-muted text-lg font-semibold" aria-label="뒤로가기">
          &lt;
        </button>
        <h1 className="text-2xl font-bold">검사 결과 입력</h1>
      </div>

      {/* 자가면역 배너 */}
      <div
        className="mt-6 flex items-center gap-3 rounded-2xl border p-4"
        style={{ borderColor: PURPLE + "55", background: PURPLE + "12" }}
      >
        <div
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl"
          style={{ background: PURPLE + "22" }}
        >
          <Pencil className="h-5 w-5" style={{ color: PURPLE }} />
        </div>
        <div>
          <p className="font-bold">자가면역 검사 결과 추적</p>
          <p className="text-sm" style={{ color: PURPLE }}>
            시간순 변화를 의료진과 공유
          </p>
        </div>
      </div>

      {/* 검사 일자 — 박스 클릭 시 showPicker()로 달력 오픈 */}
      <p className="mt-7 text-sm font-semibold text-muted-foreground">검사 일자</p>
      <div
        className="relative mt-2 cursor-pointer rounded-2xl border bg-white"
        onClick={openDatePicker}
      >
        <CalendarIcon
          className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2"
          style={{ color: PURPLE }}
        />
        <span className="block py-3.5 text-center text-lg font-bold">{fmtDot(testDate)}</span>
        <ChevronDown className="pointer-events-none absolute right-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
        <input
          ref={dateRef}
          type="date"
          value={testDate}
          onChange={(e) => e.target.value && setTestDate(e.target.value)}
          aria-label="검사 일자 선택"
          className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
        />
      </div>

      {/* 검사 항목 */}
      <p className="mt-7 text-sm font-semibold text-muted-foreground">검사 항목</p>
      {/* datalist: value=code, 텍스트=한글명 → 코드 또는 한글로 검색 가능, 선택값은 code로 저장 */}
      <datalist id="lab-presets">
        {labRefs
          .filter((r) => !EXCLUDED_CODES.includes(r.code))
          .map((r) => (
            <option key={r.code} value={r.code}>
              {r.name_ko}
            </option>
          ))}
      </datalist>
      <div className="mt-2 space-y-3">
        {items.map((it, idx) => {
          // name_ko·category·unit·reference_range_general 은 state 복제 없이 렌더 시 파생
          const ref = labRefs.find((r) => r.code === it.test_type);
          const labelLine = ref
            ? [ref.name_ko, ref.category].filter(Boolean).join(" / ")
            : null;
          const unitStr = ref?.unit ?? null; // null이면 단위 suffix 숨김 (영상검사 등)
          const rangePlaceholder = ref?.reference_range_general
            ? `참고 범위 예: ${ref.reference_range_general}`
            : "참고 범위 (검사지 그대로, 선택)";
          return (
            <Card key={idx} className="relative p-4" style={{ background: PURPLE + "12" }}>
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <input
                    list="lab-presets"
                    value={it.test_type}
                    onChange={(e) => patchItem(idx, { test_type: e.target.value })}
                    maxLength={128}
                    placeholder="검사 종류"
                    className="w-full bg-transparent text-base font-bold outline-none placeholder:font-normal placeholder:text-muted-foreground"
                  />
                  {/* 주황: name_ko / category — labRefs에서 파생, 읽기 전용 */}
                  {labelLine && (
                    <p className="mt-0.5 text-xs" style={{ color: PURPLE }}>
                      {labelLine}
                    </p>
                  )}
                </div>
              </div>

              {/* 수치 + 단위 suffix (노랑: unit은 master에서 파생, null이면 숨김) */}
              <div className="mt-3 flex items-center gap-2 rounded-xl bg-muted/40 px-3 py-3">
                <input
                  value={it.value}
                  onChange={(e) => patchItem(idx, { value: e.target.value })}
                  placeholder=""
                  className="min-w-0 flex-1 bg-transparent text-xl font-bold outline-none"
                />
                {unitStr && (
                  <span className="shrink-0 text-sm text-muted-foreground">{unitStr}</span>
                )}
              </div>

              {/* 참고범위 (초록: placeholder만 예시 — 저장은 사용자 입력값만, 자동기입 X) */}
              <input
                value={it.reference_range}
                onChange={(e) => patchItem(idx, { reference_range: e.target.value })}
                placeholder={rangePlaceholder}
                className="mt-2 w-full bg-transparent text-xs text-muted-foreground outline-none"
              />

              {items.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeItem(idx)}
                  className="mt-2 block w-full text-right text-xs text-muted-foreground"
                >
                  항목 삭제
                </button>
              )}
            </Card>
          );
        })}
      </div>

      {/* + 검사 항목 추가 */}
      <button
        type="button"
        onClick={addItem}
        className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-2xl border-2 border-dashed py-3.5 text-sm font-semibold"
        style={{ borderColor: PURPLE + "66", color: PURPLE }}
      >
        <Plus className="h-4 w-4" />
        검사 항목 추가
      </button>

      {/* 메모 */}
      <p className="mt-7 text-sm font-semibold text-muted-foreground">
        메모 <span className="font-normal">(선택)</span>
      </p>
      <textarea
        value={memo}
        onChange={(e) => setMemo(e.target.value)}
        rows={2}
        placeholder="예: 다음 진료 시 의료진과 상의"
        className="mt-2 w-full rounded-2xl border px-4 py-3 text-sm"
      />

      {/* 안전 안내 */}
      <div className="mt-4 flex items-start gap-2 rounded-xl border bg-muted/40 p-3 text-xs text-muted-foreground">
        <Info className="mt-0.5 h-4 w-4 shrink-0" />
        <p>
          수치·참고범위·상태 표시는 모두 사용자가 검사지를 보고 직접 입력·선택한 값입니다.
          앱은 자동 정상/비정상 판정을 수행하지 않으며, 결과 해석은 담당 의료진 상담을 권고합니다.
        </p>
      </div>

      {/* 저장하기 */}
      <button
        type="button"
        onClick={handleSave}
        disabled={saving || validItems.length === 0}
        className="mt-5 w-full rounded-2xl py-4 text-base font-bold text-white disabled:opacity-50"
        style={{ background: PURPLE }}
      >
        {saving ? "저장 중..." : "저장하기"}
      </button>
    </main>
  );
}
