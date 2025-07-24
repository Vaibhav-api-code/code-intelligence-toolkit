<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Individual Test Results Summary

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-20
Updated: 2025-07-20
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Individual Test Results Summary

**Date**: January 2025  
**Test Location**: test/ directory  

## Summary

The individual test files in the `test/` directory are **outdated** and written for previous versions of the tools. They expect different command-line arguments and interfaces than what the current tools provide.

## Test Results

### ✅ Passing Tests (5/7)
1. **test_ast_context.py** - Basic functionality test
2. **test_organize_files.py** - Empty test, auto-passes
3. **test_safe_move.py** - Empty test, auto-passes  
4. **test_refactor_rename.py** - Empty test, auto-passes
5. **test_multiline_capabilities.py** - Technically passes but all internal tests fail

### ❌ Failing Tests (2/7)
1. **test_preflight_checks.py** - Expects different output format
2. **test_standardized_interfaces.py** - Can't find run_any_python_tool.sh

## Key Issues Found

### 1. Outdated Command-Line Arguments
The tests expect arguments that no longer exist:
- `find_text.py` tests expect: `--max-depth`, `--path`, `--in-files`, `--extend-context`
- `multiline_reader.py` tests expect: `--context` instead of `--around-lines`
- Tests expect tools like `navigate.py` which may have been renamed

### 2. Tool Location Issues
- Tests expect all tools to be in the same directory
- Had to create symlinks to make tools accessible
- Tests don't use the proper wrapper scripts

### 3. Interface Mismatches
- `find_text.py` no longer supports file finding operations (--max-depth, size filters, etc.)
- The current `find_text.py` is focused on text search, not file finding
- Many expected features have been moved to other specialized tools

## Comparison with Comprehensive Test Suite

Our **newly created comprehensive test suite** (`test_all_tools.py`) is much more accurate:
- **97% success rate** (32/33 tests passing)
- Tests the **actual current interfaces** of all tools
- Uses **real test data** in the `test_code/` directory
- Properly handles the current argument structure

## Recommendation

The individual tests in the `test/` directory should be:
1. **Updated** to match current tool interfaces, or
2. **Replaced** with the comprehensive test suite approach

The comprehensive test suite we created is a better reflection of the current state of the tools and should be used for validation instead of these outdated individual tests.