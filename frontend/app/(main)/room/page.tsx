"use client";

// 내 방 꾸미기 (REQ-GAME-002) — Flutter room_page.dart 이식
import { useEffect, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Paintbrush, Store, X } from "lucide-react";
import { Helcy } from "@/features/gamification/Helcy";
import {
  ALL_ITEMS, CATEGORY_COLORS, CATEGORY_LABEL, FLOORS, WALLPAPERS,
  helcyLevelFromItems, itemDef,
  type PlacedItem, type RoomItemCategory, type RoomItemDef, type RoomState,
} from "@/features/gamification/room";
import { getPoints, setPoints as persistPoints, loadRoom, saveRoom } from "@/features/gamification/store";

function floorBg(pattern: string, color: string): string {
  switch (pattern) {
    case "wood":
      return `repeating-linear-gradient(0deg, ${color}, ${color} 22%, rgba(0,0,0,0.06) 22%, rgba(0,0,0,0.06) 23%), repeating-linear-gradient(90deg, ${color}, ${color} 19%, rgba(0,0,0,0.04) 19%, rgba(0,0,0,0.04) 20%)`;
    case "tile":
      return `repeating-linear-gradient(0deg, ${color}, ${color} 16%, rgba(0,0,0,0.1) 16%, rgba(0,0,0,0.1) 17%), repeating-linear-gradient(90deg, ${color}, ${color} 16%, rgba(0,0,0,0.1) 16%, rgba(0,0,0,0.1) 17%)`;
    case "marble":
      return `linear-gradient(135deg, ${color}, rgba(0,0,0,0.05))`;
    default:
      return color;
  }
}

export default function RoomPage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [room, setRoom] = useState<RoomState>({ wallpaperIndex: 0, floorIndex: 0, ownedItemIds: [], placedItems: [] });
  const [points, setPoints] = useState(0);
  const [shopOpen, setShopOpen] = useState(false);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const roomRef = useRef<HTMLDivElement>(null);
  const [roomW, setRoomW] = useState(360);

  useEffect(() => {
    setRoom(loadRoom());
    setPoints(getPoints());
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!roomRef.current) return;
    const el = roomRef.current;
    const update = () => setRoomW(el.clientWidth);
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, [mounted]);

  const persist = useCallback((next: RoomState) => {
    setRoom(next);
    saveRoom(next);
  }, []);

  function snack(msg: string) {
    setToast(msg);
    window.setTimeout(() => setToast(null), 1800);
  }

  function buy(def: RoomItemDef) {
    if (room.ownedItemIds.includes(def.id)) {
      place(def.id);
      return;
    }
    if (points < def.cost) {
      snack(`포인트가 부족합니다. (${def.cost}P 필요)`);
      return;
    }
    const np = points - def.cost;
    setPoints(np);
    persistPoints(np);
    persist({ ...room, ownedItemIds: [...room.ownedItemIds, def.id] });
    snack(`${def.emoji} ${def.name} 구매 완료!`);
  }

  function place(defId: string) {
    const def = itemDef(defId);
    persist({ ...room, placedItems: [...room.placedItems, { defId, x: 0.4, y: 0.45 }] });
    snack(`${def.emoji} ${def.name} 배치!`);
  }

  function removeAt(index: number) {
    persist({ ...room, placedItems: room.placedItems.filter((_, i) => i !== index) });
  }

  function moveAt(index: number, x: number, y: number) {
    const next = room.placedItems.map((p, i) => (i === index ? { ...p, x, y } : p));
    persist({ ...room, placedItems: next });
  }

  const helcyLv = helcyLevelFromItems(room.ownedItemIds.length);
  const hasPet = room.placedItems.some((p) => itemDef(p.defId).category === "pet");
  const wp = WALLPAPERS[room.wallpaperIndex];
  const fl = FLOORS[room.floorIndex];
  const ownedDefs = ALL_ITEMS.filter((d) => room.ownedItemIds.includes(d.id));

  if (!mounted) {
    return <main className="flex min-h-[60vh] items-center justify-center text-muted-foreground">불러오는 중…</main>;
  }

  return (
    <main className="mx-auto flex h-[100dvh] w-full max-w-md flex-col bg-muted">
      {/* 헤더 */}
      <header className="flex items-center gap-2 bg-card px-3 py-3">
        <button onClick={() => router.back()} className="flex items-center justify-center rounded-full p-1.5 hover:bg-accent text-lg font-semibold" aria-label="뒤로가기">
          &lt;
        </button>
        <h1 className="flex-1 text-base font-bold">내 방 꾸미기</h1>
        <span className="rounded-full bg-primary/10 px-2.5 py-1 text-xs font-bold text-primary">⭐ {points}P</span>
        <button onClick={() => setPickerOpen(true)} className="rounded-full p-1.5 hover:bg-accent" title="벽지/바닥">
          <Paintbrush className="h-5 w-5" />
        </button>
      </header>

      <p className="bg-card px-4 pb-2 text-[11px] text-muted-foreground">드래그로 이동 · 우측 상단 ✕ 로 제거</p>

      {/* 방 */}
      <div ref={roomRef} className="relative flex-1 overflow-hidden">
        {/* 벽 */}
        <div className="absolute inset-0" style={{ background: `linear-gradient(${wp.c1}, ${wp.c2} 68%)` }} />
        {/* 바닥 */}
        <div className="absolute bottom-0 left-0 right-0 h-[32%]" style={{ background: floorBg(fl.pattern, fl.color) }} />
        <div className="absolute bottom-[32%] left-0 right-0 h-2" style={{ background: fl.color, opacity: 0.55 }} />

        {/* 배치된 아이템 (펫 제외) */}
        {room.placedItems.map((p, i) => {
          const def = itemDef(p.defId);
          if (def.category === "pet") return null;
          return (
            <PlacedView
              key={`${p.defId}-${i}`}
              placed={p}
              def={def}
              containerRef={roomRef}
              containerW={roomW}
              onMove={(x, y) => moveAt(i, x, y)}
              onDelete={() => removeAt(i)}
            />
          );
        })}

        {/* 헬씨 */}
        <div className="absolute" style={{ left: "36%", bottom: "30%" }}>
          <Helcy level={helcyLv} mood={hasPet ? "excited" : "happy"} size={120} bounce />
        </div>

        {/* 움직이는 펫 */}
        {hasPet && <Pet defId={room.placedItems.find((p) => itemDef(p.defId).category === "pet")!.defId} containerRef={roomRef} />}
      </div>

      {/* 인벤토리 */}
      <div className="bg-card shadow-[0_-2px_8px_rgba(0,0,0,0.08)]">
        <div className="flex items-center justify-between px-4 pb-1 pt-2.5">
          <span className="text-sm font-bold">🎒 인벤토리</span>
          <button onClick={() => setShopOpen(true)} className="flex items-center gap-1 text-sm font-bold text-primary">
            <Store className="h-4 w-4" /> 상점
          </button>
        </div>
        <div className="flex gap-2.5 overflow-x-auto px-3 pb-3 pt-1" style={{ minHeight: 92 }}>
          {ownedDefs.length === 0 ? (
            <p className="w-full py-6 text-center text-[13px] text-muted-foreground">상점에서 아이템을 구매하세요!</p>
          ) : (
            ownedDefs.map((def) => {
              const c = CATEGORY_COLORS[def.category];
              return (
                <button
                  key={def.id}
                  onClick={() => place(def.id)}
                  className="flex w-[68px] shrink-0 flex-col items-center justify-center rounded-xl border-[1.5px] py-2"
                  style={{ background: c.bg, borderColor: c.border }}
                >
                  <span className="text-3xl leading-none">{def.emoji}</span>
                  <span className="mt-1 text-[10px] font-medium">{def.name}</span>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* 토스트 */}
      {toast && (
        <div className="pointer-events-none fixed bottom-28 left-1/2 z-50 -translate-x-1/2 rounded-full bg-black/80 px-4 py-2 text-sm text-white">
          {toast}
        </div>
      )}

      {/* 상점 모달 */}
      {shopOpen && (
        <ShopSheet
          room={room}
          points={points}
          onClose={() => setShopOpen(false)}
          onBuy={(def) => buy(def)}
        />
      )}

      {/* 벽지/바닥 모달 */}
      {pickerOpen && (
        <PickerSheet
          room={room}
          onClose={() => setPickerOpen(false)}
          onWall={(i) => persist({ ...room, wallpaperIndex: i })}
          onFloor={(i) => persist({ ...room, floorIndex: i })}
        />
      )}
    </main>
  );
}

// ── 배치 아이템 (드래그 + 삭제) ────────────────────────────
function PlacedView({
  placed, def, containerRef, containerW, onMove, onDelete,
}: {
  placed: PlacedItem;
  def: RoomItemDef;
  containerRef: React.RefObject<HTMLDivElement>;
  containerW: number;
  onMove: (x: number, y: number) => void;
  onDelete: () => void;
}) {
  const [pos, setPos] = useState({ x: placed.x, y: placed.y });
  const dragging = useRef(false);

  useEffect(() => setPos({ x: placed.x, y: placed.y }), [placed.x, placed.y]);

  function onPointerDown(e: React.PointerEvent) {
    dragging.current = true;
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }
  function onPointerMove(e: React.PointerEvent) {
    if (!dragging.current || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.min(0.97, Math.max(0.03, (e.clientX - rect.left) / rect.width));
    const y = Math.min(0.97, Math.max(0.03, (e.clientY - rect.top) / rect.height));
    setPos({ x, y });
  }
  function onPointerUp() {
    if (!dragging.current) return;
    dragging.current = false;
    onMove(pos.x, pos.y);
  }

  // 방 너비 대비 비율 → 실제 px (최소 34px)
  const px = Math.max(34, Math.round(containerW * def.size * 1.15));

  return (
    <div
      className="group absolute -translate-x-1/2 -translate-y-1/2 cursor-grab touch-none select-none active:cursor-grabbing"
      style={{ left: `${pos.x * 100}%`, top: `${pos.y * 100}%` }}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
    >
      <span style={{ fontSize: `${px}px` }} className="block leading-none drop-shadow-sm">{def.emoji}</span>
      <button
        onClick={onDelete}
        onPointerDown={(e) => e.stopPropagation()}
        className="absolute -right-2 -top-2 hidden h-5 w-5 items-center justify-center rounded-full bg-destructive text-white group-hover:flex"
        aria-label="제거"
      >
        <X className="h-3 w-3" />
      </button>
    </div>
  );
}

// ── 움직이는 펫 ────────────────────────────────────────────
function Pet({ defId, containerRef }: { defId: string; containerRef: React.RefObject<HTMLDivElement> }) {
  const ref = useRef<HTMLDivElement>(null);
  const def = itemDef(defId);

  useEffect(() => {
    let x = 0.25, y = 0.04, dx = 0.0018, dy = 0.0009, step = 0, raf = 0;
    let seed = 1;
    const rand = () => {
      // 결정적 의사난수 (Math.random 미사용)
      seed = (seed * 9301 + 49297) % 233280;
      return seed / 233280;
    };
    const tick = () => {
      step++;
      if (step > 50 + Math.floor(rand() * 70)) {
        dx = rand() * 0.004 - 0.002;
        dy = rand() * 0.003 - 0.0015;
        step = 0;
      }
      x += dx; y += dy;
      if (x <= 0.05 || x >= 0.8) { dx = -dx; x = Math.min(0.8, Math.max(0.05, x)); }
      if (y <= 0 || y >= 0.12) { dy = -dy; y = Math.min(0.12, Math.max(0, y)); }
      if (ref.current && containerRef.current) {
        ref.current.style.left = `${x * 100}%`;
        ref.current.style.bottom = `${32 + y * 100}%`;
        ref.current.style.transform = `scaleX(${dx >= 0 ? 1 : -1})`;
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [containerRef]);

  return (
    <div ref={ref} className="absolute" style={{ left: "25%", bottom: "32%" }}>
      <span className="block text-5xl leading-none">{def.emoji}</span>
    </div>
  );
}

// ── 상점 시트 ──────────────────────────────────────────────
const CATS: ("all" | RoomItemCategory)[] = ["all", "furniture", "plant", "pet", "prop"];
function ShopSheet({
  room, points, onClose, onBuy,
}: {
  room: RoomState;
  points: number;
  onClose: () => void;
  onBuy: (def: RoomItemDef) => void;
}) {
  const [tab, setTab] = useState<"all" | RoomItemCategory>("all");
  const items = tab === "all" ? ALL_ITEMS : ALL_ITEMS.filter((d) => d.category === tab);

  return (
    <div className="fixed inset-0 z-50 flex flex-col justify-end bg-black/40" onClick={onClose}>
      <div
        className="mx-auto flex max-h-[85vh] w-full max-w-md flex-col rounded-t-2xl bg-card"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mx-auto mt-2 h-1 w-10 rounded-full bg-muted-foreground/30" />
        <div className="flex items-center justify-between px-4 pt-3">
          <span className="text-lg font-bold">🏪 상점</span>
          <span className="text-sm font-bold text-primary">⭐ {points}P</span>
        </div>
        <div className="flex gap-2 overflow-x-auto px-4 py-3">
          {CATS.map((c) => (
            <button
              key={c}
              onClick={() => setTab(c)}
              className={"shrink-0 rounded-full px-3.5 py-1.5 text-sm font-bold " + (tab === c ? "bg-primary text-primary-foreground" : "border border-border")}
            >
              {c === "all" ? "전체" : CATEGORY_LABEL[c]}
            </button>
          ))}
        </div>
        <div className="grid grid-cols-3 gap-3 overflow-y-auto px-4 pb-6">
          {items.map((def) => {
            const owned = room.ownedItemIds.includes(def.id);
            const canAfford = points >= def.cost;
            const c = CATEGORY_COLORS[def.category];
            return (
              <button
                key={def.id}
                onClick={() => onBuy(def)}
                className="flex flex-col items-center rounded-2xl border p-2.5"
                style={{ background: owned ? c.bg : "transparent", borderColor: owned ? c.border : "hsl(var(--border))" }}
              >
                <div
                  className="flex h-12 w-12 items-center justify-center rounded-full border-[1.5px] text-3xl"
                  style={{ background: c.bg, borderColor: c.border }}
                >
                  {def.emoji}
                </div>
                <span className="mt-1.5 text-xs font-semibold">{def.name}</span>
                {owned ? (
                  <span className="mt-0.5 text-[11px] font-bold" style={{ color: c.border }}>배치하기</span>
                ) : (
                  <span className={"mt-0.5 text-[11px] font-bold " + (canAfford ? "text-primary" : "text-muted-foreground")}>{def.cost}P</span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ── 벽지/바닥 시트 ─────────────────────────────────────────
function PickerSheet({
  room, onClose, onWall, onFloor,
}: {
  room: RoomState;
  onClose: () => void;
  onWall: (i: number) => void;
  onFloor: (i: number) => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex flex-col justify-end bg-black/40" onClick={onClose}>
      <div className="mx-auto w-full max-w-md rounded-t-2xl bg-card p-5" onClick={(e) => e.stopPropagation()}>
        <div className="mx-auto mb-3 h-1 w-10 rounded-full bg-muted-foreground/30" />
        <h2 className="font-bold">벽지</h2>
        <div className="mt-2 flex gap-2.5 overflow-x-auto pb-1">
          {WALLPAPERS.map((wp, i) => (
            <button
              key={wp.name}
              onClick={() => onWall(i)}
              className="flex h-16 w-16 shrink-0 items-end justify-center rounded-xl border-[3px] pb-1 text-[10px]"
              style={{ background: `linear-gradient(135deg, ${wp.c1}, ${wp.c2})`, borderColor: room.wallpaperIndex === i ? "hsl(var(--primary))" : "transparent" }}
            >
              {wp.name}
            </button>
          ))}
        </div>
        <h2 className="mt-4 font-bold">바닥</h2>
        <div className="mt-2 flex gap-2.5 overflow-x-auto pb-1">
          {FLOORS.map((fl, i) => (
            <button
              key={fl.name}
              onClick={() => onFloor(i)}
              className="flex h-16 w-16 shrink-0 items-end justify-center rounded-xl border-[3px] pb-1 text-[10px]"
              style={{ background: fl.color, borderColor: room.floorIndex === i ? "hsl(var(--primary))" : "transparent" }}
            >
              {fl.name}
            </button>
          ))}
        </div>
        <button onClick={onClose} className="mt-5 w-full rounded-xl bg-primary py-2.5 font-bold text-primary-foreground">완료</button>
      </div>
    </div>
  );
}
