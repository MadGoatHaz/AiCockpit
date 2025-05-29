// acp_frontend/src/components/layout/HeaderBar.tsx
"use client";

import Link from "next/link";
import { usePathname } from 'next/navigation'; // Import usePathname
import React from 'react'; // Import React for useState if used directly here (though state is lifted)
import {
  PanelLeft,
  Gauge, // For Persistent Info Toggle
  Search, // Placeholder for future search
  Settings2, // Placeholder for user/settings dropdown
} from "lucide-react";

import {
  Sheet,
  SheetContent,
  SheetTrigger,
} from "@/components/ui/sheet"; // ShadCN Sheet for mobile menu
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuCheckboxItem
} from "@/components/ui/dropdown-menu"; // ShadCN Dropdown
import { Button } from "@/components/ui/button";
import { NAV_ITEMS, type NavItem } from "@/lib/constants";
import { cn } from "@/lib/utils";

interface HeaderBarProps {
  onToggleSidebar: () => void;
  // onTogglePersistentWidgets: () => void; // Add this when implementing the widgets
}

export default function HeaderBar({ onToggleSidebar }: HeaderBarProps) {
  const pathname = usePathname(); // Get current path

  const isActive = (path: string) => {
    return pathname === path || (path !== "/" && pathname.startsWith(path));
  };
  // const [showCpu, setShowCpu] = React.useState(true) // Example state for widget toggles
  // const [showMemory, setShowMemory] = React.useState(true)

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b bg-background px-4 sm:static sm:h-auto sm:border-0 sm:bg-transparent sm:px-6">
      <Sheet>
        <SheetTrigger asChild>
          <Button size="icon" variant="outline" className="sm:hidden">
            <PanelLeft className="h-5 w-5" />
            <span className="sr-only">Toggle Menu</span>
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="sm:max-w-xs">
          <nav className="grid gap-6 text-lg font-medium">
            <Link
              href="/"
              className="group flex h-10 w-10 shrink-0 items-center justify-center gap-2 rounded-full bg-primary text-lg font-semibold text-primary-foreground md:text-base"
            >
              <Gauge className="h-5 w-5 transition-all group-hover:scale-110" />
              <span className="sr-only">AiCockpit</span>
            </Link>
            {NAV_ITEMS.map((item: NavItem) => (
              <Link
                key={item.path}
                href={item.path}
                data-active={isActive(item.path)} // Add data-active attribute
                className="flex items-center gap-4 px-2.5 text-muted-foreground hover:text-foreground data-[active=true]:text-foreground data-[active=true]:font-semibold"
              >
                <item.icon className="h-5 w-5" />
                {item.label}
              </Link>
            ))}
          </nav>
        </SheetContent>
      </Sheet>

      {/* Desktop Sidebar Toggle - visible on sm+ screens, hidden on mobile (where Sheet is used) */}
      <Button
        size="icon"
        variant="outline"
        className="hidden sm:inline-flex" // Hidden on mobile
        onClick={onToggleSidebar}
      >
        <PanelLeft className="h-5 w-5" />
        <span className="sr-only">Toggle Sidebar</span>
      </Button>

      {/* Spacer to push alys to the right */}
      <div className="relative ml-auto flex-1 md:grow-0">
        {/* Search placeholder - implement later */}
        {/* <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" /> */}
        {/* <Input type="search" placeholder="Search..." className="w-full rounded-lg bg-background pl-8 md:w-[200px] lg:w-[336px]" /> */}
      </div>

      {/* Persistent Info Widgets Toggle Dropdown */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="icon" className="overflow-hidden rounded-full">
            <Gauge className="h-5 w-5" /> 
            {/* Later, this could be a different icon or User avatar */}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>Info Widgets</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {/* Example Toggles - connect to state and actual widget visibility later */}
          <DropdownMenuCheckboxItem
            // checked={showCpu}
            // onCheckedChange={setShowCpu}
          >
            CPU Usage
          </DropdownMenuCheckboxItem>
          <DropdownMenuCheckboxItem
            // checked={showMemory}
            // onCheckedChange={setShowMemory}
          >
            Memory Usage
          </DropdownMenuCheckboxItem>
          {/* Add other widgets: GPU, Alerts etc. */}
          <DropdownMenuSeparator />
          <DropdownMenuItem>Settings</DropdownMenuItem> {/* Placeholder */}
          <DropdownMenuItem>Logout</DropdownMenuItem> {/* Placeholder */}
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}
