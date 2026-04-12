import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import { AuthProvider } from "@/lib/auth-context";

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
      <body className="antialiased">
        <AuthProvider>
          <div className="flex h-screen">
            <Sidebar />
            <div className="flex-1 flex flex-col overflow-hidden">
              {children ?? null}
            </div>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
