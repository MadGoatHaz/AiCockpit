# acp_backend/core/agent_executor.py
import logging
from typing import Optional, Any, AsyncGenerator
import asyncio
import uuid
import datetime
# import sys # This import was unused

# Corrected import from config
from acp_backend.config import app_settings # Changed from 'settings'

from acp_backend.core.agent_config_handler import AgentConfigHandler
from acp_backend.core.llm_manager import LLMManager
# Assuming agent_models.py defines these correctly
from acp_backend.models.agent_models import RunAgentRequest, AgentRunStatus, AgentOutputChunk, AgentConfig
# Assuming llm_models.py defines these correctly (ChatCompletionRequest is for API, LLMChatMessage is canonical)
from acp_backend.models.llm_models import LLMChatMessage # Changed from ChatMessageInput if that was different
# ChatCompletionRequest is for the API router, LLMManager expects List[LLMChatMessage]

logger = logging.getLogger(__name__)

class AgentExecutor:
    """
    Executes agent tasks, resolving configurations and interacting with LLMs.
    """
    def __init__(self, 
                 agent_config_handler_instance: AgentConfigHandler, 
                 llm_manager_instance: Optional[LLMManager]):
        self.agent_config_handler: AgentConfigHandler = agent_config_handler_instance
        self.llm_manager: Optional[LLMManager] = llm_manager_instance
        # Accessing app_settings directly if needed for some global agent behavior,
        # though typically configuration comes via AgentConfig.
        self.settings = app_settings # Store a reference if needed by methods
        logger.debug(f"AgentExecutor initialized. AgentConfigHandler type: {type(self.agent_config_handler)}, LLMManager type: {type(self.llm_manager)}")


    async def run_agent_task(self, request: RunAgentRequest) -> AgentRunStatus:
        run_id = f"run-{uuid.uuid4().hex}" # Use hex for cleaner UUID string
        logger.info(f"Starting agent run {run_id} for agent '{request.agent_id}' in session '{request.session_id}'")
        start_time_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            agent_config: Optional[AgentConfig] = await self.agent_config_handler.get_effective_agent_config(
                request.agent_id, request.session_id
            )
            if not agent_config:
                return AgentRunStatus(
                    run_id=run_id,
                    agent_id=request.agent_id,
                    status="failed",
                    error_message=f"Agent configuration '{request.agent_id}' not found for session '{request.session_id or 'global'}'."
                )

            # Example: If agent needs to use an LLM
            if agent_config.llm_model_id:
                logger.debug(f"Agent '{agent_config.agent_id}' requires LLM: '{agent_config.llm_model_id}'.")
                if not self.llm_manager:
                    return AgentRunStatus(
                        run_id=run_id, agent_id=request.agent_id, status="failed",
                        error_message=f"Agent '{agent_config.agent_id}' requires LLM, but LLMManager is not available."
                    )
                
                # Check if the required model is loaded
                llm_meta = self.llm_manager.get_llm_meta(agent_config.llm_model_id)
                if not llm_meta or llm_meta.status != "loaded": # Assuming LLMStatus.LOADED.value is "loaded"
                    # Attempt to load the model if not loaded? Or fail? For now, fail.
                    # Consider adding auto-load logic here or in LLMManager if desired.
                    # await self.llm_manager.load_model_by_id_if_known(agent_config.llm_model_id)
                    return AgentRunStatus(
                        run_id=run_id, agent_id=request.agent_id, status="failed",
                        error_message=f"Required LLM model '{agent_config.llm_model_id}' is not loaded. Current status: {llm_meta.status if llm_meta else 'Not Found'}."
                    )
                
                # Example: Construct messages for the LLM based on agent config and request input
                # This is highly dependent on your agent's logic and prompt templating
                messages_for_llm: List[LLMChatMessage] = []
                if agent_config.system_prompt:
                    messages_for_llm.append(LLMChatMessage(role="system", content=agent_config.system_prompt))
                
                # Combine agent's base prompt (if any) with user's input prompt
                # This is just a placeholder for actual prompt engineering
                combined_prompt = f"{agent_config.system_prompt or ''}\n\nUser input: {request.input_prompt}"
                messages_for_llm.append(LLMChatMessage(role="user", content=combined_prompt))

                # Call the LLM
                # Non-streaming for run_agent_task
                completion = await self.llm_manager.chat_completion(
                    model_id=agent_config.llm_model_id,
                    messages=messages_for_llm,
                    stream=False,
                    # Pass any parameters from agent_config.llm_parameters
                    **(agent_config.llm_config_overrides or {})
                )
                
                if completion and completion.choices:
                    output_message = completion.choices[0].message.content
                else:
                    output_message = "Agent received no response from LLM."
            else:
                # Agent does not use an LLM, placeholder logic
                output_message = f"Agent '{agent_config.agent_id}' (session: {request.session_id or 'global'}) processed input: '{request.input_prompt}' without LLM. (Placeholder Output)"
            
            logger.info(f"Agent run {run_id} completed successfully.")
            return AgentRunStatus(
                run_id=run_id,
                agent_id=request.agent_id,
                status="completed",
                output=output_message, # Actual output from LLM or agent logic
                start_time=start_time_iso,
                end_time=datetime.datetime.now(datetime.timezone.utc).isoformat()
            )
        
        except AttributeError as e: 
            logger.exception(f"AttributeError during agent run {run_id}: {e}. ACH type: {type(self.agent_config_handler)}, LLMM type: {type(self.llm_manager)}")
            # Check if it's the specific "Depends object has no attribute" error
            # This indicates an uninitialized dependency, often due to FastAPI/DI issues
            # or if a dependency function returned None when it shouldn't have.
            if "'Depends' object has no attribute" in str(e) or \
               (self.agent_config_handler is None or (hasattr(agent_config, 'llm_model_id') and agent_config.llm_model_id and self.llm_manager is None)):
                 error_detail = f"Dependency Injection Error: AgentExecutor received an uninitialized core component. Detail: {str(e)}"
            else:
                error_detail = f"Unexpected AttributeError: {str(e)}"
            
            return AgentRunStatus(
                run_id=run_id, agent_id=request.agent_id, status="failed",
                error_message=error_detail, start_time=start_time_iso,
                end_time=datetime.datetime.now(datetime.timezone.utc).isoformat()
            )
        except Exception as e:
            logger.exception(f"Error during agent run {run_id}: {e}")
            return AgentRunStatus(
                run_id=run_id,
                agent_id=request.agent_id,
                status="failed",
                error_message=f"General error: {str(e)}",
                start_time=start_time_iso,
                end_time=datetime.datetime.now(datetime.timezone.utc).isoformat()
            )

    async def stream_agent_task_outputs(self, request: RunAgentRequest) -> AsyncGenerator[AgentOutputChunk, None]:
        run_id = f"run-{uuid.uuid4().hex}"
        logger.info(f"Starting streaming agent run {run_id} for agent '{request.agent_id}' in session '{request.session_id}'")

        try:
            agent_config: Optional[AgentConfig] = await self.agent_config_handler.get_effective_agent_config(
                request.agent_id, request.session_id
            )
            if not agent_config:
                yield AgentOutputChunk(
                    run_id=run_id, type="error",
                    data={"message": f"Agent configuration '{request.agent_id}' not found for session '{request.session_id or 'global'}'."}
                )
                return

            yield AgentOutputChunk(run_id=run_id, type="status", data={"message": "Agent task started.", "agent_config_used": agent_config.agent_id})
            await asyncio.sleep(0.01) # Yield control

            if agent_config.llm_model_id:
                logger.debug(f"Streaming agent '{agent_config.agent_id}' using LLM: '{agent_config.llm_model_id}'.")
                if not self.llm_manager:
                    yield AgentOutputChunk(run_id=run_id, type="error", data={"message": "LLMManager not available for agent."})
                    return
                
                llm_meta = self.llm_manager.get_llm_meta(agent_config.llm_model_id)
                if not llm_meta or llm_meta.status != "loaded": # Assuming LLMStatus.LOADED.value
                    yield AgentOutputChunk(run_id=run_id, type="error", data={"message": f"LLM '{agent_config.llm_model_id}' not loaded. Status: {llm_meta.status if llm_meta else 'Not Found'}"})
                    return

                yield AgentOutputChunk(run_id=run_id, type="status", data={"message": f"Using LLM: {agent_config.llm_model_id}"})
                await asyncio.sleep(0.01)

                messages_for_llm: List[LLMChatMessage] = []
                if agent_config.system_prompt:
                    messages_for_llm.append(LLMChatMessage(role="system", content=agent_config.system_prompt))
                combined_prompt = f"{agent_config.system_prompt or ''}\n\nUser input: {request.input_prompt}"
                messages_for_llm.append(LLMChatMessage(role="user", content=combined_prompt))

                streamer = await self.llm_manager.chat_completion(
                    model_id=agent_config.llm_model_id,
                    messages=messages_for_llm,
                    stream=True,
                    **(agent_config.llm_parameters or {})
                )
                
                async for chunk in streamer: # type: ignore # Assuming streamer is AsyncGenerator[LLMChatCompletion, None]
                    if chunk.choices and chunk.choices[0].message and chunk.choices[0].message.content:
                        yield AgentOutputChunk(run_id=run_id, type="output", data=chunk.choices[0].message.content)
                    if chunk.choices and chunk.choices[0].finish_reason:
                        yield AgentOutputChunk(run_id=run_id, type="status", data={"message": f"LLM stream finished. Reason: {chunk.choices[0].finish_reason}"})
                    await asyncio.sleep(0.01) # Yield control during streaming

            else: # No LLM model ID in agent config
                yield AgentOutputChunk(run_id=run_id, type="step", data={"step_name": "Processing (No LLM)", "details": "Agent is processing without LLM."})
                await asyncio.sleep(0.1)
                yield AgentOutputChunk(run_id=run_id, type="output", data=f"Agent '{agent_config.agent_id}' processed input: '{request.input_prompt}' (Placeholder No-LLM Output)")
                await asyncio.sleep(0.1)

            yield AgentOutputChunk(run_id=run_id, type="status", data={"message": "Agent task completed.", "final": True})

        except AttributeError as e: 
            logger.exception(f"AttributeError during streaming agent run {run_id}: {e}")
            yield AgentOutputChunk(run_id=run_id, type="error", data={"message": f"Dependency Injection Error or similar: {str(e)}"})
        except Exception as e_stream: 
            logger.exception(f"Error during streaming agent run {run_id}: {e_stream}")
            yield AgentOutputChunk(run_id=run_id, type="error", data={"message": f"Unexpected error: {str(e_stream)}"})
