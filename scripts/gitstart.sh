#!/bin/bash
# sync-and-start.sh - Run this before starting work on either computer

echo "🔄 Syncing with GitHub before starting work..."

# Check current branch
current_branch=$(git branch --show-current)
echo "Current branch: $current_branch"

# Pull latest changes
git pull origin $current_branch

if [ $? -eq 0 ]; then
    echo "✅ Successfully synced with GitHub"
    echo "📝 You can now start making changes"
else
    echo "❌ Sync failed - check for conflicts"
    git status
fi