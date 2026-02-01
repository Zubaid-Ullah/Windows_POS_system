#!/bin/bash
# Remove sensitive files from git tracking (keeps local files)
# Run this script to clean up the repository before pushing

echo "=================================================="
echo "Git Repository Cleanup Script"
echo "=================================================="
echo ""
echo "This script will remove sensitive files from git tracking"
echo "while preserving your local copies."
echo ""

# Remove database files
echo "Removing database files from git tracking..."
git rm --cached *.db 2>/dev/null
git rm --cached data/pos_system.db 2>/dev/null
git rm --cached src/ui/views/pharmacy/pos_system.db 2>/dev/null
git rm --cached -r Backup/ 2>/dev/null

# Remove credentials
echo "Removing credentials from git tracking..."
git rm --cached credentials/.env 2>/dev/null
git rm --cached credentials/useraccount.txt 2>/dev/null

# Remove __pycache__ directories
echo "Removing __pycache__ directories from git tracking..."
find . -type d -name "__pycache__" -exec git rm -r --cached {} + 2>/dev/null

# Remove .DS_Store files
echo "Removing .DS_Store files from git tracking..."
find . -name ".DS_Store" -exec git rm --cached {} + 2>/dev/null

echo ""
echo "=================================================="
echo "Cleanup Complete!"
echo "=================================================="
echo ""
echo "Files have been removed from git tracking."
echo "Your local files are preserved."
echo ""
echo "Next steps:"
echo "1. Review changes: git status"
echo "2. Commit changes: git commit -m 'Remove sensitive files from tracking'"
echo "3. Push to remote: git push"
echo ""
echo "Note: After pushing, Windows users will need to:"
echo "- Copy credentials/.env.example to credentials/.env"
echo "- Add their own Supabase credentials"
echo ""
