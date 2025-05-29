// acp_frontend/src/components/layout/AppSidebar.tsx
"use client";

import Link from "next/link";
import { usePathname } from 'next/navigation'; // Import usePathname
import { Gauge, PanelLeft } from "lucide-react"; // PanelLeft might be used in Header, Gauge for logo
import { NAV_ITEMS, type NavItem } from "@/lib/constants";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"; // Assuming tooltip is a ShadCN component

interface AppSidebarProps {
  isCollapsed: boolean;
  // Removed onToggle as sidebar itself won't toggle, header will
}

export default function AppSidebar({ isCollapsed }: AppSidebarProps) {
  const pathname = usePathname(); // Get current path

  const isActive = (path: string) => {
    // Handle exact match for root if necessary, otherwise startsWith for nested routes
    return pathname === path || (path !== "/" && pathname.startsWith(path));
  };

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-10 hidden flex-col border-r bg-background transition-all duration-300 ease-in-out sm:flex",
          isCollapsed ? "w-20" : "w-64"
        )}
      >
        <div className="flex h-16 items-center border-b px-6">
          <Link
            href="/"
            className="flex items-center gap-2 font-semibold text-primary"
          >
            <Gauge className="h-6 w-6" />
            {!isCollapsed && <span className="">AiCockpit</span>}
          </Link>
        </div>
        <nav
          className={cn(
            "flex flex-col gap-2 px-4 py-4",
            isCollapsed ? "items-center" : ""
          )}
        >
          {NAV_ITEMS.map((item: NavItem) =>
            isCollapsed ? (
              <Tooltip key={item.path} delayDuration={0}>
                <TooltipTrigger asChild>
                  <Link
                    href={item.path}
                    data-active={isActive(item.path)} // Add data-active attribute
                    className="flex h-10 w-10 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:text-foreground hover:bg-muted data-[active=true]:bg-accent data-[active=true]:text-accent-foreground"
                  >
                    <item.icon className="h-5 w-5" />
                    <span className="sr-only">{item.label}</span>
                  </Link>
                </TooltipTrigger>
                <TooltipContent side="right" sideOffset={5}>
                  {item.label}
                </TooltipContent>
              </Tooltip>
            ) : (
              <Link
                key={item.path}
                href={item.path}
                data-active={isActive(item.path)} // Add data-active attribute
                className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-foreground hover:bg-muted data-[active=true]:bg-accent data-[active=true]:text-accent-foreground"
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            )
          )}
        </nav>
      </aside>
    </TooltipProvider>
  );
}
