"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { BotMessageSquare, User } from 'lucide-react';

export interface AiChatPanelProps {
  workspaceId: string;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: Date;
}

const AiChatPanel: React.FC<AiChatPanelProps> = ({ workspaceId }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      sender: 'ai',
      text: `Hello! I'm your AI assistant for workspace ${workspaceId}. How can I help you today?`,
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    if (scrollAreaRef.current) {
      const viewport = scrollAreaRef.current.querySelector('div[data-radix-scroll-area-viewport]');
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight;
      }
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() === '') return;

    const userMessage: ChatMessage = {
      id: String(Date.now()),
      sender: 'user',
      text: inputValue,
      timestamp: new Date(),
    };

    setMessages(prevMessages => [...prevMessages, userMessage]);
    setInputValue('');

    // Mock AI response
    setTimeout(() => {
      const aiResponse: ChatMessage = {
        id: String(Date.now() + 1),
        sender: 'ai',
        text: `I received your message: "${userMessage.text.substring(0,50)}${userMessage.text.length > 50 ? '...':''}". I'm still learning, but I'll do my best to assist! This is a mock response. `,
        timestamp: new Date(),
      };
      setMessages(prevMessages => [...prevMessages, aiResponse]);
    }, 1000);
  };

  return (
    <div className="flex flex-col h-full bg-card" onClick={() => inputRef.current?.focus()}>
      <div className="p-3 border-b flex items-center">
        <BotMessageSquare className="h-5 w-5 mr-2 text-primary" />
        <h3 className="text-sm font-semibold">AI Chat</h3>
      </div>
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
              className={`p-2 rounded-lg max-w-[75%] text-xs ${
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
            placeholder="Send a message to AI..."
            className="flex-grow"
            autoComplete="off"
          />
          <Button type="submit" size="sm">Send</Button>
        </div>
      </form>
    </div>
  );
};

export default AiChatPanel;
