import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Litigation Analytics",
  description: "AI-powered litigation and eDiscovery analytics workspace",
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
