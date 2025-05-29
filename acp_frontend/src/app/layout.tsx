// acp_frontend/src/app/layout.tsx
import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css"; // Your theme and Tailwind base styles
import { cn } from "@/lib/utils";
// Import Toaster and useToast hook later when we add notifications
// import { Toaster } from "@/components/ui/toaster";

export const metadata: Metadata = {
  title: "AiCockpit",
  description: "The Ultimate AI Dev Space",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={cn(
          "min-h-screen bg-background font-sans antialiased",
          GeistSans.variable,
          GeistMono.variable
        )}
      >
        {/* Add ThemeProvider here if you implement light/dark mode toggle later */}
        {children}
        {/* <Toaster /> */} {/* We'll add this when we implement toasts */}
      </body>
    </html>
  );
}
