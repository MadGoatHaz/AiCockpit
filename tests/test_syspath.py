import sys
import os

def test_print_sys_path():
    print("\n--- sys.path ---")
    for p in sys.path:
        print(p)
    print("--- end sys.path ---")
    
    print("\n--- CWD ---")
    print(os.getcwd())
    print("--- end CWD ---")
    
    # Try the problematic import directly here
    try:
        from acp_backend.core.session_handler import SessionHandler
        print("\nSuccessfully imported SessionHandler in test_syspath.py")
    except ImportError as e:
        print(f"\nFailed to import SessionHandler in test_syspath.py: {e}")
        # Let's also check if acp_backend itself is found
        try:
            import acp_backend
            print("Successfully imported acp_backend package")
            print(f"acp_backend path: {acp_backend.__path__}") # type: ignore
            # Check if core is accessible
            import acp_backend.core
            print("Successfully imported acp_backend.core package")
            print(f"acp_backend.core path: {acp_backend.core.__path__}") # type: ignore
            # Check if session_handler module is accessible
            import acp_backend.core.session_handler as sh_module
            print("Successfully imported acp_backend.core.session_handler module")
            print(f"SessionHandler in sh_module: {hasattr(sh_module, 'SessionHandler')}")

        except ImportError as ie:
            print(f"Further import error: {ie}")

    assert True # This test is just for printing
