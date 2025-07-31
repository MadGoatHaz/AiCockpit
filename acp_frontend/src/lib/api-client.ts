/**
 * AiCockpit API Client
 * ===================
 *
 * Centralized API client for communicating with the AiCockpit backend.
 * Provides typed methods for all backend endpoints with proper error handling.
 *
 * This client supports both traditional LLM endpoints and the new containerized
 * workspace management APIs, as well as external AI service integration.
 *
 * Author: AiCockpit Development Team
 * License: GPL-3.0
 */

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface Workspace {
  id: string;
  name: string;
  selectedFile: FileSystemItem | null;
  aiConfig: {
    selectedModelId: string;
    temperature: number;
  };
  activeRightPanel: 'chat' | 'ai_settings' | 'ws_settings' | 'agentRunner';
}

export interface WorkspaceMetadata {
  id: string;
  name: string;
  description: string;
  image: string;
  status: 'running' | 'stopped' | 'error' | 'starting' | 'stopping';
  created_at: string;
  updated_at: string;
}

export interface CreateWorkspaceRequest {
  name: string;
  description?: string;
  image: string;
}

export interface FileSystemItem {
  id: string;
  name: string;
  path: string;
  type: 'file' | 'directory';
  size?: number;
  lastModified?: Date;
  children?: FileSystemItem[];
}

export interface LLMConfig {
  model_id: string;
  model_name: string;
  model_path: string;
  backend_type: 'llama_cpp' | 'pie' | 'mock';
  parameters: Record<string, any>;
}

export interface LLM {
  config: LLMConfig;
  status: 'loading' | 'loaded' | 'unloading' | 'error';
  error_message?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

export interface ChatCompletionRequest {
  model_id: string;
  messages: ChatMessage[];
  temperature?: number;
  stream?: boolean;
}

export interface ChatCompletionResponse {
  model_id: string;
  message: ChatMessage;
  finish_reason: 'stop' | 'length' | 'error';
}

export interface AIServiceConfig {
  name: string;
  type: 'openai' | 'azure' | 'lmstudio' | 'custom';
  api_key?: string;
  base_url?: string;
  model: string;
  organization?: string;
  deployment_name?: string;
  api_version?: string;
}

class ApiClient {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  private async request<T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const response = await fetch(url, {
        ...options,
        headers: {
          ...this.defaultHeaders,
          ...options.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error('API request failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  // System endpoints
  /**
   * Get the health status of the backend system.
   *
   * This method checks if the backend system is running and responding
   * to requests. It's useful for determining if the application is
   * ready to handle user requests.
   *
   * @returns ApiResponse with health status information
   */
  async getHealth() {
    return this.request('/system/health');
  }

  // External AI Service Management endpoints
  /**
   * Add an external AI service.
   *
   * This method adds a new external AI service configuration. The service
   * can be an OpenAI-compatible API, Azure OpenAI, LM Studio, or custom
   * service.
   *
   * @param config - Configuration for the external AI service
   * @returns ApiResponse indicating success or failure
   */
  async addExternalService(config: AIServiceConfig) {
    return this.request('/llm/services', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  /**
   * Remove an external AI service.
   *
   * This method removes an existing external AI service configuration
   * by its name. This will delete the service configuration from the
   * system.
   *
   * @param serviceName - Name of the external AI service to remove
   * @returns ApiResponse indicating success or failure
   */
  async removeExternalService(serviceName: string) {
    return this.request(`/llm/services/${serviceName}`, {
      method: 'DELETE',
    });
  }

  /**
   * Set an external AI service as active.
   *
   * This method sets a specific external AI service as the active service
   * for handling AI requests. Only one service can be active at a time.
   *
   * @param serviceName - Name of the external AI service to activate
   * @returns ApiResponse indicating success or failure
   */
  async setActiveService(serviceName: string) {
    return this.request(`/llm/services/${serviceName}/activate`, {
      method: 'POST',
    });
  }

  /**
   * Test the connection to an external AI service.
   *
   * This method tests the connection to a specific external AI service
   * by making a simple request to verify that the service is accessible
   * and responding correctly.
   *
   * @param serviceName - Name of the external AI service to test
   * @returns ApiResponse with test results
   */
  async testServiceConnection(serviceName: string) {
    return this.request(`/llm/services/test/${serviceName}`);
  }

  /**
   * Get a list of all external AI services.
   *
   * This method retrieves a list of all configured external AI services.
   * Each service includes its configuration details and status.
   *
   * @returns ApiResponse with list of external AI services
   */
  async listExternalServices() {
    return this.request('/llm/services');
  }

  // LLM Service endpoints (backward compatibility)
  /**
   * Get a list of available language models.
   *
   * This method retrieves a list of all available language models that
   * can be loaded and used for inference. Each model has a unique ID and
   * configuration.
   *
   * @returns ApiResponse with list of language models
   */
  async getModels() {
    return this.request<LLM[]>('/llm/models');
  }

  /**
   * Load a language model.
   *
   * This method loads a specific language model by its ID. Once loaded,
   * the model can be used for inference tasks like chat completions.
   *
   * @param modelId - ID of the model to load
   * @returns ApiResponse indicating success or failure
   */
  async loadModel(modelId: string) {
    return this.request(`/llm/models/${modelId}/load`, {
      method: 'POST',
    });
  }

  /**
   * Unload a language model.
   *
   * This method unloads a specific language model by its ID. Once unloaded,
   * the model will no longer be available for inference tasks until it is
   * loaded again.
   *
   * @param modelId - ID of the model to unload
   * @returns ApiResponse indicating success or failure
   */
  async unloadModel(modelId: string) {
    return this.request(`/llm/models/${modelId}/unload`, {
      method: 'POST',
    });
  }

  // Chat completion endpoints
  /**
   * Generate a chat completion using a language model.
   *
   * This method sends a chat completion request to a language model and
   * returns the generated response. The request includes the model ID,
   * messages, and optional parameters like temperature.
   *
   * @param request - Chat completion request with model ID, messages, and parameters
   * @returns ApiResponse with chat completion response
   */
  async chatCompletion(request: ChatCompletionRequest): Promise<ApiResponse<ChatCompletionResponse>> {
    return this.request('/llm/chat/completions', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Generate a streaming chat completion using a language model.
   *
   * This method sends a chat completion request to a language model and
   * returns a stream of generated responses. The request includes the
   * model ID, messages, and optional parameters like temperature.
   *
   * @param request - Chat completion request with model ID, messages, and parameters
   * @returns AsyncGenerator that yields chat completion responses as they are generated
   */
  async chatCompletionStream(request: ChatCompletionRequest): Promise<AsyncGenerator<ChatCompletionResponse, void, unknown>> {
    const response = await fetch(`${this.baseUrl}/llm/chat/completions`, {
      method: 'POST',
      headers: {
        ...this.defaultHeaders,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ...request, stream: true }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    async function* streamGenerator(): AsyncGenerator<ChatCompletionResponse, void, unknown> {
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') continue;
              
              try {
                const parsed = JSON.parse(data);
                if (parsed.choices && parsed.choices.length > 0) {
                  const choice = parsed.choices[0];
                  if (choice.delta) {
                    // Streaming response
                    yield {
                      model_id: parsed.model,
                      message: {
                        role: 'assistant',
                        content: choice.delta.content || '',
                        timestamp: new Date()
                      },
                      finish_reason: choice.finish_reason || 'stop'
                    };
                  } else if (choice.message) {
                    // Non-streaming response
                    yield {
                      model_id: parsed.model,
                      message: {
                        role: 'assistant',
                        content: choice.message.content || '',
                        timestamp: new Date()
                      },
                      finish_reason: choice.finish_reason || 'stop'
                    };
                  }
                }
              } catch (e) {
                console.error('Failed to parse SSE data:', data);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    }

    return streamGenerator();
  }

  // Work Sessions endpoints
  /**
   * Create a new work session.
   *
   * This method creates a new work session with the specified name.
   * A work session is a container for workspace files and settings.
   *
   * @param name - Name for the new work session
   * @returns ApiResponse with session information
   */
  async createSession(name: string) {
    return this.request('/sessions', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  }

  /**
   * Get a list of all work sessions.
   *
   * This method retrieves a list of all existing work sessions.
   * Each session includes information like ID, name, and creation date.
   *
   * @returns ApiResponse with list of sessions
   */
  async getSessions() {
    return this.request('/sessions');
  }

  /**
   * Get details of a specific work session.
   *
   * This method retrieves detailed information about a specific work session
   * by its ID. The information includes session metadata and settings.
   *
   * @param sessionId - ID of the session to retrieve
   * @returns ApiResponse with session details
   */
  async getSession(sessionId: string) {
    return this.request(`/sessions/${sessionId}`);
  }

  /**
   * Delete a work session.
   *
   * This method deletes a specific work session by its ID. This is a
   * destructive operation that will permanently remove all session data.
   *
   * @param sessionId - ID of the session to delete
   * @returns ApiResponse indicating success or failure
   */
  async deleteSession(sessionId: string) {
    return this.request(`/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }

  // Workspace Files endpoints
  /**
   * List files in a workspace directory.
   *
   * This method retrieves a list of files and directories in the specified
   * workspace directory. If no path is provided, it lists files in the
   * root directory of the workspace.
   *
   * @param workspaceId - ID of the workspace
   * @param path - Path to the directory (default: root directory)
   * @returns ApiResponse with file listing data
   */
  async listFiles(workspaceId: string, path: string = '') {
    return this.request(`/workspaces/${workspaceId}/files?path=${encodeURIComponent(path)}`);
  }

  /**
   * Read the content of a file in a workspace.
   *
   * This method retrieves the content of a specific file in the workspace.
   * The file content is returned as a string.
   *
   * @param workspaceId - ID of the workspace
   * @param path - Path to the file
   * @returns ApiResponse with file content
   */
  async readFile(workspaceId: string, path: string) {
    return this.request(`/workspaces/${workspaceId}/files/${encodeURIComponent(path)}`);
  }

  /**
   * Write content to a file in a workspace.
   *
   * This method writes content to a specific file in the workspace.
   * If the file doesn't exist, it will be created. If it does exist,
   * its content will be overwritten.
   *
   * @param workspaceId - ID of the workspace
   * @param path - Path to the file
   * @param content - Content to write to the file
   * @returns ApiResponse with file information
   */
  async writeFile(workspaceId: string, path: string, content: string) {
    return this.request(`/workspaces/${workspaceId}/files/${encodeURIComponent(path)}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  }

  /**
   * Create a directory in a workspace.
   *
   * This method creates a new directory in the specified workspace.
   * If the directory already exists, the operation will fail.
   *
   * @param workspaceId - ID of the workspace
   * @param path - Path to the directory to create
   * @returns ApiResponse with directory information
   */
  async createDirectory(workspaceId: string, path: string) {
    return this.request(`/workspaces/${workspaceId}/directories`, {
      method: 'POST',
      body: JSON.stringify({ path }),
    });
  }

  /**
   * Delete a file or directory in a workspace.
   *
   * This method deletes a file or directory in the specified workspace.
   * If the path refers to a directory, the directory must be empty for
   * the operation to succeed.
   *
   * @param workspaceId - ID of the workspace
   * @param path - Path to the file or directory to delete
   * @returns ApiResponse indicating success or failure
   */
  async deleteFile(workspaceId: string, path: string) {
    return this.request(`/workspaces/${workspaceId}/files/${encodeURIComponent(path)}`, {
      method: 'DELETE',
    });
  }

  // Terminal Service endpoints
  /**
   * Create a new terminal session in a workspace.
   *
   * This method creates a new terminal session in the specified workspace.
   * The terminal session can be used to execute commands in the workspace
   * container environment.
   *
   * @param workspaceId - ID of the workspace
   * @returns ApiResponse with terminal session information
   */
  async createTerminal(workspaceId: string) {
    return this.request(`/terminals/${workspaceId}`, {
      method: 'POST',
    });
  }

  /**
   * Send a command to a terminal session in a workspace.
   *
   * This method sends a command to an existing terminal session in the
   * specified workspace. The command will be executed in the terminal
   * environment and the output will be available through the terminal
   * WebSocket connection.
   *
   * @param workspaceId - ID of the workspace
   * @param terminalId - ID of the terminal session
   * @param command - Command to execute in the terminal
   * @returns ApiResponse indicating success or failure
   */
  async sendTerminalCommand(workspaceId: string, terminalId: string, command: string) {
    return this.request(`/terminals/${workspaceId}/${terminalId}/command`, {
      method: 'POST',
      body: JSON.stringify({ command }),
    });
  }

  /**
   * Resize a terminal session in a workspace.
   *
   * This method resizes an existing terminal session in the specified
   * workspace. The terminal dimensions are specified in columns and rows.
   *
   * @param workspaceId - ID of the workspace
   * @param terminalId - ID of the terminal session
   * @param cols - Number of columns for the terminal
   * @param rows - Number of rows for the terminal
   * @returns ApiResponse indicating success or failure
   */
  async resizeTerminal(workspaceId: string, terminalId: string, cols: number, rows: number) {
    return this.request(`/terminals/${workspaceId}/${terminalId}/resize`, {
      method: 'POST',
      body: JSON.stringify({ cols, rows }),
    });
  }

  // Agent Service endpoints
  /**
   * Run an agent in a workspace.
   *
   * This method executes an agent with the specified input in the
   * specified workspace. The agent will process the input and return
   * the result.
   *
   * @param workspaceId - ID of the workspace
   * @param agentId - ID of the agent to run
   * @param input - Input for the agent
   * @returns ApiResponse with agent execution result
   */
  async runAgent(workspaceId: string, agentId: string, input: string) {
    return this.request(`/agents/run/${workspaceId}/${agentId}`, {
      method: 'POST',
      body: JSON.stringify({ input }),
    });
  }

  /**
   * Get a list of available agents.
   *
   * This method retrieves a list of all available agents that can be
   * executed in workspaces. Each agent has a unique ID and configuration.
   *
   * @returns ApiResponse with list of agents
   */
  async getAgents() {
    return this.request('/agents');
  }

  /**
   * Get the configuration for a specific agent.
   *
   * This method retrieves the configuration for a specific agent by its ID.
   * The configuration includes details about the agent's capabilities and
   * settings.
   *
   * @param agentId - ID of the agent
   * @returns ApiResponse with agent configuration
   */
  async getAgentConfig(agentId: string) {
    return this.request(`/agents/config/${agentId}`);
  }

  /**
   * Workspace Management endpoints
   */
  
  /**
   * Get a list of all workspaces.
   *
   * This method retrieves metadata for all workspaces in the system.
   * Each workspace includes its ID, name, description, image, status,
   * and timestamps for creation and last update.
   *
   * @returns ApiResponse with list of workspace metadata
   */
  async getWorkspaces() {
    return this.request<WorkspaceMetadata[]>('/workspaces');
  }

  /**
   * Get metadata for a specific workspace.
   *
   * This method retrieves detailed metadata for a specific workspace
   * by its ID. The metadata includes the workspace's ID, name,
   * description, image, status, and timestamps.
   *
   * @param workspaceId - ID of the workspace to retrieve
   * @returns ApiResponse with workspace metadata
   */
  async getWorkspace(workspaceId: string) {
    return this.request<WorkspaceMetadata>(`/workspaces/${workspaceId}`);
  }

  /**
   * Create a new workspace.
   *
   * This method creates a new workspace with the specified name,
   * description, and Docker image. The workspace will be created
   * in a stopped state and can be started using the startWorkspace
   * method.
   *
   * @param request - Workspace creation request with name, description, and image
   * @returns ApiResponse with metadata for the newly created workspace
   */
  async createWorkspace(request: CreateWorkspaceRequest) {
    return this.request<WorkspaceMetadata>('/workspaces', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Start a workspace.
   *
   * This method starts a workspace that is in a stopped state.
   * The workspace container will be launched and the workspace
   * status will be updated to 'running'.
   *
   * @param workspaceId - ID of the workspace to start
   * @returns ApiResponse indicating success or failure
   */
  async startWorkspace(workspaceId: string) {
    return this.request(`/workspaces/${workspaceId}/start`, {
      method: 'POST',
    });
  }

  /**
   * Stop a workspace.
   *
   * This method stops a workspace that is in a running state.
   * The workspace container will be stopped and the workspace
   * status will be updated to 'stopped'.
   *
   * @param workspaceId - ID of the workspace to stop
   * @returns ApiResponse indicating success or failure
   */
  async stopWorkspace(workspaceId: string) {
    return this.request(`/workspaces/${workspaceId}/stop`, {
      method: 'POST',
    });
  }

  /**
   * Delete a workspace.
   *
   * This method deletes a workspace and all associated data.
   * The workspace container will be removed and all files
   * in the workspace will be deleted.
   *
   * @param workspaceId - ID of the workspace to delete
   * @returns ApiResponse indicating success or failure
   */
  async deleteWorkspace(workspaceId: string) {
    return this.request(`/workspaces/${workspaceId}`, {
      method: 'DELETE',
    });
  }

  /**
   * Launch the IDE for a workspace.
   *
   * This method generates a URL for launching the web-based IDE
   * for a specific workspace. The URL can be used to open the
   * IDE in a new tab or window.
   *
   * @param workspaceId - ID of the workspace to launch
   * @returns URL for the workspace IDE
   */
  getWorkspaceIdeUrl(workspaceId: string): string {
    return `${this.baseUrl}/workspaces/${workspaceId}/ide`;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export class for custom instances if needed
export { ApiClient };