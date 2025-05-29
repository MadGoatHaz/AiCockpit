"use client";

import React, { useRef, useEffect, useCallback, useState } from 'react';
import { Terminal as XtermTerminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { AttachAddon } from '@xterm/addon-attach';
import '@xterm/xterm/css/xterm.css'; // Import xterm.css
import { Terminal as TerminalIcon, AlertTriangle } from 'lucide-react';

export interface TerminalManagerPanelProps {
  workspaceId: string;
}

const TerminalManagerPanel: React.FC<TerminalManagerPanelProps> = ({ workspaceId }) => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermInstanceRef = useRef<XtermTerminal | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [terminalError, setTerminalError] = useState<string | null>(null);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);

  const connectTerminal = useCallback(() => {
    if (!workspaceId || !terminalRef.current) return;
    if (xtermInstanceRef.current) return; // Already initialized

    setTerminalError(null);

    const term = new XtermTerminal({
      cursorBlink: true,
      fontSize: 13,
      fontFamily: 'monospace',
      theme: {
        background: '#000000',
        foreground: '#FFFFFF',
        cursor: '#FFFFFF',
        selectionBackground: '#555555',
        // Add more theme colors as needed
      },
      rows: 20, // Initial rows, FitAddon will adjust
      // convertEol: true, // Handle CRLF by converting to LF
    });
    xtermInstanceRef.current = term;

    const fitAddon = new FitAddon();
    fitAddonRef.current = fitAddon;
    term.loadAddon(fitAddon);

    // Construct WebSocket URL
    // Ensure the protocol is ws or wss based on the current window location protocol
    const wsProtocol = window.location.protocol === 'https:/' ? 'wss' : 'ws';
    const wsUrl = `${wsProtocol}://${window.location.host}/api/terminals/sessions/${workspaceId}/ws`;

    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      console.log('Terminal WebSocket connected');
      setIsConnected(true);
      setTerminalError(null);
      // AttachAddon handles data flow between xterm and socket
      const attachAddon = new AttachAddon(socket);
      term.loadAddon(attachAddon);
      // Fit after connection and attach, to ensure terminal is visible and sized correctly
      if (terminalRef.current) {
        fitAddon.fit();
      }
      term.focus();
    };

    socket.onclose = (event) => {
      console.log('Terminal WebSocket disconnected:', event.reason);
      setIsConnected(false);
      const reason = event.reason || "Connection closed by server.";
      setTerminalError(`Disconnected: ${reason}`);
      term.writeln(`\r\n\x1b[31mDisconnected: ${reason}\x1b[0m`);
    };

    socket.onerror = (error) => {
      console.error('Terminal WebSocket error:', error);
      setIsConnected(false);
      setTerminalError("Connection error. Check console or server logs.");
      term.writeln("\r\n\x1b[31mWebSocket connection error.\x1b[0m");
    };

    term.open(terminalRef.current);
    fitAddon.fit();

    // Handle resize. Use ResizeObserver for robust resizing.
    if (terminalRef.current) {
      resizeObserverRef.current = new ResizeObserver(() => {
        try {
            fitAddonRef.current?.fit();
            // Inform the backend PTY about the new size
            // The backend example uses "resize:cols,rows"
            if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
                 socketRef.current.send(`resize:${term.cols},${term.rows}`);
            }
        } catch (e) {
            console.warn("Error fitting terminal on resize:", e);
        }
      });
      resizeObserverRef.current.observe(terminalRef.current.parentElement || terminalRef.current);
    }

  }, [workspaceId]);

  useEffect(() => {
    connectTerminal();

    return () => {
      // Cleanup on component unmount
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      if (xtermInstanceRef.current) {
        xtermInstanceRef.current.dispose();
        xtermInstanceRef.current = null;
      }
      if (resizeObserverRef.current && terminalRef.current?.parentElement) {
        resizeObserverRef.current.unobserve(terminalRef.current.parentElement);
      }
       if (resizeObserverRef.current && terminalRef.current) {
        resizeObserverRef.current.unobserve(terminalRef.current);
      }
      resizeObserverRef.current = null;
      fitAddonRef.current = null;
      setIsConnected(false);
    };
  }, [connectTerminal]); // Rerun if workspaceId changes, which changes connectTerminal

  // Manual resize handler if needed, but ResizeObserver is preferred
  // useEffect(() => {
  //   const handleResize = () => {
  //     fitAddonRef.current?.fit();
  //   };
  //   window.addEventListener('resize', handleResize);
  //   return () => window.removeEventListener('resize', handleResize);
  // }, []);

  return (
    <div className="flex flex-col h-full bg-black text-white font-mono text-xs">
      <div className="p-2 border-b border-gray-700 bg-gray-800 flex items-center justify-between">
        <div className="flex items-center">
            <TerminalIcon className="h-4 w-4 mr-2" />
            <h3 className="text-sm font-semibold">Terminal ({workspaceId ? workspaceId.substring(0,8) + '...': 'N/A'})</h3>
        </div>
        <div className={`text-xs px-2 py-0.5 rounded-full ${isConnected ? 'bg-green-600/80' : 'bg-red-600/80'}`}>
            {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </div>
      {terminalError && (
        <div className="p-1.5 text-center text-red-300 bg-red-700/50 border-b border-red-600 flex items-center justify-center">
            <AlertTriangle className="h-4 w-4 mr-2" /> {terminalError}
        </div>
      )}
      <div ref={terminalRef} className="flex-grow w-full h-full p-1" />
      {/* The input form is removed as xterm.js handles input directly */}
    </div>
  );
};

export default TerminalManagerPanel;
