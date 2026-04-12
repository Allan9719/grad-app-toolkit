import json
import os
import shutil
from datetime import datetime

MEMORY_FILE = "candidate_memory.json"
BACKUP_DIR = ".memory_backups"

def initialize_memory(template_path="assets/memory_schema.json"):
    """Initialize memory from template if it doesn't exist."""
    print("Initiating Memory Manager...")
    if not os.path.exists(MEMORY_FILE):
        if not os.path.exists(template_path):
            print(f"Error: Template {template_path} not found.")
            return False
            
        shutil.copy(template_path, MEMORY_FILE)
        print(f"Created {MEMORY_FILE} from template.")
        return True
    
    print(f"{MEMORY_FILE} already exists.")
    return True

def create_backup():
    """Create a timestamped backup of the current memory to prevent corruption."""
    if not os.path.exists(MEMORY_FILE):
        print("No memory file to backup.")
        return False
        
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"memory_backup_{timestamp}.json")
    
    shutil.copy(MEMORY_FILE, backup_path)
    print(f"Backup saved to: {backup_path}")
    return backup_path

def read_state():
    """Read the current state safely."""
    if not os.path.exists(MEMORY_FILE):
        print("Memory file not found. Initialize first.")
        return None
        
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            state = json.load(f)
        return state
    except json.JSONDecodeError as e:
        print(f"CRITICAL ERROR: Memory corrupted! JSON decode failed: {e}")
        print("Action required: Restore from .memory_backups folder.")
        return None

def update_field(keys_path, value):
    """
    Update a specific field dynamically.
    keys_path should be a list of keys, e.g. ['static_profile', 'GPA']
    """
    state = read_state()
    if state is None:
        return False
        
    # Create backup before mutation
    create_backup()
    
    current = state
    for key in keys_path[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
        
    current[keys_path[-1]] = value
    
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=4, ensure_ascii=False)
        
    print(f"Successfully updated {' -> '.join(keys_path)}")
    return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "init":
            template = sys.argv[2] if len(sys.argv) > 2 else "assets/memory_schema.json"
            initialize_memory(template)
            
        elif command == "backup":
            create_backup()
            
        elif command == "read":
            state = read_state()
            if state:
                print(json.dumps(state, indent=2, ensure_ascii=False))
                
        else:
            print("Usage: python memory_manager.py [init|backup|read]")
    else:
        print("No command provided. Exiting.")
