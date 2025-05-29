// Test edit: Confirming tool access.
// acp_frontend/src/app/(app)/interact/page.tsx
"use client";

import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { PlusIcon, XIcon } from 'lucide-react';
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";

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

let workspaceCounter = 1; // Use a simple counter outside component for unique IDs if preferred

export default function InteractPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>(() => {
    const initialId = `ws-${workspaceCounter++}`;
    return [{ id: initialId, name: "Workspace 1", selectedFile: null }];
  });
  const [activeTab, setActiveTab] = useState<string>(workspaces[0].id);

  const addWorkspace = () => {
    const newWorkspaceId = `ws-${workspaceCounter++}`;
    const newWorkspace: Workspace = {
      id: newWorkspaceId,
      name: `Workspace ${workspaceCounter -1}`,
      selectedFile: null,
    };
    setWorkspaces([...workspaces, newWorkspace]);
    setActiveTab(newWorkspaceId);
  };

  const handleCloseTab = (tabId: string) => {
    if (workspaces.length === 1) return; // Prevent closing the last tab

    const newWorkspaces = workspaces.filter(ws => ws.id !== tabId);
    setWorkspaces(newWorkspaces);

    // If the active tab was closed, set a new active tab
    if (activeTab === tabId) {
      setActiveTab(newWorkspaces[0]?.id || "");
    }
  };

  const handleAddWorkspace = () => {
    const newWorkspaceId = `ws-${workspaceCounter++}`;
    const newWorkspace: Workspace = {
      id: newWorkspaceId,
      name: `Workspace ${workspaceCounter -1}`,
      selectedFile: null,
    };
    setWorkspaces([...workspaces, newWorkspace]);
    setActiveTab(newWorkspaceId);
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
          <TabsContent key={ws.id} value={ws.id} className="flex-grow mt-0 flex flex-col min-h-0 p-0"> {/* Removed default padding from TabsContent */}
            <ResizablePanelGroup
              direction="horizontal"
              className="flex-grow rounded-lg border bg-background"
            >
              <ResizablePanel defaultSize={20} minSize={15} maxSize={40}>
                {currentWorkspace && (
                  <FileBrowserPanel
                    workspaceId={currentWorkspace.id}
                    onFileSelect={(file: FileSystemItem) => handleFileSelect(currentWorkspace.id, file)}
                  />
                )}
              </ResizablePanel>
              <ResizableHandle withHandle />
              <ResizablePanel defaultSize={55} minSize={30}>
                <ResizablePanelGroup direction="vertical">
                  <ResizablePanel defaultSize={70} minSize={20}>
                    <div className="flex h-full items-center justify-center">
                      {currentWorkspace && (
                        <EditorPanel
                          workspaceId={currentWorkspace.id}
                          selectedFile={currentWorkspace.selectedFile}
                        />
                      )}
                    </div>
                  </ResizablePanel>
                  <ResizableHandle withHandle />
                  <ResizablePanel defaultSize={30} minSize={20} className="p-0">
                    <TerminalManagerPanel workspaceId={ws.id} />
                  </ResizablePanel>
                </ResizablePanelGroup>
              </ResizablePanel>
              <ResizableHandle withHandle />
              <ResizablePanel defaultSize={25} minSize={15} className="p-0">
                {/* For now, just render AiChatPanel. We can add logic later to switch with WorkspaceSettingsPanel */}
                <AiChatPanel workspaceId={ws.id} />
                {/* <WorkspaceSettingsPanel workspaceId={ws.id} /> */}
              </ResizablePanel>
            </ResizablePanelGroup>
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
