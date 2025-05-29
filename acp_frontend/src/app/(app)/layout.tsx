// acp_frontend/src/app/(app)/layout.tsx
"use client"; // This layout will manage client-side state for sidebar

import React, { useState, ReactNode } from 'react';
import AppSidebar from '@/components/layout/AppSidebar';
import HeaderBar from '@/components/layout/HeaderBar';
import { cn } from '@/lib/utils';

// Import PersistentInfoWidgets later
// import PersistentInfoWidgets from '@/components/layout/PersistentInfoWidgets';

export default function AppLayout({ children }: { children: ReactNode }) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  // const [showPersistentWidgets, setShowPersistentWidgets] = useState(true); // Manage this state later

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  // const togglePersistentWidgets = () => {
  //   setShowPersistentWidgets(!showPersistentWidgets);
  // };

  return (
    <div className="flex min-h-screen w-full flex-col bg-muted/40">
      <AppSidebar isCollapsed={isSidebarCollapsed} />
      <div className={cn(
        "flex flex-col sm:gap-4 sm:py-4 transition-all duration-300 ease-in-out",
        isSidebarCollapsed ? "sm:pl-20" : "sm:pl-64" // Adjust based on actual sidebar width
      )}>
        <HeaderBar onToggleSidebar={toggleSidebar} />
        <main className="flex-1 gap-4 p-4 sm:px-6 sm:py-0 md:gap-8">
          {children}
        </main>
        {/* {showPersistentWidgets && <PersistentInfoWidgets />} */}
      </div>
    </div>
  );
}
