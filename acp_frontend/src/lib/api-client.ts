/**
 * AiCockpit API Client
 * ===================
 * 
 * Centralized API client for communicating with the AiCockpit backend.
 * Provides typed methods for all backend endpoints with proper error handling.
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
  async getHealth() {
    return this.request('/system/health');
  }

  // External AI Service Management endpoints
  async addExternalService(config: AIServiceConfig) {
    return this.request('/llm/services', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async removeExternalService(serviceName: string) {
    return this.request(`/llm/services/${serviceName}`, {
      method: 'DELETE',
    });
  }

  async setActiveService(serviceName: string) {
    return this.request(`/llm/services/${serviceName}/activate`, {
      method: 'POST',
    });
  }

  async testServiceConnection(serviceName: string) {
    return this.request(`/llm/services/test/${serviceName}`);
  }

  async listExternalServices() {
    return this.request('/llm/services');
  }

  // LLM Service endpoints (backward compatibility)
  async getModels() {
    return this.request<LLM[]>('/llm/models');
  }

  async loadModel(modelId: string) {
    return this.request(`/llm/models/${modelId}/load`, {
      method: 'POST',
    });
  }

  async unloadModel(modelId: string) {
    return this.request(`/llm/models/${modelId}/unload`, {
      method: 'POST',
    });
  }

  // Chat completion endpoints
  async chatCompletion(request: ChatCompletionRequest): Promise<ApiResponse<ChatCompletionResponse>> {
    return this.request('/llm/chat/completions', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

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
  async createSession(name: string) {
    return this.request('/sessions', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  }

  async getSessions() {
    return this.request('/sessions');
  }

  async getSession(sessionId: string) {
    return this.request(`/sessions/${sessionId}`);
  }

  async deleteSession(sessionId: string) {
    return this.request(`/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }

  // Workspace Files endpoints
  async listFiles(workspaceId: string, path: string = '') {
    return this.request(`/workspaces/${workspaceId}/files?path=${encodeURIComponent(path)}`);
  }

  async readFile(workspaceId: string, path: string) {
    return this.request(`/workspaces/${workspaceId}/files/${encodeURIComponent(path)}`);
  }

  async writeFile(workspaceId: string, path: string, content: string) {
    return this.request(`/workspaces/${workspaceId}/files/${encodeURIComponent(path)}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  }

  async createDirectory(workspaceId: string, path: string) {
    return this.request(`/workspaces/${workspaceId}/directories`, {
      method: 'POST',
      body: JSON.stringify({ path }),
    });
  }

  async deleteFile(workspaceId: string, path: string) {
    return this.request(`/workspaces/${workspaceId}/files/${encodeURIComponent(path)}`, {
      method: 'DELETE',
    });
  }

  // Terminal Service endpoints
  async createTerminal(workspaceId: string) {
    return this.request(`/terminals/${workspaceId}`, {
      method: 'POST',
    });
  }

  async sendTerminalCommand(workspaceId: string, terminalId: string, command: string) {
    return this.request(`/terminals/${workspaceId}/${terminalId}/command`, {
      method: 'POST',
      body: JSON.stringify({ command }),
    });
  }

  async resizeTerminal(workspaceId: string, terminalId: string, cols: number, rows: number) {
    return this.request(`/terminals/${workspaceId}/${terminalId}/resize`, {
      method: 'POST',
      body: JSON.stringify({ cols, rows }),
    });
  }

  // Agent Service endpoints
  async runAgent(workspaceId: string, agentId: string, input: string) {
    return this.request(`/agents/run/${workspaceId}/${agentId}`, {
      method: 'POST',
      body: JSON.stringify({ input }),
    });
  }

  async getAgents() {
    return this.request('/agents');
  }

  async getAgentConfig(agentId: string) {
    return this.request(`/agents/config/${agentId}`);
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export class for custom instances if needed
export { ApiClient };