"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronLeft, Pill, Search, X } from "lucide-react";
import { Card } from "@/components/ui/card";
import {
  searchDrugReferences,
  type DrugInfo,
} from "@/features/pills/api";
import { usePillRecognitions } from "@/features/pills/queries";

export default function PillsRecognizePage() {
  const router = useRouter();

  const { data: history = [] } = usePillRecognitions();

  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<DrugInfo[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchDone, setSearchDone] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

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

  return (
    <main className="mx-auto flex w-full max-w-md flex-col pb-10">
      {/* 헤더 */}
      <div className="flex items-center gap-2 px-5 pt-8">
        <button
          onClick={() => router.push("/home")}
          className="rounded-full p-1 hover:bg-accent"
          aria-label="뒤로가기"
        >
          <ChevronLeft className="h-5 w-5" />
        </button>
        <h1 className="text-xl font-bold">약품 검색</h1>
      </div>

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
                    <p className="font-bold">{h.selected_drug_name ?? h.drug_name ?? "알 수 없음"}</p>
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
