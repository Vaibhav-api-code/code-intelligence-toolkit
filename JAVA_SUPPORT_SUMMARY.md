<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Java Support Summary for AST Context Tools

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-08
Updated: 2025-07-08
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Java Support Summary for AST Context Tools

**Date**: January 9, 2025

## Overview

All AST context tools support Java files through the `javalang` library. The `ast_context_finder.py` module provides unified Java support for all tools.

## Test Results for Java Files

| Tool | Java Support | AST Context | Notes |
|------|--------------|-------------|-------|
| **find_text_v3.py** | ✅ Excellent | Yes | Shows context like `[TestASTContext(6-42) → processData(14-20)]` |
| **dead_code_detector.py** | ✅ Excellent | Yes | Properly analyzes Java code structure |
| **cross_file_analysis_ast.py** | ✅ Excellent | Yes | Uses CallerIdentifier for Java AST analysis |
| **method_analyzer_ast.py** | ✅ Excellent | Yes | Uses javalang for method analysis |
| **find_references_rg.py** | ✅ Excellent | Yes | Pattern-based search with AST context |
| **analyze_unused_methods_rg.py** | ✅ Excellent | Yes | Java-specific method patterns |
| **navigate.py** | ✅ Excellent | Yes | Java-aware navigation |
| **trace_calls.py** | ✅ Excellent | Yes | Enhanced with AST-based caller identification |
| **analyze_internal_usage.py** | ✅ Excellent | Yes | Java regex patterns for method detection |
| **replace_text_ast.py** | ⚠️ Limited | Yes | Basic Java support, not as robust as Python |

## Key Features for Java

### 1. AST Context Display
All tools show hierarchical context for Java code:
```
[TestASTContext(6-42) → processData(14-20)]
```
This shows the class name with line range, and the method name with line range.

### 2. Java-Specific Patterns
Tools use Java-specific regex patterns for:
- Method definitions: `public/private/protected` modifiers
- Class declarations
- Import statements
- Package declarations

### 3. Javalang Integration
When available, tools use the `javalang` library for proper Java AST parsing:
- Accurate method boundaries
- Proper handling of nested classes
- Understanding of Java syntax

## Limitations

### replace_text_ast.py
The Java support in `replace_text_ast.py` is more limited compared to Python:
- Basic scope tracking using javalang
- Simple regex-based renaming within scope
- Not as sophisticated as the rope-based Python refactoring

**Workaround**: For complex Java refactoring, consider using dedicated Java IDEs or tools like:
- IntelliJ IDEA's refactoring tools
- Eclipse's refactoring capabilities
- OpenRewrite for programmatic refactoring

## Requirements

For full Java support, ensure `javalang` is installed:
```bash
pip install javalang
```

## Example Java Analysis

```bash
# Find text in Java files with context
./run_any_python_tool.sh find_text_v3.py "processData" --scope src/ --ast-context

# Analyze Java method calls
./run_any_python_tool.sh method_analyzer_ast.py calculateValue --file PriceCalculator.java --ast-context

# Trace Java call hierarchy
./run_any_python_tool.sh trace_calls.py handleRequest --file RequestHandler.java --ast-context

# Find dead code in Java project
./run_any_python_tool.sh dead_code_detector.py src/ --language java --ast-context
```

## Conclusion

The AST context feature works excellently with Java files across 9 out of 10 tools. Only `replace_text_ast.py` has limited Java refactoring capabilities compared to its Python support, but this is expected given that rope is Python-specific. For most Java analysis tasks (finding references, analyzing call flows, detecting dead code), the tools work perfectly with full AST context support.