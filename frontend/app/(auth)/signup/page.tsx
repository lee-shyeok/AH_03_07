import { redirect } from "next/navigation";

// 이메일 인증 → 정보 입력 순서 플로우는 /signup/verify 에 통합됨
export default function SignupPage() {
  redirect("/signup/verify");
}
