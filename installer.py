import os
import json
import subprocess
import sys

def main():
    # Determine the root directory
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create data directory if it doesn't exist
    data_dir = os.path.join(root_dir, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory: {data_dir}")
    
    # Create persistent.json with default settings if it doesn't exist
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
        print(f"Created default settings file: {persistent_file}")
    
    # Create virtual environment if it doesn't exist
    venv_dir = os.path.join(root_dir, 'venv')
    if not os.path.exists(venv_dir):
        subprocess.check_call([sys.executable, '-m', 'venv', venv_dir])
        print(f"Created virtual environment: {venv_dir}")
    
    # Determine the Python executable in the virtual environment
    if os.name == 'nt':
        python_exe = os.path.join(venv_dir, 'Scripts', 'python.exe')
    else:
        python_exe = os.path.join(venv_dir, 'bin', 'python')
    
    # Install requirements from requirements.txt
    requirements_file = os.path.join(root_dir, 'requirements.txt')
    if os.path.exists(requirements_file):
        subprocess.check_call([python_exe, '-m', 'pip', 'install', '-r', requirements_file])
        print("Installed requirements from requirements.txt")
    else:
        print("Warning: requirements.txt not found. Skipping package installation.")
    
    print("Installation completed successfully.")

if __name__ == "__main__":
    main()