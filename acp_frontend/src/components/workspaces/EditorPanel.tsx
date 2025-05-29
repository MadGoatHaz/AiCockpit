"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { FileSystemDisplayItem as FileSystemItem } from "./FileBrowserPanel";
import { AlertTriangleIcon, CheckCircle2, Loader2, SaveIcon } from 'lucide-react';

export interface EditorPanelProps {
  workspaceId: string;
  selectedFile: FileSystemItem | null;
}

const EditorPanel: React.FC<EditorPanelProps> = ({ workspaceId, selectedFile }) => {
  const [fileContent, setFileContent] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [isDirty, setIsDirty] = useState(false);

  const fetchFileContent = useCallback(async () => {
    if (!selectedFile || selectedFile.type !== 'file' || !workspaceId) {
      setFileContent("");
      setError(null);
      setIsLoading(false);
      setIsDirty(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    setSaveSuccess(null);
    setIsDirty(false);
    try {
      const encodedFilePath = encodeURIComponent(selectedFile.path);
      const response = await fetch(`/api/workspaces/sessions/${workspaceId}/files/content?file_path=${encodedFilePath}`);
      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errData.detail || "Failed to load file content");
      }
      const textContent = await response.text();
      setFileContent(textContent);
    } catch (err) {
      console.error("Error fetching file content:", err);
      setError(err instanceof Error ? err.message : String(err));
      setFileContent("// Error loading file content.");
    } finally {
      setIsLoading(false);
    }
  }, [selectedFile, workspaceId]);

  useEffect(() => {
    fetchFileContent();
  }, [fetchFileContent]);

  const handleContentChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setFileContent(event.target.value);
    setIsDirty(true);
    setSaveSuccess(null);
  };

  const handleSaveFile = async () => {
    if (!selectedFile || selectedFile.type !== 'file' || !workspaceId || !isDirty) {
      return;
    }

    setIsSaving(true);
    setError(null);
    setSaveSuccess(null);
    try {
      const encodedFilePath = encodeURIComponent(selectedFile.path);
      const response = await fetch(`/api/workspaces/sessions/${workspaceId}/files/content?file_path=${encodedFilePath}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: fileContent }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errData.detail || "Failed to save file content");
      }
      setSaveSuccess(`File "${selectedFile.name}" saved successfully!`);
      setIsDirty(false);
      setTimeout(() => setSaveSuccess(null), 3000);
    } catch (err) {
      console.error("Error saving file content:", err);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsSaving(false);
    }
  };

  const fileName = selectedFile ? selectedFile.name : "(no file selected)";

  return (
    <div className="flex flex-col h-full bg-background">
      <div className="p-3 border-b bg-card flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold">Editor</h3>
          <p className="text-xs text-muted-foreground">
            Editing: {fileName} {isDirty ? <span className="text-yellow-500">(modified)</span> : ""}
          </p>
        </div>
        <Button 
          size="sm" 
          onClick={handleSaveFile} 
          disabled={!selectedFile || selectedFile.type !== 'file' || isLoading || isSaving || !isDirty}
          className="text-xs"
        >
          {isSaving ? <Loader2 className="h-4 w-4 animate-spin mr-1.5" /> : <SaveIcon className="h-4 w-4 mr-1.5" />}
          Save
        </Button>
      </div>

      {error && (
        <div className="p-2 text-xs text-center text-destructive bg-destructive/10 border-b flex items-center">
            <AlertTriangleIcon className="h-4 w-4 mr-2 flex-shrink-0"/> {error}
            {selectedFile && <Button variant="link" size="sm" className="p-0 h-auto text-xs ml-1 underline" onClick={fetchFileContent}>Retry Load</Button>}
        </div>
      )}
      {saveSuccess && (
        <div className="p-2 text-xs text-center text-green-600 bg-green-600/10 border-b flex items-center">
            <CheckCircle2 className="h-4 w-4 mr-2 flex-shrink-0"/> {saveSuccess}
        </div>
      )}

      <div className="flex-grow p-1 relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
            <Loader2 className="h-6 w-6 animate-spin text-primary mr-2" /> Loading content...
          </div>
        )}
        <Textarea
          value={fileContent}
          onChange={handleContentChange}
          readOnly={isLoading || !selectedFile || selectedFile.type !== 'file'}
          className="h-full w-full resize-none border-0 focus-visible:ring-0 focus-visible:ring-offset-0 disabled:opacity-80 disabled:cursor-not-allowed"
          placeholder={selectedFile ? (selectedFile.type === 'folder' ? "Select a file to edit." : "Loading file content or file is empty...") : "No file open. Select a file from the browser."}
          disabled={isLoading || !selectedFile || selectedFile.type !== 'file'}
        />
      </div>
      <div className="p-2 border-t bg-card text-xs text-muted-foreground">
        {selectedFile ? `Ln 1, Col 1 | Path: ${selectedFile.path}` : "Ready"}
      </div>
    </div>
  );
};

export default EditorPanel; 