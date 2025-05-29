"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { Settings, Loader2, CheckCircle2, AlertTriangleIcon, SaveIcon } from 'lucide-react';
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";

export interface WorkspaceSettingsPanelProps {
  workspaceId: string;
}

interface SessionMetadata {
  id: string;
  name: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
  // custom_ui_settings?: Record<string, any> | null;
}

const WorkspaceSettingsPanel: React.FC<WorkspaceSettingsPanelProps> = ({ workspaceId }) => {
  const [name, setName] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchWorkspaceDetails = useCallback(async () => {
    if (!workspaceId) return;
    setIsLoading(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const response = await fetch(`/api/sessions/${workspaceId}`);
      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errData.detail || "Failed to load workspace details");
      }
      const data: SessionMetadata = await response.json();
      setName(data.name || `Workspace ${workspaceId}`);
      setDescription(data.description || "");
    } catch (err) {
      console.error("Error fetching workspace details:", err);
      setError(err instanceof Error ? err.message : String(err));
      // Set defaults if load fails to allow user to see the panel
      setName(`Workspace ${workspaceId}`);
      setDescription("");
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    fetchWorkspaceDetails();
  }, [fetchWorkspaceDetails]);

  const handleSaveChanges = async () => {
    if (!workspaceId) return;
    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);

    const updatePayload = {
      name: name, // Assuming name might be editable too in future
      description: description,
    };

    try {
      const response = await fetch(`/api/sessions/${workspaceId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatePayload),
      });
      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errData.detail || "Failed to save workspace settings");
      }
      const updatedData: SessionMetadata = await response.json();
      setName(updatedData.name);
      setDescription(updatedData.description || "");
      setSuccessMessage("Workspace settings saved successfully!");
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error("Error saving workspace settings:", err);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col h-full bg-card items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground mt-2">Loading workspace settings...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-card">
      <div className="p-3 border-b flex items-center justify-between">
        <div className="flex items-center">
            <Settings className="h-5 w-5 mr-2 text-primary" />
            <h3 className="text-sm font-semibold">Workspace Settings</h3>
        </div>
        <Button size="sm" onClick={handleSaveChanges} disabled={isSaving} className="text-xs">
            {isSaving ? <Loader2 className="h-4 w-4 animate-spin mr-1.5" /> : <SaveIcon className="h-4 w-4 mr-1.5"/>}
            Save Changes
        </Button>
      </div>

      {error && (
        <div className="p-2 text-xs text-center text-destructive bg-destructive/10 border-b flex items-center">
            <AlertTriangleIcon className="h-4 w-4 mr-2 flex-shrink-0"/> {error} 
            <Button variant="link" size="sm" className="p-0 h-auto text-xs ml-1 underline" onClick={fetchWorkspaceDetails}>Retry</Button>
        </div>
      )}
      {successMessage && (
        <div className="p-2 text-xs text-center text-green-600 bg-green-600/10 border-b flex items-center">
            <CheckCircle2 className="h-4 w-4 mr-2 flex-shrink-0"/> {successMessage}
        </div>
      )}

      <div className="flex-grow p-4 overflow-auto">
        <p className="text-xs text-muted-foreground mb-4">
          Settings for workspace <span className="font-semibold">{name}</span> (ID: {workspaceId ? workspaceId.substring(0,8) + '...' : 'N/A'}).
        </p>
        <div className="space-y-6">
          <div>
            <Label htmlFor="ws-name" className="text-xs font-medium text-muted-foreground">Workspace Name</Label>
            <Input 
                type="text" 
                id="ws-name" 
                value={name} 
                onChange={(e) => setName(e.target.value)} 
                className="mt-1 text-xs" 
                disabled={isSaving}
            />
          </div>
          <div>
            <Label htmlFor="ws-description" className="text-xs font-medium text-muted-foreground">Description</Label>
            <Textarea 
                id="ws-description" 
                placeholder="Enter a brief description for this workspace..." 
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="mt-1 text-xs" 
                rows={3}
                disabled={isSaving}
            />
          </div>

          <div className="flex items-center justify-between rounded-lg border p-3 shadow-sm">
            <div className="space-y-0.5">
                <Label htmlFor="auto-save" className="text-xs font-medium">Auto-save</Label>
                <p className="text-[11px] text-muted-foreground">
                    Automatically save changes to files in this workspace.
                </p>
            </div>
            <Switch id="auto-save" disabled={isSaving}/>
          </div>

          <div>
            <Label className="block text-xs font-medium text-muted-foreground">Placeholder Setting 1</Label>
            <p className="text-xs text-muted-foreground mt-1">Details about setting 1...</p>
          </div>
           <div>
            <Label className="block text-xs font-medium text-muted-foreground">Placeholder Setting 2</Label>
            <p className="text-xs text-muted-foreground mt-1">Details about setting 2...</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkspaceSettingsPanel;
