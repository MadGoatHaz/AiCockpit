# acp_backend/core/agent_executor.py
import logging
from typing import Optional, Any, AsyncGenerator, List, Dict
import asyncio
import uuid
import datetime
# import io # No longer needed for StringIO with smol_dev
# import contextlib # No longer needed for redirect_stdout with smol_dev
import os

# Initialize logger early to be available for import error logging
logger = logging.getLogger(__name__)

# Corrected import from config
from acp_backend.config import app_settings

from acp_backend.core.agent_config_handler import AgentConfigHandler
from acp_backend.core.llm_manager import LLMManager
from acp_backend.models.agent_models import RunAgentRequest, AgentRunStatus, AgentOutputChunk, AgentConfig
from acp_backend.models.llm_models import LLMChatMessage

# Smol_dev imports
SMOL_DEV_AVAILABLE = False
try:
    from smol_dev.prompts import plan, specify_filePaths, generate_code
    # Note: smol_dev v0.0.2 does not have an async generate_code, and uses global openai model.
    # Tools are not part of smol_dev in the same way as smolagents.
    SMOL_DEV_AVAILABLE = True
    logger.info("smol_dev library and its core components loaded successfully.")
except ImportError as e_import:
    logger.warning(f"smol_dev library or its components not found or failed to import: {e_import}. smol_dev functionality will be limited.")
    # Define dummy functions if import fails to prevent crashes if called.
    def plan(*args, **kwargs): raise NotImplementedError("smol_dev.plan not available")
    def specify_filePaths(*args, **kwargs): raise NotImplementedError("smol_dev.specify_filePaths not available")
    def generate_code(*args, **kwargs): raise NotImplementedError("smol_dev.generate_code not available")

# Mapping of tool names from AgentConfig to smolagents tool classes - NO LONGER APPLICABLE for smol_dev
# AVAILABLE_SMOLAGENT_TOOLS: Dict[str, type[Tool]] = {
# "web_search": WebSearchTool,
# }

class AgentExecutor:
    """
    Executes agent tasks, resolving configurations and interacting with LLMs or smol_dev.
    """
    def __init__(self, 
                 agent_config_handler_instance: AgentConfigHandler, 
                 llm_manager_instance: Optional[LLMManager]):
        self.agent_config_handler: AgentConfigHandler = agent_config_handler_instance
        self.llm_manager: Optional[LLMManager] = llm_manager_instance
        self.settings = app_settings
        logger.debug(f"AgentExecutor initialized. AgentConfigHandler type: {type(self.agent_config_handler)}, LLMManager type: {type(self.llm_manager)}")

    # _construct_smolagents_model is no longer needed for smol_dev as it uses openai module directly.
    # If smol_dev's openai usage needs to be configurable, that will require changes in smol_dev
    # or monkeypatching its openai instance if possible.

    # _get_smolagent_tools is no longer applicable for smol_dev.

    async def stream_agent_task_outputs(self, request: RunAgentRequest) -> AsyncGenerator[AgentOutputChunk, None]:
        run_id = f"run-{uuid.uuid4().hex}"
        logger.info(f"Starting streaming agent run {run_id} for agent '{request.agent_id}' in session '{request.session_id}'")

        try:
            agent_config: Optional[AgentConfig] = await self.agent_config_handler.get_effective_agent_config(
                request.agent_id, request.session_id
            )
            if not agent_config:
                yield AgentOutputChunk(run_id=run_id, type="error", data={"message": f"Agent config '{request.agent_id}' not found."})
                return

            logger.info(f"[{run_id}] Effective agent config for '{request.agent_id}': "
                        f"agent_type='{agent_config.agent_type}', "
                        f"llm_model_id='{agent_config.llm_model_id}'") # smol_model_provider removed

            yield AgentOutputChunk(run_id=run_id, type="status", data={"message": "Agent task started.", "agent_config_used": agent_config.agent_id})
            await asyncio.sleep(0.01)

            # Updated logic for smol_dev integration
            # We might define a specific agent_type like "SmolDevCodeGenerator"
            if agent_config.agent_type == "SmolDevCodeGenerator": # Example agent type
                if not SMOL_DEV_AVAILABLE:
                    yield AgentOutputChunk(run_id=run_id, type="error", data={"message": "smol_dev library is not available on the server."})
                    return
                
                yield AgentOutputChunk(run_id=run_id, type="status", data={"message": "Using smol_dev for code generation."})
                await asyncio.sleep(0.01)

                # Step 1: Call plan
                yield AgentOutputChunk(run_id=run_id, type="smol_dev_status", data={"message": "Generating plan..."})
                try:
                    # smol_dev.plan is synchronous, run in thread pool
                    shared_dependency_manifest = await asyncio.to_thread(
                        plan,
                        request.input_prompt 
                        # smol_dev.plan does not take a model_id. It uses its internal default.
                    )
                    logger.info(f"[{run_id}] smol_dev plan generated: {shared_dependency_manifest[:200]}...")
                    yield AgentOutputChunk(run_id=run_id, type="smol_dev_plan", data={"content": shared_dependency_manifest})
                except Exception as e_plan:
                    logger.error(f"[{run_id}] Error during smol_dev.plan: {e_plan}", exc_info=True)
                    yield AgentOutputChunk(run_id=run_id, type="error", data={"message": f"Error in smol_dev planning: {str(e_plan)}"})
                    return
                await asyncio.sleep(0.01)

                # Step 2: Call specify_filePaths
                yield AgentOutputChunk(run_id=run_id, type="smol_dev_status", data={"message": "Specifying file paths..."})
                try:
                    # smol_dev.specify_filePaths is synchronous
                    file_paths_to_generate = await asyncio.to_thread(
                        specify_filePaths,
                        request.input_prompt,
                        shared_dependency_manifest
                    )
                    if not isinstance(file_paths_to_generate, list): # Ensure it's a list
                        logger.error(f"[{run_id}] smol_dev.specify_filePaths did not return a list: {file_paths_to_generate}")
                        raise ValueError("specify_filePaths did not return a list of file paths.")
                    
                    logger.info(f"[{run_id}] smol_dev file paths specified: {file_paths_to_generate}")
                    yield AgentOutputChunk(run_id=run_id, type="smol_dev_filepaths", data={"files": file_paths_to_generate})
                except Exception as e_specify:
                    logger.error(f"[{run_id}] Error during smol_dev.specify_filePaths: {e_specify}", exc_info=True)
                    yield AgentOutputChunk(run_id=run_id, type="error", data={"message": f"Error in smol_dev file path specification: {str(e_specify)}"})
                    return
                await asyncio.sleep(0.01)

                # Step 3: Loop and call generate_code for each file
                if not file_paths_to_generate:
                    yield AgentOutputChunk(run_id=run_id, type="smol_dev_status", data={"message": "No file paths specified by smol_dev. Nothing to generate."})
                
                for file_path in file_paths_to_generate:
                    yield AgentOutputChunk(run_id=run_id, type="smol_dev_status", data={"message": f"Generating code for {file_path}..."})
                    try:
                        # smol_dev.generate_code is synchronous
                        generated_file_code = await asyncio.to_thread(
                            generate_code,
                            request.input_prompt,
                            shared_dependency_manifest,
                            file_path
                        )
                        logger.info(f"[{run_id}] smol_dev code generated for {file_path}: {generated_file_code[:200]}...")
                        yield AgentOutputChunk(run_id=run_id, type="smol_dev_generated_code", data={"file_path": file_path, "code": generated_file_code})
                    except Exception as e_generate:
                        logger.error(f"[{run_id}] Error during smol_dev.generate_code for {file_path}: {e_generate}", exc_info=True)
                        yield AgentOutputChunk(run_id=run_id, type="error", data={"message": f"Error generating code for {file_path}: {str(e_generate)}"})
                        # Optionally continue to next file or return
                    await asyncio.sleep(0.01)
                
                yield AgentOutputChunk(run_id=run_id, type="status", data={"message": "smol_dev task completed."})


            # Fallback to original LLMManager logic if not a smol_dev agent_type
            # AND llm_model_id is configured AND llm_manager is available.
            elif agent_config.llm_model_id and self.llm_manager:
                logger.debug(f"Fallback: Streaming agent '{agent_config.agent_id}' using direct LLMManager with model: '{agent_config.llm_model_id}'.")
                llm_meta = self.llm_manager.get_llm_meta(agent_config.llm_model_id)
                if not llm_meta or llm_meta.status != "loaded":
                    yield AgentOutputChunk(run_id=run_id, type="error", data={"message": f"LLM '{agent_config.llm_model_id}' not loaded. Status: {llm_meta.status if llm_meta else 'Not Found'}"})
                    return
                yield AgentOutputChunk(run_id=run_id, type="status", data={"message": f"Using LLM: {agent_config.llm_model_id}"})
                await asyncio.sleep(0.01)

                messages_for_llm: List[LLMChatMessage] = []
                # system_prompt is part of AgentConfig, ensure it's used if present
                if agent_config.system_prompt:
                    messages_for_llm.append(LLMChatMessage(role="system", content=agent_config.system_prompt))
                
                messages_for_llm.append(LLMChatMessage(role="user", content=request.input_prompt))

                streamer = await self.llm_manager.chat_completion(
                    model_id=agent_config.llm_model_id,
                    messages=messages_for_llm,
                    stream=True,
                    **(agent_config.llm_config_overrides or {})
                )
                
                async for llm_chunk in streamer: 
                    if llm_chunk.choices and llm_chunk.choices[0].delta and llm_chunk.choices[0].delta.content:
                        yield AgentOutputChunk(run_id=run_id, type="output", data={"output_text": llm_chunk.choices[0].delta.content})
                    if llm_chunk.choices and llm_chunk.choices[0].finish_reason:
                        yield AgentOutputChunk(run_id=run_id, type="status", data={"message": f"LLM stream finished. Reason: {llm_chunk.choices[0].finish_reason}"})
                    await asyncio.sleep(0.01)

            else: 
                yield AgentOutputChunk(run_id=run_id, type="error", data={"message": "Agent not configured for smol_dev and no fallback LLM configured or LLMManager unavailable."})
                return

            yield AgentOutputChunk(run_id=run_id, type="status", data={"message": "Agent task completed.", "final": True})

        except Exception as e_stream: 
            logger.exception(f"Error during streaming agent run {run_id}: {e_stream}")
            yield AgentOutputChunk(run_id=run_id, type="error", data={"message": f"Unexpected error: {str(e_stream)}"})

    async def run_agent_task(self, request: RunAgentRequest) -> AgentRunStatus:
        logger.warning("run_agent_task (non-streaming) with smol_dev should be adapted or indicate it's not suitable.")
        
        agent_config: Optional[AgentConfig] = await self.agent_config_handler.get_effective_agent_config(
                request.agent_id, request.session_id
            )
        
        run_id = f"run-{uuid.uuid4().hex}" # Define run_id earlier
        start_time_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        if not agent_config:
            return AgentRunStatus(run_id=run_id, agent_id=request.agent_id, status="failed", error_message="Agent config not found", start_time=start_time_iso)

        # If it's a smol_dev agent, non-streaming might mean generating all files and returning a manifest.
        if agent_config.agent_type == "SmolDevCodeGenerator":
            if not SMOL_DEV_AVAILABLE:
                return AgentRunStatus(run_id=run_id, agent_id=request.agent_id, status="failed", error_message="smol_dev library not available.", start_time=start_time_iso)

            all_generated_files = {}
            try:
                logger.info(f"[{run_id}] smol_dev non-streaming: Generating plan...")
                # Note: asyncio.to_thread cannot be directly awaited in a synchronous function.
                # This run_agent_task is async, so it's fine.
                shared_dependency_manifest = await asyncio.to_thread(plan, request.input_prompt)
                logger.info(f"[{run_id}] smol_dev non-streaming: Plan: {shared_dependency_manifest[:100]}...")
                all_generated_files["plan.md"] = shared_dependency_manifest # Store plan

                logger.info(f"[{run_id}] smol_dev non-streaming: Specifying file paths...")
                file_paths_to_generate = await asyncio.to_thread(specify_filePaths, request.input_prompt, shared_dependency_manifest)
                if not isinstance(file_paths_to_generate, list):
                     raise ValueError("specify_filePaths did not return a list of file paths.")
                all_generated_files["files.json"] = file_paths_to_generate # Store file list as JSON compatible

                logger.info(f"[{run_id}] smol_dev non-streaming: Generating code for {len(file_paths_to_generate)} files...")
                for file_path in file_paths_to_generate:
                    logger.info(f"[{run_id}] smol_dev non-streaming: Generating {file_path}...")
                    code_content = await asyncio.to_thread(generate_code, request.input_prompt, shared_dependency_manifest, file_path)
                    all_generated_files[file_path] = code_content
                
                # For non-streaming, we might return a summary or a manifest of generated files.
                # The current AgentRunStatus.output is a single string. This needs thought.
                # For now, let's just indicate completion and list files in the message.
                output_summary = f"Smol_dev generated {len(file_paths_to_generate)} files. Plan and files are internally logged or stored."
                # To truly return all files, AgentRunStatus.output would need to be a Dict or List[Dict]
                # and the frontend would need to handle it. This is a larger change.
                # For now, we just return a success message.
                return AgentRunStatus(
                    run_id=run_id, 
                    agent_id=request.agent_id, 
                    status="completed", 
                    # output=all_generated_files, # This would require AgentRunStatus.output to be Any/Dict
                    output=output_summary, # Placeholder for now
                    start_time=start_time_iso,
                    # We could add a new field like 'artifacts' to AgentRunStatus if needed
                )

            except Exception as e_smol_run:
                logger.error(f"[{run_id}] Error during non-streaming smol_dev run: {e_smol_run}", exc_info=True)
                return AgentRunStatus(run_id=run_id, agent_id=request.agent_id, status="failed", error_message=f"Error in smol_dev non-streaming execution: {str(e_smol_run)}", start_time=start_time_iso)

        # Fallback to old logic if not a smol_dev provider config
        if agent_config.llm_model_id and self.llm_manager:
            messages_for_llm: List[LLMChatMessage] = []
            if agent_config.system_prompt:
                messages_for_llm.append(LLMChatMessage(role="system", content=agent_config.system_prompt))
            messages_for_llm.append(LLMChatMessage(role="user", content=request.input_prompt))
            
            try:
                completion = await self.llm_manager.chat_completion(
                        model_id=agent_config.llm_model_id,
                        messages=messages_for_llm,
                        stream=False, # Non-streaming call
                        **(agent_config.llm_config_overrides or {})
                )
                output_message = completion.choices[0].message.content if completion and completion.choices else "No LLM response."
                return AgentRunStatus(run_id=run_id, agent_id=request.agent_id, status="completed", output=output_message, start_time=start_time_iso)
            except Exception as e_llm_run:
                logger.error(f"[{run_id}] Error during non-streaming LLM run for agent '{agent_config.agent_id}': {e_llm_run}", exc_info=True)
                return AgentRunStatus(run_id=run_id, agent_id=request.agent_id, status="failed", error_message=f"LLM API error: {str(e_llm_run)}", start_time=start_time_iso)

        else: # No smol_dev and no LLM configured for fallback
            return AgentRunStatus(run_id=run_id, agent_id=request.agent_id, status="failed", error_message="Non-smol_dev agent requires llm_model_id and LLMManager.", start_time=start_time_iso)
