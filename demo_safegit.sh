#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# SafeGIT Demo Script - Shows context-aware git safety
#
# Author: Vaibhav-api-code
# Co-Author: Claude Code (https://claude.ai/code)
# Created: 2025-07-22
# Updated: 2025-07-23
# License: Mozilla Public License 2.0 (MPL-2.0)


echo "=== SafeGIT Context-Aware Demo ==="
echo

# Function to pause between demos
pause() {
    echo
    echo "Press Enter to continue..."
    read
}

# 1. Show default context
echo "1. Default context (development environment):"
python3 safegit.py show-context
pause

# 2. Safe operations in development
echo "2. Safe operations work normally in development:"
python3 safegit.py status | head -5
echo "✅ Status command passed through"
pause

# 3. Set production environment
echo "3. Setting environment to PRODUCTION:"
python3 safegit.py set-env production
pause

# 4. Try dangerous command in production
echo "4. Attempting 'git push --force' in production:"
echo "n" | python3 safegit.py push --force origin main 2>&1 | head -15
pause

# 5. Enable code freeze
echo "5. Enabling CODE FREEZE mode:"
python3 safegit.py set-mode code-freeze
pause

# 6. Try to commit during code freeze
echo "6. Attempting regular commit during code freeze:"
python3 safegit.py commit -m "new feature" 2>&1 | head -10
pause

# 7. Hotfix is allowed during code freeze
echo "7. Hotfix commits are allowed during code freeze:"
python3 safegit.py commit -m "[HOTFIX] Fix critical bug" --dry-run
pause

# 8. Add custom restriction
echo "8. Adding custom restriction pattern:"
python3 safegit.py add-restriction "merge.*feature"
pause

# 9. Show full context
echo "9. Current context with all restrictions:"
python3 safegit.py show-context
pause

# 10. Reset to development
echo "10. Resetting to safe development environment:"
python3 safegit.py set-env development
python3 safegit.py set-mode normal
python3 safegit.py remove-restriction "merge.*feature"
python3 safegit.py show-context

echo
echo "=== Demo Complete ==="
echo "SafeGIT provides context-aware protection to prevent git disasters!"