// acp_frontend/src/app/(app)/layout.tsx
"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { CodeIcon } from "lucide-react";
import { WorkspaceNavigation } from "@/components/workspaces/WorkspaceNavigation";

export default function AppLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  
  return (
    <div className="flex flex-col h-screen">
      {/* Navigation Bar */}
      <header className="border-b">
        <div className="container flex items-center h-14 px-4">
          <Link href="/" className="flex items-center space-x-2">
            <span className="font-bold">AiCockpit</span>
          </Link>
          <nav className="flex items-center space-x-1 ml-6">
            <Button 
              variant={pathname === "/interact" ? "secondary" : "ghost"} 
              size="sm" 
              className="justify-start"
              asChild
            >
              <Link href="/interact">
                <CodeIcon className="mr-2 h-4 w-4" />
                Interact
              </Link>
            </Button>
            <WorkspaceNavigation />
          </nav>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="flex-grow overflow-auto">
        {children}
      </main>
    </div>
  );
}