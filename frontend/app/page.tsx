import { redirect } from "next/navigation";

// 진입점 → 스플래시
export default function RootPage() {
  redirect("/splash");
}
