// acp_frontend/src/app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css"; // Your theme and Tailwind base styles
import { cn } from "@/lib/utils";
import { Toaster } from "@/components/ui/toaster"; // Assuming toaster path

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AiCockpit",
  description: "Comprehensive, collaborative development environment for AI-assisted software development.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={cn(
        inter.className, 
        "bg-slate-900 text-slate-50"
      )}>
        {/* Add ThemeProvider here if you implement light/dark mode toggle later */}
        {children}
        <Toaster />
      </body>
    </html>
  );
}
