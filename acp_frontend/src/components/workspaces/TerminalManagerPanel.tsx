"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Terminal } from 'lucide-react';

export interface TerminalManagerPanelProps {
  workspaceId: string;
}

interface TerminalOutputLine {
  id: number;
  text: string;
  type: 'input' | 'output' | 'error';
}

const mockInitialOutput: TerminalOutputLine[] = [
  { id: 1, text: "Welcome to MockTerminal v0.1.0", type: 'output' },
  { id: 2, text: "Type 'help' for a list of mock commands.", type: 'output' },
  { id: 3, text: "user@aicockpit:~$ ", type: 'output' }, // Initial prompt
];

const TerminalManagerPanel: React.FC<TerminalManagerPanelProps> = ({ workspaceId }) => {
  const [inputValue, setInputValue] = useState('');
  const [outputLines, setOutputLines] = useState<TerminalOutputLine[]>([
    ...mockInitialOutput,
  ]);
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState<number>(-1);
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
  }, [outputLines]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  const processCommand = (command: string) => {
    let newOutput: TerminalOutputLine[] = [];
    const nextId = outputLines.length > 0 ? outputLines[outputLines.length -1].id +1 : 1;

    switch (command.trim().toLowerCase()) {
      case 'help':
        newOutput = [
          { id: nextId, text: "Available commands:", type: 'output' },
          { id: nextId + 1, text: "  help   - Show this help message", type: 'output' },
          { id: nextId + 2, text: "  ls     - List mock files", type: 'output' },
          { id: nextId + 3, text: "  clear  - Clear the terminal", type: 'output' },
          { id: nextId + 4, text: "  date   - Display current date/time", type: 'output' },
        ];
        break;
      case 'ls':
        newOutput = [
          { id: nextId, text: "drwxr-xr-x  2 user user 4096 May 30 10:00 public", type: 'output' },
          { id: nextId + 1, text: "drwxr-xr-x  3 user user 4096 May 30 10:00 src", type: 'output' },
          { id: nextId + 2, text: "-rw-r--r--  1 user user  512 May 30 09:00 package.json", type: 'output' },
        ];
        break;
      case 'date':
        newOutput = [{ id: nextId, text: new Date().toString(), type: 'output' }];
        break;
      case 'clear':
        setOutputLines([{ id: 1, text: "user@aicockpit:~$ ", type: 'output' }]);
        setInputValue('');
        return;
      case '':
        break; // Do nothing for empty command
      default:
        newOutput = [{ id: nextId, text: `command not found: ${command}`, type: 'error' }];
    }
    setOutputLines(prev => [
      ...prev,
      ...newOutput,
      { id: prev.length + newOutput.length +1, text: "user@aicockpit:~$ ", type: 'output' },
    ]);
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() === '') {
        setOutputLines(prev => [
            ...prev,
            { id: prev.length + 1, text: "user@aicockpit:~$ ", type: 'output' },
          ]);
        setInputValue('');
        return;
    }

    const command = inputValue.trim();
    const newId = outputLines.length > 0 ? outputLines[outputLines.length -1].id +1 : 1;
    setOutputLines(prev => [
      ...prev.slice(0, -1), // Remove previous prompt
      { id: newId, text: `user@aicockpit:~$ ${command}`, type: 'input' },
    ]);
    processCommand(command);
    if(command) setHistory(prev => [command, ...prev].slice(0, 50)); // Add to history, limit size
    setHistoryIndex(-1);
    setInputValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (history.length > 0) {
        const newIndex = Math.min(history.length - 1, historyIndex + 1);
        setHistoryIndex(newIndex);
        setInputValue(history[newIndex] || '');
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (history.length > 0 && historyIndex > -1) {
        const newIndex = Math.max(-1, historyIndex - 1);
        setHistoryIndex(newIndex);
        setInputValue(history[newIndex] || '');
      }
    }
  };

  return (
    <div className="flex flex-col h-full bg-black text-white font-mono text-xs" onClick={() => inputRef.current?.focus()}>
      <div className="p-2 border-b border-gray-700 bg-gray-800 flex items-center">
        <Terminal className="h-4 w-4 mr-2" />
        <h3 className="text-sm font-semibold">Terminal ({workspaceId})</h3>
      </div>
      <ScrollArea className="flex-grow p-2" ref={scrollAreaRef}>
        {outputLines.map(line => (
          <div key={line.id} className={`whitespace-pre-wrap ${line.type === 'error' ? 'text-red-400' : line.type === 'input' ? 'text-green-400': ''}`}>
            {line.text}
          </div>
        ))}
      </ScrollArea>
      <form onSubmit={handleFormSubmit} className="p-1 border-t border-gray-700 bg-gray-800">
        <div className="flex items-center">
          <span className="text-green-400 mr-1">user@aicockpit:~$</span>
          <Input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            className="flex-grow bg-transparent border-none text-white focus:ring-0 focus-visible:ring-offset-0 focus-visible:ring-0 p-0 h-6"
            placeholder="Type a command..."
            spellCheck="false"
            autoComplete="off"
          />
        </div>
      </form>
    </div>
  );
};

export default TerminalManagerPanel;
