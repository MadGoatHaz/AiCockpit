"use client";

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface AgentRunnerPanelProps {
  workspaceId: string;
  // Add other props if needed, e.g., current AI config for the workspace
}

// For Phase 1, hardcode a list of predefined agents
// These IDs should correspond to AgentConfig IDs on the backend
const PREDEFINED_AGENTS = [
  { id: "smol-dev-generic", name: "Smol Generic Developer" },
  { id: "smol-dev-planner", name: "Smol Planning Agent" },
  { id: "smol-gemini-test", name: "SmolAgent Gemini Test" },
  { id: "generic-llm-chat", name: "Generic LLM Chat Agent" }, // Example for non-smoldev agent
  // Add more as defined in the backend
];

interface AgentOutputDataObject {
    output?: string; 
    message?: string; 
}
interface AgentOutputChunk {
    run_id: string;
    type: string; 
    data: AgentOutputDataObject | string; // data can be an object or a direct string (for old LLM output)
    timestamp: string;
}

export default function AgentRunnerPanel({ workspaceId }: AgentRunnerPanelProps) {
  const [selectedAgentId, setSelectedAgentId] = useState<string>(PREDEFINED_AGENTS[0]?.id || "");
  const [goal, setGoal] = useState<string>("");
  const [output, setOutput] = useState<string[]>([]); // Output is always an array of strings
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const outputEndRef = useRef<HTMLDivElement | null>(null); // For auto-scrolling

  const scrollToBottom = () => {
    outputEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [output]); // Scroll to bottom when output changes

  const handleRunAgent = useCallback(async () => {
    if (!selectedAgentId || !goal.trim()) {
      setError("Please select an agent and provide a goal.");
      return;
    }

    setIsLoading(true);
    setOutput([]);
    setError(null);

    const requestBody = {
      agent_id: selectedAgentId,
      input_prompt: goal,
      session_id: workspaceId,
    };

    try {
      setOutput(prev => [...prev, "Agent starting..."]);
      const response = await fetch("/api/agents/run/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "text/event-stream",
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok || !response.body) {
        const errorText = await response.text();
        throw new Error(`Failed to start agent: ${response.status} ${response.statusText}. ${errorText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      
      // eslint-disable-next-line no-constant-condition
      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          if (buffer.trim()) { 
            console.warn("SSE stream ended with unprocessed buffer:", buffer);
            // Attempt to parse any final partial message if it makes sense for your protocol
            // For now, we just log it.
          }
          setOutput(prev => [...prev, "Agent stream finished."]);
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        
        let eventEndIndex;
        while ((eventEndIndex = buffer.indexOf("\n\n")) !== -1) {
          const eventString = buffer.substring(0, eventEndIndex);
          buffer = buffer.substring(eventEndIndex + 2);

          let eventType = "message"; 
          let eventDataJson = "";

          const lines = eventString.split("\n");
          for (const line of lines) {
            if (line.startsWith("event:")) {
              eventType = line.substring("event:".length).trim();
            }
            if (line.startsWith("data:")) {
              eventDataJson += line.substring("data:".length).trim(); 
            }
          }
          
          if (eventDataJson) {
            try {
              const parsedChunkFromServer: AgentOutputChunk = JSON.parse(eventDataJson);
              const chunkData = parsedChunkFromServer.data;

              if (parsedChunkFromServer.type === "log" && typeof chunkData === 'object' && chunkData && "output" in chunkData) {
                setOutput(prev => [...prev, String((chunkData as AgentOutputDataObject).output) || ""]);
              } else if (parsedChunkFromServer.type === "status" && typeof chunkData === 'object' && chunkData && "message" in chunkData) {
                setOutput(prev => [...prev, `[STATUS] ${String((chunkData as AgentOutputDataObject).message)}`]);
                //  if ((chunkData as AgentOutputDataObject & {final?: boolean}).final) { // Add final to AgentOutputDataObject if used
                //      console.log("Final status update received, preparing to close stream.");
                //  }
              } else if (parsedChunkFromServer.type === "error" && typeof chunkData === 'object' && chunkData && "message" in chunkData) {
                const errorMessage = `Agent Error: ${String((chunkData as AgentOutputDataObject).message)}`;
                setError(errorMessage);
                setOutput(prev => [...prev, `[ERROR] ${String((chunkData as AgentOutputDataObject).message)}`]);
              } else if (parsedChunkFromServer.type === "output" && typeof chunkData === 'string') { 
                setOutput(prev => [...prev, chunkData]);
              } else {
                // Fallback for unknown structured data or if data is a direct string not matching "output" type
                setOutput(prev => [...prev, `Received ${parsedChunkFromServer.type}: ${typeof chunkData === 'string' ? chunkData : JSON.stringify(chunkData)}`]);
              }
            } catch (e) {
              console.error("Failed to parse SSE data JSON:", eventDataJson, e);
              setOutput(prev => [...prev, `Malformed data: ${eventDataJson}`]);
            }
          }
        }
      }
    } catch (err: any) {
      console.error("Agent run error:", err);
      setError(err.message || "Failed to run agent or process stream.");
      setOutput(prev => [...prev, `Error: ${err.message}`]);
    } finally {
      setIsLoading(false);
    }
  }, [selectedAgentId, goal, workspaceId]);

  return (
    <div className="flex flex-col h-full p-2 space-y-4">
      <div>
        <Label htmlFor="agent-select" className="mb-2 block">Select Agent</Label>
        <Select value={selectedAgentId} onValueChange={setSelectedAgentId} disabled={isLoading}>
          <SelectTrigger id="agent-select">
            <SelectValue placeholder="Choose an agent..." />
          </SelectTrigger>
          <SelectContent>
            {PREDEFINED_AGENTS.map(agent => (
              <SelectItem key={agent.id} value={agent.id}>
                {agent.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label htmlFor="agent-goal" className="mb-2 block">Agent Goal / Prompt</Label>
        <Textarea
          id="agent-goal"
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="Describe the task for the agent..."
          className="min-h-[100px]"
          disabled={isLoading}
        />
      </div>

      <Button onClick={handleRunAgent} disabled={isLoading || !selectedAgentId || !goal.trim()}>
        {isLoading ? "Running Agent..." : "Run Agent"}
      </Button>

      {error && <p className="text-sm text-destructive">Error: {error}</p>}

      <div className="flex-grow flex flex-col min-h-0 pt-2">
        <Label className="mb-2 block">Agent Output</Label>
        <ScrollArea className="flex-grow border rounded-md p-2 bg-muted/30 min-h-[150px]">
          {output.length === 0 && !isLoading && <p className="text-sm text-muted-foreground italic">Agent output will appear here.</p>}
          {output.map((line, index) => (
            <pre key={index} className="text-xs whitespace-pre-wrap break-all">
              {line} {/* Output is now guaranteed to be string */}
            </pre>
          ))}
          {isLoading && output.length > 0 && <p className="text-sm text-muted-foreground italic mt-2">Receiving output...</p>}
          <div ref={outputEndRef} /> {/* For auto-scrolling */}
        </ScrollArea>
      </div>
    </div>
  );
} 