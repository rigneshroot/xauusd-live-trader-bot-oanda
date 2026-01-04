#!/bin/bash
###############################################################################
# Quick Git Push Script
# Commits and pushes all changes to GitHub
###############################################################################

echo "=========================================="
echo "📤 Git Push Helper"
echo "=========================================="
echo ""

# Check if in git repo
if [ ! -d ".git" ]; then
    echo "❌ Not a git repository. Run 'git init' first."
    exit 1
fi

# Check for changes
if git diff-index --quiet HEAD --; then
    echo "✅ No changes to commit"
    exit 0
fi

# Show status
echo "📋 Changed files:"
git status --short
echo ""

# Get commit message
read -p "Enter commit message: " message

if [ -z "$message" ]; then
    echo "❌ Commit message required"
    exit 1
fi

# Add all changes
echo ""
echo "➕ Adding files..."
git add .

# Verify config.py is not being committed
if git diff --cached --name-only | grep -q "config.py"; then
    echo "⚠️  WARNING: config.py is being committed!"
    echo "This should NOT happen. Check your .gitignore"
    exit 1
fi

# Commit
echo "💾 Committing..."
git commit -m "$message"

# Push
echo "📤 Pushing to GitHub..."
if git push; then
    echo ""
    echo "=========================================="
    echo "✅ Successfully pushed to GitHub!"
    echo "=========================================="
else
    echo ""
    echo "❌ Push failed. You may need to:"
    echo "1. Set up remote: git remote add origin <URL>"
    echo "2. Set upstream: git push -u origin main"
    echo "3. Pull first: git pull"
fi
