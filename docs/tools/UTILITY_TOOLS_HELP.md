<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Utility Tools Help Documentation

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-20
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Utility Tools Help Documentation

**Related Code Files:**
- `common_config.py` - Configuration management system
- `analyze_errors.py` - Error log analysis tool
- `error_logger.py` - Centralized error logging system
- `enhanced_standard_arg_parser.py` - Unified argument parsing framework

---

## Table of Contents
1. [common_config.py - Configuration Management](#common_configpy---configuration-management)
2. [analyze_errors.py - Error Log Analysis](#analyze_errorspy---error-log-analysis)
3. [error_logger.py - Error Logging System](#error_loggerpy---error-logging-system)
4. [enhanced_standard_arg_parser.py - Argument Parser Framework](#enhanced_standard_arg_parserpy---argument-parser-framework)

---

## common_config.py - Configuration Management

### Overview
Unified configuration system for Python development tools. Provides project-aware defaults and reduces repetitive command-line flags.

### Usage
```bash
./run_any_python_tool.sh common_config.py [options]
```

### Options
```
usage: common_config.py [-h] [--show] [--create] [--find-root]

Manage Python development tools configuration

options:
  -h, --help   show this help message and exit
  --show       Show current configuration
  --create     Create default .pytoolsrc file
  --find-root  Find and show project root
```

### Examples
```bash
# Show current configuration
./run_any_python_tool.sh common_config.py --show

# Create default config file
./run_any_python_tool.sh common_config.py --create

# Find project root
./run_any_python_tool.sh common_config.py --find-root
```

### Key Features
- **Project-aware configuration**: Automatically finds project root by looking for markers (.pytoolsrc, .git, pyproject.toml, etc.)
- **Default values management**: Sets sensible defaults for common flags (all=false, include_build=false, max_depth=10, quiet=false)
- **Hierarchical configuration**: Supports section-based configuration with inheritance
- **Type conversion**: Automatically converts string config values to appropriate Python types (bool, int, float, list)
- **CLI override**: Command-line arguments always take precedence over config file values

### Configuration File Format (.pytoolsrc)
```ini
[defaults]
all = false
include_build = false
max_depth = 10
quiet = false
ast_context = true
check_compile = true

[find_text]
show_line_numbers = true
context_lines = 2

[directory_tools]
max_results = 50
show_hidden = false

[refactoring]
create_backup = true
dry_run = false
```

### How It Works
1. Searches for project root starting from current directory
2. Looks for .pytoolsrc file in project root
3. Loads configuration with sensible defaults
4. Tools can query configuration values using `get_config_value()`
5. CLI arguments override config file values

---

## analyze_errors.py - Error Log Analysis

### Overview
Error log analysis tool for Python tools. Provides insights into error patterns, frequencies, and trends from the centralized error logging system.

### Usage
```bash
./run_any_python_tool.sh analyze_errors.py [target] [options]
```

### Options
```
usage: analyze_errors.py [-h] [--file FILE] [--scope SCOPE]
                         [--type {method,class,function,variable,auto}]
                         [--max-depth MAX_DEPTH] [--show-callers]
                         [--show-callees] [-v] [-q] [--json]
                         [--log-dir LOG_DIR] [--days DAYS] [--tool TOOL]
                         [--summary] [--recent RECENT] [--patterns]
                         target

Analyze Python tools error logs

positional arguments:
  target                Name of method/class/symbol to analyze

options:
  -h, --help            show this help message and exit
  --file FILE           Analyze in specific file
  --scope SCOPE         Directory scope for analysis (default: current dir)
  --type {method,class,function,variable,auto}
                        Type of symbol to analyze
  --max-depth MAX_DEPTH
                        Maximum depth for dependency analysis
  --show-callers        Show where this symbol is called from
  --show-callees        Show what this symbol calls
  -v, --verbose         Enable verbose output
  -q, --quiet           Minimal output
  --json                Output in JSON format
  --log-dir LOG_DIR     Custom log directory
  --days DAYS           Analyze errors from last N days
  --tool TOOL           Filter by specific tool name
  --summary             Show summary from summary log
  --recent RECENT       Show N most recent errors
  --patterns            Focus on failure patterns
```

### Examples
```bash
# View 10 most recent errors
./run_any_python_tool.sh analyze_errors.py --recent 10

# Analyze failure patterns
./run_any_python_tool.sh analyze_errors.py --patterns

# Filter errors from last 7 days
./run_any_python_tool.sh analyze_errors.py --days 7

# Show errors from specific tool
./run_any_python_tool.sh analyze_errors.py --tool find_text.py

# Get error summary
./run_any_python_tool.sh analyze_errors.py --summary

# Export analysis as JSON
./run_any_python_tool.sh analyze_errors.py --json > error_analysis.json
```

### Key Features
- **Time-based filtering**: Analyze errors from specific time periods (--days)
- **Tool-specific analysis**: Filter errors by tool name
- **Pattern detection**: Identifies common failure patterns (file not found, permission errors, syntax errors, etc.)
- **Temporal analysis**: Shows error distribution by hour and day
- **Error frequency**: Tracks most common error types and messages
- **Argument analysis**: Identifies command patterns that frequently fail
- **Rich reporting**: Outputs detailed analysis with statistics and trends
- **JSON export**: Machine-readable output for further processing

### Analysis Output Includes
- Total error count and time range
- Errors by tool with error type breakdown
- Error type distribution
- Temporal patterns (by hour, by day)
- Common error messages
- Common failing command patterns
- Identified failure patterns with recommendations

---

## error_logger.py - Error Logging System

### Overview
Centralized error logging system for all Python tools. Automatically captures errors with context, timestamp, and structured format for analysis.

### Usage
This tool is typically not run directly but is used by other tools through the error logging wrapper. When run directly, it performs a test and shows error summary.

```bash
./run_any_python_tool.sh error_logger.py
```

### Key Features
- **Automatic error capture**: All Python tools automatically log errors through this system
- **Structured logging**: Errors stored in JSON Lines format (`.jsonl`) for easy parsing
- **Rich context capture**: Logs tool name, error type, message, stack trace, command args, system info
- **Unique error IDs**: Each error gets a unique hash ID for tracking
- **Performance metrics**: Captures execution time for failed operations
- **System information**: Logs Python version, platform, and available memory (if psutil installed)
- **Log rotation**: Maintains separate error log and summary files
- **Centralized storage**: All logs stored in `~/.pytoolserrors/` directory

### Error Record Structure
```json
{
    "id": "unique-hash-id",
    "timestamp": "2025-07-20T10:54:57.397414",
    "tool_name": "find_text.py",
    "error_type": "SubprocessError",
    "error_message": "Tool exited with code 1",
    "command_args": ["find_text.py", "pattern", "--file", "test.java"],
    "stack_trace": "Traceback...",
    "system_info": {
        "python_version": "3.9.0",
        "platform": "Darwin-24.5.0",
        "memory_available_mb": 8192
    },
    "additional_context": {
        "execution_time": 0.234
    }
}
```

### Log Files
- **`~/.pytoolserrors/errors.jsonl`**: Main error log file (one JSON object per line)
- **`~/.pytoolserrors/error_summary.json`**: Aggregated summary statistics

### Environment Variables
- **`DISABLE_ERROR_LOGGING=1`**: Disable automatic error logging
- **`PYTOOLSERRORS_DIR=/custom/path`**: Use custom log directory

### Integration
The error logger is automatically integrated through:
1. `run_with_error_logging.py` wrapper
2. `@with_error_handling` decorator for Python functions
3. Automatic capture in `run_any_python_tool.sh` script

---

## enhanced_standard_arg_parser.py - Argument Parser Framework

### Overview
Unified argument parsing framework that provides consistent command-line interfaces across all Python tools. Supports three main parser types: search, analyze, and directory operations.

### Usage
This is a library module used by other tools to create standardized argument parsers. When run directly, it shows example parsers.

```bash
./run_any_python_tool.sh enhanced_standard_arg_parser.py --help
```

### Parser Types

#### 1. Search Parser
For tools that search for patterns in code:
```
positional arguments:
  pattern               Search pattern or text

options:
  --file FILE           Search in specific file
  --scope SCOPE         Directory scope for search
  --type {text,regex,word}  Search type
  -i, --ignore-case     Case-insensitive search
  -w, --whole-word      Match whole words only
  --include, -g GLOB    Include files matching pattern
  --exclude EXCLUDE     Exclude files matching pattern
  -C, --context N       Show N lines around match
  -A, --after-context N Show N lines after match
  -B, --before-context N Show N lines before match
  -r, --recursive       Search recursively
  --ast-context         Show AST context
  --no-ast-context      Disable AST context
```

#### 2. Analyze Parser
For tools that analyze code structure:
```
positional arguments:
  target                Name of method/class/symbol to analyze

options:
  --file FILE           Analyze in specific file
  --scope SCOPE         Directory scope for analysis
  --type {method,class,function,variable,auto}  Symbol type
  --max-depth MAX_DEPTH Maximum dependency depth
  --show-callers        Show where symbol is called from
  --show-callees        Show what symbol calls
  --language {python,java,javascript,cpp,go,rust}  Filter by language
  -i, --ignore-case     Case-insensitive analysis
  --ast-context         Show AST context
  --format {text,json,markdown,csv}  Output format
  --summary             Show summary only
```

#### 3. Directory Parser
For tools that work with directory listings:
```
positional arguments:
  path                  Directory path (default: current)

options:
  -l, --long            Long format with details
  -a, --all             Show hidden files
  --sort {name,size,time,ext}  Sort order
  --include, -g GLOB    Include matching files
  --exclude EXCLUDE     Exclude matching files
  --type {f,d,l,all}    File type filter
  -r, --recursive       Recurse into subdirectories
  --max-depth MAX_DEPTH Maximum recursion depth
  --ext EXT             Filter by file extension
  --limit, --max LIMIT  Limit number of results
```

### Common Options (All Parser Types)
```
-v, --verbose         Enable verbose output
-q, --quiet           Minimal output
--json                Output in JSON format
--dry-run             Preview changes without applying
-h, --help            Show help message
```

### Key Features
- **Consistent interfaces**: All tools use the same argument patterns
- **Smart defaults**: Sensible defaults based on tool type
- **Alias support**: Common aliases (e.g., `-g` for `--glob`, `--max` for `--limit`)
- **Type validation**: Automatic validation of argument types
- **Help formatting**: Consistent, well-formatted help messages
- **Config integration**: Works with common_config.py for default values
- **Extensibility**: Easy to add new parser types or options

### Benefits for Tool Developers
1. **Reduced boilerplate**: No need to write argument parsing code
2. **Consistency**: Users learn one interface, use all tools
3. **Validation**: Built-in validation for common patterns
4. **Documentation**: Auto-generated help from parser definition
5. **Testing**: Standardized parsers are easier to test

### Integration Example
```python
from enhanced_standard_arg_parser import create_enhanced_parser

# Create a search tool parser
parser = create_enhanced_parser(
    'search',
    'Find patterns in source code'
)

# Parse arguments
args = parser.parse_args()

# Access standardized arguments
if args.file:
    search_in_file(args.pattern, args.file)
elif args.scope:
    search_in_directory(args.pattern, args.scope)
```

---

## Summary

These utility tools form the foundation of the Python development toolkit:

1. **common_config.py** - Manages project-wide configuration to reduce command-line verbosity
2. **analyze_errors.py** - Provides insights into tool failures and helps identify patterns
3. **error_logger.py** - Automatically captures all errors for later analysis
4. **enhanced_standard_arg_parser.py** - Ensures consistent command-line interfaces across all tools

Together, they create a robust, user-friendly development environment with excellent error tracking and configuration management capabilities.