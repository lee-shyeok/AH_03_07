"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { DIAGRAM_META, type DiagramKind } from "./jointDiagram";

const PURPLE = "#7C5CCF";

interface JointPickerProps {
  kind: DiagramKind;
  /** 전체 joint_swelling_areas (거친 부위 + 다른 도해 마디 포함) */
  selected: string[];
  /** 완료 시 갱신된 전체 배열을 돌려줌 */
  onSave: (next: string[]) => void;
  onClose: () => void;
}

/**
 * 손가락/발가락 부종 부위를 인체 도해 위에서 마디별로 선택하는 모달.
 * - 인쇄된 도해 원에 핫스팟이 겹쳐 있고, 탭하면 해당 마디가 보라색으로 채워짐.
 * - 저장값은 위치기반 id(예: "손_좌_검지_1")로 joint_swelling_areas 배열에 그대로 들어감.
 * - 다른 부위("어깨" 등)나 반대쪽 도해 마디는 건드리지 않고 보존.
 */
export default function JointPicker({ kind, selected, onSave, onClose }: JointPickerProps) {
  const meta = DIAGRAM_META[kind];

  const [picked, setPicked] = useState<string[]>(() =>
    selected.filter((s) => s.startsWith(meta.prefix))
  );

  // 다른 도해로 다시 열릴 때 동기화
  useEffect(() => {
    setPicked(selected.filter((s) => s.startsWith(meta.prefix)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kind]);

  const toggle = (id: string) =>
    setPicked((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  const handleSave = () => {
    const others = selected.filter((s) => !s.startsWith(meta.prefix));
    onSave([...others, ...picked]);
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 sm:items-center"
      onClick={onClose}
    >
      <div
        className="flex max-h-[92vh] w-full flex-col bg-white rounded-t-2xl sm:max-w-md sm:rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 헤더 */}
        <div className="flex items-center justify-between border-b border-gray-100 px-5 py-4">
          <div>
            <h3 className="text-base font-semibold text-gray-900">{meta.label} 부종 부위</h3>
            <p className="mt-0.5 text-xs text-gray-500">
              부은 마디를 눌러 표시하세요 · {picked.length}곳 선택
            </p>
          </div>
          <button onClick={onClose} aria-label="닫기" className="p-1 text-gray-400 hover:text-gray-600">
            <X size={22} />
          </button>
        </div>

        {/* 도해 + 핫스팟 */}
        <div className="flex-1 overflow-auto p-4">
          <div className="relative mx-auto w-full max-w-sm select-none">
            <img
              src={meta.src}
              alt={`${meta.label} 도해`}
              className="pointer-events-none h-auto w-full"
              draggable={false}
            />
            {meta.joints.map((j) => {
              const on = picked.includes(j.id);
              return (
                <button
                  key={j.id}
                  type="button"
                  onClick={() => toggle(j.id)}
                  aria-label={j.id}
                  aria-pressed={on}
                  className="absolute flex -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full"
                  style={{ left: `${j.x}%`, top: `${j.y}%`, width: "7.5%", aspectRatio: "1 / 1" }}
                >
                  <span
                    className="block rounded-full transition-all"
                    style={{
                      width: on ? "78%" : "48%",
                      aspectRatio: "1 / 1",
                      backgroundColor: on ? PURPLE : "rgba(124,92,207,0.10)",
                      border: on ? `2px solid ${PURPLE}` : "1.5px solid rgba(124,92,207,0.45)",
                      boxShadow: on ? "0 0 0 3px rgba(124,92,207,0.22)" : "none",
                    }}
                  />
                </button>
              );
            })}
          </div>
        </div>

        {/* 푸터 */}
        <div className="flex gap-2 border-t border-gray-100 px-5 py-4">
          <button
            type="button"
            onClick={() => setPicked([])}
            className="flex-1 rounded-xl border border-gray-200 py-3 text-sm font-medium text-gray-600"
          >
            모두 해제
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="flex-[2] rounded-xl py-3 text-sm font-semibold text-white"
            style={{ backgroundColor: PURPLE }}
          >
            완료 ({picked.length})
          </button>
        </div>
      </div>
    </div>
  );
}
