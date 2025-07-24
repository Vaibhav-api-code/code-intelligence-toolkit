<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

File and Directory Tools Help Documentation

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-20
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# File and Directory Tools Help Documentation

**Related Code Files:**
- `smart_ls.py` - Enhanced directory listing with advanced filtering
- `tree_view.py` - Directory tree visualization with statistics
- `dir_stats.py` - Comprehensive directory analysis and statistics
- `recent_files_v2.py` - Find and track recently modified files
- `safe_move.py` - Safe file operations with undo capability
- `organize_files.py` - Automatic file organization with rules
- `refactor_rename.py` - Code-aware file and symbol renaming

---

## Overview

This document provides comprehensive help documentation for all file and directory management tools in the code-intelligence-toolkit. These tools offer enhanced functionality beyond basic Unix commands, with features like advanced filtering, statistics, undo capability, and code-aware operations.

## smart_ls.py - Enhanced Directory Listing

### Basic Usage
```bash
python3 smart_ls.py [path] [options]
```

### Key Features
- 🎨 Colorized output with icons for different file types
- 📊 Multiple sort options (name, size, time, extension)
- 🔍 Advanced filtering by pattern, extension, size
- 📈 Summary statistics and grid display
- 🔄 Recursive directory traversal with depth control

### Options
```
positional arguments:
  path                  Directory path (default: current directory)

options:
  -h, --help            show this help message and exit
  -l, --long            Long format with details
  -a, --all             Show hidden files
  --sort {name,size,time,ext}
                        Sort order
  --include, --glob, -g GLOB
                        Include files matching pattern
  --exclude EXCLUDE     Exclude files matching pattern
  --type {f,d,l,all}    File type filter
  -r, --recursive       Recurse into subdirectories
  --max-depth MAX_DEPTH
                        Maximum recursion depth
  --ext EXT             Filter by file extension
  --limit, --max LIMIT  Limit number of results
  -v, --verbose         Enable verbose output
  -q, --quiet           Minimal output
  --json                Output in JSON format
  --dry-run             Preview changes without applying
  --summary             Show summary statistics
  --pattern PATTERN     Filter by filename pattern (e.g., "*.py")
  --dirs-only           Show only directories
  --files-only          Show only files
  --min-size MIN_SIZE   Minimum file size (e.g., "1MB")
  --max-size MAX_SIZE   Maximum file size (e.g., "100KB")
  --reverse             Reverse sort order
  --grid                Display in grid format
```

### Usage Examples
```bash
# Basic listing with details
python3 smart_ls.py -l

# Show only Python files sorted by size
python3 smart_ls.py --ext py --sort size

# Recursive search with pattern
python3 smart_ls.py -r --include "*.java" --max-depth 3

# Show large files with size limits
python3 smart_ls.py --min-size 1MB --sort size --reverse

# Grid display of directories only
python3 smart_ls.py --dirs-only --grid

# JSON output for scripting
python3 smart_ls.py --json --limit 10
```

## tree_view.py - Directory Tree Visualization

### Basic Usage
```bash
python3 tree_view.py [path] [options]
```

### Key Features
- 🌳 Visual tree structure with smart indentation
- 📊 Directory statistics and file counts
- 🎯 Pattern-based filtering
- 📏 File size display
- 🚀 Smart defaults (ignores build/cache directories)

### Options
```
positional arguments:
  path                  Directory to show tree for (default: current)

options:
  -h, --help            show this help message and exit
  --limit, -l, --max LIMIT
                        Limit items per directory (--max is an alias)
  --include-build       Include build/cache directories
  --dirs-only           Show only directories
  --files-only          Show only files (and their parent dirs)
  --ext EXT             Show only files with these extensions (comma-separated)
  --only-pattern ONLY_PATTERN
                        Show only items matching patterns (comma-separated)
  --ignore-pattern IGNORE_PATTERN
                        Ignore items matching patterns (comma-separated)
  --show-size, -s       Show file sizes
  --show-stats          Show directory statistics
  --summary             Show summary information
```

### Usage Examples
```bash
# Basic tree view
python3 tree_view.py

# Limit depth and show sizes
python3 tree_view.py --max-depth 3 --show-size

# Show only Python files
python3 tree_view.py --ext py --files-only

# Include hidden files and build dirs
python3 tree_view.py --all --include-build

# Show directory statistics
python3 tree_view.py --show-stats --summary

# Custom patterns
python3 tree_view.py --only-pattern "*.java,*.py" --max-depth 2

# Large directories with limits
python3 tree_view.py --limit 10 --show-stats
```

## dir_stats.py - Comprehensive Directory Analysis

### Basic Usage
```bash
python3 dir_stats.py [path] [options]
```

### Key Features
- 📊 Comprehensive directory statistics
- 📈 Largest files and directories analysis
- 🕒 Recently modified files tracking
- 🗑️ Empty directory detection
- 📉 File type distribution analysis

### Options
```
positional arguments:
  path                  Directory path (default: current directory)

options:
  -h, --help            show this help message and exit
  -l, --long            Long format with details
  -a, --all             Show hidden files
  --sort {name,size,time,ext}
                        Sort order
  --include, --glob, -g GLOB
                        Include files matching pattern
  --exclude EXCLUDE     Exclude files matching pattern
  --type {f,d,l,all}    File type filter
  -r, --recursive       Recurse into subdirectories
  --max-depth MAX_DEPTH
                        Maximum recursion depth
  --ext EXT             Filter by file extension
  --limit, --max LIMIT  Limit number of results
  -v, --verbose         Enable verbose output
  -q, --quiet           Minimal output
  --json                Output in JSON format
  --dry-run             Preview changes without applying
  --include-build       Include build/cache directories
  --show-files          Show largest files list
  --show-dirs           Show largest directories list
  --show-recent         Show most recently modified files
  --show-empty          Show empty directories
  --detailed            Show all detailed sections
```

### Usage Examples
```bash
# Basic directory statistics
python3 dir_stats.py

# Detailed analysis with all sections
python3 dir_stats.py --detailed

# Show largest files and directories
python3 dir_stats.py --show-files --show-dirs

# Recent modifications analysis
python3 dir_stats.py --show-recent --limit 20

# Include build directories in analysis
python3 dir_stats.py --include-build -r

# JSON output for processing
python3 dir_stats.py --json > stats.json
```

## recent_files_v2.py - Track Recently Modified Files

### Basic Usage
```bash
python3 recent_files_v2.py [options]
```

### Key Features
- 🕒 Time-based file filtering (hours, days, weeks)
- 📂 Group by directory or time period
- 🎯 Extension and pattern filtering
- 📊 Modification statistics
- 🔍 Content change detection

### Common Usage Examples
```bash
# Files modified in last 2 hours
python3 recent_files_v2.py --since 2h

# Java files changed in last 3 days
python3 recent_files_v2.py --since 3d --ext java

# Group by directory
python3 recent_files_v2.py --since 1w --by-dir

# Show with full paths
python3 recent_files_v2.py --since 24h --full-path

# Include git status
python3 recent_files_v2.py --since 4h --git-status
```

## safe_move.py - Safe File Operations with Undo

### Basic Usage
```bash
python3 safe_move.py {move|copy|undo|history} [options]
```

### Key Features
- ↩️ Full undo capability for all operations
- 🔒 Atomic operations with rollback
- 📝 Operation history tracking
- 🎯 Batch operations support
- ✅ Pre-operation validation

### Command Modes
```
Available commands:
  move (mv)    Move one or more files safely
  copy (cp)    Copy one or more files safely
  undo         Undo file operations
  history      Show recent operation history
```

### Usage Examples
```bash
# Move a single file
python3 safe_move.py move file.txt dest/

# Copy multiple files
python3 safe_move.py copy *.java backup/

# Batch move with pattern
python3 safe_move.py move --batch "*.log" logs/

# Undo last operation
python3 safe_move.py undo

# Undo specific operation interactively
python3 safe_move.py undo --interactive

# Show operation history
python3 safe_move.py history --limit 10

# Dry run to preview
python3 safe_move.py move *.tmp temp/ --dry-run
```

## organize_files.py - Automatic File Organization

### Basic Usage
```bash
python3 organize_files.py [directory] --by-{ext|date|size|type} [options]
```

### Key Features
- 🗂️ Multiple organization strategies
- 📋 Manifest-based undo system
- 📦 Archive old files with compression
- 🎯 Custom organization rules
- 🔧 Rules file support (JSON/YAML)

### Organization Modes
```
--by-ext              Organize by file extension
--by-date FORMAT      Organize by date (e.g., "%Y-%m")
--by-size SMALL LARGE Organize by size thresholds
--by-type             Organize by MIME type
--flatten             Flatten directory structure
--archive-by-date DAYS Archive files older than N days
```

### Usage Examples
```bash
# Organize by extension
python3 organize_files.py ~/Downloads --by-ext --create-manifest

# Organize by year-month
python3 organize_files.py ~/Documents --by-date "%Y-%m"

# Archive old files (>90 days)
python3 organize_files.py ~/Desktop --archive-by-date 90

# Custom extension mapping
python3 organize_files.py . --by-ext --custom ".log:Logs,.tmp:Temp"

# Use rules file
python3 organize_files.py ~/Downloads --rules-file organize_rules.json

# Undo using manifest
python3 organize_files.py --undo-manifest operations_2024-01-20.json

# Dry run preview
python3 organize_files.py ~/Downloads --by-ext --dry-run
```

## refactor_rename.py - Code-Aware File and Symbol Renaming

### Basic Usage
```bash
# File rename
python3 refactor_rename.py old_file.py new_file.py

# Symbol rename
python3 refactor_rename.py --replace old_symbol new_symbol --in "src/**/*.py"
```

### Key Features
- 🧠 AST-based code understanding
- 🔄 Updates all references automatically
- 📁 Handles related files (tests, imports)
- ✅ Syntax validation after changes
- 🚀 Batch operations support

### Options
```
positional arguments:
  target                Name of method/class/symbol to analyze
  file                  File to rename
  new_name              New name (without extension)

Symbol replacement options:
  --replace OLD NEW     Code-aware search and replace
  --in PATTERN          Target files pattern (e.g., "src/**/*.py")
  --symbol-type TYPE    Type: variable, method, class, auto
  --related             Also rename related files
  --content-only        Update content only, not filename
  --no-content          Rename file only, not content
  --yes, -y             Auto-confirm (for automation)
```

### Usage Examples
```bash
# Rename a file and update all imports
python3 refactor_rename.py utils/helper.py utils/utility.py

# Rename a variable across multiple files
python3 refactor_rename.py --replace oldVariable newVariable --in "src/**/*.java"

# Rename a method with specific type
python3 refactor_rename.py --replace getData fetchData --in "*.py" --symbol-type method

# Batch rename with pattern
python3 refactor_rename.py --batch "test_*.py" "spec_*.py" tests/ "*.py"

# Update content only (no file rename)
python3 refactor_rename.py MyClass.java YourClass.java --content-only

# Rename with auto-confirm for CI/CD
python3 refactor_rename.py --replace old new --in "src/**/*.py" --yes

# Dry run to preview changes
python3 refactor_rename.py old_name.py new_name.py --dry-run
```

## Common Patterns and Tips

### 1. Finding Files
```bash
# Recent changes
python3 recent_files_v2.py --since 2h --ext py

# Large files
python3 smart_ls.py --min-size 10MB --sort size --reverse

# Specific patterns
python3 smart_ls.py -r --include "*test*.java"
```

### 2. Analyzing Directories
```bash
# Quick overview
python3 tree_view.py --limit 5 --show-stats

# Detailed analysis
python3 dir_stats.py --detailed

# Find empty directories
python3 dir_stats.py --show-empty
```

### 3. Safe Operations
```bash
# Always preview first
python3 organize_files.py ~/Downloads --by-ext --dry-run

# Create manifest for undo
python3 organize_files.py ~/Downloads --by-ext --create-manifest

# Check operation history
python3 safe_move.py history
```

### 4. Code-Aware Refactoring
```bash
# Check compile status
python3 refactor_rename.py --replace old new --in "*.java" --check-compile

# Batch with related files
python3 refactor_rename.py UserService.java AccountService.java --related
```

## Error Handling and Recovery

All tools include:
- 🛡️ Atomic operations with rollback
- 📝 Detailed error messages
- ↩️ Undo capability for destructive operations
- 🔍 Dry-run mode for previewing changes
- 📊 Operation manifests for recovery

## Performance Considerations

- Use `--limit` to handle large directories
- Enable `--exclude` patterns to skip unwanted files
- Use `--max-depth` for recursive operations
- Consider `--dry-run` for large operations
- JSON output for scripting integration