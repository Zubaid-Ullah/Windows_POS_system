import sys
import platform
import psutil
import shutil
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk 
import os

# Note: This script requires 'psutil', 'pillow' and 'tk' (usually built-in)
# pip install psutil pillow

class CompatibilityChecker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("POS System Compatibility Check")
        self.root.geometry("500x400")
        
        self.logo_path = None
        self.results = []
        
        self.init_ui()
        
    def init_ui(self):
        # Header
        lbl_head = tk.Label(self.root, text="System Compatibility Checker", font=("Arial", 16, "bold"))
        lbl_head.pack(pady=10)
        
        # Logo Area
        self.logo_lbl = tk.Label(self.root, text="[No Logo Loaded]\nEnter path below and click Load", bg="lightgray", width=30, height=5)
        self.logo_lbl.pack(pady=10)
        
        # Logo path entry
        self.logo_entry = tk.Entry(self.root, width=40)
        self.logo_entry.insert(0, "Paste logo file path here...")
        self.logo_entry.pack(pady=5)
        
        btn_logo = tk.Button(self.root, text="Load Logo", command=self.load_logo)
        btn_logo.pack()
        
        # Check Button
        btn_check = tk.Button(self.root, text="Run System Check", command=self.run_checks, bg="green", fg="white", font=("Arial", 12))
        btn_check.pack(pady=20)
        
        # Output Area
        self.txt_output = tk.Text(self.root, height=10, width=50)
        self.txt_output.pack(pady=10)
        
    def load_logo(self):
        # Simple text input to avoid macOS Tkinter crash
        logo_path = self.logo_entry.get().strip()
        if logo_path and os.path.exists(logo_path):
            self.logo_path = logo_path
            try:
                # Resize for display
                img = Image.open(logo_path)
                img = img.resize((100, 100), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.logo_lbl.config(image=photo, text="", width=100, height=100)
                self.logo_lbl.image = photo # Keep reference
            except Exception as e:
                messagebox.showerror("Error", f"Could not load image: {e}")
        else:
            messagebox.showwarning("Invalid Path", "Please enter a valid image file path")

    def run_checks(self):
        self.results = []
        self.txt_output.delete(1.0, tk.END)
        os_name = platform.system()
        
        # 1. Check OS
        self.log(f"Operating System: {os_name} {platform.release()}")
        if os_name in ["Windows", "Darwin"]:
            self.log("✅ OS Compatible")
        else:
            self.log("⚠️ Warning: Linux support is experimental")
            
        # 2. Check RAM
        try:
            mem = psutil.virtual_memory()
            total_gb = round(mem.total / (1024**3), 2)
            self.log(f"RAM: {total_gb} GB")
            if total_gb >= 4:
                self.log("✅ RAM Sufficient (4GB+)")
            else:
                self.log("❌ Warning: Low RAM (Recommend 4GB+)")
        except:
            self.log("⚠️ Could not detect RAM")
            
        # 3. Check Disk Space
        try:
            total, used, free = shutil.disk_usage("/")
            free_gb = round(free / (1024**3), 2)
            self.log(f"Free Disk Space: {free_gb} GB")
            if free_gb > 1:
                self.log("✅ Disk Space Sufficient")
            else:
                self.log("❌ Error: Not enough disk space (Need 1GB+)")
        except:
            pass
            
        self.log("\n--- Conclusion ---")
        if "❌" in self.txt_output.get(1.0, tk.END):
            self.log("System may struggle to run the software.")
        else:
            self.log("System is fully compatible! You can install the POS software.")

    def log(self, msg):
        self.txt_output.insert(tk.END, msg + "\n")
        self.results.append(msg)

if __name__ == "__main__":
    app = CompatibilityChecker()
    app.root.mainloop()
