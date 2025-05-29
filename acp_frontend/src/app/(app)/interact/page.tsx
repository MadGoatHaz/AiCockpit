// Test edit: Confirming tool access.
// acp_frontend/src/app/(app)/interact/page.tsx
"use client";

import React, { useState, useRef } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { PlusIcon, XIcon } from 'lucide-react';
import dynamic from 'next/dynamic'; // Import dynamic

// Import the new panel components
import FileBrowserPanel, { FileSystemDisplayItem as FileSystemItem } from "@/components/workspaces/FileBrowserPanel";
import EditorPanel from "@/components/workspaces/EditorPanel";
// Dynamically import TerminalManagerPanel with SSR disabled
const TerminalManagerPanel = dynamic(() => import("@/components/workspaces/TerminalManagerPanel"), { ssr: false });
import AiChatPanel from "@/components/workspaces/AiChatPanel";
import WorkspaceSettingsPanel from "@/components/workspaces/WorkspaceSettingsPanel";
import AIModelConfigurationPanel from '@/components/workspaces/AIModelConfigurationPanel';

// Define a type for a workspace
interface Workspace {
  id: string;
  name: string;
  selectedFile: FileSystemItem | null;
  // AI Configuration for this workspace
  aiConfig: {
    selectedModelId: string;
    temperature: number;
  };
  // Which right-side panel is active: 'chat' or 'ai_settings' or 'ws_settings'
  activeRightPanel: 'chat' | 'ai_settings' | 'ws_settings'; 
}

const DEFAULT_AI_CONFIG = {
    selectedModelId: "gemma2-latest", // Default model
    temperature: 0.7,
};

export default function InteractPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([
    { id: "ws-1", name: "Workspace 1", selectedFile: null, aiConfig: { ...DEFAULT_AI_CONFIG }, activeRightPanel: 'chat' }
  ]);
  const [activeTab, setActiveTab] = useState<string>("ws-1");
  const workspaceCounterRef = useRef(2);

  const addWorkspace = () => {
    const newWorkspaceNumber = workspaceCounterRef.current;
    const newWorkspaceId = `ws-${newWorkspaceNumber}`;
    const newWorkspace: Workspace = {
      id: newWorkspaceId,
      name: `Workspace ${newWorkspaceNumber}`,
      selectedFile: null,
      aiConfig: { ...DEFAULT_AI_CONFIG },
      activeRightPanel: 'chat',
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

  // For the right-side panel, decide which component to show
  const handleAiConfigurationChange = (workspaceId: string, config: { selectedModelId?: string, temperature?: number }) => {
    setWorkspaces(prevWorkspaces =>
      prevWorkspaces.map(ws =>
        ws.id === workspaceId
          ? { ...ws, aiConfig: { 
                selectedModelId: config.selectedModelId || ws.aiConfig.selectedModelId,
                temperature: config.temperature ?? ws.aiConfig.temperature,
            } }
          : ws
      )
    );
  };

  const setActiveRightPanelForCurrentWorkspace = (panel: 'chat' | 'ai_settings' | 'ws_settings') => {
    if (currentWorkspace) {
        setWorkspaces(prev => prev.map(ws => ws.id === currentWorkspace.id ? {...ws, activeRightPanel: panel} : ws));
    }
  };

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
                <div className="col-span-2 bg-card text-card-foreground rounded-lg border h-full flex flex-col overflow-auto"> {/* Right Panel Container */}
                  {/* Tabs or Buttons to switch between Chat, AI Settings, WS Settings */}
                  {currentWorkspace && (
                    <div className="p-2 border-b flex space-x-1">
                        <Button variant={currentWorkspace.activeRightPanel === 'chat' ? 'secondary' : 'ghost'} size="sm" className="text-xs flex-1" onClick={() => setActiveRightPanelForCurrentWorkspace('chat')}>AI Chat</Button>
                        <Button variant={currentWorkspace.activeRightPanel === 'ai_settings' ? 'secondary' : 'ghost'} size="sm" className="text-xs flex-1" onClick={() => setActiveRightPanelForCurrentWorkspace('ai_settings')}>AI Config</Button>
                        <Button variant={currentWorkspace.activeRightPanel === 'ws_settings' ? 'secondary' : 'ghost'} size="sm" className="text-xs flex-1" onClick={() => setActiveRightPanelForCurrentWorkspace('ws_settings')}>WS Settings</Button>
                    </div>
                  )}

                  <div className="flex-grow overflow-auto p-1">
                    {currentWorkspace?.activeRightPanel === 'chat' && currentWorkspace && (
                        <AiChatPanel 
                            workspaceId={currentWorkspace.id} 
                            // Pass AI config to chat panel
                            selectedModelId={currentWorkspace.aiConfig.selectedModelId}
                            temperature={currentWorkspace.aiConfig.temperature}
                        />
                    )}
                    {currentWorkspace?.activeRightPanel === 'ai_settings' && currentWorkspace && (
                        <AIModelConfigurationPanel 
                            workspaceId={currentWorkspace.id} 
                            onConfigurationChange={(config) => handleAiConfigurationChange(currentWorkspace.id, config)}
                        />
                    )}
                    {currentWorkspace?.activeRightPanel === 'ws_settings' && currentWorkspace && (
                        <WorkspaceSettingsPanel workspaceId={currentWorkspace.id} />
                    )}
                  </div>
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
