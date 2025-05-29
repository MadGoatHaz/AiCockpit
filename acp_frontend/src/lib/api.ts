// acp_frontend/src/lib/api.ts

// Define the base URL for your ACP backend
// For local development, this will be http://localhost:8000
// In production, this would be your deployed backend URL
const ACP_BACKEND_URL = process.env.NEXT_PUBLIC_ACP_BACKEND_URL || 'http://localhost:8000';

// Define a type for the Workspace/Session object we expect from the backend
// This should align with what your GET /sessions endpoint returns for each session
// (e.g., based on SessionMetadata from acp_backend/models/work_session_models.py)
export interface Workspace {
  id: string; // session_id (UUID)
  name: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
  // Add any other fields you expect from the session manifest that are useful here
  // e.g., last_accessed, or even UI state if you persist it in the manifest
}

/**
 * Fetches all available workspaces (sessions) from the ACP backend.
 */
export async function getWorkspaces(): Promise<Workspace[]> {
  try {
    const response = await fetch(`${ACP_BACKEND_URL}/sessions`);
    if (!response.ok) {
      // Log the error or throw a more specific error to be caught by the caller
      const errorData = await response.text();
      console.error('Failed to fetch workspaces:', response.status, errorData);
      throw new Error(`Failed to fetch workspaces: ${response.status}`);
    }
    const data: Workspace[] = await response.json();
    return data;
  } catch (error) {
    console.error('Error in getWorkspaces:', error);
    // Re-throw the error so the component can handle it (e.g., show an error message)
    throw error;
  }
}

// We will add more API functions here later, e.g.:
// export async function createWorkspace(name: string, description?: string): Promise<Workspace> { ... }
// export async function getWorkspaceDetails(sessionId: string): Promise<Workspace> { ... }
// export async function updateWorkspaceManifest(sessionId: string, manifestData: any): Promise<Workspace> { ... }
// export async function deleteWorkspace(sessionId: string): Promise<void> { ... }

// export async function listFiles(sessionId: string, path: string = '.'): Promise<any[]> { ... }
// export async function readFile(sessionId: string, path: string): Promise<string> { ... }
// etc.
