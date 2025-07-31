// acp_frontend/src/app/(app)/workspaces/page.tsx
"use client";

import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Play, Square, Trash2, PlusIcon, ExternalLinkIcon } from 'lucide-react';
import { WorkspaceLauncher } from "@/components/workspaces/WorkspaceLauncher";

interface Workspace {
  id: string;
  name: string;
  description: string | null;
  owner_id: string;
  container_id: string;
  container_image: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export default function WorkspacesPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newWorkspace, setNewWorkspace] = useState({
    name: '',
    description: '',
    image: 'continuumio/anaconda3'
  });

  // Fetch workspaces from the backend
  const fetchWorkspaces = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/workspaces');
      if (response.ok) {
        const data = await response.json();
        setWorkspaces(data);
      } else {
        const errorText = await response.text();
        console.error('Failed to fetch workspaces:', response.status, errorText);
        // Show error to user
        alert(`Failed to fetch workspaces: ${response.status} - ${errorText}`);
      }
    } catch (error) {
      console.error('Error fetching workspaces:', error);
      // Show error to user
      alert(`Error fetching workspaces: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  // Create a new workspace
  const createWorkspace = async () => {
    try {
      const response = await fetch('/api/workspaces', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newWorkspace),
      });

      if (response.ok) {
        const workspace = await response.json();
        setWorkspaces([...workspaces, workspace]);
        setShowCreateDialog(false);
        setNewWorkspace({
          name: '',
          description: '',
          image: 'continuumio/anaconda3'
        });
        // Show success message
        alert(`Workspace "${workspace.name}" created successfully!`);
      } else {
        const errorText = await response.text();
        console.error('Failed to create workspace:', response.status, errorText);
        // Show error to user
        alert(`Failed to create workspace: ${response.status} - ${errorText}`);
      }
    } catch (error) {
      console.error('Error creating workspace:', error);
      // Show error to user
      alert(`Error creating workspace: ${error}`);
    }
  };

  // Start a workspace
  const startWorkspace = async (workspaceId: string) => {
    try {
      // Find the workspace name for better user feedback
      const workspace = workspaces.find(w => w.id === workspaceId);
      const workspaceName = workspace ? workspace.name : 'Unknown';
      
      const response = await fetch(`/api/workspaces/${workspaceId}/start`, {
        method: 'POST',
      });

      if (response.ok) {
        const updatedWorkspace = await response.json();
        setWorkspaces(workspaces.map(w =>
          w.id === workspaceId ? { ...w, status: updatedWorkspace.status } : w
        ));
        // Show success message
        alert(`Workspace "${workspaceName}" started successfully!`);
      } else {
        const errorText = await response.text();
        console.error('Failed to start workspace:', response.status, errorText);
        // Show error to user
        alert(`Failed to start workspace "${workspaceName}": ${response.status} - ${errorText}`);
      }
    } catch (error) {
      console.error('Error starting workspace:', error);
      // Show error to user
      alert(`Error starting workspace: ${error}`);
    }
  };

  // Stop a workspace
  const stopWorkspace = async (workspaceId: string) => {
    try {
      // Find the workspace name for better user feedback
      const workspace = workspaces.find(w => w.id === workspaceId);
      const workspaceName = workspace ? workspace.name : 'Unknown';
      
      const response = await fetch(`/api/workspaces/${workspaceId}/stop`, {
        method: 'POST',
      });

      if (response.ok) {
        const updatedWorkspace = await response.json();
        setWorkspaces(workspaces.map(w =>
          w.id === workspaceId ? { ...w, status: updatedWorkspace.status } : w
        ));
        // Show success message
        alert(`Workspace "${workspaceName}" stopped successfully!`);
      } else {
        const errorText = await response.text();
        console.error('Failed to stop workspace:', response.status, errorText);
        // Show error to user
        alert(`Failed to stop workspace "${workspaceName}": ${response.status} - ${errorText}`);
      }
    } catch (error) {
      console.error('Error stopping workspace:', error);
      // Show error to user
      alert(`Error stopping workspace: ${error}`);
    }
  };

  // Delete a workspace
  const deleteWorkspace = async (workspaceId: string) => {
    // Find the workspace name for better user feedback
    const workspace = workspaces.find(w => w.id === workspaceId);
    const workspaceName = workspace ? workspace.name : 'Unknown';
    
    // Confirm with user before deleting
    if (!confirm(`Are you sure you want to delete workspace "${workspaceName}"? This action cannot be undone.`)) {
      return;
    }
    
    try {
      const response = await fetch(`/api/workspaces/${workspaceId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setWorkspaces(workspaces.filter(w => w.id !== workspaceId));
        // Show success message
        alert(`Workspace "${workspaceName}" deleted successfully!`);
      } else {
        const errorText = await response.text();
        console.error('Failed to delete workspace:', response.status, errorText);
        // Show error to user
        alert(`Failed to delete workspace "${workspaceName}": ${response.status} - ${errorText}`);
      }
    } catch (error) {
      console.error('Error deleting workspace:', error);
      // Show error to user
      alert(`Error deleting workspace "${workspaceName}": ${error}`);
    }
  };

  // Load workspaces when the component mounts
  useEffect(() => {
    fetchWorkspaces();
  }, []);

  // Status badge component
  const StatusBadge = ({ status }: { status: string }) => {
    const statusColors = {
      'running': 'bg-green-500',
      'stopped': 'bg-red-500',
      'created': 'bg-yellow-500',
      'paused': 'bg-blue-500',
      'error': 'bg-red-700'
    };

    return (
      <Badge className={`${statusColors[status as keyof typeof statusColors] || 'bg-gray-500'} text-white`}>
        {status}
      </Badge>
    );
  };

  return (
    <div className="flex flex-col h-full p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Development Workspaces</h1>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={fetchWorkspaces} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </Button>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button>
                <PlusIcon className="mr-2 h-4 w-4" />
                Create Workspace
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>Create New Workspace</DialogTitle>
                <DialogDescription>
                  Create a new development workspace with the specified configuration.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="name" className="text-right">
                    Name
                  </Label>
                  <Input
                    id="name"
                    value={newWorkspace.name}
                    onChange={(e) => setNewWorkspace({...newWorkspace, name: e.target.value})}
                    className="col-span-3"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="description" className="text-right">
                    Description
                  </Label>
                  <Input
                    id="description"
                    value={newWorkspace.description}
                    onChange={(e) => setNewWorkspace({...newWorkspace, description: e.target.value})}
                    className="col-span-3"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="image" className="text-right">
                    Image
                  </Label>
                  <Select
                    value={newWorkspace.image}
                    onValueChange={(value) => setNewWorkspace({...newWorkspace, image: value})}
                  >
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder="Select an image" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="continuumio/anaconda3">Anaconda Python</SelectItem>
                      <SelectItem value="node:18">Node.js 18</SelectItem>
                      <SelectItem value="python:3.11">Python 3.11</SelectItem>
                      <SelectItem value="golang:1.21">Go 1.21</SelectItem>
                      <SelectItem value="openjdk:17">Java 17</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button type="submit" onClick={createWorkspace}>Create Workspace</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-full">
          <div className="flex flex-col items-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
            <p className="mt-4">Loading workspaces...</p>
          </div>
        </div>
      ) : (
        <Card className="flex-grow">
          <CardHeader>
            <CardTitle>Available Workspaces</CardTitle>
            <CardDescription>
              Manage your development environments
            </CardDescription>
          </CardHeader>
          <CardContent>
            {workspaces.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-12 text-center">
                <div className="bg-gray-200 border-2 border-dashed rounded-xl w-16 h-16 flex items-center justify-center mb-4">
                  <PlusIcon className="h-8 w-8 text-gray-500" />
                </div>
                <h3 className="text-lg font-medium mb-2">No workspaces yet</h3>
                <p className="text-muted-foreground mb-4">
                  Create your first development workspace to get started.
                </p>
                <Button onClick={() => setShowCreateDialog(true)}>
                  <PlusIcon className="mr-2 h-4 w-4" />
                  Create Workspace
                </Button>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Image</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {workspaces.map((workspace) => (
                    <TableRow key={workspace.id}>
                      <TableCell className="font-medium">{workspace.name}</TableCell>
                      <TableCell>{workspace.description || '-'}</TableCell>
                      <TableCell>{workspace.container_image}</TableCell>
                      <TableCell>
                        <StatusBadge status={workspace.status} />
                      </TableCell>
                      <TableCell>
                        {new Date(workspace.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end space-x-2">
                          <WorkspaceLauncher
                            workspaceId={workspace.id}
                            disabled={workspace.status !== 'running'}
                          />
                          {workspace.status === 'running' ? (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => stopWorkspace(workspace.id)}
                              title="Stop workspace"
                            >
                              <Square className="h-4 w-4" />
                            </Button>
                          ) : (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => startWorkspace(workspace.id)}
                              title="Start workspace"
                            >
                              <Play className="h-4 w-4" />
                            </Button>
                          )}
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => deleteWorkspace(workspace.id)}
                            title="Delete workspace"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}