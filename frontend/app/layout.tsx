import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Peluang.ai",
  description: "Find opportunities worth your time",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="id">
      <body>{children}</body>
    </html>
  );
}
