import subprocess
import sys
import shutil
from pathlib import Path

def build_executable():
    """Build executable using PyInstaller"""
    print("Building executable...")
    
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", "AgenticTestAutomation",
        "--add-data", "backend;backend",
        "--hidden-import", "uvicorn",
        "--hidden-import", "fastapi",
        "backend/main.py"
    ]
    
    subprocess.run(cmd)
    print("Executable built in dist/ folder")

def build_package():
    """Build Python package"""
    print("Building Python package...")
    subprocess.run([sys.executable, "-m", "build"])
    print("Package built in dist/ folder")

def clean():
    """Clean build artifacts"""
    paths_to_clean = ["build", "dist", "*.egg-info"]
    for path in paths_to_clean:
        for p in Path(".").glob(path):
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "exe":
            build_executable()
        elif sys.argv[1] == "package":
            build_package()
        elif sys.argv[1] == "clean":
            clean()
    else:
        print("Usage: python build.py [exe|package|clean]")