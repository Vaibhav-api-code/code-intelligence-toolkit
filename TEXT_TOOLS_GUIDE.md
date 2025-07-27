<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Text Tools Guide

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-21
Updated: 2025-07-21
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Text Tools Guide

**Related Code Files:**
- `code-intelligence-toolkit/find_text_v6.py` - Enhanced search with context and auto-finding
- `code-intelligence-toolkit/multiline_reader.py` - Extract arbitrary line ranges
- `code-intelligence-toolkit/extract_methods_v2.py` - Extract complete methods
- `code-intelligence-toolkit/extract_block.py` - Extract code blocks

---

## Overview

The code-intelligence-toolkit provides several specialized text tools, each optimized for different use cases. This guide helps you choose the right tool for your task.

## Quick Decision Tree

```
Need to search for text?
├─ YES → Use find_text_v7.py v5
│   ├─ Need context lines? → Use ±N syntax
│   ├─ File location unknown? → Use --auto-find
│   └─ Need method extraction? → Use --extract-method
│
└─ NO → Need to extract specific lines?
    ├─ Have line numbers? → Use multiline_reader.py
    ├─ Need whole methods? → Use extract_methods_v2.py
    └─ Need code blocks? → Use extract_block.py
```

## Tool Comparison Table

| Tool | Primary Purpose | Best For | Key Features |
|------|----------------|----------|--------------|
| **find_text_v6.py** | Search patterns in code | Finding occurrences with context | Context lines (±N), AST context, auto-find files, method extraction |
| **multiline_reader.py** | Extract line ranges | Getting specific lines/ranges | Flexible syntax (±, :, -, ,), piping support |
| **extract_methods_v2.py** | Extract complete methods | Getting full method implementations | Language-aware, handles nested methods |
| **extract_block.py** | Extract code blocks | Getting if/for/while blocks | Block-aware extraction |
| **replace_text_ast_v2.py** | AST-aware replacement | Renaming variables/functions accurately | Semantic understanding, non-interactive mode |
| **replace_text_v7.py** | Advanced text replacement | Multi-file replacements | Git integration, block-aware, non-interactive |

## Detailed Tool Usage

### find_text_v6.py - Enhanced Search Tool

**When to use:**
- Searching for patterns in code
- Need to see surrounding context
- Don't know exact file location
- Want to extract containing methods

**Key features:**
- **Context display**: Fixed -A/-B/-C flags and new ±N syntax
- **Auto file finding**: Searches common directories when file not found
- **Method extraction**: Extract complete methods containing matches
- **AST context**: Shows class → method hierarchy

**Examples:**
```bash
# Search with context
./run_any_python_tool.sh find_text_v7.py "TODO" ±10  # 10 lines before/after

# Auto-find file
./run_any_python_tool.sh find_text_v7.py "calculate" --file Calculator.java  # Finds file automatically

# Extract methods containing pattern
./run_any_python_tool.sh find_text_v7.py "deprecated" --extract-method

# Traditional context flags
./run_any_python_tool.sh find_text_v7.py "error" -C 5  # 5 lines of context

# Extract line ranges for piping
./run_any_python_tool.sh find_text_v7.py "TODO" --extract-ranges | xargs multiline_reader.py
```

### multiline_reader.py - Line Range Extractor

**When to use:**
- You know exact line numbers
- Need flexible range specifications
- Want to pipe from other tools
- Need to combine multiple ranges

**Key features:**
- **Flexible syntax**: 100±10, 50:60, 100-110, 45,50,55
- **Multiple ranges**: Can specify multiple ranges in one command
- **Piping friendly**: Designed to work with other tools
- **Smart formatting**: Handles overlapping ranges

**Examples:**
```bash
# Extract lines with context
./run_any_python_tool.sh multiline_reader.py file.java 100±10  # Lines 90-110

# Extract specific range
./run_any_python_tool.sh multiline_reader.py file.java 50:60   # Lines 50-60

# Multiple ranges
./run_any_python_tool.sh multiline_reader.py file.java 10-20,30-40,50±5

# Pipe from find_text
./run_any_python_tool.sh find_text_v7.py "TODO" --extract-ranges | xargs multiline_reader.py
```

### extract_methods_v2.py - Method Extractor

**When to use:**
- Need complete method implementations
- Want all methods in a class
- Need language-aware extraction
- Extracting for documentation

**Key features:**
- **Language support**: Python, Java, JavaScript, TypeScript
- **Complete extraction**: Gets full method including decorators/annotations
- **Multiple methods**: Can extract all or specific methods
- **Nested handling**: Properly handles nested methods

**Examples:**
```bash
# Extract specific method
./run_any_python_tool.sh extract_methods_v2.py file.java calculateTotal

# Extract all methods
./run_any_python_tool.sh extract_methods_v2.py file.py --all

# Extract method at specific line
./run_any_python_tool.sh extract_methods_v2.py file.java --line 150
```

### extract_block.py - Code Block Extractor

**When to use:**
- Need if/else blocks
- Want loop bodies
- Extracting try/catch blocks
- Need block-aware extraction

**Key features:**
- **Block types**: if, for, while, try, with, etc.
- **Nested blocks**: Handles nested structures
- **Language aware**: Understands language-specific syntax
- **Brace matching**: Proper bracket/brace handling

**Examples:**
```bash
# Extract if block at line
./run_any_python_tool.sh extract_block.py file.java --line 100 --type if

# Extract all for loops
./run_any_python_tool.sh extract_block.py file.py --type for --all

# Extract try-catch block
./run_any_python_tool.sh extract_block.py file.java --line 200 --type try
```

## Workflow Examples

### Finding and Extracting TODO Comments

```bash
# Step 1: Find all TODOs with context
./run_any_python_tool.sh find_text_v7.py "TODO" ±5

# Step 2: Extract methods containing TODOs
./run_any_python_tool.sh find_text_v7.py "TODO" --extract-method

# Step 3: Get specific line ranges
./run_any_python_tool.sh find_text_v7.py "TODO" --extract-ranges | xargs multiline_reader.py
```

### Analyzing Error Handling

```bash
# Find all error handling with context
./run_any_python_tool.sh find_text_v7.py "catch|error|exception" --type regex ±10

# Extract all try-catch blocks
./run_any_python_tool.sh extract_block.py ErrorHandler.java --type try --all

# Find and extract error handling methods
./run_any_python_tool.sh find_text_v7.py "handleError" --extract-method
```

### Code Review Workflow

```bash
# Find changes in specific area
./run_any_python_tool.sh find_text_v7.py "calculateValue" --file PriceCalculator.java ±20

# Extract the full method
./run_any_python_tool.sh extract_methods_v2.py PriceCalculator.java calculateValue

# Get specific problematic lines
./run_any_python_tool.sh multiline_reader.py PriceCalculator.java 145±15
```

## Performance Considerations

- **find_text_v6.py**: Uses ripgrep for fast searching, efficient even on large codebases
- **multiline_reader.py**: Direct file reading, very fast for known line numbers
- **extract_methods_v2.py**: Parses AST, slower but more accurate
- **extract_block.py**: Uses pattern matching, performance varies by file size

## Best Practices

1. **Start with find_text_v6.py** for initial discovery
2. **Use --extract-ranges** to prepare line numbers for multiline_reader
3. **Prefer extract_methods_v2.py** over manual line extraction for complete methods
4. **Combine tools** using pipes for complex workflows
5. **Use --auto-find** when working with unfamiliar codebases

## Integration Tips

### Creating Aliases

```bash
# Add to ~/.bashrc or ~/.zshrc
alias findtext='./run_any_python_tool.sh find_text_v7.py'
alias readlines='./run_any_python_tool.sh multiline_reader.py'
alias getmethod='./run_any_python_tool.sh extract_methods_v2.py'
```

### Combining with Other Tools

```bash
# Find and edit
findtext "deprecated" --file MyClass.java ±5 | grep -n ":" | head -1

# Extract and analyze
getmethod Calculator.java calculateTotal | grep -c "if"

# Search and document
findtext "public.*API" --type regex --extract-method > api_methods.txt
```

## Summary

- **find_text_v5.py**: Your go-to tool for searching with context
- **multiline_reader.py**: Best for extracting known line ranges
- **extract_methods_v2.py**: Use when you need complete methods
- **extract_block.py**: Specialized for code block extraction

Choose based on what you know (pattern vs. line numbers) and what you need (context vs. complete structures).

## Text Replacement Tools

### replace_text_ast_v2.py - AST-Aware Replacement

**When to use:**
- Renaming variables, functions, or classes accurately
- Need semantic understanding (not just text matching)
- Want to avoid replacing strings or comments
- Working with Python or Java code

**Key features:**
- **Line-specific targeting**: Replace only at specific line numbers
- **AST understanding**: Knows the difference between variables and strings
- **Non-interactive mode**: Full support for automation
- **Comment/string modes**: Target only comments or string literals

**Non-Interactive Mode Support:**
```bash
# Environment variable
export REPLACE_TEXT_AST_ASSUME_YES=1

# Command flags
./run_any_python_tool.sh replace_text_ast_v2.py oldVar newVar --file script.py --line 42 --yes
./run_any_python_tool.sh replace_text_ast_v2.py oldVar newVar --file script.py --line 42 --no-confirm

# Configuration file (.pytoolsrc)
[replace_text_ast]
assume_yes = true
non_interactive = true
backup = true
```

**Examples:**
```bash
# Rename variable at specific line
./run_any_python_tool.sh replace_text_ast_v2.py oldName newName --file code.py --line 25

# Replace in comments only
./run_any_python_tool.sh replace_text_ast_v2.py "TODO" "FIXME" --file script.py --comments-only

# Replace in strings only
./run_any_python_tool.sh replace_text_ast_v2.py "old_url" "new_url" --file config.py --strings-only

# Non-interactive for CI/CD
REPLACE_TEXT_AST_ASSUME_YES=1 ./run_any_python_tool.sh replace_text_ast_v2.py var1 var2 --file app.py --line 100
```

### replace_text_v7.py - Advanced Text Replacement

**When to use:**
- Multi-file replacements
- Complex regex patterns
- Git-aware replacements
- Block-specific replacements

**Key features:**
- **Multi-file support**: Replace across entire codebases
- **Git integration**: Target staged files or specific commits
- **Block-aware modes**: Replace only within/outside code blocks
- **JSON pipeline**: Chain operations for complex workflows
- **Non-interactive mode**: Full automation support

**Non-Interactive Mode Support:**
```bash
# Command flags
./run_any_python_tool.sh replace_text_v7.py "old" "new" --scope src/ --yes
./run_any_python_tool.sh replace_text_v7.py "old" "new" file.txt -y

# Configuration file (.pytoolsrc)
[replace_text]
assume_yes = true
backup = true
```

**Examples:**
```bash
# Simple replacement
./run_any_python_tool.sh replace_text_v7.py "oldAPI" "newAPI" src/

# Regex replacement
./run_any_python_tool.sh replace_text_v7.py 'import (.*) from "old"' 'import $1 from "new"' --type regex

# Git-aware replacement
./run_any_python_tool.sh replace_text_v7.py "TODO" "DONE" --git-only --staged-only

# Block-aware replacement
./run_any_python_tool.sh replace_text_v7.py "log" "logger" --block-mode within

# Non-interactive automation
./run_any_python_tool.sh replace_text_v7.py "old" "new" --scope src/ --yes --quiet
```

## Complete Tool Summary

**Search and Extract:**
- **find_text_v6.py**: Your go-to tool for searching with context
- **multiline_reader.py**: Best for extracting known line ranges
- **extract_methods_v2.py**: Use when you need complete methods
- **extract_block.py**: Specialized for code block extraction

**Replace and Refactor:**
- **replace_text_ast_v2.py**: AST-aware replacements with semantic understanding
- **replace_text_v7.py**: Powerful text replacement with advanced features

All tools support non-interactive mode for CI/CD and automation workflows.