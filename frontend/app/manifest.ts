import type { MetadataRoute } from "next";

// PWA 매니페스트 (Next.js 메타데이터 라우트) — /manifest.webmanifest 자동 생성
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "MediGuide — 의료 안내·복약 관리",
    short_name: "MediGuide",
    description: "일반·자가면역 질환자를 위한 의료 안내와 복약 관리 서비스",
    start_url: "/",
    scope: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#ffffff",
    theme_color: "#22C55E",
    lang: "ko",
    icons: [
      { src: "/icon.svg", sizes: "192x192", type: "image/svg+xml", purpose: "any" },
      { src: "/icon.svg", sizes: "512x512", type: "image/svg+xml", purpose: "any" },
      { src: "/icon.svg", sizes: "any", type: "image/svg+xml", purpose: "maskable" },
    ],
  };
}
