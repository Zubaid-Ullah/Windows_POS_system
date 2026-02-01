import os
import shutil
import subprocess
import sys
from pathlib import Path

# Configuration
SOURCE_DIR = Path(__file__).parent.parent.parent.parent.absolute()
PLATFORM_DIR = Path(__file__).parent.parent.absolute()
DIST_DIR = PLATFORM_DIR / "windows_secured_dist"
TEMP_DIR = PLATFORM_DIR / "batch_temp_win"
BATCH_SIZE = 35 
MAX_FILE_SIZE = 31500

def print_step(msg):
    print(f"\n🪟 {msg}")

def get_pyarmor_cmd():
    bin_dir = Path(sys.executable).parent
    pyarmor_bin = bin_dir / "pyarmor"
    if pyarmor_bin.exists(): return str(pyarmor_bin)
    pyarmor_exe = bin_dir / "pyarmor.exe"
    if pyarmor_exe.exists(): return str(pyarmor_exe)
    return "pyarmor"

def scan_files():
    roots = ["src", "credentials", "main.py"]
    can_protect, too_large = [], []
    for root in roots:
        path = SOURCE_DIR / root
        targets = [path] if path.is_file() else list(path.rglob("*.py"))
        for p in targets:
            if not p.is_file() or "__pycache__" in str(p): continue
            rel = p.relative_to(SOURCE_DIR)
            (too_large if p.stat().st_size > MAX_FILE_SIZE else can_protect).append(str(rel))
    return sorted(can_protect), sorted(too_large)

def run_batch(num, files):
    print_step(f"Securing Batch {num} ({len(files)} files)...")
    if TEMP_DIR.exists(): shutil.rmtree(TEMP_DIR)
    TEMP_DIR.mkdir(parents=True)

    cmd = [get_pyarmor_cmd(), "gen", "-O", str(TEMP_DIR)] + files
    subprocess.check_call(cmd, cwd=str(SOURCE_DIR))

    print(f"   - Re-structuring Batch {num} result...")
    for rel_path in files:
        filename = os.path.basename(rel_path)
        src_file = TEMP_DIR / filename
        if src_file.exists():
            dst_file = DIST_DIR / rel_path
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)

    # Runtime copy
    runtime_src = TEMP_DIR / "pyarmor_runtime_000000"
    if runtime_src.exists():
        shutil.copytree(runtime_src, DIST_DIR / "pyarmor_runtime_000000", dirs_exist_ok=True)

def audit_security(protected, skipped):
    print_step("WINDOWS SHIELD AUDIT")
    pass_count = 0
    for rel in protected:
        secured = DIST_DIR / rel
        if secured.exists():
            try:
                with open(secured, "r", encoding="utf-8") as f:
                    if "pyarmor" in f.read(500).lower(): pass_count += 1
            except UnicodeDecodeError:
                pass_count += 1
    
    print(f"📁 Files Analyzed: {len(protected) + len(skipped)}")
    print(f"🛡️  Encrypted:  {pass_count}/{len(protected)}")
    print(f"📄 Skipped:    {len(skipped)} (Size > 32KB)")
    return pass_count == len(protected)

if __name__ == "__main__":
    try:
        # Pre-flight check: Verify PyArmor is installed
        pyarmor_cmd = get_pyarmor_cmd()
        try:
            result = subprocess.run([pyarmor_cmd, "--version"], 
                                   capture_output=True, 
                                   text=True, 
                                   timeout=5)
            if result.returncode != 0:
                raise FileNotFoundError()
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            print("\n❌ ERROR: PyArmor is not installed or not found in PATH!")
            print("\n📦 To fix this, run the following command in your virtual environment:")
            print("   pip install pyarmor")
            print("\nThen run this script again.")
            sys.exit(1)
        
        if DIST_DIR.exists(): shutil.rmtree(DIST_DIR)
        DIST_DIR.mkdir(parents=True)
        
        protect_list, skip_list = scan_files()
        print(f"🚀 Plan: Protect {len(protect_list)} files in batches.")
        
        for i in range(0, len(protect_list), BATCH_SIZE):
            run_batch((i // BATCH_SIZE) + 1, protect_list[i : i + BATCH_SIZE])
            
        for folder in ["Logo", "data", "locale", "credentials", "Keys", "Backup", "src"]:
            src, dst = SOURCE_DIR / folder, DIST_DIR / folder
            if src.exists(): shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns("*.py", "*.pyc"))
        for f in [".env", "README.md", "requirements.txt", "docker-compose.yml"]:
            if (SOURCE_DIR / f).exists(): shutil.copy2(SOURCE_DIR / f, DIST_DIR / f)
        for rel in skip_list:
            target = DIST_DIR / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SOURCE_DIR / rel, target)

        if not audit_security(protect_list, skip_list):
            print("\n❌ Error: Integrity Breach!")
            sys.exit(1)
        print("\n🛡️ WINDOWS PROTECTION COMPLETE.")
    except Exception as e:
        print(f"\n❌ Final Error: {e}")
        sys.exit(1)
    finally:
        if TEMP_DIR.exists(): shutil.rmtree(TEMP_DIR)
