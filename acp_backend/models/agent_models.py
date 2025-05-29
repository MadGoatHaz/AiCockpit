# acp_backend/models/agent_models.py
from pydantic import BaseModel, Field, ConfigDict 
from typing import List, Dict, Optional, Any 
import datetime

class AgentToolConfig(BaseModel):
    model_config = ConfigDict(extra="forbid") 

    tool_id: str = Field(..., description="Identifier of the tool (e.g., 'web_search', 'code_interpreter').")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Tool-specific configuration parameters.")

class AgentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid") 

    agent_id: str = Field(..., description="Unique identifier for this agent configuration.")
    name: str = Field(..., min_length=1, description="User-friendly name for the agent.")
    description: Optional[str] = Field(None, description="Detailed description of the agent's purpose and capabilities.")
    agent_type: str = Field("CodeAgent", description="Type of smolagent (e.g., 'CodeAgent', 'ToolCallingAgent', 'PlannerAgent'). Corresponds to smolagents agent types.")
    
    # Fields for smolagents model configuration
    smol_model_provider: Optional[str] = Field(None, description="Smolagents model provider (e.g., 'LiteLLM', 'OpenAIServerModel', 'TransformersModel', 'InferenceClientModel', 'AzureOpenAIServerModel', 'AmazonBedrockServerModel').")
    smol_model_id_override: Optional[str] = Field(None, description="Model ID for the smol_model_provider (e.g., 'gemini/gemini-pro', 'openai/gpt-4o', 'Qwen/Qwen2.5-Coder-32B-Instruct'). For OpenAI-compatible, this is the model name like 'gpt-4o'. For LiteLLM, it's the full model string e.g. 'gemini/gemini-1.5-flash-latest'.")
    smol_api_key_env_var: Optional[str] = Field(None, description="Environment variable name for the API key (e.g., 'GOOGLE_API_KEY', 'OPENAI_API_KEY', 'TOGETHER_API_KEY').")
    smol_api_base_url: Optional[str] = Field(None, description="API base URL for OpenAI-compatible servers (e.g., for Together, OpenRouter).")
    smol_azure_endpoint: Optional[str] = Field(None, description="Azure endpoint for AzureOpenAIServerModel.")
    smol_azure_api_version: Optional[str] = Field(None, description="Azure API version for AzureOpenAIServerModel.")
    # smol_aws_region: Optional[str] = Field(None, description="AWS region for AmazonBedrockServerModel.") # Bedrock client usually infers from env or default profile

    # Original LLM fields - can be used as fallback or for specific smolagents models like TransformersModel
    llm_model_id: Optional[str] = Field(None, description="Legacy: Fallback Model ID, or for local TransformersModel. For other smol_model_providers, use smol_model_id_override.")
    llm_config_overrides: Dict[str, Any] = Field(default_factory=dict, description="Specific LLM parameter overrides (e.g., for custom OpenAI params not directly in smolagents models). Usually, use top-level params like temperature, max_tokens.")
    
    tools: List[str] = Field(default_factory=list, description="List of tool IDs available to the agent (tool names recognised by smolagents or custom tools). Example: ['web_search', 'python_interpreter']")
    max_steps: Optional[int] = Field(None, gt=0, description="Maximum number of steps. Must be positive if set.")
    # additional_authorized_imports: List[str] = Field(default_factory=list, description="For CodeAgent: Python modules this agent is allowed to import.") # Smolagents CodeAgent handles imports differently
    # use_e2b_executor: Optional[bool] = Field(None, description="For CodeAgent: Whether to use the E2B secure sandboxed executor.") # Smolagents has its own sandbox options
    
    # Common LLM parameters that can be configured per agent
    max_tokens: Optional[int] = Field(None, description="Max tokens for the LLM. Passed to smolagents model config.")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Temperature for LLM sampling. Passed to smolagents model config.")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Top_p for LLM sampling. Passed to smolagents model config.")
    top_k: Optional[int] = Field(None, ge=0, description="Top_k for LLM sampling. Passed to smolagents model config.")
    
    # SmolAgents specific or other useful fields
    max_retries: Optional[int] = Field(None, ge=0, description="Maximum number of retries for agent actions or LLM calls (if supported by smolagents model/agent).")
    timeout: Optional[int] = Field(None, ge=0, description="Timeout in seconds for agent actions or LLM calls (if supported by smolagents model/agent).")
    # cache_responses: Optional[bool] = Field(None, description="Whether the agent should cache LLM responses to avoid redundant calls.") # Smolagents might handle caching internally
    verbose_logging: Optional[bool] = Field(None, description="Enable detailed verbose logging for this agent's execution (passed to smolagents if supported)." )
    
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(), description="ISO timestamp of creation.")
    updated_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(), description="ISO timestamp of last update.")

class RunAgentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid") 

    agent_id: str = Field(..., description="ID of the configured agent to run.")
    input_prompt: str = Field(..., min_length=1, description="Primary input, question, or task for the agent.")
    session_id: Optional[str] = Field(None, description="Optional session context for resolving agent config and for agent's workspace.")

class AgentRunStatus(BaseModel):
    model_config = ConfigDict(extra="forbid") 

    run_id: str = Field(..., description="Unique identifier for this agent run.")
    agent_id: str = Field(..., description="ID of the agent that was run.")
    status: str = Field(..., description="Current status of the run.")
    output: Optional[Any] = Field(None, description="Final output or result from the agent.")
    error_message: Optional[str] = Field(None, description="Error message if the run failed.")
    memory_trace_ref: Optional[str] = Field(None, description="Reference to a detailed memory trace or log.")
    start_time: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(), description="ISO timestamp of when the run started.")
    end_time: Optional[str] = Field(None, description="ISO timestamp of when the run ended.")

class AgentOutputChunk(BaseModel):
    model_config = ConfigDict(extra="forbid") 

    run_id: str = Field(..., description="Identifier of the agent run this chunk belongs to.")
    type: str = Field(..., description="Type of the output chunk.")
    data: Any = Field(..., description="The actual content of the chunk.")
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(), description="ISO timestamp of when the chunk was generated.")
