import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI README Generator",
  description: "Generate high-quality README files and documentation with AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children?: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children ?? null}</body>
    </html>
  );
}
