// 헬씨(Helcy) 마스코트 — Flutter helcy_widget.dart 이식 (CustomPainter → SVG)
// 레벨 1~5에 따라 색/장식(잎·청진기·가운·왕관·망토·별)이 성장하고, 기분별 표정이 바뀜.

export type HelcyMood = "happy" | "excited" | "sad" | "neutral" | "waving";

const BODY = ["#90CAF9", "#80CBC4", "#81C784", "#FFB74D", "#FF7043"];
const ACCENT = ["#42A5F5", "#26A69A", "#43A047", "#FB8C00", "#E64A19"];

export const HELCY_NAME = (lv: number) =>
  ["씨앗 헬씨", "새싹 헬씨", "건강이", "건강 청년", "건강 영웅"][clampLv(lv) - 1];

export const HELCY_GREET = (lv: number) =>
  [
    "안녕! 나는 헬씨야 👋 함께 건강해지자!",
    "오늘도 건강 관리 잘 하고 있어! 💪",
    "꾸준함이 건강의 비결! 오늘도 파이팅! 🌟",
    "건강 마스터를 향해 달려가는 중! 🔥",
    "넌 이제 건강 영웅! 모두의 롤모델이야! 👑",
  ][clampLv(lv) - 1];

function clampLv(lv: number) {
  return Math.min(5, Math.max(1, Math.round(lv)));
}

export function Helcy({
  level = 1,
  mood = "happy",
  size = 120,
  bounce = false,
}: {
  level?: number;
  mood?: HelcyMood;
  size?: number;
  /** 위아래로 통통 튀는 애니메이션 */
  bounce?: boolean;
}) {
  const lv = clampLv(level);
  const body = BODY[lv - 1];
  const accent = ACCENT[lv - 1];

  const cx = 50;
  const cy = 54;
  const r = 32;

  // 눈
  const eyeY = cy - r * 0.1;
  const eyeLx = cx - r * 0.28;
  const eyeRx = cx + r * 0.28;
  const eyeR = r * 0.16;
  const pupilR = r * 0.09;
  const pdy = mood === "sad" ? pupilR * 0.5 : -pupilR * 0.3;
  const browY = eyeY - r * 0.22;
  const my = cy + r * 0.28;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      style={bounce ? { animation: "helcy-bounce 1.2s ease-in-out infinite" } : undefined}
    >
      <style>{`@keyframes helcy-bounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-7%)}}`}</style>

      {/* 망토 (lv5) — 몸 뒤 */}
      {lv >= 5 && (
        <path
          d={`M${cx - r * 0.7},${cy} Q${cx - r * 1.1},${cy + r * 0.8} ${cx - r * 0.5},${cy + r * 1.2} L${cx + r * 0.5},${cy + r * 1.2} Q${cx + r * 1.1},${cy + r * 0.8} ${cx + r * 0.7},${cy} Z`}
          fill={accent}
          opacity={0.8}
        />
      )}

      {/* 그림자 */}
      <circle cx={cx + 2} cy={cy + 4} r={r} fill="rgba(0,0,0,0.08)" />

      {/* 귀 (lv2+) */}
      {lv >= 2 && (
        <>
          <circle cx={cx - r * 0.75} cy={cy - r * 0.6} r={r * 0.22} fill={accent} />
          <circle cx={cx + r * 0.75} cy={cy - r * 0.6} r={r * 0.22} fill={accent} />
        </>
      )}

      {/* 몸통 */}
      <circle cx={cx} cy={cy} r={r} fill={body} />

      {/* 발광 테두리 (lv5) */}
      {lv >= 5 && (
        <circle cx={cx} cy={cy} r={r + 3} fill="none" stroke={accent} strokeOpacity={0.4} strokeWidth={3} />
      )}

      {/* 볼터치 (lv3+) */}
      {lv >= 3 && (
        <>
          <circle cx={cx - r * 0.55} cy={cy + r * 0.15} r={r * 0.2} fill="#EC407A" opacity={0.35} />
          <circle cx={cx + r * 0.55} cy={cy + r * 0.15} r={r * 0.2} fill="#EC407A" opacity={0.35} />
        </>
      )}

      {/* 눈 흰자 */}
      <circle cx={eyeLx} cy={eyeY} r={eyeR} fill="#fff" />
      <circle cx={eyeRx} cy={eyeY} r={eyeR} fill="#fff" />
      {/* 동공 */}
      <circle cx={eyeLx} cy={eyeY + pdy} r={pupilR} fill="#1A237E" />
      <circle cx={eyeRx} cy={eyeY + pdy} r={pupilR} fill="#1A237E" />
      {/* 반짝이 */}
      <circle cx={eyeLx - pupilR * 0.5} cy={eyeY + pdy - pupilR * 0.4} r={pupilR * 0.4} fill="#fff" />
      <circle cx={eyeRx - pupilR * 0.5} cy={eyeY + pdy - pupilR * 0.4} r={pupilR * 0.4} fill="#fff" />

      {/* 눈썹 */}
      <Brows mood={mood} eyeLx={eyeLx} eyeRx={eyeRx} browY={browY} r={r} />

      {/* 입 */}
      <Mouth mood={mood} cx={cx} my={my} r={r} />

      {/* 액세서리 (레벨별) */}
      {lv === 1 && (
        <path
          d={`M${cx},${cy - r - 2} Q${cx + r * 0.3},${cy - r * 1.25} ${cx},${cy - r * 1.5} Q${cx - r * 0.3},${cy - r * 1.25} ${cx},${cy - r - 2} Z`}
          fill="#81C784"
        />
      )}
      {lv >= 2 && <Stethoscope cx={cx} cy={cy} r={r} />}
      {lv >= 3 && (
        <path
          d={`M${cx - r * 0.3},${cy + r * 0.7} L${cx},${cy + r * 0.5} L${cx + r * 0.3},${cy + r * 0.7} Z`}
          fill="#fff"
          opacity={0.85}
        />
      )}
      {lv >= 4 && <Crown cx={cx} cy={cy} r={r} />}
      {lv >= 4 && <Star cx={cx} cy={cy - r * 1.3} r={r * 0.18} />}

      {/* 흔드는 팔 */}
      {mood === "waving" && (
        <>
          <path
            d={`M${cx + r * 0.75},${cy - r * 0.1} Q${cx + r * 1.1},${cy - r * 0.5} ${cx + r * 0.9},${cy - r * 0.9}`}
            fill="none"
            stroke={body}
            strokeWidth={r * 0.22}
            strokeLinecap="round"
          />
          <circle cx={cx + r * 0.9} cy={cy - r * 0.9} r={r * 0.14} fill={body} />
        </>
      )}
    </svg>
  );
}

function Brows({ mood, eyeLx, eyeRx, browY, r }: { mood: HelcyMood; eyeLx: number; eyeRx: number; browY: number; r: number }) {
  const w = r * 0.13;
  const stroke = { stroke: "#1A237E", strokeWidth: r * 0.08, strokeLinecap: "round" as const, fill: "none" };
  if (mood === "excited" || mood === "waving") {
    return (
      <>
        <path d={`M${eyeLx - w},${browY} Q${eyeLx},${browY - r * 0.12} ${eyeLx + w},${browY}`} {...stroke} />
        <path d={`M${eyeRx - w},${browY} Q${eyeRx},${browY - r * 0.12} ${eyeRx + w},${browY}`} {...stroke} />
      </>
    );
  }
  if (mood === "sad") {
    return (
      <>
        <line x1={eyeLx - w} y1={browY - r * 0.06} x2={eyeLx + w} y2={browY + r * 0.06} {...stroke} />
        <line x1={eyeRx - w} y1={browY + r * 0.06} x2={eyeRx + w} y2={browY - r * 0.06} {...stroke} />
      </>
    );
  }
  return (
    <>
      <line x1={eyeLx - w} y1={browY} x2={eyeLx + w} y2={browY} {...stroke} />
      <line x1={eyeRx - w} y1={browY} x2={eyeRx + w} y2={browY} {...stroke} />
    </>
  );
}

function Mouth({ mood, cx, my, r }: { mood: HelcyMood; cx: number; my: number; r: number }) {
  const stroke = { stroke: "#1A237E", strokeWidth: r * 0.08, strokeLinecap: "round" as const, fill: "none" };
  const hw = r * 0.2;
  if (mood === "excited") {
    return (
      <>
        <path d={`M${cx - hw},${my} Q${cx},${my + r * 0.22} ${cx + hw},${my} Z`} fill="#fff" />
        <path d={`M${cx - hw},${my} Q${cx},${my + r * 0.22} ${cx + hw},${my}`} {...stroke} />
      </>
    );
  }
  if (mood === "sad") {
    return <path d={`M${cx - r * 0.16},${my + r * 0.08} Q${cx},${my - r * 0.08} ${cx + r * 0.16},${my + r * 0.08}`} {...stroke} />;
  }
  if (mood === "neutral") {
    return <line x1={cx - r * 0.13} y1={my} x2={cx + r * 0.13} y2={my} {...stroke} />;
  }
  // happy
  return <path d={`M${cx - hw},${my} Q${cx},${my + r * 0.13} ${cx + hw},${my}`} {...stroke} />;
}

function Stethoscope({ cx, cy, r }: { cx: number; cy: number; r: number }) {
  const sx = cx + r * 0.4;
  const sy = cy + r * 0.25;
  return (
    <>
      <path
        d={`M${sx},${sy} Q${sx + r * 0.4},${sy + r * 0.3} ${sx + r * 0.15},${sy + r * 0.6}`}
        fill="none"
        stroke="#37474F"
        strokeWidth={r * 0.07}
        strokeLinecap="round"
      />
      <circle cx={sx + r * 0.15} cy={sy + r * 0.6} r={r * 0.1} fill="#78909C" />
    </>
  );
}

function Crown({ cx, cy, r }: { cx: number; cy: number; r: number }) {
  const top = cy - r * 1.1;
  return (
    <>
      <path
        d={`M${cx - r * 0.35},${top + r * 0.25} L${cx - r * 0.35},${top} L${cx - r * 0.17},${top + r * 0.15} L${cx},${top - r * 0.1} L${cx + r * 0.17},${top + r * 0.15} L${cx + r * 0.35},${top} L${cx + r * 0.35},${top + r * 0.25} Z`}
        fill="#FFD700"
        stroke="#FFA000"
        strokeWidth={1}
      />
      <circle cx={cx} cy={top - r * 0.05} r={r * 0.065} fill="#E53935" />
    </>
  );
}

function Star({ cx, cy, r }: { cx: number; cy: number; r: number }) {
  let d = "";
  for (let i = 0; i < 5; i++) {
    const a = ((i * 72 - 90) * Math.PI) / 180;
    const ia = ((i * 72 + 36 - 90) * Math.PI) / 180;
    const x = cx + r * Math.cos(a);
    const y = cy + r * Math.sin(a);
    const ix = cx + r * 0.4 * Math.cos(ia);
    const iy = cy + r * 0.4 * Math.sin(ia);
    d += `${i === 0 ? "M" : "L"}${x},${y} L${ix},${iy} `;
  }
  d += "Z";
  return <path d={d} fill="#FFD700" />;
}
