import os
import subprocess
import sys

def main():
    # Determine the root directory
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Determine the Python executable in the virtual environment
    venv_dir = os.path.join(root_dir, 'venv')
    if os.name == 'nt':
        python_exe = os.path.join(venv_dir, 'Scripts', 'python.exe')
    else:
        python_exe = os.path.join(venv_dir, 'bin', 'python')
    
    # Check if the virtual environment exists
    if not os.path.exists(python_exe):
        print(f"Error: Virtual environment not found at {venv_dir}. Please run installer.py first.")
        sys.exit(1)
    
    # Determine the path to interface.py
    interface_script = os.path.join(root_dir, 'scripts', 'interface.py')
    if not os.path.exists(interface_script):
        print(f"Error: interface.py not found at {interface_script}.")
        sys.exit(1)
    
    # Launch the main application
    subprocess.run([python_exe, interface_script])

if __name__ == "__main__":
    main()