"use client";

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { BotMessageSquare, User, Settings2Icon, ChevronDownIcon } from 'lucide-react';

export interface AiChatPanelProps {
  workspaceId: string;
  selectedModelId?: string;
  temperature?: number;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: Date;
}

interface ApiChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

const AiChatPanel: React.FC<AiChatPanelProps> = ({ workspaceId, selectedModelId, temperature }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      sender: 'ai',
      text: `Hello! I'm your AI assistant for workspace ${workspaceId.substring(0,8)}... How can I help you today?`,
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isAiResponding, setIsAiResponding] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const activeModelId = selectedModelId || "gemma2-latest";
  const activeTemperature = temperature ?? 0.7;

  const scrollToBottom = useCallback(() => {
    if (scrollAreaRef.current) {
      const viewport = scrollAreaRef.current.querySelector('div[data-radix-scroll-area-viewport]');
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight;
      }
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() === '' || isAiResponding) return;

    const userMessageText = inputValue;
    const userMessage: ChatMessage = {
      id: String(Date.now()),
      sender: 'user',
      text: userMessageText,
      timestamp: new Date(),
    };

    setMessages(prevMessages => [...prevMessages, userMessage]);
    setInputValue('');
    setIsAiResponding(true);
    setChatError(null);

    const apiMessages: ApiChatMessage[] = messages.map(msg => ({
      role: msg.sender === 'user' ? 'user' : 'assistant',
      content: msg.text
    }));
    apiMessages.push({ role: 'user', content: userMessageText });

    const aiResponsePlaceholderId = String(Date.now() + 1);
    setMessages(prev => [...prev, {
      id: aiResponsePlaceholderId,
      sender: 'ai',
      text: '...',
      timestamp: new Date()
    }]);

    try {
      const response = await fetch('/api/llm/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        },
        body: JSON.stringify({
          model_id: activeModelId,
          messages: apiMessages,
          stream: true,
          temperature: activeTemperature,
        }),
      });

      if (!response.ok || !response.body) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText || "Failed to connect to AI service"}));
        throw new Error(errorData.detail);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedResponse = "";
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          if (accumulatedResponse.trim() === '') {
            setMessages(prev => prev.map(msg => 
              msg.id === aiResponsePlaceholderId ? {...msg, text: "AI model returned an empty response." } : msg
            ));
          }
          break;
        }
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n').filter(line => line.trim() !== '');
        for (const line of lines) {
          if (line.startsWith("data:")) {
            const jsonData = line.substring(5).trim();
            try {
              const parsedEvent = JSON.parse(jsonData);
              if (parsedEvent.choices && parsedEvent.choices[0]?.delta?.content) {
                accumulatedResponse += parsedEvent.choices[0].delta.content;
                setMessages(prev => prev.map(msg => 
                  msg.id === aiResponsePlaceholderId ? {...msg, text: accumulatedResponse } : msg
                ));
              } else if (parsedEvent.error) {
                console.error("Stream error from backend:", parsedEvent.error.message);
                setChatError(`AI Error: ${parsedEvent.error.message}`);
                setMessages(prev => prev.map(msg => 
                  msg.id === aiResponsePlaceholderId ? {...msg, text: `Error: ${parsedEvent.error.message}` } : msg
                ));
                return;
              }
              if (line.startsWith("event: eos")) {
                console.log("EOS event received");
              }
            } catch (e) {
              console.warn("Failed to parse JSON from stream chunk:", jsonData, e);
            }
          }
        }
      }
    } catch (error) {
      console.error("Chat API call failed:", error);
      const errorMsg = error instanceof Error ? error.message : String(error);
      setChatError(`Failed to get AI response: ${errorMsg}`);
      setMessages(prev => prev.map(msg => 
        msg.id === aiResponsePlaceholderId ? {...msg, text: `Error: ${errorMsg}` } : msg
      ));
    } finally {
      setIsAiResponding(false);
      inputRef.current?.focus();
    }
  };

  return (
    <div className="flex flex-col h-full bg-card" onClick={() => !isAiResponding && inputRef.current?.focus()}>
      <div className="p-3 border-b flex items-center justify-between">
        <div className="flex items-center">
            <BotMessageSquare className="h-5 w-5 mr-2 text-primary" />
            <h3 className="text-sm font-semibold">AI Chat <span className="text-xs text-muted-foreground">({activeModelId})</span></h3>
        </div>
        <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm" className="text-xs px-2 py-1 h-auto" disabled title={`Model: ${activeModelId}, Temp: ${activeTemperature.toFixed(1)}`}>
                <span className="mr-1.5 truncate max-w-[100px] এলipsis">{activeModelId}</span> 
                <ChevronDownIcon className="h-3 w-3" />
            </Button>
            <Button variant="ghost" size="icon" className="h-7 w-7" disabled>
                <Settings2Icon className="h-4 w-4" />
            </Button>
        </div>
      </div>
      {chatError && (
        <div className="p-2 text-xs text-center text-destructive bg-destructive/10 border-b">
            Error: {chatError}
        </div>
      )}
      <ScrollArea className="flex-grow p-3 space-y-4" ref={scrollAreaRef}>
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`flex items-start space-x-2 ${
              msg.sender === 'user' ? 'justify-end' : ''
            }`}
          >
            {msg.sender === 'ai' && (
              <div className="flex-shrink-0 h-7 w-7 rounded-full bg-primary/20 flex items-center justify-center">
                <BotMessageSquare className="h-4 w-4 text-primary" />
              </div>
            )}
            <div
              className={`p-2 rounded-lg max-w-[75%] text-xs break-words whitespace-pre-wrap ${
                msg.sender === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
              }`}
            >
              <p>{msg.text}</p>
              <p className={`text-xs mt-1 ${
                  msg.sender === 'user' ? 'text-primary-foreground/70 text-right' : 'text-muted-foreground/70'
              }`}>
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
            {msg.sender === 'user' && (
              <div className="flex-shrink-0 h-7 w-7 rounded-full bg-muted flex items-center justify-center">
                <User className="h-4 w-4 text-foreground" />
              </div>
            )}
          </div>
        ))}
      </ScrollArea>
      <form onSubmit={handleSendMessage} className="p-2 border-t">
        <div className="flex items-center space-x-2">
          <Input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            placeholder={isAiResponding ? "AI is responding..." : "Send a message to AI..."}
            className="flex-grow"
            autoComplete="off"
            disabled={isAiResponding}
          />
          <Button type="submit" size="sm" disabled={isAiResponding || inputValue.trim() === ''}>
            {isAiResponding ? "Wait..." : "Send"}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default AiChatPanel;
