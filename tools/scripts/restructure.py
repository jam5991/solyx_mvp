#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def move_file(src, dst):
    if os.path.exists(src):
        ensure_dir(os.path.dirname(dst))
        shutil.move(src, dst)
        print(f"Moved: {src} → {dst}")
    else:
        print(f"Warning: Source file not found: {src}")

def update_imports(file_path):
    """Update imports in the specified file"""
    if not os.path.exists(file_path):
        print(f"Warning: Cannot update imports, file not found: {file_path}")
        return

    with open(file_path, 'r') as f:
        content = f.read()

    # Update imports to use drm_core package
    updates = {
        'from ..providers': 'from drm_core.providers',
        'from ..scheduler': 'from drm_core.scheduler',
        'from ..energy': 'from drm_core.energy',
        'from ..monitoring': 'from drm_core.monitoring',
        'from ..database': 'from drm_core.database',
    }

    for old, new in updates.items():
        content = content.replace(old, new)

    with open(file_path, 'w') as f:
        f.write(content)
    print(f"Updated imports in: {file_path}")

def main():
    # Project root directory
    root = Path(__file__).parent.parent.parent

    # Files to move to CMO service
    moves = [
        ("drm-core/src/main.py", "cmo-service/src/main.py"),
        ("drm-core/kubernetes/drm-deployment.yaml", 
         "cmo-service/kubernetes/cmo-deployment.yaml"),
        ("drm-core/src/check_env.py", "cmo-service/src/check_env.py"),
        ("drm-core/src/load_env.py", "cmo-service/src/load_env.py"),
    ]

    print("Starting restructure process...")
    
    # Execute moves
    for src, dst in moves:
        move_file(str(root / src), str(root / dst))

    # Update imports in moved files
    files_to_update = [
        "cmo-service/src/main.py",
        "cmo-service/src/check_env.py",
        "cmo-service/src/load_env.py",
    ]

    for file_path in files_to_update:
        update_imports(str(root / file_path))

    print("\nRestructure complete!")
    print("\nVerifying directory structure...")
    
    # Verify directories exist
    expected_dirs = [
        "drm-core/src/providers",
        "drm-core/src/energy",
        "drm-core/src/monitoring",
        "drm-core/src/database",
        "cmo-service/src/routes",
        "cmo-service/kubernetes",
    ]

    for dir_path in expected_dirs:
        full_path = root / dir_path
        if not full_path.exists():
            print(f"Warning: Expected directory not found: {dir_path}")
            ensure_dir(full_path)
        else:
            print(f"Verified: {dir_path}")

if __name__ == "__main__":
    main() 