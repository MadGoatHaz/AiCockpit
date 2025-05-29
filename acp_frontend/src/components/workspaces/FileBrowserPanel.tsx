"use client";

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { FolderIcon, FileIcon, ChevronRightIcon, ChevronDownIcon, UploadCloudIcon, RotateCwIcon, PlusCircleIcon, FilePlus2Icon, FolderPlusIcon, Trash2Icon, AlertTriangleIcon as DialogAlertIcon } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogClose } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"

// Updated to match backend FileNode structure + client-side needs (id, children)
export interface FileSystemDisplayItem {
  id: string; // Client-side unique ID (can be path)
  name: string;
  path: string; // Relative path from session data root
  type: 'file' | 'folder';
  size?: number; // For files
  children?: FileSystemDisplayItem[]; // For folders, populated by expanding
  // content?: string;
}

export interface FileBrowserPanelProps {
  workspaceId: string;
  onFileSelect?: (file: FileSystemDisplayItem) => void;
}

// Backend's FileNode structure
interface BackendFileNode {
  name: string;
  path: string;
  type: 'file' | 'folder';
  size?: number;
  // Backend doesn't send children directly for a flat list, frontend will manage hierarchy
}

interface BackendDirectoryListing {
  path: string;
  contents: BackendFileNode[];
}

const transformBackendNodesToDisplayTree = (nodes: BackendFileNode[], basePath: string = ""): FileSystemDisplayItem[] => {
  const map: { [key: string]: FileSystemDisplayItem } = {};
  const roots: FileSystemDisplayItem[] = [];

  // Initialize all items and place them in the map
  nodes.forEach(node => {
    map[node.path] = {
      ...node,
      id: node.path, // Use path as unique ID
      children: node.type === 'folder' ? [] : undefined,
    };
  });

  // This simplistic transformation assumes a flat list for the current directory.
  // For a true recursive fetch-on-demand, expand folder logic would fetch its children.
  // For now, we just return the items at the current level.
  // A more complex version would build a tree if the backend returned nested structures
  // or if we were to fetch children recursively here.
  
  // This is a basic flat list for now. If a directory is listed, its children are fetched separately by clicking it.
  // This initial load is for a single directory path.
  return nodes.map(node => ({
    ...node,
    id: node.path,
    children: node.type === 'folder' ? [] : undefined, // Folders start with empty children, to be loaded on expand
  }));
};

// Recursive component to render file system items
const RenderItem: React.FC<{
  item: FileSystemDisplayItem;
  level: number;
  onToggleExpand: (item: FileSystemDisplayItem) => void;
  isFolderExpanded: (itemId: string) => boolean;
  onSelect: (item: FileSystemDisplayItem) => void;
  selectedItemId: string | null;
}> = ({ item, level, onToggleExpand, isFolderExpanded, onSelect, selectedItemId }) => {
  const isFolder = item.type === 'folder';
  const isSelected = item.id === selectedItemId;
  const currentItemIsExpanded = isFolder && isFolderExpanded(item.id);

  const handleItemClick = () => {
    if (isFolder) {
      onToggleExpand(item);
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
          <div className="w-[18px] mr-1.5 flex-shrink-0" />
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
          {item.children.length === 0 && (
            <div style={{ paddingLeft: `${(level + 1) * 16}px` }} className="py-1 px-2 text-muted-foreground italic">
              Folder is empty or content not loaded.
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const FileBrowserPanel: React.FC<FileBrowserPanelProps> = ({ workspaceId, onFileSelect }) => {
  const [fileSystem, setFileSystem] = useState<FileSystemDisplayItem[]>([]);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [currentUploadPath, setCurrentUploadPath] = useState("."); 
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isLoadingFiles, setIsLoadingFiles] = useState(false);
  const [loadFilesError, setLoadFilesError] = useState<string | null>(null);

  // State for Create New Dialog
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [createEntityType, setCreateEntityType] = useState<'file' | 'folder' | null>(null);
  const [newEntityName, setNewEntityName] = useState("");
  const [createError, setCreateError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  // State for Delete Confirmation Dialog
  const [showDeleteConfirmDialog, setShowDeleteConfirmDialog] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<FileSystemDisplayItem | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchFiles = useCallback(async (folderPath: string = ".", forceRefresh: boolean = false) => {
    if (!workspaceId) return;
    setIsLoadingFiles(true);
    setLoadFilesError(null);
    console.log(`Fetching files for workspace: ${workspaceId}, path: ${folderPath}`);

    try {
      const response = await fetch(`/api/workspaces/sessions/${workspaceId}/files/list?path=${encodeURIComponent(folderPath)}`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `Failed to fetch files: ${response.status}`);
      }
      const data: BackendDirectoryListing = await response.json();
      
      const transformedData = transformBackendNodesToDisplayTree(data.contents, data.path);
      
      if (folderPath === "." || forceRefresh) { // Root directory load or forced refresh of root
        setFileSystem(transformedData);
      } else { // Sub-directory load (children of an expanded folder)
        setFileSystem(prevFs => {
          const updateRecursively = (items: FileSystemDisplayItem[]): FileSystemDisplayItem[] => {
            return items.map(item => {
              if (item.id === folderPath && item.type === 'folder') {
                return { ...item, children: transformedData };
              }
              if (item.children) {
                return { ...item, children: updateRecursively(item.children) };
              }
              return item;
            });
          };
          return updateRecursively(prevFs);
        });
      }

    } catch (error) {
      console.error("Error fetching files:", error);
      const errorMsg = error instanceof Error ? error.message : String(error);
      setLoadFilesError(`Failed to load files: ${errorMsg}`);
      if (folderPath === ".") {
        setFileSystem([]);
      }
    } finally {
      setIsLoadingFiles(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    fetchFiles(".");
    setExpandedFolders(new Set());
    setSelectedItemId(null);
  }, [fetchFiles, workspaceId]);

  const handleToggleExpand = async (folderItem: FileSystemDisplayItem) => {
    if (!workspaceId) return;

    const folderId = folderItem.id;
    const isCurrentlyExpanded = expandedFolders.has(folderId);

    setExpandedFolders(prev => {
      const newSet = new Set(prev);
      if (isCurrentlyExpanded) {
        newSet.delete(folderId);
      } else {
        newSet.add(folderId);
        if (!folderItem.children || folderItem.children.length === 0) {
           console.log(`Folder ${folderItem.name} expanded, fetching children for path: ${folderItem.path}`);
           fetchFiles(folderItem.path);
        }
      }
      return newSet;
    });
  };

  const handleSelectItem = (item: FileSystemDisplayItem) => {
    setSelectedItemId(item.id);
    if (item.type === 'file' && onFileSelect) {
      onFileSelect(item);
    }
    if (item.type === 'folder') {
        setCurrentUploadPath(item.path); // Set current path for uploads or new items
    }
  };

  const isFolderExpanded = (folderId: string) => expandedFolders.has(folderId);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !workspaceId) return;

    setIsUploading(true);
    setUploadError(null);
    console.log(`Selected file: ${file.name}, attempting to upload to workspace: ${workspaceId}, path: ${currentUploadPath}`);

    const formData = new FormData();
    formData.append("file", file);
    const uploadUrl = `/api/workspaces/sessions/${workspaceId}/files/upload?relative_path=${encodeURIComponent(currentUploadPath)}`;
    
    try {
      const response = await fetch(uploadUrl, { method: 'POST', body: formData });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `Upload failed: ${response.status}`);
      }
      const result = await response.json(); // Backend returns FileMetadata
      console.log("Upload successful:", result);
      // Refresh the view of the directory where the file was uploaded.
      fetchFiles(currentUploadPath, true); 
      event.target.value = ''; // Reset file input
    } catch (error) {
      console.error("Error during file upload:", error);
      const errorMsg = error instanceof Error ? error.message : String(error);
      setUploadError(`Upload failed: ${errorMsg}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleRefresh = () => {
    // Determine which path to refresh. If a folder is selected, refresh its content.
    // Otherwise, refresh the root.
    const pathToRefresh = selectedItemId && fileSystem.find(item => item.id === selectedItemId)?.type === 'folder'
        ? fileSystem.find(item => item.id === selectedItemId)!.path
        : ".";
    
    // If refreshing a subfolder that is expanded, we want its children to be re-fetched.
    // If it's the root ("."), fetchFiles will handle replacing the entire fileSystem state.
    fetchFiles(pathToRefresh, true);
    
    // If refreshing a specific folder, ensure it remains expanded or children are shown
    if (pathToRefresh !== "." && selectedItemId) {
        // If the folder was already expanded, fetchFiles will fill its children.
        // If it wasn't, expanding it will trigger fetchFiles for its path.
        // We might need to ensure the expanded state is preserved or re-applied if necessary.
        // For now, if it's expanded, its content will be updated.
        // If it's not, this refresh might not show immediate child changes until expanded.
        // The `forceRefresh` logic in fetchFiles should handle updating the specific item's children.
        const selectedItem = findItemById(fileSystem, selectedItemId);
        if (selectedItem && selectedItem.type === 'folder') {
             setExpandedFolders(prev => new Set(prev).add(selectedItem.id)); // Ensure it's marked as expanded
        }
    }
  };

  // Helper to find an item by ID in the potentially nested structure
  const findItemById = (items: FileSystemDisplayItem[], id: string): FileSystemDisplayItem | null => {
    for (const item of items) {
        if (item.id === id) return item;
        if (item.children) {
            const foundInChild = findItemById(item.children, id);
            if (foundInChild) return foundInChild;
        }
    }
    return null;
  };

  const openCreateDialog = (type: 'file' | 'folder') => {
    setCreateEntityType(type);
    setShowCreateDialog(true);
    setNewEntityName("");
    setCreateError(null);
  };

  const handleCreateEntity = async () => {
    if (!createEntityType || !newEntityName.trim() || !workspaceId) {
      setCreateError("Name cannot be empty.");
      return;
    }
    setIsCreating(true);
    setCreateError(null);

    // Determine the base path for creation: selected folder or root
    let basePath = ".";
    if (selectedItemId) {
        const selectedItem = findItemById(fileSystem, selectedItemId);
        if (selectedItem && selectedItem.type === 'folder') {
            basePath = selectedItem.path;
        } else if (selectedItem && selectedItem.type === 'file') {
            // If a file is selected, use its parent directory path
            const parentPath = selectedItem.path.substring(0, selectedItem.path.lastIndexOf('/'));
            basePath = parentPath || ".";
        }
    }
    const fullPath = basePath === "." ? newEntityName.trim() : `${basePath}/${newEntityName.trim()}`;

    try {
      const response = await fetch(`/api/workspaces/sessions/${workspaceId}/files/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: fullPath, type: createEntityType }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errData.detail || `Failed to create ${createEntityType}`);
      }
      // const createdEntity: FileSystemDisplayItem = await response.json(); // Backend returns FileNode
      setShowCreateDialog(false);
      setNewEntityName("");
      // Refresh the parent directory where the entity was created
      fetchFiles(basePath, true);
      // If we created a folder in an expanded folder, ensure the parent remains expanded
      if(basePath !== "." && expandedFolders.has(basePath)){
        // fetchFiles will update its children
      } else if (basePath === "."){
        // Root refreshed
      }

    } catch (err) {
      console.error(`Error creating ${createEntityType}:`, err);
      setCreateError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsCreating(false);
    }
  };

  // --- DELETE LOGIC ---
  const openDeleteDialog = () => {
    if (!selectedItemId) return;
    const item = findItemById(fileSystem, selectedItemId);
    if (item) {
      setItemToDelete(item);
      setShowDeleteConfirmDialog(true);
      setDeleteError(null);
    } else {
      setDeleteError("Could not find the selected item to delete.");
    }
  };

  const handleDeleteEntity = async () => {
    if (!itemToDelete || !workspaceId) {
      setDeleteError("No item selected for deletion or workspace ID missing.");
      return;
    }
    setIsDeleting(true);
    setDeleteError(null);
    try {
      const response = await fetch(`/api/workspaces/sessions/${workspaceId}/files/delete?item_path=${encodeURIComponent(itemToDelete.path)}&item_type=${itemToDelete.type}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errData.detail || `Failed to delete ${itemToDelete.type}`);
      }
      setShowDeleteConfirmDialog(false);
      setItemToDelete(null);
      setSelectedItemId(null); // Deselect after deletion
      
      // Determine parent path to refresh
      const parentPath = itemToDelete.path.includes('/') ? itemToDelete.path.substring(0, itemToDelete.path.lastIndexOf('/')) : ".";
      fetchFiles(parentPath, true);
      if (onFileSelect && selectedItemId === itemToDelete.id) { // If deleted file was shown in editor
        onFileSelect(null as any); // Signal to clear editor
      }

    } catch (err) {
      console.error(`Error deleting ${itemToDelete.type}:`, err);
      setDeleteError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsDeleting(false);
    }
  };

  const selectedItemForActions = selectedItemId ? findItemById(fileSystem, selectedItemId) : null;

  return (
    <div className="flex flex-col h-full bg-card text-card-foreground p-2 space-y-2">
      <div className="flex items-center space-x-1 flex-wrap gap-1">
        <Button variant="outline" size="sm" onClick={() => openCreateDialog('file')} className="text-xs px-2 py-1 h-auto grow">
            <FilePlus2Icon className="h-3.5 w-3.5 mr-1" /> New File
        </Button>
        <Button variant="outline" size="sm" onClick={() => openCreateDialog('folder')} className="text-xs px-2 py-1 h-auto grow">
            <FolderPlusIcon className="h-3.5 w-3.5 mr-1" /> New Folder
        </Button>
        <Button variant="outline" size="sm" onClick={handleUploadClick} disabled={isUploading || isLoadingFiles} className="text-xs px-2 py-1 h-auto grow">
          {isUploading ? <RotateCwIcon className="h-3.5 w-3.5 mr-1 animate-spin" /> : <UploadCloudIcon className="h-3.5 w-3.5 mr-1" />} Upload
        </Button>
        <Button variant="ghost" size="icon" onClick={handleRefresh} disabled={isLoadingFiles || isUploading} className="h-7 w-7">
          <RotateCwIcon className={`h-4 w-4 ${isLoadingFiles ? 'animate-spin' : ''}`} />
          <span className="sr-only">Refresh</span>
        </Button>
        {selectedItemForActions && (
             <AlertDialog>
                <AlertDialogTrigger asChild>
                    <Button variant="destructive" size="icon" className="h-7 w-7" title={`Delete ${selectedItemForActions.name}`}>
                        <Trash2Icon className="h-4 w-4" />
                    </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                    <AlertDialogHeader>
                    <DialogTitle>Delete {selectedItemForActions.type}: "{selectedItemForActions.name}"?</DialogTitle>
                    <AlertDialogDescription>
                        This action cannot be undone. This will permanently delete the {selectedItemForActions.type}
                        {selectedItemForActions.type === 'folder' && " and all its contents"}.
                        {deleteError && <p className="text-xs text-destructive mt-2"><DialogAlertIcon className="inline h-4 w-4 mr-1"/>{deleteError}</p>}
                    </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                    <AlertDialogCancel onClick={() => setDeleteError(null)} disabled={isDeleting}>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={handleDeleteEntity} disabled={isDeleting} className="bg-destructive hover:bg-destructive/90">
                        {isDeleting ? <RotateCwIcon className="h-4 w-4 animate-spin mr-1.5" /> : <Trash2Icon className="h-4 w-4 mr-1.5"/>}
                        Delete
                    </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        )}
      </div>
      <input type="file" ref={fileInputRef} onChange={handleFileChange} style={{ display: 'none' }} />
      {uploadError && <p className="text-xs text-destructive p-1 bg-destructive/10 rounded">Upload Error: {uploadError}</p>}
      {loadFilesError && (
        <div className="text-xs text-destructive p-2 bg-destructive/10 rounded">
          <p>Error loading files: {loadFilesError}</p>
          <Button variant="link" size="sm" onClick={() => fetchFiles(".", true)} className="p-0 h-auto text-xs">Retry Root Load</Button>
        </div>
      )}

      <div className="flex-grow overflow-auto border rounded-md p-1 min-h-[150px]">
        {isLoadingFiles && fileSystem.length === 0 && <p className="text-xs text-muted-foreground p-2">Loading file structure...</p>}
        {!isLoadingFiles && fileSystem.length === 0 && !loadFilesError && (
          <p className="text-xs text-center text-muted-foreground p-4">Workspace is empty. Create a file/folder or upload.</p>
        )}
        {fileSystem.map(item => (
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

      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Create New {createEntityType === 'file' ? 'File' : 'Folder'}</DialogTitle>
            <DialogDescription>
                Enter the name for the new {createEntityType}. It will be created in the currently selected folder or at the root.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="new-entity-name" className="text-right text-xs">
                Name
              </Label>
              <Input 
                id="new-entity-name" 
                value={newEntityName} 
                onChange={(e) => setNewEntityName(e.target.value)} 
                className="col-span-3 text-xs h-8"
                placeholder={createEntityType === 'file' ? 'e.g., myFile.txt' : 'e.g., my_new_folder'}
                onKeyDown={(e) => e.key === 'Enter' && handleCreateEntity()} 
              />
            </div>
            {createError && <p className="col-span-4 text-xs text-destructive text-center p-1 bg-destructive/10 rounded">{createError}</p>}
          </div>
          <DialogFooter>
            <DialogClose asChild>
                <Button type="button" variant="outline" size="sm" className="text-xs">Cancel</Button>
            </DialogClose>
            <Button type="button" onClick={handleCreateEntity} disabled={isCreating || !newEntityName.trim()} size="sm" className="text-xs">
              {isCreating ? <RotateCwIcon className="h-4 w-4 animate-spin mr-1.5" /> : (createEntityType === 'file' ? <FilePlus2Icon className="h-4 w-4 mr-1.5"/> : <FolderPlusIcon className="h-4 w-4 mr-1.5"/>)}
              Create {createEntityType}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

    </div>
  );
};

export default FileBrowserPanel;
