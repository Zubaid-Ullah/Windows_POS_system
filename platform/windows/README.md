# 🪟 Windows Build & Protection Guide

This directory contains everything needed to build a standalone Windows Executable (`.exe`).

> **Important**: You must run these steps on a **Windows** computer.

---

## 🚀 Steps to Build

### 1. Obfuscate Source Code
Run this command from the project root to protect your source code.
```powershell
python platform\windows\scripts\protect_windows_source.py
```

### 2. Package into .exe
This will create a single-file executable in the `windows_exe_dist` folder.
```powershell
python platform\windows\scripts\build_windows.py
```

---

## 📂 Directory Structure
- `scripts\`: Protection and build scripts.
- `windows_secured_dist\`: Output of the protection script.
- `windows_exe_dist\`: Contains the final standalone `FaqiriTechPOS.exe`.
- `windows_build_temp\`: PyInstaller temporary build cache.

## 🛠 Features
- **One-File**: Bundles everything into a single `.exe` for easy distribution.
- **Embedded Icons**: Includes the `logo.ico` automatically.
- **Dependencies**: Bundles `certifi`, `cryptography`, `opencv`, and `PIL`.
