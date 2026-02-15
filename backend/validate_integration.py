"""
Integration Validator - Check if all components are properly integrated
STEP 3.3: Validates that Steps 3.1 and 3.2 are correctly installed
"""

import os
import sys

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"{Colors.GREEN}✅ {description}{Colors.RESET}")
        return True
    else:
        print(f"{Colors.RED}❌ {description} - NOT FOUND{Colors.RESET}")
        print(f"   Expected: {filepath}")
        return False

def check_import(module_path, description):
    """Check if a module can be imported"""
    try:
        __import__(module_path)
        print(f"{Colors.GREEN}✅ {description}{Colors.RESET}")
        return True
    except ImportError as e:
        print(f"{Colors.RED}❌ {description} - IMPORT ERROR{Colors.RESET}")
        print(f"   Error: {str(e)}")
        return False

def check_function_exists(module_path, function_name, description):
    """Check if a function exists in a module"""
    try:
        module = __import__(module_path, fromlist=[function_name])
        if hasattr(module, function_name):
            print(f"{Colors.GREEN}✅ {description}{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}❌ {description} - FUNCTION NOT FOUND{Colors.RESET}")
            return False
    except Exception as e:
        print(f"{Colors.RED}❌ {description} - ERROR{Colors.RESET}")
        print(f"   Error: {str(e)}")
        return False

def validate_backend():
    """Validate backend integration"""
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}BACKEND VALIDATION{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")
    
    checks = []
    
    # Step 3.1 Files
    print(f"{Colors.BOLD}Step 3.1 Files:{Colors.RESET}")
    checks.append(check_file_exists("backend/engines/__init__.py", "engines/__init__.py"))
    checks.append(check_file_exists("backend/engines/interruption_analyzer.py", "interruption_analyzer.py"))
    checks.append(check_file_exists("backend/engines/live_warning_generator.py", "live_warning_generator.py"))
    checks.append(check_file_exists("backend/prompts/interruption_prompts.py", "interruption_prompts.py"))
    
    # Step 3.2 Files
    print(f"\n{Colors.BOLD}Step 3.2 Files:{Colors.RESET}")
    checks.append(check_file_exists("backend/pressure_engine.py", "pressure_engine.py (updated)"))
    checks.append(check_file_exists("backend/pressure_modes.py", "pressure_modes.py (updated)"))
    checks.append(check_file_exists("backend/main.py", "main.py (updated)"))
    
    # Models (from Step 1 & 2)
    print(f"\n{Colors.BOLD}Data Models:{Colors.RESET}")
    checks.append(check_file_exists("backend/models/__init__.py", "models/__init__.py"))
    checks.append(check_file_exists("backend/models/interruption_models.py", "interruption_models.py"))
    
    # Imports
    print(f"\n{Colors.BOLD}Python Imports:{Colors.RESET}")
    
    # Add backend to path
    sys.path.insert(0, 'backend')
    
    checks.append(check_import("engines.interruption_analyzer", "interruption_analyzer import"))
    checks.append(check_import("engines.live_warning_generator", "live_warning_generator import"))
    checks.append(check_import("models.interruption_models", "interruption_models import"))
    
    # Functions
    print(f"\n{Colors.BOLD}Key Functions:{Colors.RESET}")
    checks.append(check_function_exists("engines.interruption_analyzer", "get_interruption_analyzer", "get_interruption_analyzer()"))
    checks.append(check_function_exists("engines.live_warning_generator", "get_warning_generator", "get_warning_generator()"))
    checks.append(check_function_exists("pressure_engine", "check_interruption_trigger", "check_interruption_trigger()"))
    
    return all(checks)

def validate_frontend():
    """Validate frontend integration"""
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}FRONTEND VALIDATION{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")
    
    checks = []
    
    # Step 3.1 Files
    print(f"{Colors.BOLD}Step 3.1 Files:{Colors.RESET}")
    checks.append(check_file_exists("frontend/src/utils/audioAnalyzer.js", "audioAnalyzer.js"))
    
    # Step 3.2 Files
    print(f"\n{Colors.BOLD}Step 3.2 Files:{Colors.RESET}")
    checks.append(check_file_exists("frontend/src/components/LiveWarning.js", "LiveWarning.js"))
    checks.append(check_file_exists("frontend/src/components/LiveWarning.css", "LiveWarning.css"))
    
    # AudioRecorder integration (manual check)
    print(f"\n{Colors.BOLD}AudioRecorder.js Integration (Manual Check):{Colors.RESET}")
    
    audiorecorder_path = "frontend/src/AudioRecorder.js"
    if os.path.exists(audiorecorder_path):
        with open(audiorecorder_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Check for key integrations
        has_analyzer_import = "audioAnalyzer" in content or "AudioAnalyzer" in content
        has_warning_import = "LiveWarning" in content
        has_analyzer_state = "audioAnalyzer" in content and "useState" in content
        has_warning_state = "liveWarning" in content and "useState" in content
        
        if has_analyzer_import:
            print(f"{Colors.GREEN}✅ AudioAnalyzer imported{Colors.RESET}")
            checks.append(True)
        else:
            print(f"{Colors.YELLOW}⚠️ AudioAnalyzer NOT imported (needs manual integration){Colors.RESET}")
            checks.append(False)
        
        if has_warning_import:
            print(f"{Colors.GREEN}✅ LiveWarning imported{Colors.RESET}")
            checks.append(True)
        else:
            print(f"{Colors.YELLOW}⚠️ LiveWarning NOT imported (needs manual integration){Colors.RESET}")
            checks.append(False)
        
        if has_analyzer_state:
            print(f"{Colors.GREEN}✅ AudioAnalyzer state exists{Colors.RESET}")
            checks.append(True)
        else:
            print(f"{Colors.YELLOW}⚠️ AudioAnalyzer state NOT found (needs manual integration){Colors.RESET}")
            checks.append(False)
        
        if has_warning_state:
            print(f"{Colors.GREEN}✅ LiveWarning state exists{Colors.RESET}")
            checks.append(True)
        else:
            print(f"{Colors.YELLOW}⚠️ LiveWarning state NOT found (needs manual integration){Colors.RESET}")
            checks.append(False)
    else:
        print(f"{Colors.RED}❌ AudioRecorder.js NOT FOUND{Colors.RESET}")
        checks.append(False)
    
    return all(checks)

def validate_configuration():
    """Validate configuration settings"""
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}CONFIGURATION VALIDATION{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")
    
    checks = []
    
    # Check config.py
    print(f"{Colors.BOLD}Backend Configuration:{Colors.RESET}")
    
    try:
        sys.path.insert(0, 'backend')
        import config
        
        if hasattr(config, 'ENABLE_INTERRUPTIONS'):
            enabled = config.ENABLE_INTERRUPTIONS
            if enabled:
                print(f"{Colors.GREEN}✅ ENABLE_INTERRUPTIONS = True{Colors.RESET}")
                checks.append(True)
            else:
                print(f"{Colors.YELLOW}⚠️ ENABLE_INTERRUPTIONS = False (interruptions disabled){Colors.RESET}")
                checks.append(True)  # Still valid, just disabled
        else:
            print(f"{Colors.RED}❌ ENABLE_INTERRUPTIONS not found in config{Colors.RESET}")
            checks.append(False)
    
    except ImportError:
        print(f"{Colors.RED}❌ config.py NOT FOUND{Colors.RESET}")
        checks.append(False)
    
    return all(checks)

def run_validation():
    """Run complete validation"""
    
    print(f"\n{Colors.BOLD}{'🔍' * 35}{Colors.RESET}")
    print(f"{Colors.BOLD} " * 8 + "INTEGRATION VALIDATOR - STEP 3{Colors.RESET}")
    print(f"{Colors.BOLD}{'🔍' * 35}{Colors.RESET}\n")
    
    # Change to project root if needed
    if os.path.exists("backend") and os.path.exists("frontend"):
        print(f"{Colors.GREEN}✅ Project root directory detected{Colors.RESET}\n")
    else:
        print(f"{Colors.YELLOW}⚠️ Warning: Run this from project root directory{Colors.RESET}")
        print(f"   Expected structure:")
        print(f"   project/")
        print(f"   ├── backend/")
        print(f"   └── frontend/\n")
    
    backend_valid = validate_backend()
    frontend_valid = validate_frontend()
    config_valid = validate_configuration()
    
    # Final Summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}VALIDATION SUMMARY{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")
    
    if backend_valid:
        print(f"{Colors.GREEN}✅ Backend: VALID{Colors.RESET}")
    else:
        print(f"{Colors.RED}❌ Backend: INVALID{Colors.RESET}")
    
    if frontend_valid:
        print(f"{Colors.GREEN}✅ Frontend: VALID{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}⚠️ Frontend: NEEDS MANUAL INTEGRATION{Colors.RESET}")
        print(f"   See: AudioRecorder_integration_guide.txt")
    
    if config_valid:
        print(f"{Colors.GREEN}✅ Configuration: VALID{Colors.RESET}")
    else:
        print(f"{Colors.RED}❌ Configuration: INVALID{Colors.RESET}")
    
    all_valid = backend_valid and frontend_valid and config_valid
    
    if all_valid:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL VALIDATIONS PASSED! 🎉{Colors.RESET}")
        print(f"\n{Colors.GREEN}Next steps:{Colors.RESET}")
        print(f"   1. Run backend tests: python test_intelligent_interruptions.py")
        print(f"   2. Start backend: python backend/main.py")
        print(f"   3. Start frontend: cd frontend && npm start")
        print(f"   4. Test in browser (see FRONTEND_TESTING_GUIDE.md)")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️ VALIDATION FAILED{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Fix the issues above, then run this script again.{Colors.RESET}")
        return False

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)