<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Analysis Tools Help Documentation

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-20
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Analysis Tools Help Documentation

**Related Code Files:**
- `dead_code_detector.py` - Multi-language dead code detection
- `suggest_refactoring.py` - Java refactoring suggestions
- `analyze_unused_methods_with_timeout.py` - Find unused methods with timeout
- `trace_calls_with_timeout.py` - Method call hierarchy tracing
- `analyze_internal_usage.py` - Internal method usage analysis
- `git_commit_analyzer.py` - Git change analysis and commit messages

---

## Overview

This document provides comprehensive help documentation for the analysis tools in the Java Intelligence Analysis Toolkit. These tools provide advanced code analysis capabilities including dead code detection, refactoring suggestions, method usage analysis, and git workflow automation.

## Table of Contents

1. [dead_code_detector.py](#dead_code_detectorpy)
2. [suggest_refactoring.py](#suggest_refactoringpy)
3. [analyze_unused_methods_with_timeout.py](#analyze_unused_methods_with_timeoutpy)
4. [trace_calls_with_timeout.py](#trace_calls_with_timeoutpy)
5. [analyze_internal_usage.py](#analyze_internal_usagepy)
6. [git_commit_analyzer.py](#git_commit_analyzerpy)

---

## dead_code_detector.py

### Description
Multi-language dead code finder supporting Python, Java, and JavaScript/TypeScript. Features confidence levels (high/medium/low), framework awareness, dynamic usage detection, and parallel processing.

### Usage
```bash
python3 dead_code_detector.py [-h] [--file FILE] [--scope SCOPE]
                             [--type {method,class,function,variable,auto}]
                             [--max-depth MAX_DEPTH] [--show-callers]
                             [--show-callees] [-v] [-q] [--json]
                             [--language {auto,python,java,javascript}]
                             [--format {text,json,markdown}]
                             [--confidence {all,high,medium,low}]
                             [--threads THREADS]
                             [--ignore-pattern IGNORE_PATTERN] [--no-git]
                             [--timeout TIMEOUT] [--generate-ignore]
                             [--ast-context] [--no-ast-context]
                             target [path]
```

### Key Features
- **Multi-language support**: Python, Java, JavaScript/TypeScript
- **Confidence levels**: HIGH (definitely dead), MEDIUM (likely dead), LOW (possibly dead)
- **Framework awareness**: Recognizes test methods, main methods, Spring annotations
- **Parallel processing**: Use `--threads` for faster analysis
- **Multiple output formats**: text, JSON, markdown
- **AST context**: Shows class/method hierarchy for findings
- **Timeout protection**: Configurable timeout (default 30s)
- **Git integration**: Automatically filters using gitignore

### Options
- `target`: Name of method/class/symbol to analyze
- `path`: Path to analyze (default: current directory)
- `--file FILE`: Analyze in specific file
- `--scope SCOPE`: Directory scope for analysis
- `--type`: Type of symbol (method/class/function/variable/auto)
- `--language`: Language to analyze (auto-detect by default)
- `--format, -f`: Output format (text/json/markdown)
- `--confidence, -c`: Minimum confidence level to report
- `--threads`: Number of ripgrep worker threads
- `--ignore-pattern`: Regex patterns to ignore (can be used multiple times)
- `--no-git`: Don't use git to filter files
- `--timeout`: Timeout for subprocess commands in seconds
- `--generate-ignore`: Generate .deadcodeignore file from findings
- `--ast-context/--no-ast-context`: Enable/disable AST context display

### Examples
```bash
# Find all dead code in current directory
python3 dead_code_detector.py .

# Find high-confidence dead Java code
python3 dead_code_detector.py . --language java --confidence high

# Find dead code with 8 threads for speed
python3 dead_code_detector.py . --threads 8

# Generate markdown report
python3 dead_code_detector.py . --format markdown > dead_code_report.md

# Analyze specific file
python3 dead_code_detector.py MyClass --file src/MyClass.java

# Generate ignore file for false positives
python3 dead_code_detector.py . --generate-ignore
```

---

## suggest_refactoring.py

### Description
Analyzes Java files to suggest refactoring opportunities including long methods, complex methods, code duplication, and design pattern opportunities.

### Usage
```bash
python3 suggest_refactoring.py [-h] [--file FILE] [--scope SCOPE]
                              [--type {method,class,function,variable,auto}]
                              [--max-depth MAX_DEPTH] [--show-callers]
                              [--show-callees] [-v] [-q] [--json]
                              [--min-method-size MIN_METHOD_SIZE]
                              [--check-duplication] [--no-duplication]
                              [--output {text,markdown}]
                              target
```

### Key Features
- **Long method detection**: Identifies methods exceeding size threshold
- **Complexity analysis**: Detects highly complex methods
- **Duplication detection**: Finds duplicate code blocks
- **Design pattern suggestions**: Recommends applicable patterns
- **Refactoring priorities**: Ranks suggestions by impact
- **Markdown output**: Generate formatted reports

### Options
- `target`: File or directory to analyze
- `--file FILE`: Analyze specific file
- `--scope SCOPE`: Directory scope for analysis
- `--min-method-size`: Minimum lines for large method (default: 50)
- `--check-duplication`: Enable duplicate code detection
- `--no-duplication`: Skip duplicate code detection
- `--output`: Output format (text/markdown)

### Examples
```bash
# Analyze single Java file
python3 suggest_refactoring.py MyClass.java

# Analyze entire source directory
python3 suggest_refactoring.py src/

# Check for long methods (>100 lines)
python3 suggest_refactoring.py src/ --min-method-size 100

# Generate markdown report with duplication check
python3 suggest_refactoring.py src/ --check-duplication --output markdown

# Analyze specific file in directory
python3 suggest_refactoring.py MyClass --file src/main/java/MyClass.java
```

---

## analyze_unused_methods_with_timeout.py

### Description
Wrapper script that runs analyze_unused_methods_rg.py with a 60-second timeout to prevent hanging on large codebases.

### Usage
```bash
python3 analyze_unused_methods_with_timeout.py [all arguments passed to analyze_unused_methods_rg.py]
```

### Key Features
- **Automatic timeout**: 60-second limit (configurable via UNUSED_METHODS_TIMEOUT env var)
- **Full feature passthrough**: All features of analyze_unused_methods_rg.py
- **Clean termination**: Graceful handling of timeouts
- **Error reporting**: Clear timeout messages

### Note
This script has a syntax error in the wrapped script (analyze_unused_methods_rg.py) on line 282. The script needs to be fixed before it can be used effectively.

---

## trace_calls_with_timeout.py

### Description
Traces method call hierarchies using ripgrep with automatic 30-second timeout protection.

### Usage
```bash
python3 trace_calls_with_timeout.py [arguments]
```

The wrapped script (trace_calls_rg.py) supports:
```bash
trace_calls_rg.py [-h] [--file FILE] [--scope SCOPE]
                  [--type {method,class,function,variable,auto}]
                  [--max-depth MAX_DEPTH] [--show-callers]
                  [--show-callees] [-v] [-q] [--json]
                  [--source-file SOURCE_FILE]
                  [--direction {up,down,both}]
                  target
```

### Key Features
- **Bidirectional tracing**: Trace callers (up), callees (down), or both
- **Call hierarchy visualization**: Shows complete call chains
- **Depth control**: Configurable maximum trace depth
- **Source file specification**: Specify file containing the method
- **JSON output**: Machine-readable format for integration

### Options
- `target`: Method name to trace
- `--source-file`: File containing the method (for callee tracing)
- `--direction`: Trace direction (up/down/both)
- `--max-depth`: Maximum depth for analysis
- `--show-callers`: Show where symbol is called from
- `--show-callees`: Show what symbol calls

### Examples
```bash
# Trace all callers of processData method
python3 trace_calls_with_timeout.py processData --direction up

# Trace what sendNotification calls
python3 trace_calls_with_timeout.py sendNotification --direction down --source-file NotificationService.java

# Full bidirectional trace with depth limit
python3 trace_calls_with_timeout.py handleRequest --direction both --max-depth 3

# JSON output for tooling
python3 trace_calls_with_timeout.py validate --json > call_trace.json
```

---

## analyze_internal_usage.py

### Description
Analyzes internal method usage within Java classes to understand how methods are used within their own class context.

### Usage
```bash
python3 analyze_internal_usage.py [-h] [--file FILE] [--scope SCOPE]
                                 [--type {method,class,function,variable,auto}]
                                 [--max-depth MAX_DEPTH] [--show-callers]
                                 [--show-callees] [-v] [-q] [--json]
                                 [--ast-context]
                                 target
```

### Key Features
- **Internal usage analysis**: Focuses on intra-class method calls
- **Private method tracking**: Identifies usage of private methods
- **Helper method detection**: Finds internal helper patterns
- **AST context support**: Shows method hierarchy
- **Directory traversal**: Analyze multiple files at once

### Options
- `target`: File or directory to analyze
- `--file FILE`: Analyze specific file
- `--scope SCOPE`: Directory scope for analysis
- `--ast-context`: Show AST context for results
- `--show-callers`: Show internal callers
- `--show-callees`: Show internal callees

### Examples
```bash
# Analyze internal usage in single file
python3 analyze_internal_usage.py OrderProcessor.java

# Analyze all Java files in directory
python3 analyze_internal_usage.py src/main/java/

# Show AST context for better understanding
python3 analyze_internal_usage.py MyService.java --ast-context

# Focus on specific file in directory
python3 analyze_internal_usage.py processData --file src/DataProcessor.java
```

---

## git_commit_analyzer.py

### Description
Comprehensive git workflow tool that analyzes staged changes, generates commit messages, and supports various git workflows (GIT SEQ 1/2, SYNC CHECK, etc.).

### Usage
```bash
python3 git_commit_analyzer.py [-h] [--file FILE] [--scope SCOPE]
                              [--type {method,class,function,variable,auto}]
                              [--max-depth MAX_DEPTH] [--show-callers]
                              [--show-callees] [-v] [-q] [--json]
                              [--full-diff] [--stage-suggestions]
                              [--sync-check] [--seq1] [--detailed]
                              [--timeout TIMEOUT]
                              target
```

### Key Features
- **GIT SEQ 1**: Auto-commit with generated message
- **GIT SEQ 2**: Commit with confirmation message
- **GIT SEQ STAGE**: Smart staging suggestions
- **SYNC CHECK**: Check for CLAUDE.md updates
- **Commit message generation**: Analyzes changes to create meaningful messages
- **Full diff output**: For comprehensive analysis
- **Timeout protection**: Configurable git command timeout

### Options
- `target`: Analysis target (use "analyze" for general analysis)
- `--full-diff`: Output full diff content
- `--stage-suggestions`: Show smart staging suggestions
- `--sync-check`: Check CLAUDE.md status
- `--seq1`: Execute GIT SEQ 1 workflow
- `--detailed`: Generate detailed commit message with body
- `--timeout`: Git command timeout in seconds (default: 15)

### Examples
```bash
# Get staging suggestions (GIT SEQ STAGE)
python3 git_commit_analyzer.py analyze --stage-suggestions

# Analyze changes and suggest commit message (GIT SEQ 2)
python3 git_commit_analyzer.py analyze

# Execute GIT SEQ 1 workflow
python3 git_commit_analyzer.py analyze --seq1

# Check CLAUDE.md synchronization
python3 git_commit_analyzer.py analyze --sync-check

# Get full diff for external analysis
python3 git_commit_analyzer.py analyze --full-diff > changes.diff

# Generate detailed commit message
python3 git_commit_analyzer.py analyze --detailed
```

### Commit Message Patterns
The tool generates commit messages based on change patterns:
- `feat:` New features
- `fix:` Bug fixes
- `refactor:` Code restructuring
- `docs:` Documentation only
- `test:` Test additions/changes
- `perf:` Performance improvements
- `chore:` Maintenance tasks

---

## Common Usage Patterns

### Comprehensive Code Analysis
```bash
# Full dead code analysis with report
python3 dead_code_detector.py . --language java --format markdown > dead_code.md

# Refactoring opportunities
python3 suggest_refactoring.py src/ --check-duplication --output markdown > refactoring.md

# Method usage analysis
python3 analyze_internal_usage.py src/ --ast-context > internal_usage.txt
```

### Git Workflow Automation
```bash
# Standard workflow
python3 git_commit_analyzer.py analyze --stage-suggestions  # Review what to stage
git add [files]                                              # Stage files
python3 git_commit_analyzer.py analyze                      # Generate commit message
git commit -m "generated message"                            # Commit
```

### Performance Optimization
```bash
# Fast parallel analysis
python3 dead_code_detector.py . --threads 8 --confidence high

# Quick trace with timeout
python3 trace_calls_with_timeout.py criticalMethod --max-depth 2
```

## Environment Variables

- `DEAD_CODE_TIMEOUT`: Timeout for dead code detector (default: 30s)
- `UNUSED_METHODS_TIMEOUT`: Timeout for unused methods analysis (default: 60s)
- `TRACE_CALLS_TIMEOUT`: Timeout for call tracing (default: 30s)

## Troubleshooting

1. **Timeout Issues**: Increase timeout via environment variables
2. **Syntax Errors**: Some tools may have parsing issues with complex Java code
3. **Performance**: Use `--threads` option for faster analysis on multi-core systems
4. **False Positives**: Use `--generate-ignore` to create ignore files

## Best Practices

1. **Start with high confidence**: Use `--confidence high` to focus on definite issues
2. **Use appropriate scope**: Analyze specific packages rather than entire codebases
3. **Leverage parallelism**: Use multiple threads for large codebases
4. **Generate reports**: Use markdown output for documentation
5. **Regular analysis**: Integrate into CI/CD pipelines with JSON output