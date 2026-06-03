// 방꾸미기 (REQ-GAME-002) — Flutter room_models.dart 이식
// 가구/식물/동물/소품 + 벽지 + 바닥 + 카테고리 색상

export type RoomItemCategory = "furniture" | "plant" | "pet" | "prop";

// 카테고리별 배경색 / 테두리색 (Flutter RoomItemCategoryColor 이식)
export const CATEGORY_COLORS: Record<
  RoomItemCategory,
  { bg: string; border: string }
> = {
  furniture: { bg: "#FFE0B2", border: "#FF8C00" }, // 주황
  plant: { bg: "#C8E6C9", border: "#43A047" }, // 초록
  pet: { bg: "#F8BBD0", border: "#E91E63" }, // 핑크
  prop: { bg: "#BBDEFB", border: "#1976D2" }, // 파랑
};

export const CATEGORY_LABEL: Record<RoomItemCategory, string> = {
  furniture: "가구",
  plant: "식물",
  pet: "동물",
  prop: "소품",
};

export interface RoomItemDef {
  id: string;
  emoji: string;
  name: string;
  cost: number;
  category: RoomItemCategory;
  /** 방 너비 대비 비율 (0~1) */
  size: number;
}

export interface PlacedItem {
  defId: string;
  x: number; // 0~1 (방 너비 대비)
  y: number; // 0~1 (방 높이 대비)
}

export interface RoomState {
  wallpaperIndex: number;
  floorIndex: number;
  ownedItemIds: string[];
  placedItems: PlacedItem[];
}

export const EMPTY_ROOM: RoomState = {
  wallpaperIndex: 0,
  floorIndex: 0,
  ownedItemIds: [],
  placedItems: [],
};

// ── 벽지 (그라데이션 color1 → color2) ──────────────────────
export const WALLPAPERS = [
  { name: "베이지", c1: "#FFF8F0", c2: "#FFEDD8" },
  { name: "민트", c1: "#E0F7FA", c2: "#B2EBF2" },
  { name: "라벤더", c1: "#EDE7F6", c2: "#D1C4E9" },
  { name: "피치", c1: "#FCE4EC", c2: "#F8BBD0" },
  { name: "스카이블루", c1: "#E3F2FD", c2: "#BBDEFB" },
  { name: "연두", c1: "#F1F8E9", c2: "#DCEDC8" },
  { name: "화이트", c1: "#FFFFFF", c2: "#F5F5F5" },
  { name: "그레이", c1: "#EEEEEE", c2: "#E0E0E0" },
];

// ── 바닥 (색 + 패턴) ───────────────────────────────────────
export const FLOORS = [
  { name: "원목", color: "#D7A46F", pattern: "wood" as const },
  { name: "밝은 원목", color: "#EBC98A", pattern: "wood" as const },
  { name: "흰 타일", color: "#F5F5F5", pattern: "tile" as const },
  { name: "대리석", color: "#ECEFF1", pattern: "marble" as const },
  { name: "베이지 카펫", color: "#D7CCC8", pattern: "carpet" as const },
];

// ── 전체 아이템 목록 ───────────────────────────────────────
export const ALL_ITEMS: RoomItemDef[] = [
  // 가구
  { id: "bed", emoji: "🛏️", name: "침대", cost: 100, category: "furniture", size: 0.22 },
  { id: "sofa", emoji: "🛋️", name: "소파", cost: 80, category: "furniture", size: 0.2 },
  { id: "desk", emoji: "🖥️", name: "책상", cost: 70, category: "furniture", size: 0.16 },
  { id: "chair", emoji: "🪑", name: "의자", cost: 40, category: "furniture", size: 0.11 },
  { id: "bookshelf", emoji: "📚", name: "책장", cost: 60, category: "furniture", size: 0.14 },
  { id: "tv", emoji: "📺", name: "TV", cost: 90, category: "furniture", size: 0.16 },
  { id: "fridge", emoji: "🧊", name: "냉장고", cost: 80, category: "furniture", size: 0.13 },
  { id: "table", emoji: "🛎️", name: "탁자", cost: 50, category: "furniture", size: 0.14 },
  { id: "piano", emoji: "🎹", name: "피아노", cost: 150, category: "furniture", size: 0.18 },
  { id: "bathtub", emoji: "🛁", name: "욕조", cost: 120, category: "furniture", size: 0.18 },
  { id: "lamp", emoji: "🪔", name: "스탠드", cost: 30, category: "furniture", size: 0.09 },
  { id: "clock", emoji: "🕰️", name: "시계", cost: 40, category: "furniture", size: 0.1 },
  { id: "mirror", emoji: "🪞", name: "거울", cost: 50, category: "furniture", size: 0.12 },
  { id: "closet", emoji: "🗄️", name: "옷장", cost: 90, category: "furniture", size: 0.15 },
  // 식물
  { id: "plant1", emoji: "🪴", name: "화분", cost: 30, category: "plant", size: 0.1 },
  { id: "cactus", emoji: "🌵", name: "선인장", cost: 25, category: "plant", size: 0.09 },
  { id: "tree", emoji: "🌳", name: "나무", cost: 60, category: "plant", size: 0.15 },
  { id: "flower", emoji: "🌸", name: "꽃", cost: 20, category: "plant", size: 0.09 },
  // 동물
  { id: "dog", emoji: "🐶", name: "강아지", cost: 200, category: "pet", size: 0.12 },
  { id: "cat", emoji: "🐱", name: "고양이", cost: 200, category: "pet", size: 0.12 },
  { id: "hamster", emoji: "🐹", name: "햄스터", cost: 150, category: "pet", size: 0.09 },
  { id: "rabbit", emoji: "🐰", name: "토끼", cost: 150, category: "pet", size: 0.1 },
  // 소품
  { id: "picture", emoji: "🖼️", name: "액자", cost: 30, category: "prop", size: 0.1 },
  { id: "cushion", emoji: "🧸", name: "쿠션", cost: 20, category: "prop", size: 0.09 },
  { id: "fishtank", emoji: "🐠", name: "어항", cost: 80, category: "prop", size: 0.13 },
  { id: "trophy", emoji: "🏆", name: "트로피", cost: 100, category: "prop", size: 0.1 },
  { id: "gamepad", emoji: "🎮", name: "게임기", cost: 60, category: "prop", size: 0.1 },
  { id: "guitar", emoji: "🎸", name: "기타", cost: 80, category: "prop", size: 0.13 },
  { id: "carpet", emoji: "🟫", name: "러그", cost: 40, category: "prop", size: 0.2 },
];

export function itemDef(id: string): RoomItemDef {
  return ALL_ITEMS.find((d) => d.id === id) ?? ALL_ITEMS[0];
}

/** 헬씨 레벨 = 보유 아이템 4개당 1레벨 (1~5), Flutter 이식 */
export function helcyLevelFromItems(ownedCount: number): number {
  return Math.min(5, 1 + Math.floor(ownedCount / 4));
}
