#!/usr/bin/env python3
"""
Folder Lock Tool with Admin Access
Cross-platform implementation with focus on Windows compatibility
"""

import os
import sys
import json
import shutil
import hashlib
import getpass
import argparse
from datetime import datetime
from pathlib import Path
import platform

class FolderLock:
    def __init__(self):
        # Set up paths
        self.script_dir = Path(__file__).parent.absolute()
        self.config_dir = self.script_dir / '.config'
        self.hidden_dir = self.config_dir / '.locked_data'
        
        # Create directories if they don't exist
        self.config_dir.mkdir(exist_ok=True)
        self.hidden_dir.mkdir(exist_ok=True)
        
        # Hide config directory on Windows
        if platform.system() == 'Windows':
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(
                str(self.config_dir), 
                ctypes.windll.kernel32.GetFileAttributesW(str(self.config_dir)) | 0x02
            )
        
        # Config files
        self.admin_hash_file = self.config_dir / 'admin_hash.json'
        self.user_hash_file = self.config_dir / 'user_hash.json'
        self.lock_status_file = self.config_dir / 'lock_status.json'
        
    def generate_salt(self):
        """Generate random salt for password hashing"""
        return os.urandom(32).hex()
    
    def hash_password(self, password, salt=None):
        """Hash password with salt"""
        if salt is None:
            salt = self.generate_salt()
        
        # Use PBKDF2 for secure password hashing
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        return {
            'salt': salt,
            'hash': hash_obj.hex()
        }
    
    def verify_password(self, password, stored_data):
        """Verify password against stored hash"""
        result = self.hash_password(password, stored_data['salt'])
        return result['hash'] == stored_data['hash']
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if platform.system() == 'Windows' else 'clear')
    
    def initial_setup(self):
        """Initial setup for the tool"""
        self.clear_screen()
        print("=== Folder Lock Tool Setup ===\n")
        
        # Check if already configured
        if self.admin_hash_file.exists():
            print("System already configured. Use --admin to change settings.")
            return False
        
        # Set admin password
        while True:
            admin_pass = getpass.getpass("Create admin password: ")
            admin_pass_confirm = getpass.getpass("Confirm admin password: ")
            
            if admin_pass != admin_pass_confirm:
                print("Passwords don't match. Try again.\n")
                continue
            
            if len(admin_pass) < 6:
                print("Password too short. Minimum 6 characters.\n")
                continue
            break
        
        # Set user password
        while True:
            user_pass = getpass.getpass("\nCreate user password: ")
            user_pass_confirm = getpass.getpass("Confirm user password: ")
            
            if user_pass != user_pass_confirm:
                print("Passwords don't match. Try again.\n")
                continue
            
            if len(user_pass) < 6:
                print("Password too short. Minimum 6 characters.\n")
                continue
            break
        
        # Save password hashes
        with open(self.admin_hash_file, 'w') as f:
            json.dump(self.hash_password(admin_pass), f)
        
        with open(self.user_hash_file, 'w') as f:
            json.dump(self.hash_password(user_pass), f)
        
        # Initialize lock status
        with open(self.lock_status_file, 'w') as f:
            json.dump({}, f)
        
        print("\n✓ Setup complete!")
        print("You can now use 'lock' and 'unlock' commands.")
        return True
    
    def authenticate_user(self):
        """Authenticate user with password"""
        if not self.user_hash_file.exists():
            print("Error: System not configured. Run --setup first.")
            return False
        
        with open(self.user_hash_file, 'r') as f:
            stored_hash = json.load(f)
        
        password = getpass.getpass("Enter user password: ")
        
        if self.verify_password(password, stored_hash):
            return True
        else:
            print("Authentication failed!")
            return False
    
    def authenticate_admin(self):
        """Authenticate admin with password"""
        if not self.admin_hash_file.exists():
            print("Error: System not configured. Run --setup first.")
            return False
        
        with open(self.admin_hash_file, 'r') as f:
            stored_hash = json.load(f)
        
        password = getpass.getpass("Enter admin password: ")
        
        if self.verify_password(password, stored_hash):
            print("✓ Admin mode activated\n")
            return True
        else:
            print("Admin authentication failed!")
            return False
    
    def lock_folder(self, folder_path):
        """Lock a folder by hiding its contents"""
        folder = Path(folder_path).absolute()
        
        # Validate input
        if not folder.exists():
            print(f"Error: Folder '{folder_path}' does not exist.")
            return False
        
        if not folder.is_dir():
            print(f"Error: '{folder_path}' is not a folder.")
            return False
        
        # Authenticate user
        if not self.authenticate_user():
            return False
        
        # Load lock status
        with open(self.lock_status_file, 'r') as f:
            lock_status = json.load(f)
        
        folder_str = str(folder)
        
        # Check if already locked
        if folder_str in lock_status:
            print("Error: Folder is already locked.")
            return False
        
        # Create hidden directory for this folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hidden_name = f"{folder.name}_{timestamp}"
        hidden_path = self.hidden_dir / hidden_name
        hidden_path.mkdir()
        
        # Move all contents to hidden location
        items_moved = 0
        for item in folder.iterdir():
            try:
                shutil.move(str(item), str(hidden_path))
                items_moved += 1
            except Exception as e:
                print(f"Warning: Could not move {item.name}: {e}")
        
        # Update lock status
        lock_status[folder_str] = {
            'hidden_path': str(hidden_path),
            'locked_at': datetime.now().isoformat(),
            'items_count': items_moved
        }
        
        with open(self.lock_status_file, 'w') as f:
            json.dump(lock_status, f, indent=2)
        
        print(f"✓ Folder '{folder_path}' has been locked successfully.")
        print(f"  {items_moved} items hidden.")
        return True
    
    def unlock_folder(self, folder_path):
        """Unlock a folder by restoring its contents"""
        folder = Path(folder_path).absolute()
        
        # Authenticate user
        if not self.authenticate_user():
            return False
        
        # Load lock status
        with open(self.lock_status_file, 'r') as f:
            lock_status = json.load(f)
        
        folder_str = str(folder)
        
        # Check if folder is locked
        if folder_str not in lock_status:
            print("Error: Folder is not locked.")
            return False
        
        # Get hidden path
        hidden_path = Path(lock_status[folder_str]['hidden_path'])
        
        if not hidden_path.exists():
            print("Error: Hidden data not found. The folder might have been corrupted.")
            return False
        
        # Create folder if it doesn't exist
        folder.mkdir(exist_ok=True)
        
        # Restore contents
        items_restored = 0
        for item in hidden_path.iterdir():
            try:
                shutil.move(str(item), str(folder))
                items_restored += 1
            except Exception as e:
                print(f"Warning: Could not restore {item.name}: {e}")
        
        # Remove hidden directory
        try:
            hidden_path.rmdir()
        except:
            pass
        
        # Remove from lock status
        del lock_status[folder_str]
        
        with open(self.lock_status_file, 'w') as f:
            json.dump(lock_status, f, indent=2)
        
        print(f"✓ Folder '{folder_path}' has been unlocked successfully.")
        print(f"  {items_restored} items restored.")
        return True
    
    def change_user_password(self):
        """Change user password (admin function)"""
        print("=== Change User Password ===")
        
        while True:
            new_pass = getpass.getpass("Enter new user password: ")
            new_pass_confirm = getpass.getpass("Confirm new user password: ")
            
            if new_pass != new_pass_confirm:
                print("Passwords don't match. Try again.\n")
                continue
            
            if len(new_pass) < 6:
                print("Password too short. Minimum 6 characters.\n")
                continue
            break
        
        # Save new password hash
        with open(self.user_hash_file, 'w') as f:
            json.dump(self.hash_password(new_pass), f)
        
        print("✓ User password changed successfully.")
    
    def change_admin_password(self):
        """Change admin password"""
        print("=== Change Admin Password ===")
        
        while True:
            new_pass = getpass.getpass("Enter new admin password: ")
            new_pass_confirm = getpass.getpass("Confirm new admin password: ")
            
            if new_pass != new_pass_confirm:
                print("Passwords don't match. Try again.\n")
                continue
            
            if len(new_pass) < 6:
                print("Password too short. Minimum 6 characters.\n")
                continue
            break
        
        # Save new password hash
        with open(self.admin_hash_file, 'w') as f:
            json.dump(self.hash_password(new_pass), f)
        
        print("✓ Admin password changed successfully.")
    
    def show_lock_status(self):
        """Show all locked folders"""
        print("=== Locked Folders Status ===\n")
        
        with open(self.lock_status_file, 'r') as f:
            lock_status = json.load(f)
        
        if not lock_status:
            print("No folders are currently locked.")
            return
        
        print(f"{'Folder Path':<50} {'Locked At':<20} {'Items':<10}")
        print("-" * 80)
        
        for folder, info in lock_status.items():
            locked_at = datetime.fromisoformat(info['locked_at']).strftime("%Y-%m-%d %H:%M")
            items = info['items_count']
            
            # Truncate long paths for display
            display_path = folder
            if len(display_path) > 47:
                display_path = "..." + display_path[-44:]
            
            print(f"{display_path:<50} {locked_at:<20} {items:<10}")
    
    def unlock_all_folders(self):
        """Emergency unlock all folders"""
        print("=== Emergency Unlock All ===")
        print("This will unlock ALL locked folders.")
        
        confirmation = input("Are you sure? (yes/no): ")
        if confirmation.lower() != 'yes':
            print("Operation cancelled.")
            return
        
        with open(self.lock_status_file, 'r') as f:
            lock_status = json.load(f)
        
        unlocked_count = 0
        for folder_str, info in lock_status.copy().items():
            try:
                folder = Path(folder_str)
                hidden_path = Path(info['hidden_path'])
                
                if hidden_path.exists():
                    folder.mkdir(exist_ok=True)
                    
                    for item in hidden_path.iterdir():
                        shutil.move(str(item), str(folder))
                    
                    hidden_path.rmdir()
                
                del lock_status[folder_str]
                unlocked_count += 1
                print(f"Unlocked: {folder_str}")
            except Exception as e:
                print(f"Error unlocking {folder_str}: {e}")
        
        with open(self.lock_status_file, 'w') as f:
            json.dump(lock_status, f, indent=2)
        
        print(f"\n✓ {unlocked_count} folders unlocked.")
    
    def admin_mode(self, args):
        """Handle admin mode commands"""
        if not self.authenticate_admin():
            return
        
        if args.admin_command == 'change-pass':
            self.change_user_password()
        elif args.admin_command == 'change-admin':
            self.change_admin_password()
        elif args.admin_command == 'status':
            self.show_lock_status()
        elif args.admin_command == 'unlock-all':
            self.unlock_all_folders()
        else:
            print("Available admin commands:")
            print("  change-pass    - Change user password")
            print("  change-admin   - Change admin password")
            print("  status        - Show all locked folders")
            print("  unlock-all    - Emergency unlock all folders")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Folder Lock Tool - Secure folder locking with admin access',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    subparsers.add_parser('setup', help='Initial setup (first time only)')
    
    # Lock command
    lock_parser = subparsers.add_parser('lock', help='Lock a folder')
    lock_parser.add_argument('folder', help='Folder path to lock')
    
    # Unlock command
    unlock_parser = subparsers.add_parser('unlock', help='Unlock a folder')
    unlock_parser.add_argument('folder', help='Folder path to unlock')
    
    # Admin command
    admin_parser = subparsers.add_parser('admin', help='Admin mode')
    admin_parser.add_argument(
        'admin_command',
        nargs='?',
        choices=['change-pass', 'change-admin', 'status', 'unlock-all'],
        help='Admin command to execute'
    )
    
    args = parser.parse_args()
    
    # Create FolderLock instance
    fl = FolderLock()
    
    # Execute commands
    if args.command == 'setup':
        fl.initial_setup()
    elif args.command == 'lock':
        fl.lock_folder(args.folder)
    elif args.command == 'unlock':
        fl.unlock_folder(args.folder)
    elif args.command == 'admin':
        fl.admin_mode(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
