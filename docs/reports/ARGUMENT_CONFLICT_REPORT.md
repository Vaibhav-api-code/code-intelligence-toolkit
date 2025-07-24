<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Argument Conflict Analysis Report

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-20
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Argument Conflict Analysis Report

**Date**: Sun Jul 20 14:47:16 PDT 2025

## Summary
- Total conflicts: 27 flags
- Total tools analyzed: 49
- Standard flags: 51

## Conflicts by Flag

### `--all`
**Conflicts in 2 tools:**
- `tree_view.py`
- `find_files.py`

### `--context`
**Conflicts in 3 tools:**
- `find_references_rg.py`
- `navigate_ast_v2.py`
- `pattern_analysis.py`

### `--dry-run`
**Conflicts in 4 tools:**
- `ast_refactor_enhanced.py`
- `replace_text_ast.py`
- `refactor_rename.py`
- `ast_refactor.py`

### `--file`
**Conflicts in 1 tools:**
- `replace_text_ast.py`

### `--highlight`
**Conflicts in 2 tools:**
- `multiline_reader.py`
- `navigate_ast_v2.py`

### `--ignore-case`
**Conflicts in 4 tools:**
- `cross_file_analysis_ast.py`
- `find_references_rg.py`
- `pattern_analysis.py`
- `find_files.py`

### `--json`
**Conflicts in 5 tools:**
- `cross_file_analysis_ast.py`
- `git_commit_analyzer.py`
- `refactor_rename.py`
- `show_structure_ast_v4.py`
- `navigate_ast_v2.py`

### `--line`
**Conflicts in 1 tools:**
- `replace_text_ast.py`

### `--long`
**Conflicts in 1 tools:**
- `find_files.py`

### `--max-depth`
**Conflicts in 5 tools:**
- `cross_file_analysis_ast.py`
- `cross_file_analysis_ast.py`
- `tree_view.py`
- `show_structure_ast_v4.py`
- `find_files.py`

### `--quiet`
**Conflicts in 5 tools:**
- `semantic_diff.py`
- `semantic_diff_v3.py`
- `cross_file_analysis_ast.py`
- `navigate_ast_v2.py`
- `replace_text.py`

### `--recursive`
**Conflicts in 3 tools:**
- `cross_file_analysis_ast.py`
- `cross_file_analysis_ast.py`
- `refactor_rename.py`

### `--regex`
**Conflicts in 5 tools:**
- `log_analyzer.py`
- `smart_refactor_v2.py`
- `multiline_reader.py`
- `pattern_analysis.py`
- `find_files.py`

### `--scope`
**Conflicts in 2 tools:**
- `cross_file_analysis_ast.py`
- `pattern_analysis.py`

### `--to`
**Conflicts in 1 tools:**
- `navigate.py`

### `--type`
**Conflicts in 2 tools:**
- `ast_refactor_enhanced.py`
- `ast_refactor.py`

### `--verbose`
**Conflicts in 5 tools:**
- `semantic_diff.py`
- `semantic_diff_v3.py`
- `git_commit_analyzer.py`
- `refactor_rename.py`
- `replace_text.py`

### `-C`
**Conflicts in 3 tools:**
- `find_references_rg.py`
- `navigate_ast_v2.py`
- `pattern_analysis.py`

### `-a`
**Conflicts in 2 tools:**
- `tree_view.py`
- `find_files.py`

### `-c`
**Conflicts in 1 tools:**
- `dead_code_detector.py`

### `-g`
**Conflicts in 1 tools:**
- `pattern_analysis.py`

### `-i`
**Conflicts in 4 tools:**
- `cross_file_analysis_ast.py`
- `find_references_rg.py`
- `pattern_analysis.py`
- `replace_text.py`

### `-l`
**Conflicts in 3 tools:**
- `replace_text_ast.py`
- `tree_view.py`
- `find_files.py`

### `-m`
**Conflicts in 1 tools:**
- `replace_text.py`

### `-q`
**Conflicts in 5 tools:**
- `semantic_diff.py`
- `semantic_diff_v3.py`
- `cross_file_analysis_ast.py`
- `navigate_ast_v2.py`
- `replace_text.py`

### `-r`
**Conflicts in 2 tools:**
- `refactor_rename.py`
- `find_files.py`

### `-v`
**Conflicts in 5 tools:**
- `semantic_diff.py`
- `semantic_diff_v3.py`
- `git_commit_analyzer.py`
- `refactor_rename.py`
- `replace_text.py`

## Potential New Standard Arguments
Arguments used by multiple tools that could be standardized:

- `--ast-context`: 11 tools
- `--language`: 6 tools
- `--no-ast-context`: 5 tools
- `--summary`: 5 tools
- `--summary-only`: 4 tools
- `--output`: 4 tools
- `--pattern`: 3 tools
- `--format`: 3 tools
- `-f`: 3 tools
- `--analyze`: 3 tools
- `-o`: 3 tools
- `--lang`: 3 tools
- `--max-samples`: 3 tools
- `--trace-flow`: 3 tools
- `--java-only`: 3 tools
- `--python-only`: 3 tools
- `--force`: 3 tools
- `--check-compile`: 3 tools
- `--no-check-compile`: 3 tools
- `--include-build`: 3 tools
- `--limit`: 3 tools
- `--max`: 3 tools
- `--dirs-only`: 3 tools
- `--files-only`: 3 tools
- `-s`: 3 tools
- `--include-fields`: 3 tools
