#!/bin/bash

# Git Auto Commit & Push Script
# Usage: ./git-auto.sh "Your commit message"

# Check if commit message is provided
if [ -z "$1" ]; then
    echo "Error: Please provide a commit message"
    echo "Usage: $0 \"Your commit message\""
    exit 1
fi

# Store the commit message
COMMIT_MESSAGE="$1"

echo "🔄 Starting Git workflow..."

# Add all changes
echo "📁 Adding all changes..."
git add .

# Check if there are any changes to commit
if git diff --cached --quiet; then
    echo "ℹ️  No changes to commit"
    exit 0
fi

# Commit with the provided message
echo "💾 Committing changes..."
git commit -m "$COMMIT_MESSAGE"

# Check if commit was successful
if [ $? -eq 0 ]; then
    echo "✅ Commit successful"
else
    echo "❌ Commit failed"
    exit 1
fi

# Push to remote repository
echo "🚀 Pushing to remote..."
git push

# Check if push was successful
if [ $? -eq 0 ]; then
    echo "✅ Push successful"
    echo "🎉 All done!"
else
    echo "❌ Push failed"
    exit 1
fi