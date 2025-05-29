"use client";

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"; // Assuming ShadCN UI components are available
import { Textarea } from "@/components/ui/textarea"; // Assuming ShadCN Textarea is available
import { FileSystemItem } from "./FileBrowserPanel"; // Import FileSystemItem

export interface EditorPanelProps {
  workspaceId: string;
  selectedFile: FileSystemItem | null; // Add selectedFile prop
}

const mockFileContent = `
// Welcome to the mock editor!
// This is a placeholder for ${"```"}My Project/src/App.tsx${"```"}

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <p>
          Edit <code>src/App.tsx</code> and save to reload.
        </p>
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a>
      </header>
    </div>
  );
}

export default App;
`;

const EditorPanel: React.FC<EditorPanelProps> = ({ workspaceId, selectedFile }) => {
  // In a real scenario, this would fetch/manage the content of the currently selected file.
  // For now, it's just a placeholder.
  const fileName = selectedFile ? selectedFile.name : "(no file selected)";
  const fileContent = selectedFile 
    ? `// Displaying content for: ${selectedFile.name}\n// Workspace: ${workspaceId}\n\n// Actual file content would go here.\n// For now, this is just a mock.
\nfunction ${selectedFile.name.split('.')[0]}() {\n  console.log("Hello from ${selectedFile.name}!");\n}`
    : mockFileContent; // Show initial mock if no file selected

  return (
    <div className="flex flex-col h-full bg-background">
      <div className="p-3 border-b bg-card">
        <h3 className="text-sm font-semibold">Editor</h3>
        <p className="text-xs text-muted-foreground">Editing: {fileName}</p>
      </div>
      <div className="flex-grow p-1">
        <Textarea
          value={fileContent} // Use dynamic content
          readOnly // For now, it's a mock display
          className="h-full w-full resize-none border-0 focus-visible:ring-0 focus-visible:ring-offset-0"
          placeholder="No file open. Select a file from the browser."
        />
      </div>
      <div className="p-2 border-t bg-card text-xs text-muted-foreground">
        Ln 1, Col 1 | Spaces: 2 | UTF-8 | TypeScript React | Git: main
      </div>
    </div>
  );
};

export default EditorPanel; 