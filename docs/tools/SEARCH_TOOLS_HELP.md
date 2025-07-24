<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Search Tools Help Documentation

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-21
Updated: 2025-07-21
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Search Tools Help Documentation

**Related Code Files:**
- `find_text.py` / `find_text_v6.py` - Enhanced text search with AST context, block extraction, method extraction, and robustness improvements
- `find_files.py` - Fast file finding with comprehensive filters
- `find_references_rg.py` - Find references to methods, fields, or classes using ripgrep
- `pattern_analysis.py` - Pattern analysis with aggregation and frequency analysis
- `cross_file_analysis_ast.py` - AST-based cross-file dependency analysis

---

## Overview

This document provides comprehensive help documentation for the search tools in the code-intelligence-toolkit. These tools provide powerful capabilities for searching code, finding files, analyzing patterns, and understanding code dependencies.

## 1. find_text.py / find_text_v6.py

### Description
Enhanced text search with AST context support, block extraction, method extraction capabilities, and full context line display. Shows hierarchical context (class → method) for search matches and can extract complete code blocks or methods when matches are found inside them. Version 6 adds structural block extraction and robustness improvements for enhanced developer experience.

### Key Features
- **AST Context**: Shows class and method hierarchy for each match
- **Standalone File Display** (v6): Use `--wholefile` without pattern to display entire files
- **Block Extraction** (v6): Extract complete structural code blocks (if/for/while/try/catch)
- **Method Extraction**: Extract complete methods containing search matches
- **Multiple Search Types**: Text, regex, or word boundary matching
- **Context Lines**: Show lines before/after matches (v5: now properly displays with -A/-B/-C)
- **± Syntax** (v5): Intuitive context syntax - `±10` shows 10 lines before and after
- **Auto File Finding** (v5): Automatically searches common directories when file not found
- **Multiple File Support** (v6): Fixed enhanced parser to accept multiple files with `--file file1 file2 file3`
- **Robustness** (v6): Enhanced ripgrep integration with explicit flags and cross-platform path support
- **Clean Parsing** (v6): Refactored argument handling without sys.argv manipulation
- **File Filtering**: Search specific files or use glob patterns
- **Language Support**: Multi-language AST parsing (Python, Java, JavaScript)

### Usage
```bash
find_text.py [pattern] [options]
```

### Options
- `pattern` - Search pattern (optional when using --wholefile standalone)
- `±N` - Show N lines before and after match (v5 syntax, e.g., `±10`)
- `--file FILE [FILE...]` - Search in specific file(s), supports multiple files (v6)
- `--auto-find` - Automatically find files in common directories (v5)
- `--scope SCOPE` - Directory scope to search
- `--type {text,regex,word}` - Search type (default: text)
- `-i, --ignore-case` - Case-insensitive search
- `-g, --glob GLOB` - File pattern (e.g., "*.java")
- `-C, --context N` - Show N lines before and after match
- `-B, --before-context N` - Show N lines before match
- `-A, --after-context N` - Show N lines after match
- `--ast-context` - Show AST context (class/method hierarchy)
- `--no-ast-context` - Disable AST context
- `--extract-block` - Extract complete structural code blocks (if/for/while/try) (v6)
- `--extract-method` - Extract containing methods (up to 500 lines)
- `--extract-method-alllines` - Extract methods regardless of size
- `--wholefile` - Return entire file content (v6: can be used standalone without pattern)
- `--json` - Output results as JSON
- `-q, --quiet` - Suppress headers
- `-v, --verbose` - Verbose output

### Examples
```bash
# Basic text search
find_text.py "TODO" --scope src/

# Search in specific file with context
find_text.py "calculateValue" --file DataBook.java -C 3

# Regex search with OR pattern
find_text.py "velocity|Velocity" --file File.java --type regex

# Case-insensitive search
find_text.py "error" --scope logs/ -i

# Extract methods containing TODOs
find_text.py "TODO" --scope src/ --extract-method

# Search Java files only with AST context
find_text.py "processData" --scope src/ -g "*.java" --ast-context

# Complex regex search
find_text.py "public.*class|@Override" --scope src/ --type regex -g "*.java"

# V5: Using ± syntax for context
find_text.py "error" --file log.txt ±10

# V5: Auto-find file feature
find_text.py "processData" --file DataManager.java  # Will auto-find if not in current dir

# V5: Combine features - auto-find with context
find_text.py "TODO" --file MyClass.java ±5 --extract-method

# V6: Block extraction - extract complete code structures
find_text.py "error" --file Handler.java --extract-block
find_text.py "validate" --file Process.py --extract-block
find_text.py "catch" --file App.java --extract-block  # Extract entire try-catch structure

# V6: Standalone wholefile mode - display entire files without searching
find_text.py --wholefile --file config.py                       # Single file
find_text.py --wholefile --file file1.txt file2.txt file3.txt  # Multiple files
find_text.py --wholefile --file *.log --json                   # JSON output for pipelines

# V6: Wholefile with pattern - show entire files containing matches
find_text.py "TODO" --file src/*.java --wholefile              # Full files with TODOs
find_text.py "error" --scope logs/ --wholefile --json          # JSON format
```

### Output Example with AST Context
```
OrderProcessor.java:145: calculateTotal(items);
AST context of line 145 - [OrderProcessor → processData → calculateTotal]
```

## 2. find_files.py

### Description
Fast file finding with comprehensive filters. Supports name patterns, size filters, time-based searches, and file attributes.

### Key Features
- **Multiple Filter Types**: Name, size, time, permissions
- **Wildcard Support**: Shell-style pattern matching
- **Size Filtering**: Human-readable size specifications
- **Time-based Search**: Find recently modified files
- **Directory Statistics**: Summary and size information
- **Performance**: Fast parallel search

### Usage
```bash
find_files.py [paths...] [options]
```

### Options
- `paths` - Paths to search (default: current directory)
- `--name, -n NAME` - Filename pattern (supports wildcards)
- `--regex, -r REGEX` - Filename regex pattern
- `--ext EXT` - File extension(s) - comma separated
- `--files-only, -f` - Find only files
- `--dirs-only, -d` - Find only directories
- `--min-size MIN_SIZE` - Minimum file size (e.g., "1MB")
- `--max-size MAX_SIZE` - Maximum file size (e.g., "100KB")
- `--newer-than NEWER_THAN` - Modified within timeframe (e.g., "2d", "3h")
- `--older-than OLDER_THAN` - Modified before timeframe (e.g., "1w")
- `--executable, -x` - Find executable files
- `--readable` - Find readable files
- `--writable` - Find writable files
- `--include-build` - Include build/cache directories
- `--size-info, -s` - Show file sizes
- `--summary` - Show summary statistics
- `--limit, --max LIMIT` - Limit number of results

### Examples
```bash
# Find all Python files
find_files.py --ext py

# Find large files (>10MB)
find_files.py --min-size 10MB

# Find recently modified files (last 2 days)
find_files.py --newer-than 2d

# Find by name pattern
find_files.py --name "*.java" --size-info

# Find executable files
find_files.py --executable --files-only

# Complex search: Java files >1KB, modified in last week
find_files.py --ext java --min-size 1KB --newer-than 1w

# Find in specific directories with limit
find_files.py src/ tests/ --ext py --max 50
```

## 3. find_references_rg.py

### Description
Find references to methods, fields, or classes using ripgrep for fast searching. Supports automatic type detection and context display.

### Key Features
- **Auto-detection**: Automatically determines if target is method, field, or class
- **Context Lines**: Show surrounding code for each reference
- **Summary Reports**: Get overview or detailed reference list
- **Case Sensitivity**: Optional case-insensitive searching
- **Fast Performance**: Uses ripgrep for speed

### Usage
```bash
find_references_rg.py target [options]
```

### Options
- `target` - Name of method, field, or class to find
- `--scope SCOPE` - Directory to search in (default: current)
- `--type {method,field,class,auto}` - Type of reference (default: auto)
- `--context CONTEXT` - Number of context lines (default: 3)
- `--summary-only` - Show only summary without details
- `-i, --ignore-case` - Case-insensitive search
- `--ast-context` - Show AST context for matches
- `--threads N` - Number of parallel threads

### Examples
```bash
# Find all references to a method
find_references_rg.py sendOrder --type method

# Find class references with context
find_references_rg.py OrderManager --type class --context 5

# Search in specific directory
find_references_rg.py calculateValue --scope src/main/

# Summary only
find_references_rg.py processData --summary-only

# Case-insensitive search
find_references_rg.py updatestatus -i

# Parallel search with 8 threads
find_references_rg.py validateOrder --threads 8
```

## 4. pattern_analysis.py

### Description
Advanced pattern analysis with aggregation, frequency analysis, and trend detection. Ideal for analyzing logs, error patterns, and code patterns across files.

### Key Features
- **Frequency Analysis**: Count occurrences by file and overall
- **Timeline Analysis**: Analyze patterns over time (for logs)
- **Trend Detection**: Identify increasing/decreasing patterns
- **Content Analysis**: Categorize patterns (error, warning, info)
- **Co-occurrence**: Find related patterns
- **Top Files**: Identify files with most occurrences

### Usage
```bash
pattern_analysis.py pattern [options]
```

### Options
- `pattern` - Pattern to search for and analyze
- `--scope SCOPE` - Directory to search (default: current)
- `--regex` - Use regex pattern matching
- `--ignore-case, -i` - Case-insensitive search
- `--file-pattern, -g FILE_PATTERN` - File pattern (e.g., "*.java")
- `--context CONTEXT` - Lines of context around matches
- `--count-by-file` - Count occurrences by file
- `--show-frequency` - Show frequency analysis
- `--show-timeline` - Show timeline analysis for log data
- `--show-trends` - Calculate and show trend analysis
- `--content-patterns` - Analyze content patterns
- `--co-occurrence` - Show word co-occurrence analysis
- `--top-files TOP_FILES` - Number of top files to show (default: 10)
- `--max-samples MAX_SAMPLES` - Maximum sample matches to show
- `--time-window {minute,hour,day}` - Time window for trend analysis
- `--json` - Output results as JSON
- `--summary-only` - Show only summary statistics

### Examples
```bash
# Basic pattern frequency analysis
pattern_analysis.py "Log\.info.*REVERSAL" --count-by-file --show-frequency

# Timeline analysis for log patterns
pattern_analysis.py "ERROR" --scope ~/Desktop/TradeLog/ --show-timeline --time-window hour

# Multi-pattern analysis with regex
pattern_analysis.py "TODO|FIXME" --regex --count-by-file --co-occurrence

# File type specific analysis
pattern_analysis.py "sendOrder" -g "*.java" --show-frequency --top-files 20

# Trend analysis with content patterns
pattern_analysis.py "REVERSAL.*executed" --show-trends --content-patterns --regex

# Analyze exceptions in logs
pattern_analysis.py "Exception|Error" --regex -i --show-timeline --content-patterns
```

## 5. cross_file_analysis_ast.py

### Description
AST-based cross-file dependency analysis. Understands code structure to find true dependencies, not just text matches.

### Key Features
- **AST Understanding**: Uses abstract syntax trees for accuracy
- **Import Analysis**: Track import dependencies
- **Call Graph**: Build method call relationships
- **Circular Detection**: Find circular dependencies
- **Visual Output**: Generate dependency graphs
- **Multi-language**: Supports Python, Java, JavaScript

### Usage
```bash
cross_file_analysis_ast.py target [options]
```

### Options
- `target` - Class, method, or module to analyze
- `--scope SCOPE` - Directory to analyze (default: current)
- `--depth DEPTH` - Maximum dependency depth to explore
- `--show-imports` - Include import analysis
- `--show-calls` - Include method call analysis
- `--detect-cycles` - Detect circular dependencies
- `--format {text,json,dot}` - Output format
- `--ast-context` - Include AST context in output
- `--threads N` - Number of parallel threads
- `--verbose` - Detailed output

### Examples
```bash
# Analyze dependencies of a class
cross_file_analysis_ast.py OrderManager --scope src/

# Find circular dependencies
cross_file_analysis_ast.py . --detect-cycles

# Generate dependency graph
cross_file_analysis_ast.py MyModule --format dot > deps.dot

# Deep dependency analysis
cross_file_analysis_ast.py processData --depth 5 --show-calls

# Analyze with parallel processing
cross_file_analysis_ast.py DataProcessor --threads 8 --verbose

# Full analysis with all options
cross_file_analysis_ast.py MainApp --show-imports --show-calls --ast-context
```

## Common Usage Patterns

### 1. Finding TODOs and FIXMEs
```bash
# Find all TODOs with their methods
find_text.py "TODO" --scope src/ --extract-method

# Analyze TODO frequency by file
pattern_analysis.py "TODO|FIXME" --regex --count-by-file --top-files 20
```

### 2. Understanding Code Flow
```bash
# Find where a method is called
find_references_rg.py calculateValue --context 5

# Analyze dependencies
cross_file_analysis_ast.py calculateValue --show-calls --depth 3
```

### 3. Code Refactoring Research
```bash
# Find all uses of deprecated method
find_text.py "@Deprecated.*oldMethod" --type regex -g "*.java"

# Find files to update
find_files.py --name "*Test*.java" --newer-than 7d
```

### 4. Log Analysis
```bash
# Analyze error patterns over time
pattern_analysis.py "ERROR|Exception" --regex --show-timeline --scope logs/

# Find most problematic files
pattern_analysis.py "failed" -i --top-files 10 --show-frequency
```

### 5. Large Codebase Navigation
```bash
# Find entry points
find_text.py "public static void main" -g "*.java"

# Locate configuration files
find_files.py --name "*.properties" --name "*.yaml" --name "*.xml"

# Find test files
find_files.py --name "*Test.java" --name "*Spec.js"
```

## Performance Tips

1. **Use Glob Patterns**: Limit search to relevant files with `-g` flag
2. **Scope Searches**: Use `--scope` to search specific directories
3. **Parallel Processing**: Use `--threads N` for faster processing
4. **Limit Results**: Use `--limit` or `--max` to avoid overwhelming output
5. **Summary Mode**: Use `--summary-only` for overview before detailed search

## Troubleshooting

### Common Issues

1. **"No matches found"**
   - Check pattern syntax (especially regex escaping)
   - Verify file patterns with `-g` flag
   - Try case-insensitive search with `-i`

2. **Syntax Errors**
   - Some tools may have syntax errors in current versions
   - Try earlier versions in `earlierversions/` or `archive/` directories
   - Check `--help` for correct syntax

3. **Performance Issues**
   - Use file patterns to limit search scope
   - Increase thread count for parallel tools
   - Use `--summary-only` first to gauge result size

4. **AST Context Not Working**
   - Ensure AST parser is available for language
   - Check if file has valid syntax
   - Use `--no-ast-context` to disable if causing issues

## Integration with Other Tools

These search tools work well with other toolkit components:

- Use with `navigate_ast.py` after finding references
- Pipe results to `semantic_diff.py` for comparing versions
- Use findings with `replace_text_ast.py` for refactoring
- Combine with `git_commit_analyzer.py` to understand changes

## Limitations

1. **Language Support**: AST features work best with Python, Java, JavaScript
2. **Binary Files**: Tools skip binary files by default
3. **Large Files**: Very large files may cause memory issues
4. **Regex Complexity**: Complex regex patterns may impact performance