<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Parsing Issues and Solutions

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-17
Updated: 2025-07-17
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Parsing Issues and Solutions

**Related Code Files:**
- `show_structure_ast_v4.py` - Main structure analyzer
- `show_structure_ast_v4_enhanced.py` - Enhanced version with better error handling
- `diagnose_parsing_issues.py` - Diagnostic tool for parsing problems

---

## Common Causes of "No code elements found or unable to parse file"

### 1. **File Access Issues**
- **File not found**: Check if file path is correct
- **Permission denied**: Ensure file is readable
- **Encoding issues**: File contains non-UTF-8 characters

### 2. **Syntax Problems**
- **Brace mismatches**: Unbalanced `{` and `}` in Java files
- **Invalid syntax**: Malformed code that breaks AST parsers
- **Incomplete files**: Files that are currently being edited

### 3. **Large File Issues**
- **Memory constraints**: Very large files (>10MB) may cause timeouts
- **Complex structures**: Deeply nested code structures
- **Parser limitations**: AST parsers failing on complex code

### 4. **Language-Specific Issues**
- **Unsupported file types**: Only supports .py, .java, .js, .jsx, .ts, .tsx
- **Java-specific**: Missing imports, annotation parsing failures
- **Python-specific**: Syntax errors in Python AST parsing

## Diagnostic Tools

### 1. **Built-in Diagnostic Script**
```bash
python3 diagnose_parsing_issues.py <file_path>
```

**What it checks:**
- File existence and permissions
- File size and encoding
- Basic syntax validation
- Content preview

### 2. **Verbose Mode**
```bash
python3 show_structure_ast_v4.py <file> --verbose
```

**Provides:**
- Detailed error messages
- Parser-specific failures
- Stack traces for debugging

## Solutions and Workarounds

### 1. **For Large Files**
```bash
# Skip preprocessing for faster parsing
python3 show_structure_ast_v4.py large_file.java --no-preprocess

# Limit depth to reduce processing
python3 show_structure_ast_v4.py large_file.java --max-depth 2

# Use enhanced version with fallback strategies
python3 show_structure_ast_v4_enhanced.py large_file.java --max-depth 1
```

### 2. **For Syntax Issues**
```bash
# Use enhanced version with multiple fallback parsers
python3 show_structure_ast_v4_enhanced.py problematic_file.java

# Force regex parser (bypasses AST parsing)
python3 show_structure_ast_v4.py file.java --no-preprocess
```

### 3. **For Encoding Issues**
```bash
# Convert file to UTF-8 first
iconv -f ISO-8859-1 -t UTF-8 file.java > file_utf8.java
python3 show_structure_ast_v4.py file_utf8.java
```

### 4. **For Complex Java Files**
```bash
# Use enhanced version with fallback strategies
python3 show_structure_ast_v4_enhanced.py complex_file.java --verbose
```

## Enhanced Version Features

The `show_structure_ast_v4_enhanced.py` provides:

### **Multiple Parsing Strategies**
1. **javalang parser** - Most accurate, handles complex Java syntax
2. **Regex parser with preprocessing** - Removes comments/strings first
3. **Regex parser without preprocessing** - Faster, less accurate
4. **Minimal parser** - Last resort, basic pattern matching

### **Detailed Error Reporting**
- File validation diagnostics
- Brace mismatch detection
- Parser failure explanations
- Troubleshooting suggestions

### **Automatic Fallback**
- Tries multiple parsers automatically
- Reports which parser succeeded
- Provides element count feedback

## Troubleshooting Workflow

1. **First, try basic parsing:**
   ```bash
   python3 show_structure_ast_v4.py file.java
   ```

2. **If it fails, run diagnostics:**
   ```bash
   python3 diagnose_parsing_issues.py file.java
   ```

3. **Try with verbose output:**
   ```bash
   python3 show_structure_ast_v4.py file.java --verbose
   ```

4. **For large files, use optimizations:**
   ```bash
   python3 show_structure_ast_v4.py file.java --no-preprocess --max-depth 2
   ```

5. **For persistent issues, use enhanced version:**
   ```bash
   python3 show_structure_ast_v4_enhanced.py file.java --verbose
   ```

6. **Last resort - minimal parsing:**
   ```bash
   python3 show_structure_ast_v4_enhanced.py file.java --verbose --max-depth 1
   ```

## Example: Troubleshooting a Complex File

```bash
# File: ComplexAnalyzerV7_1_5.java (600KB, 11K lines)
# Issue: "No code elements found or unable to parse file"

# Step 1: Diagnose
python3 diagnose_parsing_issues.py ComplexAnalyzerV7_1_5.java
# Result: ⚠️  Brace mismatch: 1387 open, 1386 close

# Step 2: Use enhanced version
python3 show_structure_ast_v4_enhanced.py ComplexAnalyzerV7_1_5.java --max-depth 1 --verbose
# Result: ✅ Regex parser with preprocessing succeeded: 2 elements

# Step 3: Get more details
python3 show_structure_ast_v4_enhanced.py ComplexAnalyzerV7_1_5.java --max-depth 2
# Result: Shows class structure with methods
```

## Prevention Tips

1. **File Quality:**
   - Ensure files compile before parsing
   - Check for balanced braces
   - Verify file encoding is UTF-8

2. **Performance:**
   - Use `--no-preprocess` for large files
   - Limit `--max-depth` for complex structures
   - Consider file size before parsing

3. **Tool Selection:**
   - Use enhanced version for problematic files
   - Use standard version for known-good files
   - Use diagnostic tool for investigation

## When to Use Each Tool

- **show_structure_ast_v4.py**: Standard tool for most files
- **show_structure_ast_v4_enhanced.py**: For problematic or large files
- **diagnose_parsing_issues.py**: For investigating parsing failures

All tools support the same command-line arguments, making them interchangeable for troubleshooting workflows.