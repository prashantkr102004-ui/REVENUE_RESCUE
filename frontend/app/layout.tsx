import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RevenueRescue AI",
  description: "Autonomous revenue recovery engine",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
