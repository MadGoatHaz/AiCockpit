// Test edit: Confirming tool access.
// acp_frontend/src/app/(app)/interact/page.tsx
"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { PlusIcon, XIcon } from 'lucide-react';
import dynamic from 'next/dynamic'; // Import dynamic
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';

// Import the new panel components
import FileBrowserPanel, { FileSystemDisplayItem as FileSystemItem } from "@/components/workspaces/FileBrowserPanel";
import EditorPanel from "@/components/workspaces/EditorPanel";
// Dynamically import TerminalManagerPanel with SSR disabled
const TerminalManagerPanel = dynamic(() => import("@/components/workspaces/TerminalManagerPanel"), { ssr: false });
import AiChatPanel from "@/components/workspaces/AiChatPanel";
import WorkspaceSettingsPanel from "@/components/workspaces/WorkspaceSettingsPanel";
import AIModelConfigurationPanel from '@/components/workspaces/AIModelConfigurationPanel';
// Import AgentRunnerPanel (will be created next)
import AgentRunnerPanel from "@/components/workspaces/AgentRunnerPanel";

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
  // Which right-side panel is active: 'chat' or 'ai_settings' or 'ws_settings' or 'agentRunner'
  activeRightPanel: 'chat' | 'ai_settings' | 'ws_settings' | 'agentRunner'; 
}

const DEFAULT_AI_CONFIG = {
    selectedModelId: "gpt-3.5-turbo", // Default model for external services
    temperature: 0.7,
};

export default function InteractPage() {
  const searchParams = useSearchParams();
  const workspaceId = searchParams.get('workspace');
  
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeTab, setActiveTab] = useState<string>("");
  const workspaceCounterRef = useRef(1); // Start at 1 for naming the first workspace
  
  // If we have a workspaceId from query params, we'll use it
  // Otherwise, we'll use the existing workspace functionality
  const hasWorkspaceId = !!workspaceId;

  // Initialize first workspace on client-side to prevent hydration errors with UUID
  useEffect(() => {
    const initialWorkspaceId = crypto.randomUUID();
    setWorkspaces([
      { id: initialWorkspaceId, name: "Workspace 1", selectedFile: null, aiConfig: { ...DEFAULT_AI_CONFIG }, activeRightPanel: 'chat' }
    ]);
    setActiveTab(initialWorkspaceId);
    workspaceCounterRef.current = 2; // Set counter for next workspace
  }, []); // Empty dependency array ensures this runs only once on mount

  const addWorkspace = () => {
    const newWorkspaceNumber = workspaceCounterRef.current;
    const newWorkspaceId = crypto.randomUUID();
    const newWorkspace: Workspace = {
      id: newWorkspaceId,
      name: `Workspace ${newWorkspaceNumber}`,
      selectedFile: null,
      aiConfig: { ...DEFAULT_AI_CONFIG },
      activeRightPanel: 'chat',
    };
    setWorkspaces(prevWorkspaces => [...prevWorkspaces, newWorkspace]);
    setActiveTab(newWorkspaceId);
    workspaceCounterRef.current++;
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

  const setActiveRightPanelForCurrentWorkspace = (panel: 'chat' | 'ai_settings' | 'ws_settings' | 'agentRunner') => {
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
                  <button
                    type="button"
                    className="absolute top-1/2 right-1 -translate-y-1/2 h-6 w-6 ml-2 rounded-full hover:bg-muted/50 flex items-center justify-center"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCloseTab(ws.id);
                    }}
                  >
                    <XIcon className="h-4 w-4" />
                    <span className="sr-only">Close tab {ws.name}</span>
                  </button>
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
          <TabsContent key={ws.id} value={ws.id} className="flex-grow mt-0 flex flex-col min-h-0 p-0"> 
            {/* Original Grid Layout Start */}
            <div className="flex-grow grid grid-rows-[3fr_1fr] gap-4 p-1"> 
              
              {/* Top Row: Main Content Grid */}
              <div className="grid grid-cols-6 gap-4 overflow-auto"> 
                <div className="col-span-1 bg-card text-card-foreground rounded-lg border h-full overflow-auto p-2">
                  {currentWorkspace && (
                    <FileBrowserPanel
                      workspaceId={currentWorkspace.id}
                      onFileSelect={(file: FileSystemItem) => handleFileSelect(currentWorkspace.id, file)}
                    />
                  )}
                </div>
                <div className="col-span-3 bg-card text-card-foreground rounded-lg border h-full overflow-auto p-2">
                  {currentWorkspace && (
                    <EditorPanel
                      workspaceId={currentWorkspace.id}
                      selectedFile={currentWorkspace.selectedFile}
                    />
                  )}
                </div>
                <div className="col-span-2 bg-card text-card-foreground rounded-lg border h-full flex flex-col overflow-auto">
                  {currentWorkspace && (
                    <div className="p-2 border-b flex space-x-1">
                        <Button variant={currentWorkspace.activeRightPanel === 'chat' ? 'secondary' : 'ghost'} size="sm" className="text-xs flex-1" onClick={() => setActiveRightPanelForCurrentWorkspace('chat')}>AI Chat</Button>
                        <Button variant={currentWorkspace.activeRightPanel === 'agentRunner' ? 'secondary' : 'ghost'} size="sm" className="text-xs flex-1" onClick={() => setActiveRightPanelForCurrentWorkspace('agentRunner')}>Agent Runner</Button>
                        <Button variant={currentWorkspace.activeRightPanel === 'ai_settings' ? 'secondary' : 'ghost'} size="sm" className="text-xs flex-1" onClick={() => setActiveRightPanelForCurrentWorkspace('ai_settings')}>AI Config</Button>
                        <Button variant={currentWorkspace.activeRightPanel === 'ws_settings' ? 'secondary' : 'ghost'} size="sm" className="text-xs flex-1" onClick={() => setActiveRightPanelForCurrentWorkspace('ws_settings')}>WS Settings</Button>
                    </div>
                  )}
                  <div className="flex-grow overflow-auto p-1">
                    {currentWorkspace?.activeRightPanel === 'chat' && currentWorkspace && (
                        <AiChatPanel 
                            workspaceId={currentWorkspace.id} 
                            selectedModelId={currentWorkspace.aiConfig.selectedModelId}
                            temperature={currentWorkspace.aiConfig.temperature}
                        />
                    )}
                    {currentWorkspace?.activeRightPanel === 'agentRunner' && currentWorkspace && (
                        <AgentRunnerPanel 
                            workspaceId={currentWorkspace.id} 
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

              {/* Bottom Row: Terminal */}
              <div className="bg-card text-card-foreground rounded-lg border h-full overflow-auto p-2">
                {/* Show terminal or workspace message */}
                {hasWorkspaceId ? (
                  <TerminalManagerPanel workspaceId={workspaceId} />
                ) : currentWorkspace ? (
                  <TerminalManagerPanel workspaceId={currentWorkspace.id} />
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center p-6">
                      <h3 className="text-lg font-medium mb-2">No Active Workspace</h3>
                      <p className="text-muted-foreground mb-4">
                        {hasWorkspaceId
                          ? "The specified workspace could not be loaded."
                          : "Select a workspace from the Workspaces page to begin."}
                      </p>
                      <Button asChild>
                        <a href="/workspaces">Go to Workspaces</a>
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
            {/* Original Grid Layout End */}
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
