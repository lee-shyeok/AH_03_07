"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Camera, Pill, Search, X } from "lucide-react";
import { Card } from "@/components/ui/card";
import {
  recognizePill,
  searchDrugReferences,
  type PillCandidate,
  type DrugInfo,
} from "@/features/pills/api";
import { usePillRecognitions } from "@/features/pills/queries";

interface StaticCandidate {
  name: string;
  ingredient: string;
  category: string;
  confidence: number;
}

const CANDIDATES: StaticCandidate[] = [
  { name: "타이레놀 500mg", ingredient: "아세트아미노펜", category: "해열진통제", confidence: 98 },
  { name: "게보린", ingredient: "아세트아미노펜 복합", category: "진통제", confidence: 85 },
  { name: "펜잘큐", ingredient: "아세트아미노펜 복합", category: "진통제", confidence: 72 },
];

export default function PillsRecognizePage() {
  const router = useRouter();
  const [candidates, setCandidates] = useState<PillCandidate[]>([]);
  const [recognizing, setRecognizing] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: history = [] } = usePillRecognitions();

  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<DrugInfo[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchDone, setSearchDone] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (preview) URL.revokeObjectURL(preview);
    setPreview(URL.createObjectURL(file));
    setRecognizing(true);
    setCandidates([]);
    try {
      const result = await recognizePill(file);
      setCandidates(result);
    } catch {
      setCandidates([]);
    } finally {
      setRecognizing(false);
      e.target.value = "";
    }
  };

  const openSearch = () => {
    setShowSearch(true);
    setSearchQuery("");
    setSearchResults([]);
    setSearchDone(false);
    setTimeout(() => searchInputRef.current?.focus(), 50);
  };

  const closeSearch = () => {
    setShowSearch(false);
    setSearchQuery("");
    setSearchResults([]);
    setSearchDone(false);
  };

  const handleSearch = async () => {
    const q = searchQuery.trim();
    if (!q || searching) return;
    setSearching(true);
    setSearchDone(false);
    setSearchResults([]);
    try {
      const result = await searchDrugReferences(q);
      setSearchResults(result);
    } catch {
      setSearchResults([]);
    } finally {
      setSearching(false);
      setSearchDone(true);
    }
  };

  const recognized = candidates.length > 0;

  const confidenceColors = (pct: number) =>
    pct >= 90
      ? { badge: "bg-green-100 text-green-700", icon: "bg-green-50", pill: "text-green-600" }
      : { badge: "bg-yellow-100 text-yellow-700", icon: "bg-yellow-50", pill: "text-yellow-600" };

  return (
    <main className="mx-auto flex w-full max-w-md flex-col pb-10">
      {/* 헤더 */}
      <div className="flex items-center gap-2 px-5 pt-8">
        <button
          onClick={() => router.push("/home")}
          className="flex items-center justify-center rounded-full p-1.5 hover:bg-muted"
          aria-label="뒤로가기"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <h1 className="text-xl font-bold">약품 카메라 인식</h1>
      </div>

      {/* 상단 안내 배너 */}
      <div className="mx-5 mt-4 rounded-2xl bg-orange-50 px-5 py-4 text-center">
        <p className="font-bold text-orange-600">약품을 촬영해주세요</p>
        <p className="mt-0.5 text-sm text-orange-400">인식 후보 중 직접 선택하세요</p>
      </div>

      {/* 카메라 뷰 영역 */}
      <div className="relative mx-5 mt-4 flex h-64 flex-col items-center justify-center overflow-hidden rounded-2xl bg-[#2A2D34]">
        {preview ? (
          <img src={preview} alt="업로드 이미지" className="h-full w-full object-contain" />
        ) : (
          <>
            <div className="h-32 w-48 rounded-full border-2 border-dashed border-white/50" />
            <p className="mt-4 text-xs text-white/60">알약을 가이드 안에 맞춰주세요</p>
          </>
        )}
        {recognizing && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-white border-t-transparent" />
          </div>
        )}
      </div>

      {/* 카메라 / 검색 버튼 */}
      <div className="mt-5 flex justify-center gap-4">
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={recognizing}
          className="flex h-16 w-16 items-center justify-center rounded-full bg-green-500 shadow-lg hover:bg-green-600 active:scale-95 disabled:opacity-50"
          aria-label="촬영"
        >
          <Camera className="h-7 w-7 text-white" />
        </button>
        <button
          onClick={openSearch}
          className="flex h-16 w-16 items-center justify-center rounded-full border border-border bg-background text-muted-foreground shadow"
          aria-label="검색"
        >
          <Search className="h-6 w-6" />
        </button>
      </div>

      {/* 숨김 파일 입력 */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={handleFileChange}
      />

      {/* 인식 결과 */}
      {recognized && (
        <div className="mx-5 mt-7">
          <p className="text-sm font-semibold text-muted-foreground">
            인식 결과 (Top {Math.min(candidates.length, 3)})
          </p>
          <div className="mt-3 space-y-3">
            {candidates.slice(0, 3).map((c, i) => {
              const pct =
                c.confidence > 1
                  ? Math.round(c.confidence)
                  : Math.round(c.confidence * 100);
              const colors = confidenceColors(pct);
              return (
                <Card
                  key={i}
                  className="flex cursor-pointer items-center gap-3 p-4 hover:bg-accent"
                  onClick={() => router.push(`/medication/${c.drug_name}`)}
                >
                  <div
                    className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${colors.icon}`}
                  >
                    <Pill className={`h-5 w-5 ${colors.pill}`} />
                  </div>
                  <div className="flex-1">
                    <p className="font-bold">{c.name ?? c.drug_name}</p>
                    <p className="text-sm text-muted-foreground">
                      {c.ingredient && `${c.ingredient} · `}{c.category}
                    </p>
                  </div>
                  <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-bold ${colors.badge}`}>
                    {pct}%
                  </span>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* 이전 인식 기록 */}
      {history.length > 0 && (
        <section className="mx-5 mt-8">
          <p className="text-sm font-semibold text-muted-foreground">이전 인식 기록</p>
          <div className="mt-2 space-y-2">
            {history.map((h) => {
              const pct =
                h.confidence !== undefined
                  ? h.confidence > 1
                    ? Math.round(h.confidence)
                    : Math.round(h.confidence * 100)
                  : null;
              return (
                <Card key={h.id} className="flex items-center gap-3 p-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-muted">
                    <Pill className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <div className="flex-1">
                    <p className="font-bold">{h.drug_name ?? "알 수 없음"}</p>
                    {h.created_at && (
                      <p className="text-xs text-muted-foreground">{h.created_at}</p>
                    )}
                  </div>
                  {pct !== null && (
                    <span className="shrink-0 rounded-full bg-muted px-2.5 py-1 text-xs font-bold text-muted-foreground">
                      {pct}%
                    </span>
                  )}
                </Card>
              );
            })}
          </div>
          <div className="mt-3 text-center">
            <Link href="/pills/history" className="text-sm text-primary hover:underline">
              인식 내역 보기
            </Link>
          </div>
        </section>
      )}

      {/* 정적 후보 예시 (촬영 전) */}
      {!recognized && !recognizing && (
        <div className="mx-5 mt-7">
          <p className="text-sm font-semibold text-muted-foreground">인식 예시</p>
          <div className="mt-2 space-y-3 opacity-40">
            {CANDIDATES.map((c) => {
              const high = c.confidence >= 90;
              return (
                <Card key={c.name} className="flex items-center gap-3 p-4">
                  <div
                    className={
                      "flex h-12 w-12 items-center justify-center rounded-xl " +
                      (high ? "bg-secondary" : "bg-muted")
                    }
                  >
                    <Pill
                      className={
                        "h-6 w-6 " + (high ? "text-primary" : "text-muted-foreground")
                      }
                    />
                  </div>
                  <div className="flex-1">
                    <p className="font-bold">{c.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {c.ingredient} · {c.category}
                    </p>
                  </div>
                  <span
                    className={
                      "rounded-full px-2.5 py-1 text-xs font-bold " +
                      (high ? "bg-secondary text-primary" : "bg-amber-50 text-amber-700")
                    }
                  >
                    {c.confidence}%
                  </span>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* 직접 검색 + 면책 문구 */}
      <div className="mx-5 mt-8">
        {!showSearch ? (
          <button
            onClick={openSearch}
            className="flex w-full items-center justify-center gap-2 rounded-2xl border border-border py-4 text-sm text-muted-foreground hover:bg-accent"
          >
            <Search className="h-4 w-4" />
            찾는 약품이 없어요 · 직접 검색
          </button>
        ) : (
          <div>
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold">약품 검색</p>
              <button
                onClick={closeSearch}
                className="rounded-full p-1 hover:bg-muted"
                aria-label="닫기"
              >
                <X className="h-4 w-4 text-muted-foreground" />
              </button>
            </div>
            <div className="mt-2 flex gap-2">
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="약품명 입력 (예: 타이레놀)"
                className="flex-1 rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-primary"
              />
              <button
                onClick={handleSearch}
                disabled={searching || !searchQuery.trim()}
                className="flex items-center justify-center rounded-xl bg-primary px-4 py-3 text-primary-foreground disabled:opacity-50"
                aria-label="검색"
              >
                {searching ? (
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                ) : (
                  <Search className="h-4 w-4" />
                )}
              </button>
            </div>

            {searchResults.length > 0 && (
              <div className="mt-3 space-y-2">
                {searchResults.map((drug, i) => (
                  <Card key={i} className="p-4">
                    <p className="font-bold">
                      {drug.item_name ?? drug.name ?? drug.drug_name}
                    </p>
                    {drug.entp_name && (
                      <p className="mt-0.5 text-xs text-muted-foreground">{drug.entp_name}</p>
                    )}
                    {drug.efcy_qesitm && (
                      <p className="mt-2 line-clamp-2 text-sm text-foreground">
                        {drug.efcy_qesitm}
                      </p>
                    )}
                  </Card>
                ))}
              </div>
            )}

            {searchDone && searchResults.length === 0 && (
              <p className="mt-4 text-center text-sm text-muted-foreground">
                검색 결과가 없습니다.
              </p>
            )}
          </div>
        )}

        <p className="mt-4 text-center text-xs text-muted-foreground">
          AI 인식 결과는 참고용입니다.<br />
          정확한 약품은 직접 확인 후 선택하세요
        </p>
      </div>
    </main>
  );
}
