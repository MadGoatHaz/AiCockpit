"use client";

import React from 'react';
import { Settings } from 'lucide-react';

export interface WorkspaceSettingsPanelProps {
  workspaceId: string;
}

const WorkspaceSettingsPanel: React.FC<WorkspaceSettingsPanelProps> = ({ workspaceId }) => {
  return (
    <div className="flex flex-col h-full bg-card">
      <div className="p-3 border-b flex items-center">
        <Settings className="h-5 w-5 mr-2 text-primary" />
        <h3 className="text-sm font-semibold">Workspace Settings</h3>
      </div>
      <div className="flex-grow p-4 overflow-auto">
        <p className="text-xs text-muted-foreground">
          Settings for workspace <span className="font-semibold">{workspaceId}</span> will be configured here.
        </p>
        <div className="mt-4 space-y-3">
          <div>
            <label htmlFor="ws-name" className="block text-xs font-medium text-muted-foreground">Workspace Name</label>
            <input type="text" id="ws-name" defaultValue={`Workspace ${workspaceId}`} className="mt-1 block w-full rounded-md border-input bg-transparent p-2 text-xs shadow-sm" />
          </div>
          <div>
            <label className="block text-xs font-medium text-muted-foreground">Placeholder Setting 1</label>
            <p className="text-xs text-muted-foreground mt-1">Details about setting 1...</p>
          </div>
           <div>
            <label className="block text-xs font-medium text-muted-foreground">Placeholder Setting 2</label>
            <p className="text-xs text-muted-foreground mt-1">Details about setting 2...</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkspaceSettingsPanel;
