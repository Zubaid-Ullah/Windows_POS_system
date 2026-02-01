import os
import subprocess
import shutil
import platform
import sys
from pathlib import Path

# Configuration - Root is up 3 levels
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.absolute()
PLATFORM_DIR = Path(__file__).parent.parent.absolute()
SECURED_DIR = PLATFORM_DIR / "windows_secured_dist"
BUILD_TEMP_DIR = PLATFORM_DIR / "windows_build_temp"
FINAL_DIST_DIR = PLATFORM_DIR / "windows_exe_dist"
APP_NAME = "AfexPOS"

def print_step(msg):
    print(f"\n🪟 {msg}")

def run_command(cmd, cwd=None, env=None):
    print(f"Executing: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd, cwd=cwd, env=env)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

PYINSTALLER_CMD = "pyinstaller"

def check_requirements():
    global PYINSTALLER_CMD
    print_step("Checking prerequisites...")
    try:
        subprocess.check_call(["pyinstaller", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        PYINSTALLER_CMD = "pyinstaller"
    except:
        bin_dir = Path(sys.executable).parent
        pyi_bin = bin_dir / ("pyinstaller.exe" if os.name == 'nt' else "pyinstaller")
        if pyi_bin.exists():
            PYINSTALLER_CMD = str(pyi_bin)
        else:
            run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])
            PYINSTALLER_CMD = f"{sys.executable} -m PyInstaller"

def setup_dirs():
    print_step("Cleaning build environment...")
    for d in [BUILD_TEMP_DIR, FINAL_DIST_DIR]:
        if d.exists(): shutil.rmtree(d)
        d.mkdir(parents=True)

def build():
    if not SECURED_DIR.exists():
        print(f"❌ Secured source not found at: {SECURED_DIR}")
        print("   Run protect_windows_source.py first.")
        sys.exit(1)

    print_step("Building Windows EXE from Obfuscated Source...")
    
    icon_path = SECURED_DIR / "Logo" / "logo.ico"
    sep = ";" # Windows specific separator for --add-data
    
    # Dynamic Data Collection
    data_args = []
    # Directories to potentially skip from --add-data
    skip_dirs = ["__pycache__", "windows_build_temp", "windows_exe_dist", "windows_secured_dist", ".git", ".venv", ".idea"]
    
    print("🔍 Collecting assets dynamically...")
    for item in SECURED_DIR.iterdir():
        if item.is_dir() and item.name not in skip_dirs:
            # We add EVERYTHING in these folders as data (Logo, data, credentials, src, etc.)
            # PyInstaller handles overlapping code/data.
            data_args.append(f"--add-data={item}{sep}{item.name}")
            print(f"   + Added directory: {item.name}")
        elif item.is_file() and item.name in [".env", "README.md", "SystemCheck.json"]:
            data_args.append(f"--add-data={item}{sep}.")
            print(f"   + Added file: {item.name}")

    cmd_base = PYINSTALLER_CMD.split() if " " in PYINSTALLER_CMD else [PYINSTALLER_CMD]
    cmd = cmd_base + [
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", APP_NAME,
        "--distpath", str(FINAL_DIST_DIR),
        "--workpath", str(BUILD_TEMP_DIR),
        "--specpath", str(BUILD_TEMP_DIR),
        
        # Add SECURED_DIR to paths so PyInstaller can find 'src' and other packages
        "--paths", str(SECURED_DIR),
        
        # Heavy collections
        "--collect-all", "certifi",
        "--collect-all", "cryptography",
        "--collect-all", "cv2",
        "--collect-all", "PIL",
        "--collect-all", "PyQt6",
        "--collect-all", "reportlab",
        "--collect-all", "qtawesome",
        "--collect-all", "bcrypt",
        "--collect-all", "supabase",
        "--collect-all", "requests",
        "--collect-all", "barcode",
        "--collect-all", "psutil",
        "--collect-all", "dotenv",
        "--collect-all", "machineid",
        "--collect-all", "qtpy",
        "--collect-all", "dateutil",
        "--collect-all", "openpyxl",
        "--collect-all", "qrcode",
        
        # Module specific sub-collections
        "--collect-submodules", "babel",
        "--collect-submodules", "pandas",
        "--collect-submodules", "numpy",
        "--collect-submodules", "googleapiclient",
        "--collect-submodules", "google",
        "--collect-submodules", "grpc",
        
        # Hidden imports for common dynamic logic
        "--hidden-import", "sqlite3",
        "--hidden-import", "json",
        "--hidden-import", "uuid",
        
        # Exclude test-only dependencies
        "--exclude-module", "pytest",
        "--exclude-module", "pytest-runner",

        *data_args
    ]
    
    if icon_path.exists(): 
        cmd.extend(["--icon", str(icon_path)])
    
    # Entry point
    cmd.append(str(SECURED_DIR / "main.py"))

    print("\n🚀 Starting PyInstaller Build...")
    run_command(cmd, cwd=str(SECURED_DIR))

if __name__ == "__main__":
    if platform.system() != "Windows":
        print("⚠️ Warning: Running Windows build on non-Windows OS may fail or produce a non-functional EXE.")
    check_requirements()
    setup_dirs()
    build()
    print(f"\n✅ Windows Build Complete! EXE in: {FINAL_DIST_DIR}")
