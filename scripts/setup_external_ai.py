#!/usr/bin/env python3
"""
Setup Script for External AI Services
====================================

This script helps users configure external AI services for AiCockpit.

Author: AiCockpit Development Team
License: GPL-3.0
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add the backend directory to the Python path
backend_path = Path(__file__).parent.parent / "acp_backend"
sys.path.insert(0, str(backend_path))

from acp_backend.core.external_ai_manager import AIServiceConfig

def create_default_config() -> Dict[str, Any]:
    """Create a default configuration with common external AI services."""
    return {
        "services": [
            {
                "name": "lmstudio",
                "type": "lmstudio",
                "base_url": "http://localhost:1234/v1",
                "model": "gpt-3.5-turbo"
            },
            {
                "name": "openai",
                "type": "openai",
                "api_key": "YOUR_OPENAI_API_KEY",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-3.5-turbo"
            }
        ],
        "active_service": "lmstudio"
    }

def save_config(config: Dict[str, Any], config_path: Path) -> None:
    """Save the configuration to a JSON file."""
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"Configuration saved to {config_path}")

def load_config(config_path: Path) -> Dict[str, Any]:
    """Load the configuration from a JSON file."""
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

def setup_lmstudio(config: Dict[str, Any]) -> Dict[str, Any]:
    """Setup LM Studio service."""
    print("\n=== LM Studio Setup ===")
    print("LM Studio is a local AI model server that runs models on your machine.")
    print("Default URL: http://localhost:1234/v1")
    
    base_url = input("Enter LM Studio API URL (press Enter for default): ").strip()
    if not base_url:
        base_url = "http://localhost:1234/v1"
    
    model = input("Enter default model name (press Enter for gpt-3.5-turbo): ").strip()
    if not model:
        model = "gpt-3.5-turbo"
    
    # Add to services if not already present
    lmstudio_service = {
        "name": "lmstudio",
        "type": "lmstudio",
        "base_url": base_url,
        "model": model
    }
    
    # Check if service already exists
    service_exists = False
    for i, service in enumerate(config.get("services", [])):
        if service.get("name") == "lmstudio":
            config["services"][i] = lmstudio_service
            service_exists = True
            break
    
    if not service_exists:
        if "services" not in config:
            config["services"] = []
        config["services"].append(lmstudio_service)
    
    return config

def setup_openai(config: Dict[str, Any]) -> Dict[str, Any]:
    """Setup OpenAI service."""
    print("\n=== OpenAI Setup ===")
    print("OpenAI provides access to GPT models.")
    print("You need an API key from https://platform.openai.com/api-keys")
    
    api_key = input("Enter your OpenAI API key: ").strip()
    if not api_key:
        print("API key is required for OpenAI service.")
        return config
    
    base_url = input("Enter OpenAI API URL (press Enter for default): ").strip()
    if not base_url:
        base_url = "https://api.openai.com/v1"
    
    model = input("Enter default model name (press Enter for gpt-3.5-turbo): ").strip()
    if not model:
        model = "gpt-3.5-turbo"
    
    # Add to services if not already present
    openai_service = {
        "name": "openai",
        "type": "openai",
        "api_key": api_key,
        "base_url": base_url,
        "model": model
    }
    
    # Check if service already exists
    service_exists = False
    for i, service in enumerate(config.get("services", [])):
        if service.get("name") == "openai":
            config["services"][i] = openai_service
            service_exists = True
            break
    
    if not service_exists:
        if "services" not in config:
            config["services"] = []
        config["services"].append(openai_service)
    
    return config

def main():
    """Main setup function."""
    print("AiCockpit External AI Services Setup")
    print("====================================")
    
    # Determine config path
    config_dir = Path.home() / ".acp"
    config_dir.mkdir(exist_ok=True)
    config_path = config_dir / "external_ai_config.json"
    
    # Load existing config
    config = load_config(config_path)
    if not config:
        config = create_default_config()
        print(f"Created default configuration at {config_path}")
    
    while True:
        print("\nCurrent configuration:")
        print(json.dumps(config, indent=2))
        
        print("\nOptions:")
        print("1. Setup LM Studio (local models)")
        print("2. Setup OpenAI")
        print("3. Set active service")
        print("4. Save and exit")
        print("5. Exit without saving")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            config = setup_lmstudio(config)
        elif choice == "2":
            config = setup_openai(config)
        elif choice == "3":
            if "services" in config and config["services"]:
                print("\nAvailable services:")
                for i, service in enumerate(config["services"]):
                    print(f"{i+1}. {service['name']} ({service['type']})")
                
                try:
                    service_choice = int(input("Select service number: ")) - 1
                    if 0 <= service_choice < len(config["services"]):
                        config["active_service"] = config["services"][service_choice]["name"]
                        print(f"Active service set to: {config['active_service']}")
                    else:
                        print("Invalid service number.")
                except ValueError:
                    print("Invalid input.")
            else:
                print("No services configured yet.")
        elif choice == "4":
            save_config(config, config_path)
            print("Setup complete!")
            break
        elif choice == "5":
            print("Exiting without saving.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()