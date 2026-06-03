// 미니게임 데이터 (REQ-GAME-002) — Flutter game_pages.dart 이식
import { getPoints, setPoints } from "./store";

export function shuffle<T>(arr: readonly T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/** 점수(0~100)에 비례해 포인트 적립, 적립량 반환 */
export function awardForScore(score: number): number {
  const earned = Math.max(1, Math.round(score / 10));
  setPoints(getPoints() + earned);
  return earned;
}

// 의료 이모지 풀 (카드 매칭 / 타이머)
export const EMOJI_POOL = [
  "💊", "🏥", "🩺", "💉", "🩹", "🧬", "🦠", "🧪", "🫀", "🫁",
  "🧠", "🦷", "🦴", "👁️", "👂", "🩻", "🩸", "💪", "🌡️", "⚕️",
];

// OX 퀴즈 (25문제 중 10개 랜덤 출제)
export interface OxQuestion { q: string; answer: boolean; desc: string }
export const OX_QUESTIONS: OxQuestion[] = [
  { q: "류마티스 관절염은 노인에게만 발생한다.", answer: false, desc: "청년층에도 발생하며 30~50대에 많습니다." },
  { q: "루푸스(SLE)는 남성에게 더 흔한 질환이다.", answer: false, desc: "루푸스는 여성 환자가 약 9배 더 많습니다." },
  { q: "자가면역 질환은 면역계가 자기 몸을 공격하는 질환이다.", answer: true, desc: "면역계 오작동으로 자신의 조직을 공격합니다." },
  { q: "류마티스 관절염은 완치가 가능한 질환이다.", answer: false, desc: "완치는 어렵지만 적절한 치료로 증상을 관리할 수 있습니다." },
  { q: "루푸스 환자는 햇빛을 피하는 것이 좋다.", answer: true, desc: "자외선이 루푸스 증상을 악화시킬 수 있습니다." },
  { q: "혈압 정상 범위는 수축기 120mmHg 미만입니다.", answer: true, desc: "정상 혈압은 120/80mmHg 미만입니다." },
  { q: "공복 혈당 정상치는 100mg/dL 미만이다.", answer: true, desc: "100 이상이면 당뇨 전단계로 봅니다." },
  { q: "혈압이 높으면 증상이 항상 나타난다.", answer: false, desc: "고혈압은 증상이 없어 '침묵의 살인자'라 불립니다." },
  { q: "당뇨 환자는 과일을 전혀 먹으면 안 된다.", answer: false, desc: "적정량의 과일은 섭취 가능하며 혈당 관리가 중요합니다." },
  { q: "복약은 식사와 상관없이 아무 때나 먹어도 된다.", answer: false, desc: "약에 따라 식전/식후/공복 복용 지침이 다릅니다." },
  { q: "항생제는 바이러스 감염에 효과적이다.", answer: false, desc: "항생제는 세균에만 효과적이며 바이러스에는 무효합니다." },
  { q: "약을 먹다가 증상이 나아지면 바로 중단해도 된다.", answer: false, desc: "임의 중단 시 내성이 생기거나 재발할 수 있습니다." },
  { q: "두 가지 이상의 약을 함께 먹으면 항상 위험하다.", answer: false, desc: "병용 가능한 약도 많지만 의사·약사와 상담이 필요합니다." },
  { q: "관절염 환자는 운동을 완전히 피해야 한다.", answer: false, desc: "적절한 저강도 운동은 관절 기능 유지에 도움이 됩니다." },
  { q: "BMI 25 이상은 과체중으로 분류된다.", answer: true, desc: "WHO 기준 BMI 25~29.9는 과체중입니다." },
  { q: "하루 물 권장 섭취량은 약 2리터이다.", answer: true, desc: "성인 기준 하루 1.5~2리터 섭취를 권장합니다." },
  { q: "스트레스는 면역계에 영향을 미친다.", answer: true, desc: "만성 스트레스는 면역 기능을 저하시킬 수 있습니다." },
  { q: "정상 체온은 약 36.5°C입니다.", answer: true, desc: "36~37.5°C가 정상 체온 범위입니다." },
  { q: "성인의 정상 심박수는 분당 60~100회이다.", answer: true, desc: "60 미만이면 서맥, 100 이상이면 빈맥입니다." },
  { q: "수면 중에는 면역 기능이 저하된다.", answer: false, desc: "수면 중 면역 세포가 활성화되어 회복을 돕습니다." },
  { q: "흡연은 류마티스 관절염 위험을 높인다.", answer: true, desc: "흡연은 류마티스 관절염의 주요 위험 인자입니다." },
  { q: "칼슘 섭취는 뼈 건강에만 중요하다.", answer: false, desc: "칼슘은 근육 수축, 신경 전달 등 다양한 역할을 합니다." },
  { q: "비타민 D는 햇빛을 통해 체내에서 합성된다.", answer: true, desc: "피부가 자외선에 노출되면 비타민 D가 합성됩니다." },
  { q: "오메가-3 지방산은 염증을 줄이는 데 도움이 된다.", answer: true, desc: "항염증 효과가 있어 자가면역 질환에도 도움됩니다." },
  { q: "고혈압 치료제는 평생 먹어야 한다.", answer: false, desc: "생활 습관 개선으로 감량·중단이 가능한 경우도 있습니다." },
];

// 단어 맞추기 (초성 퀴즈) — 20개 중 8개 랜덤
export interface WordItem { word: string; hint: string; desc: string }
export const WORD_LIST: WordItem[] = [
  { word: "류마티스", hint: "ㄹㅁㅌㅅ", desc: "관절에 염증이 생기는 자가면역 질환" },
  { word: "혈압", hint: "ㅎㅇ", desc: "혈관 벽에 가해지는 혈액의 압력" },
  { word: "항생제", hint: "ㅎㅅㅈ", desc: "세균 감염을 치료하는 약물" },
  { word: "루푸스", hint: "ㄹㅍㅅ", desc: "피부·관절·신장 등을 침범하는 자가면역 질환" },
  { word: "복약", hint: "ㅂㅇ", desc: "약을 정해진 방법대로 먹는 것" },
  { word: "혈당", hint: "ㅎㄷ", desc: "혈액 속 포도당 농도" },
  { word: "면역", hint: "ㅁㅇ", desc: "외부 병원체로부터 몸을 보호하는 시스템" },
  { word: "염증", hint: "ㅇㅈ", desc: "조직 손상 시 나타나는 발적·부종·통증 반응" },
  { word: "고혈압", hint: "ㄱㅎㅇ", desc: "혈압이 지속적으로 높은 상태" },
  { word: "당뇨", hint: "ㄷㄴ", desc: "인슐린 이상으로 혈당 조절이 안 되는 질환" },
  { word: "골다공증", hint: "ㄱㄷㄱㅈ", desc: "뼈 밀도가 감소하여 골절 위험이 높아지는 질환" },
  { word: "빈혈", hint: "ㅂㅎ", desc: "혈액 내 적혈구나 헤모글로빈이 부족한 상태" },
  { word: "갑상선", hint: "ㄱㅅㅅ", desc: "목 앞에 위치한 나비 모양의 내분비 기관" },
  { word: "인슐린", hint: "ㅇㅅㄹ", desc: "혈당을 낮추는 췌장 호르몬" },
  { word: "백신", hint: "ㅂㅅ", desc: "감염병 예방을 위해 투여하는 항원 물질" },
  { word: "항체", hint: "ㅎㅊ", desc: "면역계가 생산하는 방어 단백질" },
  { word: "처방전", hint: "ㅊㅂㅈ", desc: "의사가 약 종류·용량을 적어주는 문서" },
  { word: "부작용", hint: "ㅂㅈㅇ", desc: "약물 투여 시 나타나는 의도치 않은 효과" },
  { word: "소염제", hint: "ㅅㅇㅈ", desc: "염증과 통증을 완화하는 약물" },
  { word: "스테로이드", hint: "ㅅㅌㄹㅇㄷ", desc: "강력한 항염증 효과를 가진 약물 또는 호르몬" },
];
