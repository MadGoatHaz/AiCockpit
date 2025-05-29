// acp_frontend/src/app/(app)/layout.tsx
"use client"; // This layout will manage client-side state for sidebar

import React, { useState, ReactNode } from 'react';
import AppSidebar from '@/components/layout/AppSidebar';
import HeaderBar from '@/components/layout/HeaderBar';
import PersistentInfoWidgets from '@/components/layout/PersistentInfoWidgets';
import { cn } from '@/lib/utils';

// This is the layout for the main application views that require the AppSidebar, Header, etc.
// It will be nested inside the root RootLayout (src/app/layout.tsx)

export interface WidgetVisibilityState {
  showCpu: boolean;
  showMemory: boolean;
  showGpuMemory: boolean;
  showGpuUsage: boolean;
  showCriticalAlerts: boolean;
}

export default function AppLayout({ children }: { children: ReactNode }) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [widgetVisibility, setWidgetVisibility] = useState<WidgetVisibilityState>({
    showCpu: true,
    showMemory: true,
    showGpuMemory: false, // Initially off
    showGpuUsage: false,  // Initially off
    showCriticalAlerts: true,
  });

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const toggleWidget = (widgetName: keyof WidgetVisibilityState) => {
    setWidgetVisibility(prevState => ({
      ...prevState,
      [widgetName]: !prevState[widgetName],
    }));
  };

  return (
    <div className="flex min-h-screen w-full flex-col bg-muted/40">
      <AppSidebar isCollapsed={isSidebarCollapsed} />
      <div className={cn(
        "flex flex-col sm:gap-4 sm:py-4 transition-all duration-300 ease-in-out",
        isSidebarCollapsed ? "sm:pl-20" : "sm:pl-64" // Corrected padding based on w-20 and w-64
      )}>
        <HeaderBar 
          onToggleSidebar={toggleSidebar} 
          widgetVisibility={widgetVisibility}
          onToggleWidget={toggleWidget}
        />
        <main className="flex-1 gap-4 p-4 sm:px-6 sm:py-0 md:gap-8 overflow-auto">
          {children}
        </main>
      </div>
      <PersistentInfoWidgets {...widgetVisibility} />
    </div>
  );
}
