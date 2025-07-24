<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Enhanced Parser Guide

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-20
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Enhanced Parser Guide

**Related Code Files:**
- `scripts/python_tools/enhanced_parsers.py` - Core enhanced parser implementation
- `scripts/python_tools/find_text.py` - Example search tool using enhanced parser
- `scripts/python_tools/smart_ls.py` - Example directory tool using enhanced parser
- `scripts/python_tools/method_analyzer_ast.py` - Example analysis tool using enhanced parser

---

## Overview

The Enhanced Parser System provides standardized argument parsing for Python development tools, ensuring consistency across the entire toolkit. It offers three specialized parser types (search, analyze, directory) with common arguments, automatic conflict resolution, and enterprise-grade features.

### Key Benefits
- **Consistency**: All tools use the same argument patterns
- **No Conflicts**: Automatic resolution of argparse partial matching issues
- **Enterprise Features**: Built-in logging, error handling, and security
- **Easy Migration**: Drop-in replacement for standard argparse

## The Three Parser Types

### 1. Search Parser
Used for tools that search for patterns in files.

**Standard Arguments:**
```python
# Core search arguments
--file FILE                  # Search in specific file
--scope SCOPE               # Search in directory/scope
--ext EXT                   # Filter by extension
-g, --glob PATTERN          # Glob pattern filter
-r, --recursive             # Recursive search (default: True)
--no-recursive              # Disable recursive search

# Output control
-v, --verbose               # Verbose output
-q, --quiet                 # Quiet mode
--json                      # JSON output format
--output FILE               # Write output to file

# Common options
--threads N                 # Parallel processing threads
--timeout SECONDS           # Operation timeout
--limit N, --max N          # Limit results (with alias)
```

**Example Usage:**
```python
from enhanced_parsers import create_enhanced_parser

parser = create_enhanced_parser(
    'search',
    description='Search for text patterns in files'
)

# Add tool-specific arguments
parser.add_argument('pattern', help='Pattern to search for')
parser.add_argument('-i', '--ignore-case', action='store_true',
                   help='Case insensitive search')

args = parser.parse_args()
```

### 2. Analyze Parser
Used for tools that analyze code structure, dependencies, or quality.

**Standard Arguments:**
```python
# Core analysis arguments
TARGET                      # What to analyze (file/method/class)
--file FILE                 # Analyze specific file
--scope SCOPE              # Analyze directory/scope
--type TYPE                # Analysis type (method/class/function)

# Output control
-v, --verbose              # Verbose output
-q, --quiet                # Quiet mode
--json                     # JSON output format
--output FILE              # Write output to file

# Analysis options
--detailed                 # Detailed analysis
--ast-context              # Show AST context
--no-ast-context           # Disable AST context
--threads N                # Parallel processing
--timeout SECONDS          # Operation timeout
```

**Example Usage:**
```python
parser = create_enhanced_parser(
    'analyze',
    description='Analyze code structure and dependencies'
)

# Add analysis-specific arguments
parser.add_argument('--depth', type=int, default=3,
                   help='Analysis depth')
parser.add_argument('--show-imports', action='store_true',
                   help='Show import analysis')

args = parser.parse_args()
```

### 3. Directory Parser
Used for tools that operate on directories and files.

**Standard Arguments:**
```python
# Core directory arguments
PATH                       # Directory path (positional)
--ext EXT                  # Filter by extension
-g, --glob PATTERN         # Glob pattern filter
-r, --recursive            # Recursive operation
--no-recursive             # Disable recursive

# Output control
-v, --verbose              # Verbose output
-q, --quiet                # Quiet mode
--json                     # JSON output format
--output FILE              # Write output to file

# Directory options
--limit N, --max N         # Limit results (with alias)
--sort FIELD               # Sort by field
--reverse                  # Reverse sort order
--size-format FORMAT       # Size display format
--show-hidden              # Include hidden files
```

**Example Usage:**
```python
parser = create_enhanced_parser(
    'directory',
    description='Enhanced directory listing tool'
)

# Add directory-specific arguments
parser.add_argument('--group-by', choices=['ext', 'dir', 'size'],
                   help='Group results by criteria')
parser.add_argument('--min-size', type=str,
                   help='Minimum file size (e.g., 1M, 100K)')

args = parser.parse_args()
```

## Migration Guide

### Step 1: Identify Parser Type
Determine which parser type fits your tool:
- **Search**: Tools that find patterns in files
- **Analyze**: Tools that analyze code structure
- **Directory**: Tools that work with files/directories

### Step 2: Replace ArgumentParser
```python
# Old code
import argparse
parser = argparse.ArgumentParser(description='My tool')

# New code
from enhanced_parsers import create_enhanced_parser
parser = create_enhanced_parser('search', description='My tool')
```

### Step 3: Review Existing Arguments
Check for conflicts with standard arguments:
```python
# If you had custom --limit argument
parser.add_argument('--limit', ...)  # Remove this

# Use the standard limit/max instead
# It's already included with alias support
```

### Step 4: Add Tool-Specific Arguments
```python
# Add only arguments unique to your tool
parser.add_argument('--my-special-option', 
                   help='Tool-specific functionality')
```

### Step 5: Test Thoroughly
```bash
# Test standard arguments work
./tool.py --help
./tool.py pattern --file test.py --verbose
./tool.py pattern --scope src/ --limit 10
./tool.py pattern --scope src/ --max 10  # Alias should work
```

## Conflict Resolution Strategies

### 1. Automatic Aliasing
The enhanced parser automatically adds aliases for common conflicts:
```python
# --limit automatically gets --max alias
# Users can use either:
./tool.py --limit 10
./tool.py --max 10
```

### 2. Parser Exclusions
Some arguments are excluded from certain parser types:
```python
# Directory parser doesn't include:
# --type (conflicts with file type filtering)
# --ast-context (not applicable to directory ops)
```

### 3. Custom Conflict Resolution
Override standard arguments if needed:
```python
parser = create_enhanced_parser('search', description='My tool')

# Remove standard argument
for action in parser._actions:
    if '--threads' in action.option_strings:
        parser._remove_action(action)
        break

# Add custom version
parser.add_argument('--threads', type=int, default=1,
                   help='Number of worker threads (max 4)')
```

## Code Examples

### Complete Search Tool
```python
#!/usr/bin/env python3
"""Enhanced text search tool."""

import sys
from enhanced_parsers import create_enhanced_parser

def main():
    parser = create_enhanced_parser(
        'search',
        description='Search for text patterns with context'
    )
    
    # Add search-specific arguments
    parser.add_argument('pattern', help='Pattern to search for')
    parser.add_argument('-i', '--ignore-case', action='store_true',
                       help='Case insensitive search')
    parser.add_argument('-C', '--context', type=int, default=0,
                       help='Lines of context')
    
    args = parser.parse_args()
    
    # Use standard arguments
    if args.file:
        search_file(args.file, args.pattern, args)
    elif args.scope:
        search_directory(args.scope, args.pattern, args)
    else:
        parser.error("Either --file or --scope required")

def search_file(filepath, pattern, args):
    """Search in a single file."""
    # Implementation using args.verbose, args.json, etc.
    pass

def search_directory(directory, pattern, args):
    """Search in directory."""
    # Use args.recursive, args.glob, args.ext, etc.
    pass

if __name__ == '__main__':
    main()
```

### Complete Analysis Tool
```python
#!/usr/bin/env python3
"""Code structure analyzer."""

from enhanced_parsers import create_enhanced_parser

def main():
    parser = create_enhanced_parser(
        'analyze',
        description='Analyze code structure and dependencies'
    )
    
    # Target is already added as positional
    parser.add_argument('--show-calls', action='store_true',
                       help='Show method calls')
    parser.add_argument('--max-depth', type=int, default=3,
                       help='Maximum analysis depth')
    
    args = parser.parse_args()
    
    # Analyze based on args.type
    if args.type == 'method':
        analyze_method(args.target, args)
    elif args.type == 'class':
        analyze_class(args.target, args)

if __name__ == '__main__':
    main()
```

### Complete Directory Tool
```python
#!/usr/bin/env python3
"""Enhanced directory operations."""

from enhanced_parsers import create_enhanced_parser

def main():
    parser = create_enhanced_parser(
        'directory',
        description='Smart directory listing and analysis'
    )
    
    # Path is already added as positional
    parser.add_argument('--min-size', type=str,
                       help='Minimum file size (e.g., 1M)')
    parser.add_argument('--max-size', type=str,
                       help='Maximum file size (e.g., 10M)')
    
    args = parser.parse_args()
    
    # List directory with filters
    list_directory(args.path, args)

def list_directory(path, args):
    """List directory contents."""
    # Use args.ext, args.glob, args.recursive, etc.
    # Use args.limit or args.max (same thing due to alias)
    pass

if __name__ == '__main__':
    main()
```

## Common Patterns and Best Practices

### 1. Version Management
```python
# Always set version for tracking
parser = create_enhanced_parser(
    'search',
    description='My search tool',
    version='2.0.0'  # Optional but recommended
)
```

### 2. Argument Validation
```python
# Validate combinations in parse_args override
class MyParser(EnhancedArgumentParser):
    def parse_args(self, args=None, namespace=None):
        args = super().parse_args(args, namespace)
        
        # Custom validation
        if args.file and args.scope:
            self.error("Cannot use both --file and --scope")
        
        return args
```

### 3. Default Handling
```python
# Set sensible defaults for your tool
parser.set_defaults(
    recursive=True,      # Override standard default
    threads=4,           # Tool-specific default
    ast_context=True     # Enable by default
)
```

### 4. Help Text Enhancement
```python
# Add examples to help
parser.epilog = """
Examples:
  %(prog)s "TODO" --file main.py
  %(prog)s "import.*" --scope src/ --type regex
  %(prog)s "def.*test" --scope tests/ -r
"""
```

### 5. Exit Code Standards
```python
# Use consistent exit codes
def main():
    try:
        # ... tool logic ...
        return 0  # Success
    except KeyboardInterrupt:
        return 130  # Ctrl+C
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1  # General error
```

## Troubleshooting Guide

### Issue: Argument Conflict
**Symptom**: `ArgumentError: argument --limit: conflicting option string`

**Solution**: The enhanced parser handles common conflicts. Check if:
1. You're using the right parser type
2. You're not manually adding standard arguments
3. You need to exclude the argument first

### Issue: Partial Matching Problems
**Symptom**: `--ma` matches both `--max` and `--match`

**Solution**: Enhanced parser disables partial matching by default. Users must type full argument names or use short versions.

### Issue: Missing Standard Arguments
**Symptom**: `--ast-context` not available in directory tool

**Solution**: Some arguments are excluded by parser type. Check the parser type's standard arguments list.

### Issue: Import Errors
**Symptom**: `ImportError: cannot import name 'create_enhanced_parser'`

**Solution**: Ensure enhanced_parsers.py is in your Python path:
```bash
export PYTHONPATH=/path/to/scripts/python_tools:$PYTHONPATH
```

### Issue: Version Compatibility
**Symptom**: Different behavior in different environments

**Solution**: Check Python version (requires 3.6+) and ensure latest enhanced_parsers.py version.

## Advanced Topics

### Custom Parser Types
Create your own parser type:
```python
def create_custom_parser():
    parser = EnhancedArgumentParser()
    
    # Add your standard arguments
    parser.add_argument('--custom-arg', help='Custom standard arg')
    
    # Set parser type for identification
    parser.parser_type = 'custom'
    
    return parser
```

### Integration with .pytoolsrc
Enhanced parsers automatically respect .pytoolsrc settings:
```ini
[DEFAULT]
verbose = true
ast_context = true
threads = 8
```

### Performance Considerations
- Use `--threads` for parallel operations
- Set reasonable `--timeout` values
- Use `--limit` to cap results in large operations

## Summary

The Enhanced Parser System provides a robust foundation for Python development tools with:
- Standardized argument patterns across all tools
- Automatic conflict resolution
- Enterprise-grade features
- Easy migration path

By following this guide, you can create consistent, professional tools that integrate seamlessly with the existing toolkit while avoiding common argparse pitfalls.