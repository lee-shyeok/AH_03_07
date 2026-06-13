import type { Metadata, Viewport } from "next";
import { Noto_Sans_KR } from "next/font/google";
import "./globals.css";
import { Providers } from "@/lib/query/Providers";
import { ServiceWorkerRegister } from "@/components/pwa/ServiceWorkerRegister";

const font = Noto_Sans_KR({
  weight: ["400", "500", "700", "900"],
  subsets: ["latin"],
  preload: false,
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "MediGuide — 의료 안내·복약 관리",
  description: "일반·자가면역 질환자를 위한 의료 안내와 복약 관리 서비스",
  manifest: "/manifest.webmanifest",
  applicationName: "MediGuide",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "MediGuide",
  },
  icons: {
    icon: "/icon.svg",
    apple: "/icon.svg",
  },
  formatDetection: { telephone: false },
};

export const viewport: Viewport = {
  themeColor: "#22C55E",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko" className={font.variable}>
      <body className="font-sans antialiased">
        <Providers>{children}</Providers>
        <ServiceWorkerRegister />
      </body>
    </html>
  );
}
