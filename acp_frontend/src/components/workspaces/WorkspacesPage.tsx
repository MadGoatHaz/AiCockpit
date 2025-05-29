// acp_frontend/src/components/workspaces/WorkspacesPage.tsx
"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { getWorkspaces, Workspace } from '@/lib/api'; // Import our API function and type
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Plus, X } from 'lucide-react';

// Import panel components later when they are ready
// import FileBrowserPanel from './FileBrowserPanel';
// import AIChatPanel from './AIChatPanel';
// import FileViewerPanel from './FileViewerPanel';
// import WorkspaceSettingsPanel from './WorkspaceSettingsPanel';
// import AIModelAndParametersPanel from './AIModelAndParametersPanel';

export default function WorkspacesPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAndSetWorkspaces = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const fetchedWorkspaces = await getWorkspaces();
      setWorkspaces(fetchedWorkspaces);
      if (fetchedWorkspaces.length > 0 && !activeWorkspaceId) {
        // If no active workspace is set, default to the first one
        setActiveWorkspaceId(fetchedWorkspaces[0].id);
      } else if (fetchedWorkspaces.length === 0) {
        setActiveWorkspaceId(null);
      }
    } catch (err) {
      setError("Failed to load workspaces. Ensure the backend is running.");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [activeWorkspaceId]); // Re-run if activeWorkspaceId changes to ensure it's still valid

  useEffect(() => {
    fetchAndSetWorkspaces();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Initial fetch

  const handleAddWorkspace = async () => {
    // Placeholder for now - will call createWorkspace API endpoint
    const newWorkspaceName = prompt("Enter new workspace name:");
    if (newWorkspaceName) {
      console.log("TODO: Call API to create workspace:", newWorkspaceName);
      // For now, simulate adding locally and refetch (or optimistically update)
      // const newSimulatedWorkspace: Workspace = {
      //   id: `temp-${Date.now()}`,
      //   name: newWorkspaceName,
      // };
      // setWorkspaces(prev => [...prev, newSimulatedWorkspace]);
      // setActiveWorkspaceId(newSimulatedWorkspace.id);
      // alert("Workspace creation is not yet connected to the backend.");
      // After backend integration:
      // try {
      //   const createdWorkspace = await createWorkspace(newWorkspaceName);
      //   fetchAndSetWorkspaces(); // Refetch to get the new list with proper ID
      //   setActiveWorkspaceId(createdWorkspace.id);
      // } catch (err) {
      //   setError("Failed to create workspace.");
      // }
      alert("Add workspace functionality not yet fully implemented with backend.");
    }
  };

  const handleCloseWorkspace = (workspaceIdToClose: string) => {
    // Placeholder for now - will call deleteWorkspace API endpoint
    console.log("TODO: Call API to delete workspace:", workspaceIdToClose);
    // Simulate closing locally
    // setWorkspaces(prev => prev.filter(ws => ws.id !== workspaceIdToClose));
    // if (activeWorkspaceId === workspaceIdToClose) {
    //   setActiveWorkspaceId(workspaces.length > 1 ? workspaces.find(ws => ws.id !== workspaceIdToClose)!.id : null);
    // }
    // alert("Close workspace functionality is not yet connected to the backend.");
    alert("Close workspace functionality not yet fully implemented with backend.");
  };

  if (isLoading) {
    return <div className="p-4 text-center">Loading workspaces...</div>;
  }

  if (error) {
    return <div className="p-4 text-center text-destructive">{error}</div>;
  }

  return (
    <div className="flex flex-col h-full">
      <Tabs
        value={activeWorkspaceId || "none"}
        onValueChange={(value) => setActiveWorkspaceId(value === "none" ? null : value)}
        className="flex flex-col"
      >
        <div className="flex items-center p-2 border-b">
          <TabsList className="mr-auto">
            {workspaces.map((ws) => (
              <TabsTrigger key={ws.id} value={ws.id} className="relative group pr-8">
                {ws.name}
                {workspaces.length > 0 && ( // Show close button if not the only tab, or always allow closing
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute top-1/2 right-0 transform -translate-y-1/2 h-5 w-5 opacity-0 group-hover:opacity-100"
                    onClick={(e) => {
                      e.stopPropagation(); // Prevent tab activation when clicking close
                      handleCloseWorkspace(ws.id);
                    }}
                  >
                    <X className="h-3 w-3" />
                    <span className="sr-only">Close workspace {ws.name}</span>
                  </Button>
                )}
              </TabsTrigger>
            ))}
            {workspaces.length === 0 && !isLoading && (
                 <div className="p-2 text-muted-foreground">No workspaces found.</div>
            )}
          </TabsList>
          <Button variant="outline" size="sm" onClick={handleAddWorkspace} className="ml-2">
            <Plus className="h-4 w-4 mr-1" /> Add Workspace
          </Button>
        </div>

        {workspaces.map((ws) => (
          <TabsContent key={ws.id} value={ws.id} className="flex-grow p-1 overflow-auto">
            {/* This is where the panel layout for the active workspace will go */}
            <div className="border rounded-lg p-4 h-full">
              <h2 className="text-xl font-semibold mb-2">Workspace: {ws.name} (ID: {ws.id})</h2>
              <p>Content for workspace "{ws.name}" will be rendered here.</p>
              <p>Panels like File Browser, AI Chat, File Viewer, Settings will be children of this.</p>
              {/* 
                Example structure for later:
                <div className="grid md:grid-cols-6 gap-4">
                  <div className="md:col-span-2"> <FileBrowserPanel sessionId={ws.id} /> </div>
                  <div className="md:col-span-4"> <FileViewerPanel sessionId={ws.id} selectedFile={...} /> </div>
                </div>
                <AIChatPanel sessionId={ws.id} />
              */}
            </div>
          </TabsContent>
        ))}
        {activeWorkspaceId === null && !isLoading && workspaces.length > 0 && (
            <div className="flex-grow p-4 text-center text-muted-foreground">Select a workspace to begin.</div>
        )}
         {activeWorkspaceId === null && !isLoading && workspaces.length === 0 && (
            <div className="flex-grow p-4 text-center text-muted-foreground">
                Click "Add Workspace" to create your first workspace.
            </div>
        )}
      </Tabs>
    </div>
  );
}
