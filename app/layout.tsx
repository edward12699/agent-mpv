import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "合同分析 Agent 控制台",
  description: "多工具 AI 工作流 — 合同检索、排序与流程可视化",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
