# 🚀 POS System - Multi-Platform Build Guide

This project is structured to support clean, cross-platform builds for macOS, Windows, and Linux. Each platform has its own dedicated directory and instructions.

---

## 📂 Platform Specific Instructions

Please click on the link below for your specific operating system to see the detailed build steps:

- [🍎 **Build for macOS**](platform/macos/README.md)
  - Uses forward slashes (`/`)
  - Packages into a `.app` bundle.
  - Fixes Apple Silicon (M1/M2/M3) security permissions.

- [🪟 **Build for Windows**](platform/windows/README.md)
  - Uses backward slashes (`\`)
  - Packages into a single-file `.exe`.
  - Includes `logo.ico` embedding.

- [🐧 **Build for Linux**](platform/linux/README.md)
  - Uses forward slashes (`/`)
  - Packages into a standalone binary.

---

## 🏛 Directory Hierarchy

The project uses a strict separation between source code and build artifacts:

```text
platform/
├── macos/    --> Read platform/macos/README.md
├── windows/  --> Read platform/windows/README.md
└── linux/    --> Read platform/linux/README.md
```

## 🛡️ Security Note
All platforms use a **Source Protection** step before building. This obfuscates your Python code (making it unreadable) before it is packaged into the final executable. This ensures your intellectual property is safe.
