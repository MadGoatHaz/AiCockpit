# AiCockpit Technical Architecture
## AI-Collaborative Development Platform with Containerized Workspaces

This document provides detailed technical specifications for AiCockpit's architecture, centered around containerized development environments and integration with external AI services via OpenAI-compatible APIs.

---

## 🏗️ System Architecture Overview

### Core Philosophy

AiCockpit's architecture embodies the concept of **containerized development environments as the foundation for AI collaboration** - providing isolated, reproducible environments where humans and AI can work together seamlessly.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AiCockpit Ecosystem                     │
├─────────────────────────────────────────────────────────────┤
│  Web-Based IDE (Containerized Workspaces)                  │
│  ├── File Browser          ├── Terminal Access            │
│  ├── Code Editor           ├── AI Chat Interface           │
│  └── Workspace Management  └── Settings Panel              │
├─────────────────────────────────────────────────────────────┤
│  Communication Layer (OpenAI-Compatible API)               │
│  ├── HTTP/WebSocket        ├── Streaming Responses        │
│  ├── Authentication        └── Load Balancing             │
├─────────────────────────────────────────────────────────────┤
│  External AI Services                                      │
│  ├── LM Studio             ├── OpenAI                      │
│  ├── Azure OpenAI          ├── Custom Services            │
│  └── API Integration       └── Model Management           │
├─────────────────────────────────────────────────────────────┤
│  Container Orchestration                                   │
│  ├── Docker/Podman         ├── Kubernetes (Future)        │
│  ├── Workspace Lifecycle   ├── Resource Management        │
│  └── Network Isolation     └── Security Controls          │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure & Scaling                                  │
│  ├── Docker Integration    ├── Monitoring/Logging         │
│  ├── Auto-scaling          └── Performance Optimization   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🐳 Containerized Development Environments

### Container Orchestration

The containerized workspace system provides isolated development environments with:

#### Key Benefits
- **Isolation**: Each workspace runs in its own secure container
- **Reproducibility**: Consistent environments across development, testing, and production
- **Resource Efficiency**: Optimized resource usage with container orchestration
- **Easy Setup**: Instant workspace creation with pre-configured development stacks

#### Supported Development Stacks

```python
# Configuration for different development environments
workspace_configs = {
    "python_anaconda": {
        "base_image": "continuumio/anaconda3",
        "packages": ["numpy", "pandas", "scikit-learn", "jupyter"],
        "ports": [8888],  # Jupyter notebook
        "description": "Python with Anaconda distribution for data science"
    },
    "nodejs_18": {
        "base_image": "node:18",
        "packages": ["npm", "yarn"],
        "ports": [3000],  # Common development port
        "description": "JavaScript/Node.js development environment"
    },
    "python_311": {
        "base_image": "python:3.11",
        "packages": ["pip"],
        "description": "Clean Python 3.11 installation"
    },
    "go_121": {
        "base_image": "golang:1.21",
        "packages": [],
        "description": "Go programming language environment"
    },
    "java_17": {
        "base_image": "openjdk:17",
        "packages": ["maven", "gradle"],
        "description": "Java development environment"
    }
}
```

### Container Management System

```python
class ContainerManager:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.workspaces = {}
    
    async def create_workspace(self, workspace_id: str, config: dict):
        """Create a new containerized workspace"""
        try:
            # Pull the base image if not already present
            await self._pull_image(config["base_image"])
            
            # Create and start the container
            container = self.docker_client.containers.run(
                config["base_image"],
                name=f"workspace-{workspace_id}",
                detach=True,
                tty=True,
                stdin_open=True,
                volumes={
                    f"workspace-{workspace_id}-data": {
                        "bind": "/workspace",
                        "mode": "rw"
                    }
                },
                ports=config.get("ports", {}),
                environment=config.get("environment", {}),
                working_dir="/workspace"
            )
            
            self.workspaces[workspace_id] = {
                "container": container,
                "config": config,
                "status": "running"
            }
            
            return container
        except Exception as e:
            raise ContainerCreationError(f"Failed to create workspace: {str(e)}")
    
    async def start_workspace(self, workspace_id: str):
        """Start an existing workspace container"""
        if workspace_id in self.workspaces:
            container = self.workspaces[workspace_id]["container"]
            container.start()
            self.workspaces[workspace_id]["status"] = "running"
    
    async def stop_workspace(self, workspace_id: str):
        """Stop a running workspace container"""
        if workspace_id in self.workspaces:
            container = self.workspaces[workspace_id]["container"]
            container.stop()
            self.workspaces[workspace_id]["status"] = "stopped"
    
    async def delete_workspace(self, workspace_id: str):
        """Delete a workspace and its associated container"""
        if workspace_id in self.workspaces:
            container = self.workspaces[workspace_id]["container"]
            container.remove(force=True)
            del self.workspaces[workspace_id]
```

### Resource Management

Advanced resource management for containerized environments:

```python
# Optimal container configuration
container_config = {
    # CPU allocation
    "cpu_quota": 50000,      # 50% of one CPU core
    "cpu_period": 100000,    # Standard period
    
    # Memory limits
    "mem_limit": "2g",       # 2GB memory limit
    "memswap_limit": "2g",   # No swap space
    
    # Storage quotas
    "storage_opt": {
        "size": "10G"        # 10GB storage limit per container
    },
    
    # Network limits
    "network_disabled": False,
    "dns": ["8.8.8.8", "8.8.4.4"]
}
```

---

## 🎯 External AI Service Integration

### OpenAI-Compatible API Integration

AiCockpit connects to external AI services via OpenAI-compatible APIs, supporting:

#### Supported Services
1. **LM Studio**: Run local AI models on your machine
2. **OpenAI**: Access to GPT models
3. **Azure OpenAI**: Enterprise-grade AI services
4. **Custom Services**: Connect to any OpenAI-compatible API

#### Service Configuration

```python
class ExternalAIServiceManager:
    def __init__(self):
        self.services = {}
        self.active_service = None
    
    async def add_service(self, service_id: str, config: dict):
        """Add a new external AI service"""
        service = ExternalAIService(
            name=config["name"],
            api_base=config["api_base"],
            api_key=config.get("api_key"),
            model=config.get("model", "gpt-3.5-turbo")
        )
        self.services[service_id] = service
    
    async def test_connection(self, service_id: str):
        """Test connection to an external AI service"""
        if service_id in self.services:
            service = self.services[service_id]
            try:
                # Test with a simple completion request
                response = await service.create_chat_completion(
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                return True
            except Exception:
                return False
        return False
    
    async def set_active_service(self, service_id: str):
        """Set the active AI service for the platform"""
        if service_id in self.services:
            self.active_service = service_id
            return True
        return False
```

### Core Features Implementation

#### 1. Inline Completions System
Real-time code suggestions with <100ms latency:

```typescript
class AiCockpitInlineCompletionProvider implements vscode.InlineCompletionItemProvider {
    async provideInlineCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        context: vscode.InlineCompletionContext
    ): Promise<vscode.InlineCompletionItem[]> {
        
        // Gather context from containerized workspace
        const codeContext = await this.gatherContext(document, position);
        
        // Construct completion prompt for external AI service
        const prompt = this.buildCompletionPrompt(codeContext);
        
        // Stream completion from external AI service
        const completion = await this.streamCompletion(prompt);
        
        return [new vscode.InlineCompletionItem(completion)];
    }
    
    private async gatherContext(document: vscode.TextDocument, position: vscode.Position) {
        return {
            beforeCursor: document.getText(new vscode.Range(0, 0, position.line, position.character)),
            afterCursor: document.getText(new vscode.Range(position, document.lineCount, 0)),
            language: document.languageId,
            fileName: document.fileName,
            projectContext: await this.getProjectContext()
        };
    }
}
```

#### 2. Command-Based Code Editing (Ctrl+K)
Natural language code transformation:

```typescript
class CodeEditingFeature {
    async editSelection(instruction: string) {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;
        
        const selection = editor.selection;
        const selectedText = editor.document.getText(selection);
        
        // Construct edit prompt for external AI service
        const prompt = this.buildEditPrompt(selectedText, instruction, {
            language: editor.document.languageId,
            context: await this.gatherSurroundingContext(editor, selection)
        });
        
        // Stream edit from external AI service
        const editedCode = await this.streamEdit(prompt);
        
        // Apply edit to document
        await editor.edit(editBuilder => {
            editBuilder.replace(selection, editedCode);
        });
    }
    
    private buildEditPrompt(code: string, instruction: string, context: any): string {
        return `
You are an expert ${context.language} developer. Edit the following code according to the instruction.

Context:
${context.context}

Current code:
\`\`\`${context.language}
${code}
\`\`\`

Instruction: ${instruction}

Return only the edited code without explanation:
\`\`\`${context.language}
`;
    }
}
```

#### 3. Intelligent Chat Interface
Conversation with codebase using @-mentions:

```typescript
class ChatInterface {
    async handleChatMessage(message: string) {
        // Parse @-mentions for file references
        const mentions = this.parseFileMentions(message);
        
        // Gather context from mentioned files in containerized workspace
        const fileContents = await Promise.all(
            mentions.map(file => this.getFileContent(file))
        );
        
        // Construct chat prompt with context for external AI service
        const prompt = this.buildChatPrompt(message, fileContents);
        
        // Stream response from external AI service
        const response = await this.streamChatResponse(prompt);
        
        // Display in chat panel
        this.displayChatResponse(response);
    }
    
    private parseFileMentions(message: string): string[] {
        const mentionRegex = /@([^\s]+)/g;
        const matches = message.match(mentionRegex);
        return matches ? matches.map(m => m.substring(1)) : [];
    }
}
```

#### 4. Terminal Integration
AI executes commands through natural language:

```typescript
class TerminalIntegration {
    async executeNaturalLanguageCommand(description: string) {
        // Convert natural language to shell command using external AI service
        const command = await this.generateCommand(description);
        
        // Show command to user for confirmation
        const confirmed = await vscode.window.showInformationMessage(
            `Execute: ${command}?`,
            'Yes', 'No'
        );
        
        if (confirmed === 'Yes') {
            // Execute in containerized terminal
            const terminal = vscode.window.createTerminal('AiCockpit');
            terminal.sendText(command);
            terminal.show();
        }
    }
    
    private async generateCommand(description: string): Promise<string> {
        const prompt = `
Convert this natural language description to a shell command:
"${description}"

Return only the command without explanation:
`;
        return await this.streamCompletion(prompt);
    }
}
```

---

## 🔗 Communication Layer

### OpenAI-Compatible API Client

Seamless integration with external AI services:

```python
# FastAPI server with OpenAI compatibility for internal routing
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import asyncio

app = FastAPI()
ai_service_manager = ExternalAIServiceManager()

class ChatCompletionRequest(BaseModel):
    model: str
    messages: list
    temperature: float = 0.7
    max_tokens: int = 256
    stream: bool = False

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    # Get the active external AI service
    active_service = ai_service_manager.get_active_service()
    if not active_service:
        raise HTTPException(status_code=503, detail="No active AI service configured")
    
    # Forward request to external AI service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{active_service.api_base}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {active_service.api_key}",
                    "Content-Type": "application/json"
                },
                json=request.dict()
            )
            
            if request.stream:
                return StreamingResponse(
                    response.aiter_bytes(),
                    media_type="text/event-stream"
                )
            else:
                return response.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")
```

### Streaming Implementation

Real-time response streaming for immediate feedback:

```typescript
class StreamingClient {
    async streamCompletion(prompt: string): Promise<string> {
        const activeService = this.getExternalAIService();
        
        const response = await fetch(`${activeService.apiBase}/v1/chat/completions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${activeService.apiKey}`
            },
            body: JSON.stringify({
                model: activeService.model,
                messages: [{ role: 'user', content: prompt }],
                stream: true,
                temperature: 0.2,
                max_tokens: 500
            })
        });
        
        const reader = response.body?.getReader();
        let result = '';
        
        while (true) {
            const { done, value } = await reader!.read();
            if (done) break;
            
            const chunk = new TextDecoder().decode(value);
            const lines = chunk.split('\n').filter(line => line.trim());
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.substring(6);
                    if (data === '[DONE]') return result;
                    
                    try {
                        const parsed = JSON.parse(data);
                        const delta = parsed.choices[0]?.delta?.content;
                        if (delta) {
                            result += delta;
                            this.onToken(delta); // Real-time updates
                        }
                    } catch (e) {
                        console.error('Parse error:', e);
                    }
                }
            }
        }
        
        return result;
    }
}
```

---

## 🚀 Performance Optimization

### Container Resource Management

Advanced resource optimization for containerized environments:

```python
# Optimal container configuration
container_config = {
    # CPU allocation
    "cpu_quota": 50000,      # 50% of one CPU core
    "cpu_period": 100000,    # Standard period
    
    # Memory limits
    "mem_limit": "2g",       # 2GB memory limit
    "memswap_limit": "2g",   # No swap space
    
    # Storage quotas
    "storage_opt": {
        "size": "10G"        # 10GB storage limit per container
    },
    
    # Network limits
    "network_disabled": False,
    "dns": ["8.8.8.8", "8.8.4.4"]
}
```

### Latency Optimization

Techniques for achieving <100ms response times:

```python
class LatencyOptimizer:
    def __init__(self):
        self.prompt_cache = {}
        self.service_cache = {}
    
    async def optimize_request(self, prompt: str, service_id: str):
        # 1. Prompt caching
        prompt_hash = hash(prompt)
        if prompt_hash in self.prompt_cache:
            return self.prompt_cache[prompt_hash]
        
        # 2. Service warming
        if service_id not in self.service_cache:
            await self.warm_service(service_id)
        
        # 3. Connection pooling
        connection_pool = self.get_connection_pool(service_id)
        
        # 4. Request optimization
        optimized_request = self.optimize_request_params(prompt)
        
        result = await self.send_optimized_request(
            optimized_request, service_id, connection_pool
        )
        
        self.prompt_cache[prompt_hash] = result
        return result
```

---

## 🏗️ Infrastructure & Deployment

### Containerization

Docker containers for consistent deployment:

```dockerfile
# Dockerfile for AiCockpit backend
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    docker-ce-cli \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY acp_backend/ /app/
WORKDIR /app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
  CMD curl -f http://localhost:8000/health || exit 1

# Start server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose Setup

Local development environment:

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./data:/app/data
    environment:
      - DOCKER_HOST=unix:///var/run/docker.sock
    depends_on:
      - redis
    restart: unless-stopped

  frontend:
    build:
      context: ./acp_frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  redis_data:
```

---

## 📊 Monitoring & Observability

### Performance Metrics

Comprehensive monitoring for production deployments:

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics collection
REQUEST_COUNT = Counter('aicockpit_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('aicockpit_request_duration_seconds', 'Request latency')
CONTAINER_COUNT = Gauge('aicockpit_containers_total', 'Total containers', ['status'])
AI_SERVICE_LATENCY = Histogram('aicockpit_ai_service_latency_seconds', 'AI service latency')

class MetricsCollector:
    def __init__(self):
        self.start_time = time.time()
    
    def track_request(self, method: str, endpoint: str):
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
    
    def track_latency(self, duration: float):
        REQUEST_LATENCY.observe(duration)
    
    def update_container_metrics(self):
        # Collect container metrics
        container_stats = self.get_container_stats()
        for status, count in container_stats.items():
            CONTAINER_COUNT.labels(status=status).set(count)
```

### Health Checks

Comprehensive health monitoring:

```python
from fastapi import FastAPI, HTTPException
import docker

app = FastAPI()
docker_client = docker.from_env()

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/ready")
async def readiness_check():
    """Readiness check for containerized environments"""
    try:
        # Check Docker connectivity
        if not docker_client.ping():
            raise HTTPException(status_code=503, detail="Docker not available")
        
        # Check container management
        containers = docker_client.containers.list()
        
        # Check Redis connection
        if not redis_client.ping():
            raise HTTPException(status_code=503, detail="Redis not available")
        
        return {
            "status": "ready", 
            "container_count": len(containers),
            "docker_version": docker_client.version()["Version"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    """Detailed metrics for monitoring"""
    return {
        "container_stats": get_container_stats(),
        "request_count": get_request_count(),
        "average_latency": get_average_latency(),
        "ai_service_status": get_ai_service_status()
    }
```

---

This technical architecture provides the foundation for AiCockpit's transformation into a world-class AI-collaborative development platform. By focusing on containerized workspaces and external AI service integration, we create a flexible, scalable platform that can leverage the best AI models without the complexity of hosting them ourselves.