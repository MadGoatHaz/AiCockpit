# acp_backend/core/agent_executor.py
import logging
from typing import Optional, Any, AsyncGenerator
import asyncio
import uuid
import datetime
import sys 

from acp_backend.config import settings
from acp_backend.core.agent_config_handler import AgentConfigHandler
from acp_backend.core.llm_manager import LLMManager 
from acp_backend.models.agent_models import RunAgentRequest, AgentRunStatus, AgentOutputChunk, AgentConfig
from acp_backend.models.llm_models import ChatCompletionRequest, ChatMessageInput

logger = logging.getLogger(__name__)

class AgentExecutor:
    """
    Executes agent tasks, resolving configurations and interacting with LLMs.
    """
    def __init__(self, agent_config_handler_instance: AgentConfigHandler, llm_manager_instance: Optional[LLMManager]):
        self.agent_config_handler = agent_config_handler_instance
        self.llm_manager = llm_manager_instance
        logger.debug(f"AgentExecutor initialized. AgentConfigHandler type: {type(self.agent_config_handler)}, LLMManager type: {type(self.llm_manager)}")


    async def run_agent_task(self, request: RunAgentRequest) -> AgentRunStatus:
        run_id = f"run-{uuid.uuid4()}"
        logger.info(f"Starting agent run {run_id} for agent '{request.agent_id}' in session '{request.session_id}'")

        try:
            agent_config = await self.agent_config_handler.get_effective_agent_config(
                request.agent_id, request.session_id
            )
            if not agent_config:
                return AgentRunStatus(
                    run_id=run_id,
                    agent_id=request.agent_id,
                    status="failed",
                    error_message=f"Agent configuration '{request.agent_id}' not found for session '{request.session_id or 'None'}'."
                )

            if agent_config.llm_model_id:
                logger.debug(f"Agent config '{agent_config.agent_id}' requests LLM: '{agent_config.llm_model_id}'.")
                if not self.llm_manager:
                    return AgentRunStatus(
                        run_id=run_id,
                        agent_id=request.agent_id,
                        status="failed",
                        error_message=f"Agent '{agent_config.agent_id}' requires LLM model '{agent_config.llm_model_id}', but LLM module is disabled or LLMManager failed to initialize."
                    )
                
                model_info = await self.llm_manager.get_model_details(agent_config.llm_model_id)
                logger.debug(f"Model info for '{agent_config.llm_model_id}': {model_info}. Loaded: {model_info.loaded if model_info else 'N/A'}")
                if not model_info or not model_info.loaded:
                    return AgentRunStatus(
                        run_id=run_id,
                        agent_id=request.agent_id,
                        status="failed",
                        error_message=f"LLM model '{agent_config.llm_model_id}' for agent not loaded."
                    )
            
            output_message = f"Agent '{agent_config.agent_id}' (session: {request.session_id or 'None'}) processed input: '{request.input_prompt}' (Placeholder Output)"
            
            logger.info(f"Agent run {run_id} completed successfully.")
            return AgentRunStatus(
                run_id=run_id,
                agent_id=request.agent_id,
                status="completed",
                output=output_message,
                end_time=datetime.datetime.now(datetime.timezone.utc).isoformat()
            )
        except AttributeError as e: 
            logger.exception(f"AttributeError during agent run {run_id}: {e}. self.agent_config_handler type: {type(self.agent_config_handler)}")
            if "'Depends' object has no attribute" in str(e): 
                 return AgentRunStatus(
                    run_id=run_id,
                    agent_id=request.agent_id,
                    status="failed",
                    error_message=f"Dependency Injection Error: AgentExecutor received unresolved dependency. Detail: {str(e)}",
                    end_time=datetime.datetime.now(datetime.timezone.utc).isoformat()
                )
            return AgentRunStatus(
                run_id=run_id,
                agent_id=request.agent_id,
                status="failed",
                error_message=f"Unexpected error: {str(e)}", 
                end_time=datetime.datetime.now(datetime.timezone.utc).isoformat()
            )
        except Exception as e:
            logger.exception(f"Error during agent run {run_id}: {e}")
            return AgentRunStatus(
                run_id=run_id,
                agent_id=request.agent_id,
                status="failed",
                error_message=str(e),
                end_time=datetime.datetime.now(datetime.timezone.utc).isoformat()
            )

    async def stream_agent_task_outputs(self, request: RunAgentRequest) -> AsyncGenerator[AgentOutputChunk, None]:
        run_id = f"run-{uuid.uuid4()}"
        logger.info(f"Starting streaming agent run {run_id} for agent '{request.agent_id}' in session '{request.session_id}'")

        try:
            agent_config = await self.agent_config_handler.get_effective_agent_config(
                request.agent_id, request.session_id
            )
            if not agent_config:
                yield AgentOutputChunk(
                    run_id=run_id,
                    type="error",
                    data=f"Agent configuration '{request.agent_id}' not found for session '{request.session_id or 'None'}'."
                )
                return

            if agent_config.llm_model_id:
                logger.debug(f"Streaming agent config '{agent_config.agent_id}' requests LLM: '{agent_config.llm_model_id}'.")
                if not self.llm_manager:
                    yield AgentOutputChunk(
                        run_id=run_id,
                        type="error",
                        data=f"Agent '{agent_config.agent_id}' requires LLM model '{agent_config.llm_model_id}', but LLM module is disabled or LLMManager failed to initialize."
                    )
                    return
                
                model_info = await self.llm_manager.get_model_details(agent_config.llm_model_id)
                logger.debug(f"Streaming model info for '{agent_config.llm_model_id}': {model_info}. Loaded: {model_info.loaded if model_info else 'N/A'}")
                if not model_info or not model_info.loaded:
                    yield AgentOutputChunk(
                        run_id=run_id,
                        type="error",
                        data=f"LLM model '{agent_config.llm_model_id}' for agent not loaded."
                    )
                    return

            yield AgentOutputChunk(run_id=run_id, type="status", data={"message": "Agent task started."})
            await asyncio.sleep(0.1) 

            yield AgentOutputChunk(run_id=run_id, type="step", data={"step_name": "Planning", "details": "Agent is formulating a plan."})
            await asyncio.sleep(0.1)

            yield AgentOutputChunk(run_id=run_id, type="output", data=f"Agent '{agent_config.agent_id}' (session: {request.session_id or 'None'}) processed input: '{request.input_prompt}' (Placeholder Output)")
            await asyncio.sleep(0.1) 

            yield AgentOutputChunk(run_id=run_id, type="status", data={"message": "Agent task completed.", "final": True})

        except AttributeError as e: 
            logger.exception(f"AttributeError during streaming agent run {run_id}: {e}")
            yield AgentOutputChunk(run_id=run_id, type="error", data=f"Dependency Injection Error or similar: {str(e)}")
        except Exception as e_stream: 
            logger.exception(f"Error during streaming agent run {run_id}: {e_stream}")
            yield AgentOutputChunk(run_id=run_id, type="error", data=f"Unexpected error: {str(e_stream)}")
