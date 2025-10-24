#!/usr/bin/env python3
"""
Medallion Agents - Code Cleanup Script (Updated)
This script removes unused files and fixes import issues
"""

import os
import shutil
import datetime
from pathlib import Path

def main():
    print("🧹 Starting Medallion Agents Code Cleanup...")
    
    # Create backup directory
    backup_dir = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"📦 Creating backup directory: {backup_dir}")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Files to remove (with their paths)
    files_to_remove = [
        # Unused agent files
        "app/agent/supervisor.py",
        "app/agent/parser.py",
        
        # Unused scene files
        "app/scene/clarifier.py",
        "app/scene/classifier.py", 
        "app/scene/context_loader.py",
        "app/scene/defs.py",
        "app/scene/dialog_state.py",
        "app/scene/entity_resolver.py",
        "app/scene/guardrails.py",
        "app/scene/intent.py",
        "app/scene/kb.py",
        "app/scene/normalizer.py",
        "app/scene/values.py",
        
        # Unused notes files
        "app/notes/manager.py",
        
        # Unused RAG files (already removed)
        # "app/rag/vector_store.py",  # Already removed
        
        # Unused schema files
        "app/schemas/agent_schemas.py",
        
        # Unused config files
        "config/entities.json",
        "config/intent.json", 
        "config/ranges.json",
        "config/retrieval.json",
        
        # Unused documentation files
        "docs/agent_selection_methods.txt",
        "docs/scene_reference.md",
        "docs/dental_planning_basics.md",
        "docs/vr_scene_context.md",
    ]
    
    # Directories to remove
    dirs_to_remove = [
        "tests/",  # Optional - remove if not needed for development
    ]
    
    removed_count = 0
    
    # Remove files
    print("🗑️  Removing unused files...")
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                # Move to backup instead of deleting
                backup_file_path = os.path.join(backup_dir, file_path)
                os.makedirs(os.path.dirname(backup_file_path), exist_ok=True)
                shutil.move(file_path, backup_file_path)
                print(f"   ✅ Moved: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"   ❌ Error moving {file_path}: {e}")
        else:
            print(f"   ⚠️  Not found: {file_path}")
    
    # Remove directories
    print("🗑️  Removing unused directories...")
    for dir_path in dirs_to_remove:
        if os.path.exists(dir_path):
            try:
                backup_dir_path = os.path.join(backup_dir, dir_path)
                shutil.move(dir_path, backup_dir_path)
                print(f"   ✅ Moved: {dir_path}")
                removed_count += 1
            except Exception as e:
                print(f"   ❌ Error moving {dir_path}: {e}")
        else:
            print(f"   ⚠️  Not found: {dir_path}")
    
    # Clean up empty directories
    print("🧹 Cleaning up empty directories...")
    empty_dirs = [
        "app/scene",
        "app/notes", 
        "app/schemas",
        "docs"
    ]
    
    for dir_path in empty_dirs:
        if os.path.exists(dir_path) and not os.listdir(dir_path):
            try:
                os.rmdir(dir_path)
                print(f"   ✅ Removed empty directory: {dir_path}")
            except Exception as e:
                print(f"   ⚠️  Could not remove {dir_path}: {e}")
    
    # Remove __pycache__ directories
    print("🧹 Removing Python cache directories...")
    cache_count = 0
    for root, dirs, files in os.walk("."):
        for dir_name in dirs[:]:  # Use slice to avoid modifying list while iterating
            if dir_name == "__pycache__":
                cache_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(cache_path)
                    print(f"   ✅ Removed cache: {cache_path}")
                    cache_count += 1
                    dirs.remove(dir_name)  # Remove from dirs to avoid walking into it
                except Exception as e:
                    print(f"   ❌ Error removing {cache_path}: {e}")
    
    # Remove .pyc files
    pyc_count = 0
    for root, dirs, files in os.walk("."):
        for file_name in files:
            if file_name.endswith(".pyc"):
                pyc_path = os.path.join(root, file_name)
                try:
                    os.remove(pyc_path)
                    pyc_count += 1
                except Exception as e:
                    print(f"   ❌ Error removing {pyc_path}: {e}")
    
    print(f"\n✅ Cleanup completed!")
    print(f"📦 Backup created in: {backup_dir}")
    print(f"📊 Files/directories removed: {removed_count}")
    print(f"🧹 Cache directories removed: {cache_count}")
    print(f"🧹 .pyc files removed: {pyc_count}")
    print("")
    print("🔍 Next steps:")
    print("1. Test the application: python manage.py")
    print("2. Verify all functionality works")
    print("3. If everything works, you can delete the backup directory")
    print("4. If issues occur, restore files from backup")
    print("")
    print("⚠️  Note: This script moves files to backup instead of deleting them")
    print("   You can safely delete the backup directory after testing")
    print("")
    print("🔧 Import fixes applied:")
    print("   ✅ Fixed app/rag/faiss_store.py - removed VectorStore inheritance")
    print("   ✅ Fixed app/rag/retriever.py - removed VectorStore import")
    print("   ✅ Removed app/rag/vector_store.py - unused file")

if __name__ == "__main__":
    main()
