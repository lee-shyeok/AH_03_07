"use client";

interface TimePickerProps {
  value: string; // "HH:MM" 24시간 형식
  onChange: (v: string) => void;
  accentColor?: string;
}

export function TimePicker({ value, onChange, accentColor }: TimePickerProps) {
  const parts = value.split(":");
  const h = parseInt(parts[0] ?? "8", 10);
  const m = parseInt(parts[1] ?? "0", 10);
  const isAM = h < 12;
  const h12 = h % 12 || 12;

  function update(newH24: number, newM: number) {
    onChange(
      `${String(newH24).padStart(2, "0")}:${String(newM).padStart(2, "0")}`
    );
  }

  function toggleAMPM() {
    update(isAM ? h + 12 : h - 12, m);
  }

  function setHour12(v: number) {
    const h24 = isAM ? (v === 12 ? 0 : v) : v === 12 ? 12 : v + 12;
    update(h24, m);
  }

  const sel =
    "h-10 w-14 rounded-xl border border-input bg-background text-center text-sm font-semibold appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary/40";

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={toggleAMPM}
        className="h-10 min-w-[52px] rounded-xl px-3 text-xs font-bold text-white transition-opacity active:opacity-80"
        style={{ background: accentColor ?? "hsl(var(--primary))" }}
      >
        {isAM ? "오전" : "오후"}
      </button>

      <select
        value={h12}
        onChange={(e) => setHour12(Number(e.target.value))}
        className={sel}
      >
        {Array.from({ length: 12 }, (_, i) => i + 1).map((n) => (
          <option key={n} value={n}>
            {String(n).padStart(2, "0")}
          </option>
        ))}
      </select>

      <span className="text-base font-bold text-muted-foreground">:</span>

      <select
        value={m}
        onChange={(e) => update(h, Number(e.target.value))}
        className={sel}
      >
        {[0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55].map((n) => (
          <option key={n} value={n}>
            {String(n).padStart(2, "0")}
          </option>
        ))}
      </select>
    </div>
  );
}
