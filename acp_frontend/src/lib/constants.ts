import {
  LayoutDashboard,
  MessageSquareText,
  ScrollText,
  BellRing,
  History,
  Users,
  type LucideIcon
} from "lucide-react";

export interface NavItem {
  path: string;
  label: string;
  icon: LucideIcon;
  subItems?: NavItem[]; // For nested navigation if needed in the future
}

export const NAV_ITEMS: NavItem[] = [
  {
    path: "/dashboard",
    label: "Dashboard", // AiSight page
    icon: LayoutDashboard,
  },
  {
    path: "/interact",
    label: "Workspaces", // Main interaction area
    icon: MessageSquareText,
  },
  {
    path: "/logs",
    label: "Logs",
    icon: ScrollText,
  },
  {
    path: "/alerts",
    label: "Alerts",
    icon: BellRing,
  },
  {
    path: "/history",
    label: "History",
    icon: History,
  },
  {
    path: "/fleet",
    label: "Fleet",
    icon: Users,
  },
  // Add "Live Preview" and "AI Settings" if they become top-level nav items
];
