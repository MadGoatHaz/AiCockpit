// acp_frontend/src/components/layout/AppSidebar.tsx
"use client";

import React from 'react';
import { cn } from '@/lib/utils'; // Assuming you have this from ShadCN setup

// Import icons later, e.g., import { Gauge, MessageSquare, BarChart, ShieldCheck, History, Users, PlaySquare } from 'lucide-react';

// Define NAV_ITEMS later in constants.ts
// For now, a placeholder
const NAV_ITEMS = [
  { href: "/interact", label: "Workspaces", icon: "MessageSquare" }, // Placeholder icon name
  { href: "/aisight", label: "AiSight", icon: "Gauge" },
  { href: "/logs", label: "Logs", icon: "BarChart" },
  { href: "/alerts", label: "Alerts", icon: "ShieldCheck" },
  { href: "/history", label: "History", icon: "History" },
  { href: "/fleet", label: "Fleet", icon: "Users" },
  { href: "/live-preview", label: "Live Preview", icon: "PlaySquare" },
];


// This will be a more complex component later
// For now, a simple placeholder
interface AppSidebarProps {
  isCollapsed: boolean;
  // Add other props as needed, e.g., toggle function
}

export default function AppSidebar({ isCollapsed }: AppSidebarProps) {
  return (
    <aside
      className={cn(
        "h-screen bg-card text-card-foreground border-r transition-all duration-300 ease-in-out",
        isCollapsed ? "w-20" : "w-64"
      )}
    >
      <div className="p-4">
        <div className={cn("flex items-center", isCollapsed ? "justify-center" : "justify-between")}>
          {!isCollapsed && <h1 className="text-2xl font-bold text-primary">AiCockpit</h1>}
          {/* Placeholder for logo if isCollapsed */}
          {isCollapsed && <span className="text-2xl font-bold text-primary">A</span>}
        </div>
      </div>
      <nav className="mt-8">
        <ul>
          {NAV_ITEMS.map((item) => (
            <li key={item.href} className="mb-2">
              <a
                href={item.href}
                className={cn(
                  "flex items-center p-3 rounded-md hover:bg-muted",
                  isCollapsed ? "justify-center" : ""
                )}
              >
                {/* Icon placeholder - replace with actual Lucide icon later */}
                <span className="w-6 h-6 mr-3">{/* Icon: {item.icon} */}</span>
                {!isCollapsed && <span>{item.label}</span>}
              </a>
              {isCollapsed && (
                <span className="sr-only">{item.label}</span> // For accessibility
              )}
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
