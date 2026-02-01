import sys
import os
import subprocess
import platform
import time
import shutil

def run_command(cmd, shell=False, check=True):
    """Runs a shell command and returns output."""
    try:
        if shell:
            print(f"🔧 Executing: {cmd}")
        else:
            print(f"🔧 Executing: {' '.join(cmd)}")
        subprocess.run(cmd, shell=shell, check=check)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        return False
    except FileNotFoundError:
        return False

def install_system_dependency(program):
    """Auto-installs missing system tools using available package managers."""
    os_name = platform.system()
    print(f"⚠️  {program} is missing. Attempting auto-installation...")

    if os_name == "Darwin":  # MacOS
        if not shutil.which("brew"):
            print("❌ Homebrew not found. Installing Homebrew first...")
            run_command('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"', shell=True)
        
        if program == "docker":
            run_command(["brew", "install", "--cask", "docker"])
            print("⏳ Opening Docker Desktop to finish setup...")
            run_command(["open", "-a", "Docker"])
            print("⚠️  PLEASE WAIT for Docker to fully start, then run this script again.")
            sys.exit(0)
            
        elif program == "xquartz":
            print("🖥️  Installing XQuartz for GUI support...")
            run_command(["brew", "install", "--cask", "xquartz"])
            print("⚠️  XQuartz installed. You MUST Log Out and Log Back In for it to work.")
            sys.exit(0)
            
        elif program == "socat":
            run_command(["brew", "install", "socat"])

    elif os_name == "Windows":
        if not shutil.which("winget"):
            print("❌ winget not found. Please install Docker Desktop manually.")
            sys.exit(1)
            
        if program == "docker":
            run_command(["winget", "install", "Docker.DockerDesktop"])
            print("⚠️  Docker installed. Please restart your computer.")
            sys.exit(0)

def check_requirements():
    """Verifies Docker and X11 exist."""
    print("🔍 Checking System Environment...")
    
    # 1. Check Docker
    if not shutil.which("docker"):
        install_system_dependency("docker")
    
    # 2. Check GUI Support (Mac specific)
    if platform.system() == "Darwin":
        if not os.path.exists("/Applications/Utilities/XQuartz.app"):
            install_system_dependency("xquartz")
        
        if not shutil.which("socat"):
             # socat is often needed to bridge X11 sockets on modern Mac Docker setup
             install_system_dependency("socat")

def setup_mac_display():
    """Configures X11 forwarding for Mac."""
    print("📺 Configuring X11 Display...")
    
    # Try finding xhost
    xhost_cmd = "xhost"
    if not shutil.which("xhost"):
        if os.path.exists("/opt/X11/bin/xhost"):
            xhost_cmd = "/opt/X11/bin/xhost"
        else:
            print("⚠️  'xhost' command not found. You may need to Log Out and Log Back In to activate XQuartz.")
            print("    Alternatively, try running: export PATH=$PATH:/opt/X11/bin")
    
    # Check if XQuartz is running
    run_command("open -a XQuartz", shell=True, check=False)
    time.sleep(2) # Wait for XQuartz to launch
    
    # Initialize DISPLAY if missing
    if not os.environ.get("DISPLAY"):
        print("🔧 Setting default DISPLAY=:0")
        os.environ["DISPLAY"] = ":0"
    
    # Allow local connections
    # We pass the env with DISPLAY set
    if not run_command([xhost_cmd, "+localhost"], shell=False, check=False):
        print("⚠️  Failed to run xhost. GUI might not appear.")

    # Prepare socat for forwarding if needed (modern approach)
    # Using simple display var first
    return "host.docker.internal:0"

def run_container():
    print("\n🚀 Preparing to launch POS System in Docker...")
    
    check_requirements()
    
    # Build Image
    print("\n🔨 Building Docker Image (this may take a while first time)...")
    run_command(["docker", "build", "-t", "pos-system", "."])
    
    # Prepare Args
    os_name = platform.system()
    pwd = os.getcwd()
    data_vol = f"{pwd}/data:/app/data"
    
    docker_cmd = [
        "docker", "run", "-it", "--rm",
        "-v", data_vol,
        "--name", "pos_instance"
    ]
    
    if os_name == "Darwin":
        # Mac X11 Setup
        display = setup_mac_display()
        docker_cmd.extend(["-e", f"DISPLAY={display}"])
        docker_cmd.extend(["-v", "/tmp/.X11-unix:/tmp/.X11-unix"])
        
    elif os_name == "Windows":
        # Windows needs XServer (VcXsrv) assumed running at localhost:0.0
        print("⚠️  Ensure VcXsrv is running on Windows with 'Disable access control' checked.")
        docker_cmd.extend(["-e", "DISPLAY=host.docker.internal:0.0"])
    
    else:
        # Linux
        docker_cmd.extend(["-e", "DISPLAY=" + os.environ.get("DISPLAY", ":0")])
        docker_cmd.extend(["-v", "/tmp/.X11-unix:/tmp/.X11-unix"])

    docker_cmd.append("pos-system")
    
    print("\n▶️  Starting Container...")
    run_command(docker_cmd)

if __name__ == "__main__":
    try:
        run_container()
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
