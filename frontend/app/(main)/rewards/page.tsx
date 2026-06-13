"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Home, Gamepad2, ChevronRight } from "lucide-react";
import {
  levelOf, levelName, progressRatio, nextLevelPoints,
} from "@/features/gamification/types";
import { BADGES, REWARDS } from "@/features/gamification/data";
import { Helcy, HELCY_GREET, HELCY_NAME } from "@/features/gamification/Helcy";
import {
  getPoints, setPoints as persistPoints, isCheckedInToday, markCheckedIn,
  loadRoom,
} from "@/features/gamification/store";
import { helcyLevelFromItems } from "@/features/gamification/room";

type Tab = "badge" | "reward";

export default function RewardsPage() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("badge");
  const [mounted, setMounted] = useState(false);
  const [points, setPoints] = useState(0);
  const [checkedIn, setCheckedIn] = useState(false);
  const [helcyLv, setHelcyLv] = useState(1);

  useEffect(() => {
    setPoints(getPoints());
    setCheckedIn(isCheckedInToday());
    setHelcyLv(helcyLevelFromItems(loadRoom().ownedItemIds.length));
    setMounted(true);
  }, []);

  const lv = levelOf(points);
  const ratio = progressRatio(points);
  const earnedCount = BADGES.filter((b) => b.earned).length;

  function checkIn() {
    if (checkedIn) return;
    const np = points + 10;
    setPoints(np);
    persistPoints(np);
    markCheckedIn();
    setCheckedIn(true);
  }

  function buyReward(id: string, cost: number) {
    if (points < cost) return;
    const np = points - cost;
    setPoints(np);
    persistPoints(np);
  }

  if (!mounted) {
    return <main className="flex min-h-[60vh] items-center justify-center text-muted-foreground">불러오는 중…</main>;
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-8">
      <div className="flex items-center gap-2">
        <button onClick={() => router.back()} className="flex items-center justify-center rounded-full p-1.5 hover:bg-muted text-lg font-semibold" aria-label="뒤로가기">
          &lt;
        </button>
        <h1 className="text-2xl font-bold">포인트 · 보상</h1>
      </div>

      {/* 헬씨 + 인사 */}
      <div className="mt-4 flex items-center gap-3 rounded-2xl bg-secondary/60 p-4">
        <Helcy level={helcyLv} mood="waving" size={76} bounce />
        <div className="flex-1">
          <p className="text-sm font-bold">{HELCY_NAME(helcyLv)} · Lv.{helcyLv}</p>
          <p className="mt-0.5 text-xs leading-snug text-muted-foreground">{HELCY_GREET(helcyLv)}</p>
        </div>
      </div>

      {/* 방 꾸미기 진입 */}
      <Link href="/room" className="mt-3 flex items-center gap-3 rounded-2xl border border-border bg-card p-4 hover:bg-accent">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
          <Home className="h-5 w-5 text-primary" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-bold">내 방 꾸미기</p>
          <p className="text-xs text-muted-foreground">포인트로 가구를 사고 헬씨를 키워요</p>
        </div>
        <ChevronRight className="h-4 w-4 text-muted-foreground" />
      </Link>

      {/* 미니게임 진입 */}
      <Link href="/games" className="mt-3 flex items-center gap-3 rounded-2xl border border-border bg-card p-4 hover:bg-accent">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
          <Gamepad2 className="h-5 w-5 text-primary" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-bold">건강 미니게임</p>
          <p className="text-xs text-muted-foreground">OX퀴즈·카드맞추기 등 4종으로 포인트 획득</p>
        </div>
        <ChevronRight className="h-4 w-4 text-muted-foreground" />
      </Link>

      {/* 포인트 카드 */}
      <Card className="mt-3 bg-primary p-5 text-primary-foreground">
        <div className="flex items-center justify-between">
          <span className="text-sm opacity-90">Lv.{lv} {levelName(points)}</span>
          <span className="text-2xl font-extrabold">{points}P</span>
        </div>
        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-white/30">
          <div className="h-full rounded-full bg-white" style={{ width: `${ratio * 100}%` }} />
        </div>
        <p className="mt-1.5 text-xs opacity-90">
          다음 레벨까지 {Math.max(0, nextLevelPoints(points) - points)}P
        </p>
        <button
          onClick={checkIn}
          disabled={checkedIn}
          className="mt-4 w-full rounded-xl bg-white py-2.5 font-bold text-primary disabled:opacity-60"
        >
          {checkedIn ? "오늘 출석 완료 ✓" : "출석체크 +10P"}
        </button>
      </Card>

      {/* 탭 */}
      <div className="mt-5 flex gap-2">
        <button onClick={() => setTab("badge")} className={"flex-1 rounded-full py-2.5 text-sm font-bold " + (tab === "badge" ? "bg-primary text-primary-foreground" : "border border-border")}>
          뱃지 {earnedCount}/{BADGES.length}
        </button>
        <button onClick={() => setTab("reward")} className={"flex-1 rounded-full py-2.5 text-sm font-bold " + (tab === "reward" ? "bg-primary text-primary-foreground" : "border border-border")}>
          보상 상점
        </button>
      </div>

      {/* 뱃지 그리드 */}
      {tab === "badge" && (
        <div className="mt-5 grid grid-cols-4 gap-3 pb-6">
          {BADGES.map((b) => (
            <div key={b.id} className="flex flex-col items-center text-center">
              <div className={"flex h-14 w-14 items-center justify-center rounded-2xl text-2xl " + (b.earned ? "bg-secondary" : "bg-muted opacity-40 grayscale")}>
                {b.icon}
              </div>
              <span className="mt-1 line-clamp-1 text-[11px] text-muted-foreground">{b.name}</span>
            </div>
          ))}
        </div>
      )}

      {/* 보상 상점 */}
      {tab === "reward" && (
        <div className="mt-5 space-y-3 pb-6">
          {REWARDS.map((r) => {
            const canAfford = points >= r.requiredPoints;
            return (
              <Card key={r.id} className="flex items-center justify-between p-4">
                <div>
                  <p className="font-semibold">{r.name}</p>
                  <p className="text-xs text-muted-foreground">{r.type === "title" ? "칭호" : "테마"} · {r.requiredPoints}P</p>
                </div>
                {r.owned ? (
                  <span className="rounded-md bg-secondary px-3 py-1.5 text-xs font-bold text-primary">보유</span>
                ) : (
                  <button
                    onClick={() => buyReward(r.id, r.requiredPoints)}
                    disabled={!canAfford}
                    className="rounded-md bg-primary px-3 py-1.5 text-xs font-bold text-primary-foreground disabled:opacity-40"
                  >
                    {canAfford ? "교환" : "포인트 부족"}
                  </button>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </main>
  );
}
