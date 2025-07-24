#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Configuration setup script for Code Intelligence Toolkit
#
# Author: Vaibhav-api-code
# Co-Author: Claude Code (https://claude.ai/code)
# Created: 2025-07-24
# Updated: 2025-07-24
# License: Mozilla Public License 2.0 (MPL-2.0)

echo "Code Intelligence Toolkit - Configuration Setup"
echo "=============================================="
echo ""

# Check if .pytoolsrc already exists
if [ -f ".pytoolsrc" ]; then
    echo "⚠️  .pytoolsrc already exists!"
    echo ""
    echo "Options:"
    echo "1) Keep existing configuration"
    echo "2) Backup existing and create new"
    echo "3) View existing configuration"
    echo ""
    read -p "Choose option (1-3): " choice
    
    case $choice in
        1)
            echo "Keeping existing configuration."
            exit 0
            ;;
        2)
            backup_name=".pytoolsrc.backup.$(date +%Y%m%d_%H%M%S)"
            mv .pytoolsrc "$backup_name"
            echo "Backed up existing config to: $backup_name"
            ;;
        3)
            echo ""
            echo "Current configuration:"
            echo "----------------------"
            head -50 .pytoolsrc
            echo ""
            echo "(Showing first 50 lines)"
            exit 0
            ;;
        *)
            echo "Invalid choice. Exiting."
            exit 1
            ;;
    esac
fi

# Detect environment
echo ""
echo "Detecting environment..."

if [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ] || [ -n "$GITLAB_CI" ]; then
    echo "✓ CI/CD environment detected"
    config_type="ci"
elif [ -n "$CONTAINER_ID" ] || [ -f /.dockerenv ]; then
    echo "✓ Container environment detected"
    config_type="ci"
else
    echo "✓ Development environment detected"
    config_type="dev"
fi

# Ask user preference
echo ""
echo "Configuration profiles available:"
echo "1) Development (interactive, safe defaults)"
echo "2) CI/CD (non-interactive, automation-friendly)"
echo "3) Custom (start with sample and customize)"
echo ""
read -p "Choose configuration type (1-3): " config_choice

case $config_choice in
    1)
        # Development config is already created as .pytoolsrc
        echo "✓ Creating development configuration..."
        echo "✓ Configuration created: .pytoolsrc"
        ;;
    2)
        # Use CI config
        if [ -f ".pytoolsrc.ci" ]; then
            cp .pytoolsrc.ci .pytoolsrc
            echo "✓ Created CI/CD configuration: .pytoolsrc"
        else
            echo "❌ .pytoolsrc.ci not found!"
            exit 1
        fi
        ;;
    3)
        # Use sample
        if [ -f ".pytoolsrc.sample" ]; then
            cp .pytoolsrc.sample .pytoolsrc
            echo "✓ Created configuration from sample: .pytoolsrc"
            echo ""
            echo "📝 Edit .pytoolsrc to customize your settings"
        else
            echo "❌ .pytoolsrc.sample not found!"
            exit 1
        fi
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

# Show quick tips
echo ""
echo "🚀 Quick Start Tips:"
echo "-------------------"
echo ""
echo "1. For temporary non-interactive mode:"
echo "   export SFM_ASSUME_YES=1"
echo "   export SAFEGIT_NONINTERACTIVE=1"
echo ""
echo "2. For different environments:"
echo "   export PYTOOLSRC=.pytoolsrc.ci    # Use CI config"
echo "   export PYTOOLSRC=.pytoolsrc.prod  # Use production config"
echo ""
echo "3. Test your configuration:"
echo "   ./run_any_python_tool.sh common_config.py --show"
echo ""
echo "4. Create tool-specific sections in .pytoolsrc:"
echo "   [your_tool_name]"
echo "   setting = value"
echo ""
echo "✅ Configuration setup complete!"