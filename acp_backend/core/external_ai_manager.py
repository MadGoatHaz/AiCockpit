"""
External AI Service Manager
==========================

Manages connections to external AI services like LM Studio, OpenAI, Azure OpenAI, etc.
Provides a unified interface for AI interactions while abstracting the underlying service.

Author: AiCockpit Development Team
License: GPL-3.0
"""

import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from pydantic import BaseModel
from openai import AsyncOpenAI, AsyncAzureOpenAI
import httpx
import asyncio

logger = logging.getLogger(__name__)


class AIServiceConfig(BaseModel):
    """Configuration for an external AI service."""
    name: str
    type: str  # 'openai', 'azure', 'lmstudio', 'custom'
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    organization: Optional[str] = None
    deployment_name: Optional[str] = None  # For Azure
    api_version: Optional[str] = None  # For Azure


class ChatMessage(BaseModel):
    """Represents a chat message."""
    role: str  # 'system', 'user', 'assistant'
    content: str


class ChatCompletionRequest(BaseModel):
    """Request for chat completion."""
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    # Add other parameters as needed


class ChatCompletionResponse(BaseModel):
    """Response from chat completion."""
    id: str
    choices: List[Dict[str, Any]]
    created: int
    model: str
    object: str = "chat.completion"
    usage: Optional[Dict[str, Any]] = None


class ExternalAIServiceManager:
    """Manages connections to external AI services."""
    
    def __init__(self):
        self.services: Dict[str, Any] = {}
        self.active_service: Optional[str] = None
        self.default_model: str = "gpt-3.5-turbo"
        self.clients: Dict[str, Any] = {}
        
    async def add_service(self, config: AIServiceConfig) -> bool:
        """
        Add an external AI service configuration.
        
        Args:
            config: AIServiceConfig with service details
            
        Returns:
            bool: True if service was added successfully
        """
        try:
            # Validate configuration
            if not config.name:
                raise ValueError("Service name is required")
                
            if config.type not in ['openai', 'azure', 'lmstudio', 'custom']:
                raise ValueError(f"Unsupported service type: {config.type}")
                
            # Store configuration
            self.services[config.name] = config
            
            # Initialize client based on service type
            if config.type == 'openai':
                if not config.api_key:
                    raise ValueError("API key is required for OpenAI service")
                self.clients[config.name] = AsyncOpenAI(
                    api_key=config.api_key,
                    organization=config.organization
                )
                
            elif config.type == 'azure':
                if not config.api_key:
                    raise ValueError("API key is required for Azure service")
                if not config.base_url:
                    raise ValueError("Base URL is required for Azure service")
                if not config.deployment_name:
                    raise ValueError("Deployment name is required for Azure service")
                if not config.api_version:
                    raise ValueError("API version is required for Azure service")
                    
                self.clients[config.name] = AsyncAzureOpenAI(
                    api_key=config.api_key,
                    azure_endpoint=config.base_url,
                    azure_deployment=config.deployment_name,
                    api_version=config.api_version
                )
                
            elif config.type in ['lmstudio', 'custom']:
                if not config.base_url:
                    raise ValueError("Base URL is required for LM Studio/Custom service")
                    
                # For LM Studio and custom services, we use a generic OpenAI client
                # with a custom base URL
                self.clients[config.name] = AsyncOpenAI(
                    base_url=config.base_url,
                    api_key=config.api_key or "not-needed",  # LM Studio doesn't require API key
                    http_client=httpx.AsyncClient(
                        timeout=60.0,
                        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
                    )
                )
            
            logger.info(f"Added external AI service: {config.name} ({config.type})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add external AI service {config.name}: {e}")
            return False
    
    async def remove_service(self, name: str) -> bool:
        """
        Remove an external AI service.
        
        Args:
            name: Name of the service to remove
            
        Returns:
            bool: True if service was removed successfully
        """
        if name in self.services:
            del self.services[name]
            
        if name in self.clients:
            # Close client connection if it has a close method
            client = self.clients[name]
            if hasattr(client, 'close'):
                await client.close()
            del self.clients[name]
            
        if self.active_service == name:
            self.active_service = None
            
        logger.info(f"Removed external AI service: {name}")
        return True
    
    async def set_active_service(self, name: str) -> bool:
        """
        Set the active service for AI interactions.
        
        Args:
            name: Name of the service to activate
            
        Returns:
            bool: True if service was activated successfully
        """
        if name not in self.services:
            logger.error(f"Service {name} not found")
            return False
            
        self.active_service = name
        logger.info(f"Set active AI service: {name}")
        return True
    
    async def test_connection(self, name: str) -> Dict[str, Any]:
        """
        Test connection to an external AI service.
        
        Args:
            name: Name of the service to test
            
        Returns:
            Dict with test results
        """
        if name not in self.services:
            return {"success": False, "error": f"Service {name} not found"}
            
        try:
            client = self.clients.get(name)
            if not client:
                return {"success": False, "error": f"Client for {name} not initialized"}
                
            # Send a simple test request
            response = await client.chat.completions.create(
                model=self.services[name].model,
                messages=[{"role": "user", "content": "Hello, are you there?"}],
                max_tokens=10,
                temperature=0.7
            )
            
            return {
                "success": True,
                "model": response.model,
                "response": response.choices[0].message.content if response.choices else "No response"
            }
            
        except Exception as e:
            logger.error(f"Connection test failed for {name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def list_services(self) -> List[Dict[str, Any]]:
        """
        List all configured services.
        
        Returns:
            List of service information
        """
        services_info = []
        for name, config in self.services.items():
            services_info.append({
                "name": name,
                "type": config.type,
                "model": config.model,
                "active": name == self.active_service,
                "base_url": config.base_url
            })
        return services_info
    
    async def chat_completion(
        self, 
        request: ChatCompletionRequest,
        service_name: Optional[str] = None
    ) -> ChatCompletionResponse:
        """
        Perform chat completion using the active or specified service.
        
        Args:
            request: Chat completion request
            service_name: Optional service name to use (defaults to active service)
            
        Returns:
            Chat completion response
        """
        # Determine which service to use
        target_service = service_name or self.active_service
        if not target_service:
            raise ValueError("No active service set and no service specified")
            
        if target_service not in self.services:
            raise ValueError(f"Service {target_service} not found")
            
        # Get the client
        client = self.clients.get(target_service)
        if not client:
            raise ValueError(f"Client for service {target_service} not initialized")
            
        # Get the service config
        config = self.services[target_service]
        
        # Prepare the request parameters
        model = request.model or config.model
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        try:
            if request.stream:
                # Handle streaming response
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    stream=True
                )
                # For streaming, we return the response directly
                # The caller will need to handle the async generator
                return response
            else:
                # Handle non-streaming response
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    stream=False
                )
                
                # Convert to our response format
                return ChatCompletionResponse(
                    id=response.id,
                    choices=[choice.model_dump() for choice in response.choices],
                    created=response.created,
                    model=response.model,
                    usage=response.usage.model_dump() if response.usage else None
                )
                
        except Exception as e:
            logger.error(f"Chat completion failed for service {target_service}: {e}")
            raise
    
    async def close_all_connections(self):
        """Close all active connections."""
        for name, client in self.clients.items():
            if hasattr(client, 'close'):
                await client.close()
        self.clients.clear()
        logger.info("Closed all external AI service connections")


# Global instance for the application
external_ai_manager = ExternalAIServiceManager()