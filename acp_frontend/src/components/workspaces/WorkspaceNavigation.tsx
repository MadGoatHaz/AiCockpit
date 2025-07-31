// acp_frontend/src/components/workspaces/WorkspaceNavigation.tsx
"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ComputerIcon, ListIcon } from "lucide-react";

export function WorkspaceNavigation() {
  return (
    <div className="space-y-1">
      <Button variant="ghost" className="w-full justify-start" asChild>
        <Link href="/workspaces">
          <ComputerIcon className="mr-2 h-4 w-4" />
          Workspaces
        </Link>
      </Button>
      <Button variant="ghost" className="w-full justify-start" asChild>
        <Link href="/workspaces">
          <ListIcon className="mr-2 h-4 w-4" />
          My Workspaces
        </Link>
      </Button>
    </div>
  );
}