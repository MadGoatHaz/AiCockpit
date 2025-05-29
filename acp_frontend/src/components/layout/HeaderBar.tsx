// acp_frontend/src/components/layout/HeaderBar.tsx
"use client";

import React from 'react';
import { cn } from '@/lib/utils';
// Import icons later, e.g., import { PanelLeft, Gauge as GaugeIcon } from 'lucide-react';
// Import ShadCN components like Button, DropdownMenu later

interface HeaderBarProps {
  onToggleSidebar: () => void;
  // Add other props as needed
}

export default function HeaderBar({ onToggleSidebar }: HeaderBarProps) {
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b bg-background px-4 sm:static sm:h-auto sm:border-0 sm:bg-transparent sm:px-6">
      <button
        onClick={onToggleSidebar}
        className="p-2 rounded-md hover:bg-muted lg:hidden" // Hidden on larger screens where sidebar might be fixed
      >
        {/* <PanelLeft className="h-5 w-5" /> */}
        <span>MENU</span> {/* Placeholder for PanelLeft icon */}
        <span className="sr-only">Toggle Menu</span>
      </button>
      <div className="ml-auto flex items-center gap-2">
        {/* Placeholder for Persistent Info Widgets Toggle */}
        <button className="p-2 rounded-md hover:bg-muted">
          {/* <GaugeIcon className="h-5 w-5" /> */}
          <span>GAUGE</span> {/* Placeholder for Gauge icon */}
        </button>
        {/* Placeholder for User Dropdown / Profile */}
        <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground">
          G {/* User initial */}
        </div>
      </div>
    </header>
  );
}
