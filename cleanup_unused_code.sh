#!/bin/bash
# Medallion Agents - Code Cleanup Script
# This script removes unused files and code from the codebase

echo "🧹 Starting Medallion Agents Code Cleanup..."

# Create backup directory
echo "📦 Creating backup directory..."
mkdir -p backup_$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"

# Phase 1: Remove unused agent files
echo "🗑️  Removing unused agent files..."
mv app/agent/supervisor.py $BACKUP_DIR/ 2>/dev/null || echo "supervisor.py not found"
mv app/agent/parser.py $BACKUP_DIR/ 2>/dev/null || echo "parser.py not found"

# Phase 2: Remove unused scene files
echo "🗑️  Removing unused scene files..."
mv app/scene/clarifier.py $BACKUP_DIR/ 2>/dev/null || echo "clarifier.py not found"
mv app/scene/classifier.py $BACKUP_DIR/ 2>/dev/null || echo "classifier.py not found"
mv app/scene/context_loader.py $BACKUP_DIR/ 2>/dev/null || echo "context_loader.py not found"
mv app/scene/defs.py $BACKUP_DIR/ 2>/dev/null || echo "defs.py not found"
mv app/scene/dialog_state.py $BACKUP_DIR/ 2>/dev/null || echo "dialog_state.py not found"
mv app/scene/entity_resolver.py $BACKUP_DIR/ 2>/dev/null || echo "entity_resolver.py not found"
mv app/scene/guardrails.py $BACKUP_DIR/ 2>/dev/null || echo "guardrails.py not found"
mv app/scene/intent.py $BACKUP_DIR/ 2>/dev/null || echo "intent.py not found"
mv app/scene/kb.py $BACKUP_DIR/ 2>/dev/null || echo "kb.py not found"
mv app/scene/normalizer.py $BACKUP_DIR/ 2>/dev/null || echo "normalizer.py not found"
mv app/scene/values.py $BACKUP_DIR/ 2>/dev/null || echo "values.py not found"

# Phase 3: Remove unused notes files
echo "🗑️  Removing unused notes files..."
mv app/notes/manager.py $BACKUP_DIR/ 2>/dev/null || echo "manager.py not found"

# Phase 4: Remove unused RAG files
echo "🗑️  Removing unused RAG files..."
mv app/rag/vector_store.py $BACKUP_DIR/ 2>/dev/null || echo "vector_store.py not found"

# Phase 5: Remove unused schema files
echo "🗑️  Removing unused schema files..."
mv app/schemas/agent_schemas.py $BACKUP_DIR/ 2>/dev/null || echo "agent_schemas.py not found"

# Phase 6: Remove unused config files
echo "🗑️  Removing unused config files..."
mv config/entities.json $BACKUP_DIR/ 2>/dev/null || echo "entities.json not found"
mv config/intent.json $BACKUP_DIR/ 2>/dev/null || echo "intent.json not found"
mv config/ranges.json $BACKUP_DIR/ 2>/dev/null || echo "ranges.json not found"
mv config/retrieval.json $BACKUP_DIR/ 2>/dev/null || echo "retrieval.json not found"

# Phase 7: Remove unused documentation files
echo "🗑️  Removing unused documentation files..."
mv docs/agent_selection_methods.txt $BACKUP_DIR/ 2>/dev/null || echo "agent_selection_methods.txt not found"
mv docs/scene_reference.md $BACKUP_DIR/ 2>/dev/null || echo "scene_reference.md not found"
mv docs/dental_planning_basics.md $BACKUP_DIR/ 2>/dev/null || echo "dental_planning_basics.md not found"
mv docs/vr_scene_context.md $BACKUP_DIR/ 2>/dev/null || echo "vr_scene_context.md not found"

# Phase 8: Remove test directory (optional)
echo "🗑️  Removing test directory (optional)..."
mv tests/ $BACKUP_DIR/ 2>/dev/null || echo "tests/ not found"

# Phase 9: Clean up empty directories
echo "🧹 Cleaning up empty directories..."
find app/scene -type d -empty -delete 2>/dev/null || true
find app/notes -type d -empty -delete 2>/dev/null || true
find app/schemas -type d -empty -delete 2>/dev/null || true
find docs -type d -empty -delete 2>/dev/null || true

# Phase 10: Remove __pycache__ directories
echo "🧹 Removing Python cache directories..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

echo "✅ Cleanup completed!"
echo "📦 Backup created in: $BACKUP_DIR"
echo "📊 Files removed: $(ls -1 $BACKUP_DIR | wc -l)"
echo ""
echo "🔍 Next steps:"
echo "1. Test the application: python manage.py"
echo "2. Verify all functionality works"
echo "3. If everything works, you can delete the backup directory"
echo "4. If issues occur, restore files from backup"
