#!/bin/bash

# AiCockpit (ACP) Backend Installation Script (Draft v0.5.8)
# This script automates the setup of the ACP backend on Linux systems.
# It aims for idempotency and improved error handling and user experience.

# Exit on error and pipefail
set -e
set -o pipefail

# --- Configuration ---
MIN_PYTHON_VERSION_MAJOR=3
MIN_PYTHON_VERSION_MINOR=10 # Requires Python 3.10+
VENV_DIR=".venv-acp"      # Name of the virtual environment directory
INSTALL_LOG_FILE="acp_install.log"
DISCOVER_MODELS_SCRIPT="acp_backend/scripts/discover_models.py" # Script for model discovery

# --- Global Flags ---
QUICK_INSTALL=false # Set to true if --quick argument is passed
SCRIPT_ACTIVATED_VENV=false # Flag for cleanup trap

# --- ANSI Color Codes (for better CLI UX) ---
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
BLUE=$(tput setaf 4)
RED=$(tput setaf 1)
BOLD=$(tput bold)
RESET=$(tput sgr0)

# --- Helper Functions ---
_log_to_file() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$INSTALL_LOG_FILE"
}

_print_msg() {
    echo -e "${GREEN}${BOLD}ACP INSTALLER:${RESET} $1" | tee -a "$INSTALL_LOG_FILE"
}
_print_error() {
    echo -e "${RED}${BOLD}ACP ERROR:${RESET} $1" | tee -a "$INSTALL_LOG_FILE" >&2
}
_print_warning() {
    echo -e "${YELLOW}${BOLD}ACP WARNING:${RESET} $1" | tee -a "$INSTALL_LOG_FILE" >&2
}
_print_info() {
    echo -e "${BLUE}ACP INFO:${RESET} $1" | tee -a "$INSTALL_LOG_FILE"
}

_print_section_header() {
    echo
    _print_msg "--- ${BOLD}$1${RESET} ---"
    echo
    _log_to_file "Starting section: $1"
}

_command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Cleanup function to be called on exit
_cleanup() {
    _log_to_file "Script exiting."
    if [ "$SCRIPT_ACTIVATED_VENV" = true ] && _command_exists deactivate; then
        _print_info "Deactivating virtual environment for script session." >&2 
        deactivate
    fi
}
trap _cleanup EXIT 

_check_python_version() {
    _log_to_file "Checking Python version."
    if ! _command_exists python3; then
        _print_error "Python 3 is not installed. Please install Python 3.10 or higher."
        return 1
    fi
    local python_major=$(python3 -c 'import sys; print(sys.version_info.major)')
    local python_minor=$(python3 -c 'import sys; print(sys.version_info.minor)')
    if [ "$python_major" -lt "$MIN_PYTHON_VERSION_MAJOR" ] || ([ "$python_major" -eq "$MIN_PYTHON_VERSION_MAJOR" ] && [ "$python_minor" -lt "$MIN_PYTHON_VERSION_MINOR" ]); then
        _print_error "Installed Python version is ${BOLD}$python_major.$python_minor${RESET}. ACP requires Python ${BOLD}$MIN_PYTHON_VERSION_MAJOR.$MIN_PYTHON_VERSION_MINOR${RESET} or higher."
        return 1
    fi
    _print_msg "Python version ${BOLD}$python_major.$python_minor${RESET} found."
    return 0
}

_prompt_user_yes_no() {
    local prompt_message="$1"; local default_answer="${2:-N}"; local answer
    if [ "$QUICK_INSTALL" = true ]; then _print_info "Quick install: Auto-answering '${BOLD}Yes${RESET}' to '$prompt_message'" >&2; return 0; fi
    while true; do
        read -r -p "${BLUE}QUESTION:${RESET} $prompt_message [${BOLD}y/N${RESET}]: " answer >&2
        answer="${answer:-$default_answer}"
        case "$answer" in
            [Yy]* ) return 0;; [Nn]* ) return 1;; * ) echo "${YELLOW}Please answer yes (y) or no (n).${RESET}" >&2;;
        esac
    done
}

_prompt_user_input() {
    local prompt_message="$1"; local default_value="$2"; local user_input
    if [ "$QUICK_INSTALL" = true ]; then _print_info "Quick install: Auto-using default '${BOLD}$default_value${RESET}' for '$prompt_message'" >&2; echo "$default_value"; return; fi
    read -r -p "${BLUE}INPUT:${RESET} $prompt_message [${BOLD}$default_value${RESET}]: " user_input >&2
    echo "${user_input:-$default_value}"
}

_prompt_model_selection() {
    local json_models="$1"; local selected_model_id_output=""
    if [ "$QUICK_INSTALL" = true ]; then
        FIRST_MODEL_ID=$(echo "$json_models" | jq -r '.[0].id // ""')
        if [ -n "$FIRST_MODEL_ID" ]; then _print_info "Quick install: Auto-selecting model: '${BOLD}$FIRST_MODEL_ID${RESET}'" >&2; selected_model_id_output="$FIRST_MODEL_ID";
        else _print_warning "No models for quick install." >&2; fi
        echo "$selected_model_id_output"; return
    fi
    local num_models=$(echo "$json_models" | jq '. | length')
    if [ "$num_models" -eq 0 ]; then _print_info "No LLM models available." >&2; echo ""; return; fi
    _print_info "Select default LLM (ID will be set as LLAMA_CPP_MODEL_PATH):" >&2; echo >&2
    echo "$json_models" | jq -r '.[] | "\(.id) | \(.name) (\(.size_gb)GB, \(.quantization))"' | nl -w 2 -s '. ' >&2
    local selection_valid=false
    while [ "$selection_valid" = false ]; do
        read -r -p "${BLUE}SELECT:${RESET} Model number (1-${num_models}) or blank: " model_num_input >&2
        if [ -z "$model_num_input" ]; then _print_info "No default LLM selected." >&2; selected_model_id_output=""; selection_valid=true;
        elif [[ "$model_num_input" =~ ^[0-9]+$ ]] && [ "$model_num_input" -ge 1 ] && [ "$model_num_input" -le "$num_models" ]; then
            selected_model_id_output=$(echo "$json_models" | jq -r ".[$((model_num_input-1))].id")
            _print_info "Selected model ID: ${BOLD}$selected_model_id_output${RESET}" >&2; selection_valid=true;
        else _print_warning "Invalid selection." >&2; fi
    done
    echo "$selected_model_id_output"
}

_install_package_manager_pkg() {
    local pkg_name="$1"; local cmd_to_check="${2:-$pkg_name}"; local apt_pkg_name="${3:-$pkg_name}" 
    if ! _command_exists "$cmd_to_check"; then
        _print_warning "$cmd_to_check not installed."
        if _prompt_user_yes_no "Install ${BOLD}$apt_pkg_name${RESET} via apt?" "N"; then
            _print_msg "Installing ${BOLD}$apt_pkg_name${RESET}..."; local log_tmp=$(mktemp)
            if sudo apt update > "$log_tmp" 2>&1 && sudo apt install -y "$apt_pkg_name" >> "$log_tmp" 2>&1; then
                _print_msg "${BOLD}$apt_pkg_name${RESET} installed."; rm "$log_tmp"
            else _print_error "Failed to install ${BOLD}$apt_pkg_name${RESET}. See log."; cat "$log_tmp" >&2; rm "$log_tmp"; return 1; fi
        else _print_error "${BOLD}$cmd_to_check${RESET} required."; return 1; fi
    fi; _print_msg "${BOLD}$cmd_to_check${RESET} found."
}

_detect_gpu_and_set_cmake_args() {
    _print_info "Detecting GPU for llama-cpp-python..." >&2; local args=""
    if _command_exists nvidia-smi; then _print_msg "NVIDIA GPU detected." >&2
        if _prompt_user_yes_no "Build with ${BOLD}CUDA${RESET}?" "Y"; then args="-DGGML_CUDA=on"; fi
    elif _command_exists rocm-smi || _command_exists rocminfo; then _print_msg "AMD GPU detected." >&2
        if _prompt_user_yes_no "Build with ${BOLD}ROCm/HIP${RESET}?" "Y"; then args="-DGGML_HIPBLAS=on -DGGML_ROCM_NO_EVENT=on"; fi
    elif [[ "$(uname -s)" == "Darwin" ]] && system_profiler SPDisplaysDataType 2>/dev/null | grep -q "Metal Family: Supported"; then
        _print_msg "Apple Metal GPU detected." >&2
        if _prompt_user_yes_no "Build with ${BOLD}Metal${RESET}?" "Y"; then args="-DGGML_METAL=on"; fi
    else _print_warning "No known GPU detected." >&2; fi
    if [ -z "$args" ]; then _print_msg "Proceeding with ${BOLD}CPU-only${RESET} build." >&2; else _print_msg "CMAKE_ARGS for GPU: ${BOLD}$args${RESET}" >&2; fi
    echo "$args"
}

_update_env_file() {
    local env_file_path="$1"; local key_to_update="$2"; local new_value="$3"; local comment_char="#"
    local escaped_new_value=$(printf '%s\n' "$new_value" | sed -e 's/[\/&]/\\&/g' -e 's/$/\\/' -e '$s/\\$//')
    if grep -q "^\s*${comment_char}\?\s*${key_to_update}=" "$env_file_path"; then
        sed -i -E "s|^\s*${comment_char}?\s*(${key_to_update}=).*|\1\"${escaped_new_value}\"|" "$env_file_path"
    else echo "${key_to_update}=\"${new_value}\"" >> "$env_file_path"; fi
    _print_msg "Updated ${BOLD}$key_to_update${RESET} in ${BOLD}$env_file_path${RESET}"
}

main() {
    echo "" > "$INSTALL_LOG_FILE"; _print_msg "Welcome to AiCockpit (ACP) Backend Installer (v0.5.8)!"
    PROJECT_ROOT=$(pwd); _print_msg "Project root: ${BOLD}$PROJECT_ROOT${RESET}"
    for arg in "$@"; do if [[ "$arg" == "--quick" ]]; then QUICK_INSTALL=true; _print_info "Quick install activated." >&2; shift; fi; done
    local force_reinstall_deps=false; local reconfigure_env=false
    if [ -d "$VENV_DIR" ]; then _print_warning "Existing venv '${BOLD}$VENV_DIR${RESET}' detected." >&2
        if _prompt_user_yes_no "(${BOLD}U${RESET})pdate deps or (${BOLD}F${RESET})orce reinstall?" "U"; then
            if [[ $(echo "$REPLY" | tr '[:upper:]' '[:lower:]') == "f" ]]; then force_reinstall_deps=true; _print_info "Forcing reinstall." >&2;
            else _print_info "Will update deps." >&2; fi
        else _print_info "Skipping dep modification." >&2; fi
        if _prompt_user_yes_no "(${BOLD}R${RESET})econfigure .env paths?" "N"; then reconfigure_env=true; fi
    fi

    _print_section_header "Step 1: Checking System Prerequisites"
    _check_python_version; _install_package_manager_pkg "pip3" "pip3" "python3-pip";
    _install_package_manager_pkg "venv" "python3-venv" "python3-venv"; _install_package_manager_pkg "git";
    _install_package_manager_pkg "cmake"; _install_package_manager_pkg "g++" "g++ C++ compiler" "g++";
    if ! _command_exists jq; then _print_warning "jq not installed (recommended)." >&2
        if _prompt_user_yes_no "Install ${BOLD}jq${RESET} via apt?" "N"; then
            _print_msg "Installing ${BOLD}jq${RESET}..."; if sudo apt install -y jq; then _print_msg "${BOLD}jq${RESET} installed."; else _print_error "jq install failed."; fi
        fi; fi

    _print_section_header "Step 2: Setting up Python Virtual Environment"
    if [ "$force_reinstall_deps" = true ] && [ -d "$VENV_DIR" ]; then _print_warning "Force reinstall: Removing venv '${BOLD}$VENV_DIR${RESET}'." >&2; rm -rf "$VENV_DIR"; fi
    if [ ! -d "$VENV_DIR" ]; then _print_msg "Creating venv in '${BOLD}$VENV_DIR${RESET}'..." >&2; if ! python3 -m venv "$VENV_DIR"; then _print_error "Venv creation failed."; exit 1; fi; _print_msg "Venv created." >&2; fi
    _print_msg "Activating virtual environment..." >&2; source "$VENV_DIR/bin/activate" || { _print_error "Venv activation failed."; exit 1; }; SCRIPT_ACTIVATED_VENV=true

    _print_section_header "Step 3: Installing Project Dependencies with PDM"
    if ! _command_exists pdm; then _print_msg "PDM not found. Installing PDM..." >&2; if ! python -m pip install "pdm>=1.14"; then _print_error "PDM install failed."; exit 1; fi; fi
    _print_msg "PDM found: ${BOLD}$(pdm --version)${RESET}"
    LLAMA_CPP_CMAKE_ARGS=""; if [ "$force_reinstall_deps" = true ] || ! pdm list --graph | grep -q "llama-cpp-python"; then LLAMA_CPP_CMAKE_ARGS=$(_detect_gpu_and_set_cmake_args); else _print_info "llama-cpp-python seems installed." >&2; fi
    _print_msg "Installing/updating project dependencies..." >&2; _print_info "This may take time." >&2
    if ! env CMAKE_ARGS="$LLAMA_CPP_CMAKE_ARGS" pdm install --no-self; then _print_error "PDM install failed (GPU: ${BOLD}$LLAMA_CPP_CMAKE_ARGS${RESET})."
        if [ -n "$LLAMA_CPP_CMAKE_ARGS" ]; then _print_warning "GPU build failed." >&2; if _prompt_user_yes_no "Attempt ${BOLD}CPU-only${RESET} build?" "Y"; then if ! pdm install --no-self; then _print_error "CPU build failed."; exit 1; fi; else _print_error "Install aborted."; exit 1; fi; else _print_error "Install failed."; exit 1; fi; fi
    _print_msg "Project dependencies installed/updated."

    _print_section_header "Step 4: Configuring Environment (.env file)"
    if [ ! -f ".env" ]; then if [ -f "example.env" ]; then _print_msg "Copying example.env to .env..."; cp "example.env" ".env"; else _print_warning "example.env not found. Creating minimal .env."; touch ".env"; fi; reconfigure_env=true;
    elif [ "$reconfigure_env" = false ]; then _print_msg ".env file exists."; if ! _prompt_user_yes_no "Review/update .env paths?" "N"; then reconfigure_env=false; else reconfigure_env=true; fi; fi
    
    if [ "$reconfigure_env" = true ]; then
        _print_info "Provide paths for ACP directories. Press ${BOLD}Enter${RESET} for defaults." >&2
        PYTHON_IN_VENV="$VENV_DIR/bin/python"
        DEFAULT_MODELS_DIR=$($PYTHON_IN_VENV -c "from acp_backend.config import settings; print(settings.MODELS_DIR)")
        USER_MODELS_DIR=$(_prompt_user_input "Path for LLM MODELS_DIR (recursive search)" "$DEFAULT_MODELS_DIR")
        _update_env_file ".env" "MODELS_DIR" "$USER_MODELS_DIR"

        if [ -f "$DISCOVER_MODELS_SCRIPT" ]; then
            _print_info "Scanning LLM models in '${BOLD}$USER_MODELS_DIR${RESET}' (subdirs)..." >&2
            set +e
            DISCOVERY_RAW_OUTPUT=$(PDM_VERBOSITY=-1 ACP_MODELS_DIR_FOR_SCAN="$USER_MODELS_DIR" pdm run python "$DISCOVER_MODELS_SCRIPT" 2>&1)
            DISCOVERY_EXIT_CODE=$?
            set -e
            _log_to_file "Discovery exit: $DISCOVERY_EXIT_CODE. Output: $DISCOVERY_RAW_OUTPUT"
            echo -e "${YELLOW}DEBUG (Installer): Discovery exit: ${BOLD}$DISCOVERY_EXIT_CODE${RESET}. Output:\n$DISCOVERY_RAW_OUTPUT${RESET}" >&2

            if [ "$DISCOVERY_EXIT_CODE" -ne 0 ]; then
                _print_error "LLM model discovery script failed (Code: ${BOLD}$DISCOVERY_EXIT_CODE${RESET}). Check output/log.";
                _update_env_file ".env" "LLAMA_CPP_MODEL_PATH" ""
            else
                DISCOVERY_STATUS=$(echo "$DISCOVERY_RAW_OUTPUT" | grep -m 1 -E "^(MODELS_FOUND|NO_MODELS_FOUND|ERROR:)")
                JSON_MODELS=$(echo "$DISCOVERY_RAW_OUTPUT" | sed -n '/^---JSON_MODELS_START---/,/^---JSON_MODELS_END---/p' | sed '1d;$d')

                if [[ "$DISCOVERY_STATUS" == "MODELS_FOUND" ]]; then
                    _print_msg "Discovered LLM models:"
                    echo "$DISCOVERY_RAW_OUTPUT" | sed -n '/^MODELS_FOUND/,/^---JSON_MODELS_START---/p' | sed '1d;$d' | sed 's/^DEBUG: //; s/^  //' >&2 
                    if [ -n "$JSON_MODELS" ] && _command_exists jq; then
                        USER_DEFAULT_LLM_MODEL_ID=$(_prompt_model_selection "$JSON_MODELS") 
                        if [ -n "$USER_DEFAULT_LLM_MODEL_ID" ]; then
                            _print_info "Setting LLAMA_CPP_MODEL_PATH to: ${BOLD}$USER_DEFAULT_LLM_MODEL_ID${RESET}" >&2
                            _update_env_file ".env" "LLAMA_CPP_MODEL_PATH" "$USER_DEFAULT_LLM_MODEL_ID"
                        else _print_info "No default LLM model. Clearing LLAMA_CPP_MODEL_PATH." >&2; _update_env_file ".env" "LLAMA_CPP_MODEL_PATH" ""; fi
                    else _print_warning "jq not found or no JSON. Manual ID input." >&2
                        USER_DEFAULT_LLM_MODEL_ID=$(_prompt_user_input "Enter ID of default LLM (blank for none)" "")
                        _update_env_file ".env" "LLAMA_CPP_MODEL_PATH" "$USER_DEFAULT_LLM_MODEL_ID"; fi
                elif [[ "$DISCOVERY_STATUS" == "NO_MODELS_FOUND" ]]; then
                    _print_warning "No GGUF models found in '${BOLD}$USER_MODELS_DIR${RESET}'." >&2;
                    _update_env_file ".env" "LLAMA_CPP_MODEL_PATH" ""
                else _print_error "Model discovery unexpected status: '${BOLD}$DISCOVERY_STATUS${RESET}'. Check output/log."; _update_env_file ".env" "LLAMA_CPP_MODEL_PATH" ""; fi
            fi
        else _print_warning "Discovery script '${BOLD}$DISCOVER_MODELS_SCRIPT${RESET}' not found." >&2; fi

        DEFAULT_SESSIONS_DIR=$($PYTHON_IN_VENV -c "from acp_backend.config import settings; print(settings.WORK_SESSIONS_DIR)")
        DEFAULT_LOG_DIR=$($PYTHON_IN_VENV -c "from acp_backend.config import settings; print(settings.LOG_DIR)")
        DEFAULT_TEMP_DIR=$($PYTHON_IN_VENV -c "from acp_backend.config import settings; print(settings.TEMP_DIR)")
        DEFAULT_APP_PORT=$($PYTHON_IN_VENV -c "from acp_backend.config import settings; print(settings.APP_PORT)")
        USER_SESSIONS_DIR=$(_prompt_user_input "Path for WORK_SESSIONS_DIR" "$DEFAULT_SESSIONS_DIR")
        USER_LOG_DIR=$(_prompt_user_input "Path for LOG_DIR" "$DEFAULT_LOG_DIR")
        USER_TEMP_DIR=$(_prompt_user_input "Path for TEMP_DIR" "$DEFAULT_TEMP_DIR")
        USER_APP_PORT=$(_prompt_user_input "Port for the application server" "$DEFAULT_APP_PORT")
        _update_env_file ".env" "WORK_SESSIONS_DIR" "$USER_SESSIONS_DIR"
        _update_env_file ".env" "LOG_DIR" "$USER_LOG_DIR"
        _update_env_file ".env" "TEMP_DIR" "$USER_TEMP_DIR"
        _update_env_file ".env" "APP_PORT" "$USER_APP_PORT"
        _print_msg ".env file configured."; 
    else _print_msg "Skipping .env path reconfiguration."; fi

    _print_section_header "Step 5: Creating Application Directories"
    PYTHON_IN_VENV="$VENV_DIR/bin/python" # Ensure PYTHON_IN_VENV is defined here too
    MODELS_DIR_FINAL=$($PYTHON_IN_VENV -c "from acp_backend.config import settings; print(settings.MODELS_DIR)")
    SESSIONS_DIR_FINAL=$($PYTHON_IN_VENV -c "from acp_backend.config import settings; print(settings.WORK_SESSIONS_DIR)")
    LOG_DIR_FINAL=$($PYTHON_IN_VENV -c "from acp_backend.config import settings; print(settings.LOG_DIR)")
    TEMP_DIR_FINAL=$($PYTHON_IN_VENV -c "from acp_backend.config import settings; print(settings.TEMP_DIR)")
    GLOBAL_AGENTS_DIR_FINAL=$($PYTHON_IN_VENV -c "from acp_backend.config import settings; print(settings.get_global_agent_configs_path())")


    for dir_path_var_name in MODELS_DIR_FINAL SESSIONS_DIR_FINAL LOG_DIR_FINAL TEMP_DIR_FINAL GLOBAL_AGENTS_DIR_FINAL; do
        eval "local dir_path=\$$dir_path_var_name"
        if [ -n "$dir_path" ]; then if mkdir -p "$dir_path"; then _print_msg "Ensured dir: ${BOLD}$dir_path${RESET}"; else _print_error "Failed to create dir: ${BOLD}$dir_path${RESET}."; fi
        else _print_warning "Dir path for ${BOLD}$dir_path_var_name${RESET} not set." >&2; fi
    done

    echo; _print_msg "--- ${BOLD}AiCockpit (ACP) Backend Installation/Update Complete!${RESET} ---"
    _print_info "Log file: ${BOLD}$PROJECT_ROOT/$INSTALL_LOG_FILE${RESET}" >&2
    _print_info "To activate venv: ${BOLD}source $PROJECT_ROOT/$VENV_DIR/bin/activate${RESET}" >&2
    _print_info "Models dir: ${BOLD}$MODELS_DIR_FINAL${RESET}" >&2
    APP_PORT_FINAL=$($PYTHON_IN_VENV -c "from acp_backend.config import settings; print(settings.APP_PORT)")
    _print_info "To run app: ${BOLD}pdm run dev${RESET} (port 8000) or ${BOLD}python acp_backend/main.py${RESET} (port ${BOLD}$APP_PORT_FINAL${RESET})" >&2
    echo; _log_to_file "Installation script finished successfully."
}
main "$@"
