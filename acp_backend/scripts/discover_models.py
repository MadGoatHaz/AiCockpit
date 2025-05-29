# acp_backend/scripts/discover_models.py (v0.5 - Serialization Fix)
import os
import sys
import json
import asyncio
import glob
from typing import List, Dict, Any

# This script is designed to be run by the install_acp.sh script
# to discover LLM models in a given directory.

# Ensure acp_backend is in sys.path if running as a script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_REAL_BACKEND_AVAILABLE = False
_backend_instance = None
_LLM_MODEL_INFO_CLASS = None
_DISCOVER_FUNCTION = None

print("DEBUG: Starting discover_models.py script.", file=sys.stderr) 

try:
    print("DEBUG: Attempting to import from acp_backend.llm_backends.llama_cpp...", file=sys.stderr) 
    from acp_backend.llm_backends.llama_cpp import LlamaCppBackend
    from acp_backend.models.llm_models import LLMModelInfo
    from acp_backend.config import settings
    
    _models_dir_from_env = os.environ.get("ACP_MODELS_DIR_FOR_SCAN")
    if _models_dir_from_env:
        settings.MODELS_DIR = _models_dir_from_env
        print(f"DEBUG: settings.MODELS_DIR overridden by env var: {settings.MODELS_DIR}", file=sys.stderr) 
    else:
        print(f"DEBUG: Using default settings.MODELS_DIR: {settings.MODELS_DIR}", file=sys.stderr) 
    
    _backend_instance = LlamaCppBackend() 
    _LLM_MODEL_INFO_CLASS = LLMModelInfo
    _DISCOVER_FUNCTION = _backend_instance.discover_models
    _REAL_BACKEND_AVAILABLE = True
    print("DEBUG: Real LlamaCppBackend initialized successfully.", file=sys.stderr) 
except (ImportError, RuntimeError) as e:
    print(f"DEBUG: Caught exception during real backend import/init: {type(e).__name__}: {e}", file=sys.stderr) 
    print("DEBUG: Falling back to mock classes for LLM discovery.", file=sys.stderr) 
    class MockLLMModelInfo: # Simplified mock, as real one should be used
        def __init__(self, id: str, name: str, path: str, size_gb: float, quantization: str, loaded: bool, backend: str):
            self.id = id; self.name = name; self.path = path; self.size_gb = size_gb; 
            self.quantization = quantization; self.loaded = loaded; self.backend = backend
            self.context_length = None
        def model_dump(self): # Changed to model_dump for consistency if mock is ever hit
            return {"id": self.id, "name": self.name, "path": self.path, "size_gb": self.size_gb,
                    "quantization": self.quantization, "loaded": self.loaded, "backend": self.backend,
                    "context_length": self.context_length}

    class MockLlamaCppBackend: # Simplified mock
        async def discover_models(self, models_dir: str) -> List[MockLLMModelInfo]:
            print(f"DEBUG: Mock discover_models called with models_dir: {models_dir}", file=sys.stderr)
            return [] # Keep mock simple, real path should work

    _LLM_MODEL_INFO_CLASS = MockLLMModelInfo
    _DISCOVER_FUNCTION = MockLlamaCppBackend().discover_models
    _REAL_BACKEND_AVAILABLE = False
    print(f"WARNING: LLM discovery running in fallback mode due to: {e}", file=sys.stderr)


async def main():
    models_dir = os.environ.get("ACP_MODELS_DIR_FOR_SCAN")
    print(f"DEBUG: Script received MODELS_DIR from env: {models_dir}", file=sys.stderr) 

    if not models_dir:
        print("ERROR: MODELS_DIR not provided via environment variable ACP_MODELS_DIR_FOR_SCAN.", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(models_dir):
        print(f"ERROR: Specified MODELS_DIR '{models_dir}' does not exist or is not a directory.", file=sys.stderr)
        sys.exit(1)

    try:
        print(f"DEBUG: Calling discover function ({'real' if _REAL_BACKEND_AVAILABLE else 'mock'})...", file=sys.stderr) 
        models = await _DISCOVER_FUNCTION(models_dir)
    except Exception as e:
        print(f"ERROR: Failed to discover models in '{models_dir}': {e}", file=sys.stderr)
        sys.exit(1)

    if not models:
        print("NO_MODELS_FOUND")
        print("DEBUG: No models found by discover function.", file=sys.stderr) 
        sys.exit(0)

    print("MODELS_FOUND")
    print(f"DEBUG: Discovered {len(models)} models.", file=sys.stderr) 
    for i, model in enumerate(models):
        print(f"  {i+1}. {model.name} (ID: {model.id}, Size: {model.size_gb}GB, Quant: {model.quantization})")
    
    print("---JSON_MODELS_START---")
    # Use model_dump() for Pydantic v2 models
    print(json.dumps([m.model_dump() for m in models])) # <<< THE FIX IS HERE
    print("---JSON_MODELS_END---")

if __name__ == "__main__":
    asyncio.run(main())
