import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "컷앤킵 포트폴리오",
  description: "사진·GIF·짧은 영상을 한 문장으로 다루는 컷앤킵의 구성, 화면, 서버, AI를 설명하는 사이트.",
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/favicon.ico" },
    ],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
