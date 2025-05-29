// Test edit: Confirming tool access.
// acp_frontend/src/app/(app)/interact/page.tsx
"use client";

import React, { useState, useRef } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { PlusIcon, XIcon } from 'lucide-react';

// Import the new panel components
import FileBrowserPanel, { FileSystemItem } from "@/components/workspaces/FileBrowserPanel";
import EditorPanel from "@/components/workspaces/EditorPanel";
import TerminalManagerPanel from "@/components/workspaces/TerminalManagerPanel";
import AiChatPanel from "@/components/workspaces/AiChatPanel";
import WorkspaceSettingsPanel from "@/components/workspaces/WorkspaceSettingsPanel";

// Define a type for a workspace
interface Workspace {
  id: string;
  name: string;
  selectedFile: FileSystemItem | null;
  // Later, we can add more properties like file tree, open files, panel layouts, etc.
}

export default function InteractPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([
    // Initialize with one static workspace to prevent hydration errors
    { id: "ws-1", name: "Workspace 1", selectedFile: null }
  ]);
  const [activeTab, setActiveTab] = useState<string>("ws-1"); // Default to the static ID

  // Use a ref for the counter for new workspaces. Start at 2 because ws-1 is statically created.
  const workspaceCounterRef = useRef(2);

  const addWorkspace = () => {
    const newWorkspaceNumber = workspaceCounterRef.current;
    const newWorkspaceId = `ws-${newWorkspaceNumber}`;
    const newWorkspace: Workspace = {
      id: newWorkspaceId,
      name: `Workspace ${newWorkspaceNumber}`,
      selectedFile: null,
    };
    setWorkspaces(prevWorkspaces => [...prevWorkspaces, newWorkspace]);
    setActiveTab(newWorkspaceId);
    workspaceCounterRef.current++; // Increment for the next workspace
  };

  const handleCloseTab = (tabId: string) => {
    if (workspaces.length === 1) return; // Prevent closing the last tab

    const newWorkspaces = workspaces.filter(ws => ws.id !== tabId);
    setWorkspaces(newWorkspaces);

    if (activeTab === tabId) {
      setActiveTab(newWorkspaces[0]?.id || "");
    }
  };

  const handleFileSelect = (workspaceId: string, file: FileSystemItem) => {
    setWorkspaces(prevWorkspaces =>
      prevWorkspaces.map(ws =>
        ws.id === workspaceId ? { ...ws, selectedFile: file } : ws
      )
    );
    // Potentially switch focus to editor panel if not already there
  };

  const currentWorkspace = workspaces.find(ws => ws.id === activeTab);

  // For the right-side panel, decide which component to show (e.g., AI Chat or Settings)
  // This could be managed by another state variable per workspace, or a sub-tab system.
  // For now, let's just show AiChatPanel by default.

  return (
    <div className="flex flex-col h-full p-4 md:p-6">
      <div className="flex items-center mb-4">
        <h1 className="text-2xl font-semibold mr-auto">Workspaces</h1>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-grow flex flex-col min-h-0">
        <div className="flex items-center border-b">
          <TabsList className="py-0 px-0 h-auto rounded-none border-none -mb-px">
            {workspaces.map((ws) => (
              <TabsTrigger
                key={ws.id}
                value={ws.id}
                className="relative data-[state=active]:border-b-primary data-[state=active]:text-primary data-[state=active]:shadow-none rounded-none border-b-2 border-transparent px-4 py-3 font-medium h-auto"
              >
                {ws.name}
                {workspaces.length > 1 && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute top-1/2 right-1 -translate-y-1/2 h-6 w-6 ml-2 rounded-full hover:bg-muted/50"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCloseTab(ws.id);
                    }}
                  >
                    <XIcon className="h-4 w-4" />
                    <span className="sr-only">Close tab {ws.name}</span>
                  </Button>
                )}
              </TabsTrigger>
            ))}
          </TabsList>
          <Button variant="ghost" size="icon" onClick={addWorkspace} className="ml-2 text-muted-foreground hover:text-foreground">
            <PlusIcon className="h-5 w-5" />
            <span className="sr-only">Add new workspace</span>
          </Button>
        </div>

        {workspaces.map((ws) => (
          <TabsContent key={ws.id} value={ws.id} className="flex-grow mt-0 flex flex-col min-h-0 p-0"> {/* Ensure TabsContent allows flex-grow for its children */}
            {/* New Grid Layout Start */}
            <div className="flex-grow grid grid-rows-[5fr_1fr] gap-4 p-1"> {/* Outer container for 2 rows, adjust fr units as needed */}
              
              {/* Top Row: Main Content Grid (e.g., 6 columns) */}
              <div className="grid grid-cols-6 gap-4 overflow-auto"> {/* Added overflow-auto for content */}
                <div className="col-span-1 bg-card text-card-foreground rounded-lg border h-full overflow-auto p-2"> {/* FileBrowserPanel - Added bg-card, text-card-foreground, p-2 */}
                  {currentWorkspace && (
                    <FileBrowserPanel
                      workspaceId={currentWorkspace.id}
                      onFileSelect={(file: FileSystemItem) => handleFileSelect(currentWorkspace.id, file)}
                    />
                  )}
                </div>
                <div className="col-span-3 bg-card text-card-foreground rounded-lg border h-full overflow-auto p-2"> {/* EditorPanel - Added bg-card, text-card-foreground, p-2 */}
                  {currentWorkspace && (
                    <EditorPanel
                      workspaceId={currentWorkspace.id}
                      selectedFile={currentWorkspace.selectedFile}
                    />
                  )}
                </div>
                <div className="col-span-2 bg-card text-card-foreground rounded-lg border h-full overflow-auto p-2"> {/* AiChatPanel - Added bg-card, text-card-foreground, p-2 */}
                  <AiChatPanel workspaceId={ws.id} />
                  {/* Placeholder for WorkspaceSettingsPanel later */}
                  {/* <WorkspaceSettingsPanel workspaceId={ws.id} /> */}
                </div>
              </div>

              {/* Bottom Row: Terminal (spans full width of the top grid) */}
              <div className="bg-card text-card-foreground rounded-lg border h-full overflow-auto p-2"> {/* TerminalManagerPanel - Added bg-card, text-card-foreground, p-2 */}
                <TerminalManagerPanel workspaceId={ws.id} />
              </div>

            </div>
            {/* New Grid Layout End */}
          </TabsContent>
        ))}
        {workspaces.length === 0 && (
          <div className="flex-grow flex flex-col items-center justify-center text-muted-foreground p-10">
            <p className="mb-2">No workspaces open.</p>
            <Button onClick={addWorkspace}>Create a new Workspace</Button>
          </div>
        )}
      </Tabs>
    </div>
  );
}
