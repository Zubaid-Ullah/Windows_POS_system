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
        print("❌ Run protect_windows_source.py first.")
        sys.exit(1)

    print_step("Building Windows EXE from Obfuscated Source...")
    print("ℹ️  Note: Windows system DLL warnings (e.g., ntdll.dll, bcrypt.dll) are normal and expected.")
    print("    These libraries are present on all Windows systems and don't need bundling.")
    
    icon_path = SECURED_DIR / "Logo" / "logo.ico"
    sep = ";"
    
    # Data arguments
    data_args = []
    
    # NOTE: Don't use --add-data for src directory - it needs to be importable
    # PyInstaller will auto-detect src when running from SECURED_DIR
    # But we add --paths to be explicit
    
    # Add src/ui/assets as data (non-Python files)
    src_assets = SECURED_DIR / "src" / "ui" / "assets"
    if src_assets.exists():
        data_args.append(f"--add-data={src_assets}{sep}src/ui/assets")
    
    runtime_dir = SECURED_DIR / "pyarmor_runtime_000000"
    if runtime_dir.exists():
        data_args.append(f"--add-data={runtime_dir}{sep}pyarmor_runtime_000000")

    items = ["Logo", "data", "locale", "credentials", "Keys", "Backup"]
    for item in items:
        if (SECURED_DIR / item).exists():
            data_args.append(f"--add-data={SECURED_DIR / item}{sep}{item}")

    cmd_base = PYINSTALLER_CMD.split() if " " in PYINSTALLER_CMD else [PYINSTALLER_CMD]
    cmd = cmd_base + [
        "--noconfirm",
        "--onefile",       # Windows users prefer onefile
        "--windowed",
        "--name", APP_NAME,
        "--distpath", str(FINAL_DIST_DIR),
        "--workpath", str(BUILD_TEMP_DIR),
        "--specpath", str(BUILD_TEMP_DIR),
        
        # Add SECURED_DIR to Python path so src can be imported
        "--paths", str(SECURED_DIR),
        
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
        
        # Collections for larger libraries that cause issues with --collect-all
        "--collect-submodules", "babel",
        "--collect-submodules", "pandas",
        "--collect-submodules", "numpy",
        "--collect-submodules", "googleapiclient",
        "--collect-submodules", "google",
        
        # Exclude test-only dependencies that cause bloat/errors
        "--exclude-module", "pytest",
        "--exclude-module", "pytest-runner",
        "--exclude-module", "grpc",

        *data_args
    ]
    
    if icon_path.exists(): cmd.extend(["--icon", str(icon_path)])
    cmd.append(str(SECURED_DIR / "main.py"))

    run_command(cmd, cwd=str(SECURED_DIR))

if __name__ == "__main__":
    if platform.system() != "Windows":
        print("⚠️ Warning: Running Windows build on non-Windows OS may fail or produce a non-functional EXE.")
    check_requirements()
    setup_dirs()
    build()
    print(f"\n✅ Windows Build Complete! EXE in: {FINAL_DIST_DIR}")
