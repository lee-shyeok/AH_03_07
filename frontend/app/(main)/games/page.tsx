"use client";

// 미니게임 (REQ-GAME-002) — Flutter game_pages.dart 이식
// 4종: 카드 맞추기 / OX 퀴즈 / 단어 맞추기 / 타이머 챌린지
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, ArrowLeft } from "lucide-react";
import {
  EMOJI_POOL, OX_QUESTIONS, WORD_LIST, shuffle, awardForScore,
} from "@/features/gamification/gameData";

type GameKey = "memory" | "ox" | "word" | "timer" | null;

const GAMES = [
  { key: "memory" as const, emoji: "🃏", name: "카드 맞추기", desc: "같은 의료 카드 짝 맞추기" },
  { key: "ox" as const, emoji: "⭕", name: "OX 퀴즈", desc: "건강 상식 O/X 10문제" },
  { key: "word" as const, emoji: "🔤", name: "단어 맞추기", desc: "초성 보고 의학 용어 맞히기" },
  { key: "timer" as const, emoji: "⏱️", name: "타이머 챌린지", desc: "30초 안에 8쌍 맞추기" },
];

export default function GamesPage() {
  const router = useRouter();
  const [active, setActive] = useState<GameKey>(null);

  if (active) {
    const close = () => setActive(null);
    return (
      <main className="mx-auto min-h-[100dvh] w-full max-w-md bg-muted">
        {active === "memory" && <Memory onClose={close} />}
        {active === "ox" && <Ox onClose={close} />}
        {active === "word" && <Word onClose={close} />}
        {active === "timer" && <Timer onClose={close} />}
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 pt-8">
      <div className="flex items-center gap-2">
        <button onClick={() => router.back()} className="rounded-full p-1 hover:bg-accent" aria-label="뒤로가기">
          <ChevronLeft className="h-5 w-5" />
        </button>
        <h1 className="text-2xl font-bold">건강 미니게임</h1>
      </div>
      <p className="mt-1 pl-9 text-sm text-muted-foreground">게임하고 포인트도 모아요</p>

      <div className="mt-6 grid grid-cols-2 gap-3 pb-6">
        {GAMES.map((g) => (
          <button
            key={g.key}
            onClick={() => setActive(g.key)}
            className="flex flex-col items-center rounded-2xl border border-border bg-card p-5 text-center hover:bg-accent"
          >
            <span className="text-4xl">{g.emoji}</span>
            <span className="mt-2 font-bold">{g.name}</span>
            <span className="mt-1 text-[11px] leading-snug text-muted-foreground">{g.desc}</span>
          </button>
        ))}
      </div>
    </main>
  );
}

// ── 공통 헤더 + 결과 다이얼로그 ────────────────────────────
function GameHeader({ title, right, onClose }: { title: string; right?: React.ReactNode; onClose: () => void }) {
  return (
    <header className="flex items-center gap-2 bg-card px-3 py-3">
      <button onClick={onClose} className="rounded-full p-1.5 hover:bg-accent">
        <ArrowLeft className="h-5 w-5" />
      </button>
      <h1 className="flex-1 text-base font-bold">{title}</h1>
      {right}
    </header>
  );
}

function ResultDialog({
  emoji, title, detail, earned, onRetry, onClose,
}: {
  emoji: string; title: string; detail: string; earned: number; onRetry: () => void; onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-8">
      <div className="w-full max-w-xs rounded-2xl bg-card p-6 text-center">
        <div className="text-5xl">{emoji}</div>
        <h2 className="mt-3 text-xl font-bold">{title}</h2>
        <p className="mt-1 whitespace-pre-line text-sm text-muted-foreground">{detail}</p>
        <p className="mt-3 rounded-xl bg-primary/10 py-2 font-bold text-primary">+{earned}P 적립!</p>
        <div className="mt-5 flex gap-2">
          <button onClick={onClose} className="flex-1 rounded-xl border border-border py-2.5 font-bold">나가기</button>
          <button onClick={onRetry} className="flex-1 rounded-xl bg-primary py-2.5 font-bold text-primary-foreground">다시하기</button>
        </div>
      </div>
    </div>
  );
}

// ── 카드 맞추기 ────────────────────────────────────────────
function Memory({ onClose }: { onClose: () => void }) {
  const PAIRS = 6;
  const [cards, setCards] = useState<string[]>([]);
  const [flipped, setFlipped] = useState<boolean[]>([]);
  const [matched, setMatched] = useState<boolean[]>([]);
  const [first, setFirst] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [moves, setMoves] = useState(0);
  const [done, setDone] = useState<{ score: number; earned: number } | null>(null);

  function init() {
    const picks = shuffle(EMOJI_POOL).slice(0, PAIRS);
    setCards(shuffle([...picks, ...picks]));
    setFlipped(Array(PAIRS * 2).fill(false));
    setMatched(Array(PAIRS * 2).fill(false));
    setFirst(null); setBusy(false); setMoves(0); setDone(null);
  }
  useEffect(init, []);

  function tap(i: number) {
    if (busy || flipped[i] || matched[i]) return;
    const nf = [...flipped]; nf[i] = true; setFlipped(nf);
    if (first === null) { setFirst(i); return; }
    setBusy(true);
    setMoves((m) => m + 1);
    if (cards[first] === cards[i]) {
      const nm = [...matched]; nm[first] = true; nm[i] = true; setMatched(nm);
      setFirst(null); setBusy(false);
      if (nm.every(Boolean)) {
        const score = Math.max(0, 100 - (moves + 1 - PAIRS) * 5);
        setDone({ score, earned: awardForScore(score) });
      }
    } else {
      const f = first; setFirst(null);
      setTimeout(() => {
        setFlipped((prev) => { const x = [...prev]; x[f] = false; x[i] = false; return x; });
        setBusy(false);
      }, 700);
    }
  }

  return (
    <>
      <GameHeader title="카드 맞추기" onClose={onClose} right={<span className="text-sm text-muted-foreground">{moves}회</span>} />
      <div className="grid grid-cols-3 gap-3 p-5">
        {cards.map((c, i) => {
          const open = flipped[i] || matched[i];
          return (
            <button
              key={i}
              onClick={() => tap(i)}
              className={"flex aspect-square items-center justify-center rounded-2xl text-4xl transition-colors " + (open ? "bg-card " + (matched[i] ? "opacity-60" : "") : "bg-primary text-primary-foreground")}
            >
              {open ? c : "?"}
            </button>
          );
        })}
      </div>
      {done && (
        <ResultDialog emoji="🎉" title="완료!" detail={`시도 ${moves}회 · 점수 ${done.score}점`} earned={done.earned} onRetry={init} onClose={onClose} />
      )}
    </>
  );
}

// ── OX 퀴즈 ────────────────────────────────────────────────
function Ox({ onClose }: { onClose: () => void }) {
  const [qs, setQs] = useState(() => shuffle(OX_QUESTIONS).slice(0, 10));
  const [idx, setIdx] = useState(0);
  const [correct, setCorrect] = useState(0);
  const [picked, setPicked] = useState<boolean | null>(null);
  const [done, setDone] = useState<{ score: number; earned: number } | null>(null);

  const q = qs[idx];

  function answer(v: boolean) {
    if (picked !== null) return;
    setPicked(v);
    const ok = v === q.answer;
    if (ok) setCorrect((c) => c + 1);
    setTimeout(() => {
      if (idx + 1 >= qs.length) {
        const score = Math.round(((correct + (ok ? 1 : 0)) / qs.length) * 100);
        setDone({ score, earned: awardForScore(score) });
      } else {
        setIdx((i) => i + 1); setPicked(null);
      }
    }, 1400);
  }
  function retry() {
    setQs(shuffle(OX_QUESTIONS).slice(0, 10));
    setIdx(0); setCorrect(0); setPicked(null); setDone(null);
  }

  return (
    <>
      <GameHeader title="OX 퀴즈" onClose={onClose} right={<span className="text-sm text-muted-foreground">{idx + 1}/{qs.length}</span>} />
      <div className="px-5 pt-2">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
          <div className="h-full bg-primary transition-all" style={{ width: `${((idx + 1) / qs.length) * 100}%` }} />
        </div>
      </div>
      <div className="flex flex-col items-center px-6 pt-10">
        <div className="flex min-h-[140px] w-full items-center justify-center rounded-2xl bg-card p-6 text-center text-lg font-bold leading-relaxed">
          {q.q}
        </div>
        {picked !== null && (
          <div className={"mt-4 w-full rounded-xl p-3 text-center text-sm " + (picked === q.answer ? "bg-secondary text-primary" : "bg-red-50 text-red-600")}>
            {picked === q.answer ? "정답! " : `오답! 정답은 ${q.answer ? "O" : "X"} · `}{q.desc}
          </div>
        )}
        <div className="mt-8 flex w-full gap-4">
          <button onClick={() => answer(true)} disabled={picked !== null} className="flex-1 rounded-2xl bg-green-500 py-8 text-4xl font-extrabold text-white disabled:opacity-50">O</button>
          <button onClick={() => answer(false)} disabled={picked !== null} className="flex-1 rounded-2xl bg-red-400 py-8 text-4xl font-extrabold text-white disabled:opacity-50">X</button>
        </div>
      </div>
      {done && (
        <ResultDialog emoji={done.score >= 80 ? "🎉" : done.score >= 50 ? "👍" : "💪"} title="퀴즈 완료!" detail={`${correct}/${qs.length} 정답 · ${done.score}점`} earned={done.earned} onRetry={retry} onClose={onClose} />
      )}
    </>
  );
}

// ── 단어 맞추기 (초성) ─────────────────────────────────────
function Word({ onClose }: { onClose: () => void }) {
  const [words, setWords] = useState(() => shuffle(WORD_LIST).slice(0, 8));
  const [idx, setIdx] = useState(0);
  const [correct, setCorrect] = useState(0);
  const [input, setInput] = useState("");
  const [result, setResult] = useState<boolean | null>(null);
  const [done, setDone] = useState<{ score: number; earned: number } | null>(null);
  const w = words[idx];

  function next(wasCorrect: boolean) {
    setTimeout(() => {
      setInput(""); setResult(null);
      if (idx + 1 >= words.length) {
        const score = Math.round(((correct + (wasCorrect ? 1 : 0)) / words.length) * 100);
        setDone({ score, earned: awardForScore(score) });
      } else {
        setIdx((i) => i + 1);
      }
    }, 1000);
  }
  function submit() {
    if (result !== null) return;
    const ans = input.trim();
    if (!ans) return;
    const ok = ans === w.word;
    if (ok) setCorrect((c) => c + 1);
    setResult(ok);
    next(ok);
  }
  function skip() {
    if (result !== null) return;
    setResult(false);
    next(false);
  }
  function retry() {
    setWords(shuffle(WORD_LIST).slice(0, 8));
    setIdx(0); setCorrect(0); setInput(""); setResult(null); setDone(null);
  }

  return (
    <>
      <GameHeader title="단어 맞추기" onClose={onClose} right={<span className="text-sm text-muted-foreground">{idx + 1}/{words.length}</span>} />
      <div className="flex flex-col items-center px-6 pt-10">
        <p className="text-sm text-muted-foreground">초성 힌트</p>
        <p className="mt-2 text-5xl font-extrabold tracking-widest text-primary">{w.hint}</p>
        <p className="mt-4 rounded-xl bg-card px-4 py-3 text-center text-sm">{w.desc}</p>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          disabled={result !== null}
          placeholder="정답을 입력하세요"
          className="mt-6 w-full rounded-xl border border-border bg-background px-4 py-3 text-center text-lg outline-none focus:border-primary"
        />
        {result !== null && (
          <p className={"mt-3 text-sm font-bold " + (result ? "text-primary" : "text-red-500")}>
            {result ? "정답!" : `정답: ${w.word}`}
          </p>
        )}
        <div className="mt-6 flex w-full gap-3">
          <button onClick={skip} disabled={result !== null} className="flex-1 rounded-xl border border-border py-3 font-bold disabled:opacity-50">모르겠어요</button>
          <button onClick={submit} disabled={result !== null} className="flex-1 rounded-xl bg-primary py-3 font-bold text-primary-foreground disabled:opacity-50">제출</button>
        </div>
      </div>
      {done && (
        <ResultDialog emoji={done.score >= 80 ? "🎉" : done.score >= 50 ? "👍" : "💪"} title="단어 완료!" detail={`${correct}/${words.length} 정답 · ${done.score}점`} earned={done.earned} onRetry={retry} onClose={onClose} />
      )}
    </>
  );
}

// ── 타이머 챌린지 ──────────────────────────────────────────
function Timer({ onClose }: { onClose: () => void }) {
  const PAIRS = 8;
  const TOTAL = 30;
  const [cards, setCards] = useState<string[]>([]);
  const [flipped, setFlipped] = useState<boolean[]>([]);
  const [matched, setMatched] = useState<boolean[]>([]);
  const [first, setFirst] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [pairs, setPairs] = useState(0);
  const [time, setTime] = useState(TOTAL);
  const [started, setStarted] = useState(false);
  const [done, setDone] = useState<{ score: number; earned: number; clear: boolean } | null>(null);
  const pairsRef = useRef(0);

  function init() {
    const picks = shuffle(EMOJI_POOL).slice(0, PAIRS);
    setCards(shuffle([...picks, ...picks]));
    setFlipped(Array(PAIRS * 2).fill(false));
    setMatched(Array(PAIRS * 2).fill(false));
    setFirst(null); setBusy(false); setPairs(0); setTime(TOTAL); setStarted(false); setDone(null);
    pairsRef.current = 0;
  }
  useEffect(init, []);

  useEffect(() => {
    if (!started || done) return;
    if (time <= 0) { end(); return; }
    const t = setTimeout(() => setTime((s) => s - 1), 1000);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [started, time, done]);

  function end() {
    if (done) return;
    const p = pairsRef.current;
    const score = Math.min(100, Math.round((p * 100) / PAIRS));
    setDone({ score, earned: awardForScore(score), clear: p === PAIRS });
  }

  function tap(i: number) {
    if (!started) setStarted(true);
    if (done || busy || flipped[i] || matched[i]) return;
    const nf = [...flipped]; nf[i] = true; setFlipped(nf);
    if (first === null) { setFirst(i); return; }
    setBusy(true);
    if (cards[first] === cards[i]) {
      const nm = [...matched]; nm[first] = true; nm[i] = true; setMatched(nm);
      setFirst(null); setBusy(false);
      pairsRef.current += 1; setPairs(pairsRef.current);
      if (pairsRef.current === PAIRS) end();
    } else {
      const f = first; setFirst(null);
      setTimeout(() => {
        setFlipped((prev) => { const x = [...prev]; x[f] = false; x[i] = false; return x; });
        setBusy(false);
      }, 550);
    }
  }

  const timerColor = time <= 10 ? "text-red-500" : time <= 20 ? "text-amber-500" : "text-primary";

  return (
    <>
      <GameHeader title="타이머 챌린지" onClose={onClose} right={<span className={"text-base font-extrabold " + timerColor}>⏱️ {time}초</span>} />
      <p className="px-5 pt-1 text-center text-xs text-muted-foreground">{started ? `${pairs}/${PAIRS} 짝 완료` : "카드를 누르면 시작!"}</p>
      <div className="grid grid-cols-4 gap-2.5 p-4">
        {cards.map((c, i) => {
          const open = flipped[i] || matched[i];
          return (
            <button
              key={i}
              onClick={() => tap(i)}
              className={"flex aspect-square items-center justify-center rounded-xl text-2xl transition-colors " + (open ? "bg-card " + (matched[i] ? "opacity-60" : "") : "bg-primary text-primary-foreground")}
            >
              {open ? c : "?"}
            </button>
          );
        })}
      </div>
      {done && (
        <ResultDialog
          emoji={done.clear ? "🏆" : "⏱️"}
          title={done.clear ? "완벽 클리어!" : "시간 초과!"}
          detail={`${pairs}/${PAIRS} 완료 · ${done.score}점`}
          earned={done.earned}
          onRetry={init}
          onClose={onClose}
        />
      )}
    </>
  );
}
