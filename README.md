# Folder Lock 🔐

A Python-based folder locking tool for Windows that helps hide or protect folders from unauthorized access.

## Features
- Lock and unlock folders
- Simple command-line interface
- Lightweight and fast

## Requirements
- Python 3.10+

Requirements File (requirements.txt)
# No external dependencies required!
# This tool uses only Python standard library

Installation and Usage
1. Installation
# Create project directory
mkdir folder-lock
cd folder-lock

# Create the Python file
# Copy the code above into folder_lock.py
# Make it executable (optional on Windows)
# On Windows, Python files are automatically executable

2. Initial Setup
# Run initial setup
python folder_lock.py setup
# Or if python3 is required
python3 folder_lock.py setup

3. Basic Usage
# Lock a folder
python folder_lock.py lock "C:\Users\YourName\Documents\SecretFolder"
# Unlock a folder
python folder_lock.py unlock
"C:\Users\YourName\Documents\SecretFolder"
# Lock with relative path
python folder_lock.py lock MyFolder

4. Admin Operations
# Change user password
python folder_lock.py admin change-pass
# View all locked folders
python folder_lock.py admin status
# Emergency unlock all
python folder_lock.py admin unlock-all
# Change admin password
python folder_lock.py admin change-admin

Features
Windows-Specific Optimizations:
• Works in Command Prompt, PowerShell, and Windows Terminal
• Handles Windows paths (with spaces and special characters)
• Hides config directory using Windows file attributes
• No external dependencies needed
Security Features:
• PBKDF2 password hashing with salt
• 100,000 iterations for brute-force protection
• Hidden configuration directory
• Secure password input (no echo)
User-Friendly:
• Clear error messages
• Progress feedback
• Colorful output support (if terminal supports it)
• Works with both absolute and relative paths




