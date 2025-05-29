"use client";

import React, { useState } from 'react';
import { FolderIcon, FileIcon, ChevronRightIcon, ChevronDownIcon, UploadCloudIcon } from 'lucide-react'; // Import icons and Chevron icons

// Define a type for file system items
export interface FileSystemItem {
  id: string;
  name: string;
  type: 'file' | 'folder';
  children?: FileSystemItem[]; // Children for folders
  // content?: string; // For files, if we decide to load content here later
}

export interface FileBrowserPanelProps {
  workspaceId: string; // To associate with a specific workspace context if needed later
  // We might want to lift selected file state up or use a context later
  // For now, let's add a callback prop for when a file is selected
  onFileSelect?: (file: FileSystemItem) => void;
}

// Mock file system data for display
const mockFileSystem: FileSystemItem[] = [
  {
    id: 'root',
    name: 'My Project',
    type: 'folder',
    children: [
      {
        id: 'f1',
        name: 'public',
        type: 'folder',
        children: [
          { id: 'file1-1', name: 'index.html', type: 'file' },
          { id: 'file1-2', name: 'favicon.ico', type: 'file' },
        ],
      },
      {
        id: 'f2',
        name: 'src',
        type: 'folder',
        children: [
          { id: 'file2-1', name: 'App.tsx', type: 'file' },
          { id: 'file2-2', name: 'main.tsx', type: 'file' },
          {
            id: 'f2-1',
            name: 'components',
            type: 'folder',
            children: [
              { id: 'file2-1-1', name: 'Button.tsx', type: 'file' },
            ],
          },
        ],
      },
      { id: 'file3', name: 'package.json', type: 'file' },
      { id: 'file4', name: 'README.md', type: 'file' },
    ],
  },
];

// Recursive component to render file system items
const RenderItem: React.FC<{
  item: FileSystemItem;
  level: number;
  onToggleExpand: (itemId: string) => void;
  isFolderExpanded: (itemId: string) => boolean;
  onSelect: (item: FileSystemItem) => void;
  selectedItemId: string | null;
}> = ({ item, level, onToggleExpand, isFolderExpanded, onSelect, selectedItemId }) => {
  const isFolder = item.type === 'folder';
  const isSelected = item.id === selectedItemId;
  const currentItemIsExpanded = isFolder && isFolderExpanded(item.id);

  const handleItemClick = () => {
    if (isFolder) {
      onToggleExpand(item.id);
    }
    onSelect(item);
  };

  const indentStyle = { paddingLeft: `${level * 16}px` };

  return (
    <div className="text-xs">
      <div
        style={indentStyle}
        className={`flex items-center py-1 px-2 hover:bg-muted rounded-md cursor-pointer ${
          isSelected ? 'bg-primary/20 text-primary-foreground' : ''
        }`}
        onClick={handleItemClick}
      >
        {isFolder ? (
          currentItemIsExpanded ? (
            <ChevronDownIcon className="h-4 w-4 mr-1.5 text-muted-foreground flex-shrink-0" />
          ) : (
            <ChevronRightIcon className="h-4 w-4 mr-1.5 text-muted-foreground flex-shrink-0" />
          )
        ) : (
          <div className="w-[18px] mr-1.5 flex-shrink-0" /> // Adjusted width to align chevron and file icon space
        )}
        {isFolder ? (
          <FolderIcon className="h-4 w-4 mr-2 text-accent flex-shrink-0" />
        ) : (
          <FileIcon className="h-4 w-4 mr-2 text-muted-foreground flex-shrink-0" />
        )}
        <span className={`truncate ${isSelected && !isFolder ? 'font-medium text-primary' : 'text-foreground/90'}`}>{item.name}</span>
      </div>
      {isFolder && currentItemIsExpanded && item.children && (
        <div>
          {item.children.map(child => (
            <RenderItem
              key={child.id}
              item={child}
              level={level + 1}
              onToggleExpand={onToggleExpand}
              isFolderExpanded={isFolderExpanded}
              onSelect={onSelect}
              selectedItemId={selectedItemId}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const FileBrowserPanel: React.FC<FileBrowserPanelProps> = ({ workspaceId, onFileSelect }) => {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(['root', 'f2'])); // Default expanded folders
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);

  const handleToggleExpand = (folderId: string) => {
    setExpandedFolders(prev => {
      const newSet = new Set(prev);
      if (newSet.has(folderId)) {
        newSet.delete(folderId);
      } else {
        newSet.add(folderId);
      }
      return newSet;
    });
  };

  const handleSelectItem = (item: FileSystemItem) => {
    setSelectedItemId(item.id);
    if (item.type === 'file' && onFileSelect) {
      onFileSelect(item);
    }
    // If a folder is selected, we could also trigger an action, e.g., show folder details
  };

  // Helper to check if a folder is expanded
  const isFolderExpanded = (folderId: string) => {
    return expandedFolders.has(folderId);
  };

  return (
    <div className="flex flex-col h-full bg-card text-card-foreground border-r border-border" suppressHydrationWarning>
      <div className="p-3 border-b border-border flex justify-between items-center">
        <div>
          <h3 className="text-base font-semibold text-foreground">File Browser</h3>
          {workspaceId && <p className="text-xs text-muted-foreground">Workspace: {workspaceId}</p>}
        </div>
        <button className="p-1.5 hover:bg-muted rounded-md" title="Upload File (Not Implemented)">
          <UploadCloudIcon className="h-4 w-4 text-muted-foreground" />
        </button>
      </div>
      <div className="flex-grow p-1.5 space-y-0.5 overflow-y-auto">
        {mockFileSystem.map(item => (
          <RenderItem
            key={item.id}
            item={item}
            level={0}
            onToggleExpand={handleToggleExpand}
            isFolderExpanded={isFolderExpanded}
            onSelect={handleSelectItem}
            selectedItemId={selectedItemId}
          />
        ))}
      </div>
    </div>
  );
};

export default FileBrowserPanel;
