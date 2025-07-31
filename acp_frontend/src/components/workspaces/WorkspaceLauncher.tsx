// acp_frontend/src/components/workspaces/WorkspaceLauncher.tsx
"use client";

import React from 'react';
import { Button } from "@/components/ui/button";
import { ExternalLinkIcon } from "lucide-react";

interface WorkspaceLauncherProps {
  workspaceId: string;
  disabled?: boolean;
}

export function WorkspaceLauncher({ workspaceId, disabled }: WorkspaceLauncherProps) {
  const handleLaunch = async () => {
    try {
      // Check if the workspace is running by calling the backend
      const response = await fetch(`/api/workspaces/${workspaceId}`);
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to verify workspace status: ${response.status} - ${errorText}`);
      }
      
      const workspace = await response.json();
      if (workspace.status !== 'running') {
        alert(`Workspace is not running. Current status: ${workspace.status}\nPlease start the workspace before launching the IDE.`);
        return;
      }
      
      // Open the workspace IDE in a new tab
      window.open(`/interact?workspace=${workspaceId}`, '_blank');
    } catch (error) {
      console.error('Error launching workspace:', error);
      alert(`Failed to launch workspace: ${error}`);
    }
  };

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleLaunch}
      disabled={disabled}
      title={disabled ? "Start the workspace to enable IDE access" : "Launch workspace IDE"}
    >
      <ExternalLinkIcon className="h-4 w-4 mr-2" />
      Open IDE
    </Button>
  );
}