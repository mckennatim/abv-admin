#!/bin/bash
# commit-and-push.sh - Run this after making changes

echo "💾 Committing and pushing changes to GitHub..."

# Check if there are any changes
if [[ -z $(git status -s) ]]; then
    echo "No changes to commit"
    exit 0
fi

# Show what's changed
echo "📋 Changes to be committed:"
git status --short

# Get commit message from user
read -p "Enter commit message: " commit_msg

if [ -z "$commit_msg" ]; then
    echo "❌ Commit message required"
    exit 1
fi

# Add all changes
git add .

# Commit with message
git commit -m "$commit_msg"
git tag ${commit_msg}

# Push to GitHub
current_branch=$(git branch --show-current)
git push origin $current_branch
git push origin --tags

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to GitHub"
    echo "🔄 Other computer can now pull these changes"
else
    echo "❌ Push failed - check for conflicts"
    git status
fi