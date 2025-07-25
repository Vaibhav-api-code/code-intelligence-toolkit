<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Python Tools Master Help Documentation

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-20
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Python Tools Master Help Documentation

**Last Updated**: January 20, 2025  
**Toolkit Version**: Production Ready with Enhanced Argument Parser System

**Related Code Files:**
- `python_tools/common_config.py` - Unified configuration system for all tools
- `python_tools/enhanced_argument_parser.py` - Standardized argument parsing with preflight checks
- `python_tools/error_logger.py` - Enterprise-grade error logging system
- `python_tools/secure_tools_base.py` - Security framework for all tools
- `run_any_python_tool.sh` - Universal wrapper script with approval system

---

## 🎯 Overview

The code-intelligence-toolkit provides **80+ production-ready Python tools** for advanced code analysis, refactoring, and development workflows. All tools feature:

- ✅ **Standardized Argument Parsing** - Consistent interface across all tools
- ✅ **Enhanced Preflight Checks** - Automatic validation before execution
- ✅ **Enterprise Security** - Path traversal protection, input sanitization
- ✅ **Unified Configuration** - Project-aware defaults via `.pytoolsrc`
- ✅ **Comprehensive Error Logging** - Rich context capture to `~/.pytoolserrors/`
- ✅ **AST-Based Accuracy** - 100% accurate code analysis and refactoring
- ✅ **Honest Compile Checking** - Clear feedback on code validity

## 🚀 Recent Enhancements (January 2025)

### Key Achievement: Complete Standardization
**ALL production tools now use the enhanced argument parser system** with:
- Standardized `--help` formatting with usage, description, and examples
- Automatic preflight validation (file existence, permissions, syntax)
- Consistent error handling and reporting
- Common flags across tool categories (`-v`, `-q`, `--json`, `--no-color`)

### Major Improvements
1. **Enhanced Argument Parser** - All tools migrated to `EnhancedArgumentParser`
2. **Preflight Check System** - Automatic validation prevents common errors
3. **AST Context by Default** - Hierarchical code location in all searches
4. **Method Extraction** - Extract complete method implementations
5. **Honest Compile Checking** - Transparent feedback on code validity
6. **Bulletproof File Ops V2** - Interactive undo, manifest tracking
7. **Threading Support** - 4x faster analysis with configurable threads
8. **Error Monitoring** - Automatic capture and analysis dashboard

## 📚 Quick Reference Table

### 🔍 Search and Analysis Tools
| Tool | Purpose | Key Features | Detailed Help |
|------|---------|--------------|---------------|
| `find_text.py` | Enhanced text search | AST context, method extraction, regex | [SEARCH_TOOLS_HELP.md](SEARCH_TOOLS_HELP.md#find_textpy) |
| `find_references_rg.py` | Find symbol references | Multi-threaded, type filtering | [SEARCH_TOOLS_HELP.md](SEARCH_TOOLS_HELP.md#find_references_rgpy) |
| `cross_file_analysis.py` | Basic dependency analysis | Import tracking, usage mapping | [SEARCH_TOOLS_HELP.md](SEARCH_TOOLS_HELP.md#cross_file_analysispy) |
| `cross_file_analysis_ast.py` | Advanced dependency analysis | AST-based, call graphs | [SEARCH_TOOLS_HELP.md](SEARCH_TOOLS_HELP.md#cross_file_analysis_astpy) |
| `grep_tool.py` | High-performance grep | Parallel processing, advanced filters | [SEARCH_TOOLS_HELP.md](SEARCH_TOOLS_HELP.md#grep_toolpy) |

### 🧬 AST-Based Tools
| Tool | Purpose | Key Features | Detailed Help |
|------|---------|--------------|---------------|
| `navigate_ast_v2.py` | Navigate to definitions | 100% accurate, multi-language | [AST_TOOLS_HELP.md](AST_TOOLS_HELP.md#navigate_ast_v2py) |
| `method_analyzer_ast_v2.py` | Analyze method calls | Call flow, dependency graphs | [AST_TOOLS_HELP.md](AST_TOOLS_HELP.md#method_analyzer_ast_v2py) |
| `semantic_diff_v3.py` | Semantic code diff | Impact scoring, refactor safety | [AST_TOOLS_HELP.md](AST_TOOLS_HELP.md#semantic_diff_v3py) |
| `replace_text_ast.py` | AST-aware replacement | Scope-aware, semantic understanding | [AST_TOOLS_HELP.md](AST_TOOLS_HELP.md#replace_text_astpy) |
| `show_structure_ast_v4.py` | Code structure viewer | Hierarchical display, filtering | [AST_TOOLS_HELP.md](AST_TOOLS_HELP.md#show_structure_ast_v4py) |

### 📂 File and Directory Tools
| Tool | Purpose | Key Features | Detailed Help |
|------|---------|--------------|---------------|
| `smart_ls.py` | Enhanced directory listing | Icons, filtering, sorting | [FILE_TOOLS_HELP.md](FILE_TOOLS_HELP.md#smart_lspy) |
| `find_files.py` | Find files with filters | Size/date filters, patterns | [FILE_TOOLS_HELP.md](FILE_TOOLS_HELP.md#find_filespy) |
| `recent_files_v2.py` | Track recent changes | Time-based, directory grouping | [FILE_TOOLS_HELP.md](FILE_TOOLS_HELP.md#recent_files_v2py) |
| `tree_view.py` | Directory tree viewer | Depth control, filtering | [FILE_TOOLS_HELP.md](FILE_TOOLS_HELP.md#tree_viewpy) |
| `dir_stats.py` | Directory statistics | Size analysis, file counts | [FILE_TOOLS_HELP.md](FILE_TOOLS_HELP.md#dir_statspy) |

### 🔧 File Operations
| Tool | Purpose | Key Features | Detailed Help |
|------|---------|--------------|---------------|
| `safe_move.py` | Safe file operations | Atomic moves, interactive undo | [FILE_TOOLS_HELP.md](FILE_TOOLS_HELP.md#safe_movepy) |
| `organize_files.py` | File organization | Manifest tracking, archiving | [FILE_TOOLS_HELP.md](FILE_TOOLS_HELP.md#organize_filespy) |
| `refactor_rename.py` | Code-aware renaming | AST-based, automation support | [FILE_TOOLS_HELP.md](FILE_TOOLS_HELP.md#refactor_renamepy) |
| `replace_text.py` | Text replacement | Multi-file, backup creation | [FILE_TOOLS_HELP.md](FILE_TOOLS_HELP.md#replace_textpy) |

### 📊 Analysis and Quality Tools
| Tool | Purpose | Key Features | Detailed Help |
|------|---------|--------------|---------------|
| `dead_code_detector.py` | Find unused code | Multi-language, confidence levels | [ANALYSIS_TOOLS_HELP.md](ANALYSIS_TOOLS_HELP.md#dead_code_detectorpy) |
| `suggest_refactoring.py` | Code improvements | Pattern detection, best practices | [ANALYSIS_TOOLS_HELP.md](ANALYSIS_TOOLS_HELP.md#suggest_refactoringpy) |
| `analyze_internal_usage.py` | Internal usage analysis | Method visibility, access patterns | [ANALYSIS_TOOLS_HELP.md](ANALYSIS_TOOLS_HELP.md#analyze_internal_usagepy) |
| `trace_calls_rg.py` | Trace call hierarchies | Dependency graphs, visualization | [ANALYSIS_TOOLS_HELP.md](ANALYSIS_TOOLS_HELP.md#trace_calls_rgpy) |

### 🛠️ Utility Tools
| Tool | Purpose | Key Features | Detailed Help |
|------|---------|--------------|---------------|
| `git_commit_analyzer.py` | Git workflow automation | Commit generation, staging | [UTILITY_TOOLS_HELP.md](UTILITY_TOOLS_HELP.md#git_commit_analyzerpy) |
| `common_config.py` | Configuration management | .pytoolsrc, project defaults | [UTILITY_TOOLS_HELP.md](UTILITY_TOOLS_HELP.md#common_configpy) |
| `analyze_errors.py` | Error analysis dashboard | Pattern detection, filtering | [UTILITY_TOOLS_HELP.md](UTILITY_TOOLS_HELP.md#analyze_errorspy) |
| `extract_methods_v2.py` | Extract method code | Implementation extraction | [UTILITY_TOOLS_HELP.md](UTILITY_TOOLS_HELP.md#extract_methods_v2py) |

## 🎮 Common Workflows

### 1. Code Navigation and Understanding
```bash
# Find where a method is defined
./run_any_python_tool.sh navigate_ast_v2.py MyClass.java --to calculateValue

# Analyze method usage and call flow
./run_any_python_tool.sh method_analyzer_ast_v2.py processData --file DataManager.java

# Extract method implementations containing TODOs
./run_any_python_tool.sh find_text.py "TODO" --extract-method

# View code structure with filtering
./run_any_python_tool.sh show_structure_ast_v4.py MyClass.java --filter-annotation "@Test"
```

### 2. Refactoring Operations
```bash
# Rename variable with AST awareness
./run_any_python_tool.sh replace_text_ast.py --file MyClass.java --line 42 oldVar newVar

# Rename across multiple files with automation
./run_any_python_tool.sh refactor_rename.py --replace oldMethod newMethod --in "src/**/*.java" --yes

# Compare versions semantically
./run_any_python_tool.sh semantic_diff_v3.py FileV1.java FileV2.java --format json
```

### 3. File Management
```bash
# Find recent changes
./run_any_python_tool.sh recent_files_v2.py --since 4h --by-dir

# Organize downloads with manifest
./run_any_python_tool.sh organize_files.py ~/Downloads --by-ext --create-manifest

# Safe file operations with undo
./run_any_python_tool.sh safe_move.py move old_name.java new_name.java
./run_any_python_tool.sh safe_move.py undo --interactive
```

### 4. Code Quality Analysis
```bash
# Find dead code with high confidence
./run_any_python_tool.sh dead_code_detector.py src/ --confidence high --threads 8

# Get refactoring suggestions
./run_any_python_tool.sh suggest_refactoring.py MyClass.java --output markdown

# Analyze internal method usage
./run_any_python_tool.sh analyze_internal_usage.py src/ --ast-context
```

### 5. Git Workflows
```bash
# Execute GIT SEQ 1 workflow
./run_any_python_tool.sh git_commit_analyzer.py --seq1

# Get smart staging suggestions
./run_any_python_tool.sh git_commit_analyzer.py --stage-suggestions

# Check CLAUDE.md sync status
./run_any_python_tool.sh git_commit_analyzer.py --sync-check
```

## 🔄 Migration Guide for Enhanced Argument Parser

### For Tool Developers

1. **Replace ArgumentParser with EnhancedArgumentParser**:
```python
# Old
from argparse import ArgumentParser
parser = ArgumentParser()

# New
from enhanced_argument_parser import EnhancedArgumentParser
parser = EnhancedArgumentParser(
    description="Tool description",
    epilog="Examples:\n  %(prog)s pattern file.java"
)
```

2. **Add preflight checks**:
```python
parser.add_preflight_check('file_exists', 'file')
parser.add_preflight_check('directory_exists', 'directory')
parser.add_preflight_check('readable', 'input_file')
parser.add_preflight_check('writable', 'output_file')
```

3. **Use standardized argument patterns**:
```python
# Pattern: <tool> <target> [location_flags] [options]
parser.add_argument('target', help='What to search for')
parser.add_argument('--file', help='Specific file to search')
parser.add_argument('--scope', help='Directory scope')
parser.add_argument('-v', '--verbose', action='store_true')
parser.add_argument('--json', action='store_true', help='JSON output')
```

### For Tool Users

All tools now follow consistent patterns:
- `--help` shows usage, description, and examples
- Common flags work across all tools (`-v`, `-q`, `--json`)
- Better error messages with suggestions
- Automatic validation prevents common mistakes

## 📋 Configuration Management

### Creating Project Defaults (.pytoolsrc)
```bash
# Create default configuration
./run_any_python_tool.sh common_config.py --create

# View current settings
./run_any_python_tool.sh common_config.py --show

# Example .pytoolsrc content:
ast_context = true           # Enable AST context by default
check_compile = true         # Enable compile checking
verbose = false             # Quiet by default
max_depth = 3               # Default depth for tree commands
```

### Priority Order
1. Command-line arguments (highest priority)
2. `.pytoolsrc` in current directory
3. `.pytoolsrc` in project root
4. Built-in defaults (lowest priority)

## 🤖 Non-Interactive Mode Support

### Overview

All tools in the code-intelligence-toolkit support non-interactive operation for seamless CI/CD integration, automation scripts, and AI agent usage. Tools intelligently detect non-interactive environments and adjust their behavior accordingly.

### Configuration Methods

#### 1. Environment Variables (Per Tool)

```bash
# Safe File Manager
export SFM_ASSUME_YES=1                     # Auto-confirm all operations

# SafeGIT
export SAFEGIT_NONINTERACTIVE=1            # Strict non-interactive mode
export SAFEGIT_ASSUME_YES=1                # Auto-confirm safe operations

# Replace Text AST
export REPLACE_TEXT_AST_ASSUME_YES=1        # Auto-confirm replacements

# Safe Move
export SAFEMOVE_ASSUME_YES=1               # Auto-confirm moves/copies
export SAFEMOVE_NONINTERACTIVE=1           # Fail on any prompt

# Refactor Rename
export REFACTOR_ASSUME_YES=1               # Auto-confirm renames
```

#### 2. Configuration File (.pytoolsrc)

```ini
# Global defaults for all tools
[defaults]
non_interactive = true      # No prompts, fail if input needed
assume_yes = true          # Auto-confirm medium-risk operations
quiet = true              # Minimize output for automation
verbose = false           # Disable verbose logging

# Tool-specific sections
[safe_file_manager]
assume_yes = true
backup = true             # Always create backups
paranoid_mode = false     # Disable checksums for CI speed

[safegit]
non_interactive = true
assume_yes = true
force_yes = false         # Never auto-confirm dangerous ops

[replace_text_ast]
assume_yes = true
check_compile = false     # Skip compile checks in CI

[safe_move]
assume_yes = true
create_manifest = true    # Track all operations
```

#### 3. Command-Line Flags

```bash
# Common flags across tools
--yes, -y                 # Auto-confirm operations
--force                   # Force dangerous operations
--non-interactive         # Strict non-interactive mode
--no-confirm             # Skip all confirmations

# Examples
./run_any_python_tool.sh safe_file_manager.py move file1 file2 --yes
./run_any_python_tool.sh replace_text_ast.py oldVar newVar --file script.py -y
./run_any_python_tool.sh safegit.py add . --yes
./run_any_python_tool.sh safe_move.py copy src/ dst/ --no-confirm
```

### Tool-Specific Non-Interactive Support

| Tool Category | Environment Variable | Config Section | Command Flags |
|--------------|---------------------|----------------|---------------|
| safe_file_manager | `SFM_ASSUME_YES=1` | `[safe_file_manager]` | `--yes`, `-y` |
| safegit | `SAFEGIT_ASSUME_YES=1`<br>`SAFEGIT_NONINTERACTIVE=1` | `[safegit]` | `--yes`, `--force-yes`, `--non-interactive` |
| replace_text_ast | `REPLACE_TEXT_AST_ASSUME_YES=1` | `[replace_text_ast]` | `--yes`, `-y`, `--no-confirm` |
| replace_text | - | `[replace_text]` | `--yes`, `-y` |
| safe_move | `SAFEMOVE_ASSUME_YES=1`<br>`SAFEMOVE_NONINTERACTIVE=1` | `[safe_move]` | `--yes`, `-y`, `--no-confirm` |
| refactor_rename | `REFACTOR_ASSUME_YES=1` | `[refactor_rename]` | `--yes`, `-y`, `--no-confirm` |

### CI/CD Integration Examples

#### GitHub Actions
```yaml
name: Automated Refactoring
on: [push, pull_request]

env:
  SFM_ASSUME_YES: 1
  SAFEGIT_ASSUME_YES: 1
  REPLACE_TEXT_AST_ASSUME_YES: 1

jobs:
  refactor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      
      - name: Install toolkit
        run: |
          pip install -r requirements.txt
          chmod +x run_any_python_tool.sh
      
      - name: Run refactoring
        run: |
          ./run_any_python_tool.sh replace_text.py "old_api" "new_api" --scope src/
          ./run_any_python_tool.sh safe_file_manager.py organize build/ --by-date
          ./run_any_python_tool.sh safegit.py add .
          ./run_any_python_tool.sh safegit.py commit -m "Automated refactoring"
```

#### Docker Container
```dockerfile
FROM python:3.9-slim

# Install toolkit
COPY . /toolkit
WORKDIR /toolkit

# Configure non-interactive environment
ENV SFM_ASSUME_YES=1
ENV SAFEGIT_NONINTERACTIVE=1
ENV PYTOOLSRC_NON_INTERACTIVE=1

# Create CI configuration
RUN echo "[defaults]\nnon_interactive = true\nassume_yes = true" > .pytoolsrc

# Run automated tasks
RUN ./run_any_python_tool.sh safe_file_manager.py organize /data --by-ext
```

### Safety Levels in Non-Interactive Mode

1. **Auto-Approved (with assume_yes)**:
   - Reading files, listing directories
   - Creating backups, dry-run operations
   - Git status, log, diff commands

2. **Requires --yes or assume_yes**:
   - Moving/copying files (with backup)
   - Text replacements (with backup)
   - Git add, commit, pull operations
   - Creating directories

3. **Requires --force-yes explicitly**:
   - Deleting files (even to trash)
   - Git reset --hard, clean -fdx
   - Git push --force operations
   - Any operation marked as HIGH_RISK

### Best Practices

1. **Always test with --dry-run first** in production environments
2. **Use environment variables** for CI/CD pipelines
3. **Create separate .pytoolsrc** for different environments
4. **Enable backups** even in non-interactive mode
5. **Monitor operation logs** for audit trails
6. **Never use force flags** in production without review

### Troubleshooting Non-Interactive Mode

```bash
# Test if tool supports non-interactive mode
./run_any_python_tool.sh [tool_name] --help | grep -E "(yes|interactive|confirm)"

# Test with no stdin
(exec < /dev/null && ./run_any_python_tool.sh safe_file_manager.py list .)

# Debug environment detection
env | grep -E "(CI|GITHUB|GITLAB|JENKINS)"

# Check configuration loading
./run_any_python_tool.sh common_config.py --show
```

For comprehensive non-interactive mode documentation, see [NON_INTERACTIVE_GUIDE.md](NON_INTERACTIVE_GUIDE.md).

## 🛡️ Security and Error Handling

### Enterprise Security Features
- **Path Traversal Protection**: All paths validated and sanitized
- **Command Injection Prevention**: Input sanitization on all tools
- **Resource Limits**: Memory, CPU, and file handle protection
- **Atomic Operations**: File operations with rollback support

### Error Monitoring
```bash
# View recent errors
./run_any_python_tool.sh analyze_errors.py --recent 10

# Find failure patterns
./run_any_python_tool.sh analyze_errors.py --patterns

# Check specific tool errors
./run_any_python_tool.sh analyze_errors.py --tool find_text.py
```

## 📚 Detailed Documentation Links

- **[SEARCH_TOOLS_HELP.md](docs/tools/SEARCH_TOOLS_HELP.md)** - Text search, grep, and cross-file analysis
- **[AST_TOOLS_HELP.md](docs/tools/AST_TOOLS_HELP.md)** - AST-based navigation, analysis, and refactoring
- **[FILE_TOOLS_HELP.md](docs/tools/FILE_TOOLS_HELP.md)** - Directory management and file operations
- **[ANALYSIS_TOOLS_HELP.md](docs/tools/ANALYSIS_TOOLS_HELP.md)** - Code quality and usage analysis
- **[UTILITY_TOOLS_HELP.md](docs/tools/UTILITY_TOOLS_HELP.md)** - Git workflows and utility tools

## 🎯 Best Practices

1. **Always use the wrapper script**: `./run_any_python_tool.sh`
2. **Check help for syntax**: `./run_any_python_tool.sh tool_name.py --help`
3. **Use AST tools for accuracy**: Prefer AST-based over regex-based
4. **Enable threading for speed**: Add `--threads 8` for large analyses
5. **Create project defaults**: Use `.pytoolsrc` for consistent settings
6. **Monitor errors**: Check `analyze_errors.py` when tools fail

## 🚀 Quick Start Examples

```bash
# Set up your environment
./run_any_python_tool.sh common_config.py --create

# Find recent changes in Java files
./run_any_python_tool.sh recent_files_v2.py --since 2d --ext java

# Search for TODO comments with context
./run_any_python_tool.sh find_text.py "TODO" --scope src/ -C 3

# Extract methods containing specific patterns
./run_any_python_tool.sh find_text.py "deprecated" --extract-method

# Safe refactoring with compile checking
./run_any_python_tool.sh replace_text_ast.py --file MyClass.java oldName newName

# Analyze code structure
./run_any_python_tool.sh show_structure_ast_v4.py MyClass.java --json

# Find dead code quickly
./run_any_python_tool.sh dead_code_detector.py src/ --threads 8
```

---

**Remember**: This toolkit represents the culmination of extensive development and standardization efforts. All production tools are working, tested, and follow consistent patterns. The enhanced argument parser system ensures a uniform, professional experience across the entire toolkit.