// src/app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import "@/styles/learn-fonts.css";
import { PageLayout } from "@/components/PageLayout";
import { FontApplier } from "@/components/FontApplier";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Project Dashboard",
  description: "My awesome project dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className={inter.className}>
        <FontApplier />
        <PageLayout>{children}</PageLayout>
      </body>
    </html>
  );
}
