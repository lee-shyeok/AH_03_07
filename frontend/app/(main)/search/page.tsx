"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Search, X, Pill, FileText, BookOpen, BarChart3, ChevronRight, Gift } from "lucide-react";

const POPULAR = ["통증", "관절통", "활성도", "수면", "복약 시간", "메토트렉세이트"];
const CATEGORIES = [
  { label: "내 약물", href: "/medication", icon: Pill },
  { label: "진료 기록", href: "/records", icon: FileText },
  { label: "가이드 모음", href: "/guides", icon: BookOpen },
  { label: "활성도 기록", href: "/lab", icon: BarChart3 },
  { label: "혜택 · 게임", href: "/rewards", icon: Gift },
];

export default function SearchPage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [recent, setRecent] = useState<string[]>([
    "메토트렉세이트",
    "활성도 기록 방법",
    "비염",
    "면역억제제 부작용",
  ]);

  function submit(q: string) {
    const term = q.trim();
    if (!term) return;
    setRecent((prev) => [term, ...prev.filter((r) => r !== term)].slice(0, 10));
    setQuery(term);
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-8">
      {/* 검색바 */}
      <div className="flex items-center gap-2">
        <button onClick={() => router.back()} aria-label="뒤로">
          <ChevronRight className="h-6 w-6 rotate-180 text-foreground" />
        </button>
        <div className="flex flex-1 items-center gap-2 rounded-full bg-muted px-4 py-2.5">
          <Search className="h-4 w-4 text-muted-foreground" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit(query)}
            placeholder="검색..."
            className="flex-1 bg-transparent text-sm outline-none"
          />
        </div>
      </div>

      {/* 최근 검색어 */}
      {recent.length > 0 && (
        <section className="mt-7">
          <h2 className="text-sm font-semibold text-muted-foreground">최근 검색어</h2>
          <div className="mt-2 overflow-hidden rounded-xl border border-border">
            {recent.map((r, i) => (
              <div
                key={r}
                className={"flex items-center justify-between px-4 py-3 " + (i > 0 ? "border-t border-border" : "")}
              >
                <button onClick={() => submit(r)} className="text-sm">{r}</button>
                <button onClick={() => setRecent((prev) => prev.filter((x) => x !== r))} aria-label="삭제">
                  <X className="h-4 w-4 text-muted-foreground" />
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 인기 검색어 */}
      <section className="mt-7">
        <h2 className="text-sm font-semibold text-muted-foreground">인기 검색어</h2>
        <div className="mt-2 flex flex-wrap gap-2">
          {POPULAR.map((p) => (
            <button
              key={p}
              onClick={() => submit(p)}
              className="rounded-full border border-border px-3.5 py-2 text-sm font-medium"
            >
              {p}
            </button>
          ))}
        </div>
      </section>

      {/* 카테고리별 탐색 */}
      <section className="mt-7">
        <h2 className="text-sm font-semibold text-muted-foreground">카테고리별 탐색</h2>
        <div className="mt-2 overflow-hidden rounded-xl border border-border">
          {CATEGORIES.map(({ label, href, icon: Icon }, i) => (
            <button
              key={label}
              onClick={() => router.push(href)}
              className={"flex w-full items-center gap-3 px-4 py-3.5 " + (i > 0 ? "border-t border-border" : "")}
            >
              <Icon className="h-5 w-5 text-muted-foreground" />
              <span className="flex-1 text-left text-sm">{label}</span>
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}
