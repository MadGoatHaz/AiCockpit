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
    agent_type: str = Field("CodeAgent", description="Type of smolagent (e.g., 'CodeAgent', 'ToolCallingAgent', 'PlannerAgent').")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt to guide the agent's behavior.")
    llm_model_id: str = Field(..., description="ID of the loaded LLM model to be used by this agent.")
    llm_config_overrides: Dict[str, Any] = Field(default_factory=dict, description="Specific LLM parameter overrides for this agent.")
    tools: List[str] = Field(default_factory=list, description="List of tool IDs available to the agent.")
    max_steps: Optional[int] = Field(None, gt=0, description="Maximum number of steps. Must be positive if set.")
    additional_authorized_imports: List[str] = Field(default_factory=list, description="For CodeAgent: Python modules this agent is allowed to import.")
    use_e2b_executor: Optional[bool] = Field(None, description="For CodeAgent: Whether to use the E2B secure sandboxed executor.")
    # Common LLM parameters that can be configured per agent, overriding global LLM settings
    max_tokens: Optional[int] = Field(None, description="Max tokens for the LLM. Overrides model's default if set.")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Temperature for LLM sampling. Overrides model's default if set.")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Top_p for LLM sampling. Overrides model's default if set.")
    top_k: Optional[int] = Field(None, ge=0, description="Top_k for LLM sampling. Overrides model's default if set.")
    # SmolAgents specific or other useful fields
    max_retries: Optional[int] = Field(None, ge=0, description="Maximum number of retries for agent actions or LLM calls.")
    timeout: Optional[int] = Field(None, ge=0, description="Timeout in seconds for agent actions or LLM calls.")
    cache_responses: Optional[bool] = Field(None, description="Whether the agent should cache LLM responses to avoid redundant calls.")
    verbose_logging: Optional[bool] = Field(None, description="Enable detailed verbose logging for this agent's execution.")
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
