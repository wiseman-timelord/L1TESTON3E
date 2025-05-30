import os
import json
import subprocess
import sys
import time

def clear_screen():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    """Print a formatted header with the given title."""
    clear_screen()
    print("=" * 120)
    print(f"    {title}")
    print("=" * 120, "")

def main():
    """Main installation function with enhanced UI and validation."""
    # Installation header
    print_header("L1teSton3E - Installation")
    
    # Initialize installation tracking
    install_steps = []
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Step 1: Create data directory
    try:
        data_dir = os.path.join(root_dir, 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            install_steps.append(("Create data directory", "Pass", data_dir))
        else:
            install_steps.append(("Data directory exists", "Pass", data_dir))
    except Exception as e:
        install_steps.append(("Create data directory", "Fail", str(e)))
    
    # Step 2: Create persistent.json
    try:
        persistent_file = os.path.join(data_dir, 'persistent.json')
        if not os.path.exists(persistent_file):
            default_settings = {
                "window_width": 800,
                "window_height": 600,
                "default_font": "Arial",
                "default_font_size": 12
            }
            with open(persistent_file, 'w') as f:
                json.dump(default_settings, f, indent=2)
            install_steps.append(("Create persistent.json", "Pass", persistent_file))
        else:
            install_steps.append(("persistent.json exists", "Pass", persistent_file))
    except Exception as e:
        install_steps.append(("Create persistent.json", "Fail", str(e)))
    
    # Step 3: Create requirements.txt
    try:
        requirements_file = os.path.join(root_dir, 'requirements.txt')
        if not os.path.exists(requirements_file):
            with open(requirements_file, 'w') as f:
                f.write("PyQt5\n")
            install_steps.append(("Create requirements.txt", "Pass", requirements_file))
        else:
            install_steps.append(("requirements.txt exists", "Pass", requirements_file))
    except Exception as e:
        install_steps.append(("Create requirements.txt", "Fail", str(e)))
    
    # Step 4: Create virtual environment
    try:
        venv_dir = os.path.join(root_dir, 'venv')
        if not os.path.exists(venv_dir):
            subprocess.check_call([sys.executable, '-m', 'venv', venv_dir])
            install_steps.append(("Create virtual environment", "Pass", venv_dir))
        else:
            install_steps.append(("Virtual environment exists", "Pass", venv_dir))
    except Exception as e:
        install_steps.append(("Create virtual environment", "Fail", str(e)))
    
    # Step 5: Install requirements
    try:
        if os.path.exists(requirements_file):
            python_exe = os.path.join(venv_dir, 'Scripts', 'python.exe' if os.name == 'nt' else 'bin/python')
            subprocess.check_call([python_exe, '-m', 'pip', 'install', '-r', requirements_file])
            install_steps.append(("Install requirements", "Pass", requirements_file))
        else:
            install_steps.append(("Install requirements", "Fail", "requirements.txt not found"))
    except Exception as e:
        install_steps.append(("Install requirements", "Fail", str(e)))
    
    # Wait before showing results
    time.sleep(2)
    
    # Installation results header
    print_header("L1teSton3E - Install Result")
    
    # Print installation results
    for step, status, details in install_steps:
        print(f"{step}: {status} ({details})")
    
    # Determine overall result
    overall_status = "Pass"
    for step, status, _ in install_steps:
        if status == "Fail":
            overall_status = "Fail"
            break
    
    print(f"\nFinal Result: {overall_status}\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
    print("-" * 120)
    print("Press enter key to return to Batch Menu...")
    input()

if __name__ == "__main__":
    main()