import { z } from "zod";

export const MED_CATEGORIES = ["스테로이드", "면역억제제", "항말라리아제", "생물학적제제", "NSAID"] as const;

/** 화면 표시용 한국어 → 백엔드 DrugClass enum 매핑 */
export const CATEGORY_TO_DRUG_CLASS: Record<string, string> = {
  "스테로이드": "STEROID",
  "면역억제제": "IMMUNOSUPPRESSANT",
  "항말라리아제": "ANTIMALARIAL",
  "생물학적제제": "BIOLOGIC",
  "NSAID": "NSAID",
};

/** 백엔드 DrugClass → 한국어 표시명 */
export const DRUG_CLASS_LABEL: Record<string, string> = {
  STEROID: "스테로이드",
  IMMUNOSUPPRESSANT: "면역억제제",
  ANTIMALARIAL: "항말라리아제",
  BIOLOGIC: "생물학적제제",
  NSAID: "NSAID",
};

/** DrugClass 배지 색상 */
export const DRUG_CLASS_COLOR: Record<string, string> = {
  STEROID: "#F59E0B",
  IMMUNOSUPPRESSANT: "#7C5CCF",
  ANTIMALARIAL: "#10B981",
  BIOLOGIC: "#3B82F6",
  NSAID: "#6B7280",
};
export const MED_UNITS = ["정", "캡슐", "ml", "mg", "포"] as const;
export const MED_TIMINGS = ["아침", "점심", "저녁", "취침 전"] as const;

export const medicationSchema = z.object({
  name: z.string().min(1, "약품명을 입력하세요").max(60),
  category: z.string(),
  dose: z.string().min(1, "복용량을 입력하세요"),
  unit: z.string(),
  freq: z.number().int().min(1).max(4),
  timings: z.array(z.string()),
  start: z.string().optional(),
  end: z.string().optional(),
  memo: z.string().max(300).optional(),
});

export type MedicationInput = z.infer<typeof medicationSchema>;

/** 일반 모드 약품 자동완성 목록 */
export const GENERAL_DRUG_SUGGESTIONS = [
  "타이레놀 (아세트아미노펜)",
  "이부프로펜 400mg",
  "아스피린",
  "세티리진",
  "로라타딘",
  "오메프라졸",
  "판토프라졸",
  "에소메프라졸",
  "암로디핀",
  "아토르바스타틴",
  "메트포르민",
  "글리메피리드",
  "클라리스로마이신",
  "아목시실린",
  "독시사이클린",
  "비타민D",
  "오메가3",
  "마그네슘",
] as const;

/** 자가면역 모드 약품 자동완성 목록 */
export const AUTOIMMUNE_DRUG_SUGGESTIONS = [
  "메토트렉세이트",
  "메토트렉세이트 7.5mg",
  "메토트렉세이트 10mg",
  "메토트렉세이트 15mg",
  "하이드록시클로로퀸",
  "하이드록시클로로퀸 200mg",
  "하이드록시클로로퀸 400mg",
  "프레드니솔론",
  "프레드니솔론 5mg",
  "프레드니솔론 10mg",
  "메틸프레드니솔론",
  "덱사메타손",
  "아자티오프린",
  "아자티오프린 50mg",
  "레플루노마이드",
  "셀레콕시브",
  "설파살라진",
  "사이클로스포린",
  "타크로리무스",
  "미코페놀레이트모페틸",
  "엔브렐 (에타너셉트)",
  "휴미라 (아달리무맙)",
  "렘리케이드 (인플릭시맙)",
  "오렌시아 (아바타셉트)",
  "악템라 (토실리주맙)",
  "리툭시맙",
  "엽산",
  "엽산 1mg",
  "엽산 5mg",
] as const;
