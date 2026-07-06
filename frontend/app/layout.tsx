import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LegalSight",
  description: "AI-powered litigation and eDiscovery analytics workspace for LegalSight",
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
