#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Comprehensive interface audit for all Python tools.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import subprocess
import sys
from pathlib import Path
import re

# List of all tools from run_any_python_tool.sh
TOOLS = {
    'Structure and Navigation': [
        'check_structure.py',
        'navigate.py', 
        'extract_methods.py',
        'extract_class_structure.py',
        'extract_block.py'
    ],
    'Search and Find': [
        'find_text.py'
    ],
    'Analysis Tools': [
        'find_references.py',
        'find_references_rg.py',
        'analyze_dependencies.py',
        'analyze_dependencies_rg.py',
        'analyze_unused_methods.py',
        'analyze_unused_methods_rg.py',
        'trace_calls.py',
        'trace_calls_rg.py'
    ],
    'Smart Code-Aware Tools': [
        'smart_find_references.py',
        'analyze_usage.py',
        'method_analyzer.py',
        'method_analyzer_ast.py',
        'pattern_analysis.py',
        'log_analyzer.py',
        'smart_refactor.py',
        'cross_file_analysis.py',
        'cross_file_analysis_ast.py',
        'semantic_diff.py',
        'semantic_diff_ast.py',
        'navigate_ast.py',
        'replace_text_ast.py'
    ],
    'Refactoring and Quality': [
        'suggest_refactoring.py',
        'analyze_internal_usage.py',
        'smart_diff.py',
        'replace_text.py',
        'ast_refactor.py'
    ],
    'Directory and File Management': [
        'smart_ls.py',
        'find_files.py',
        'recent_files.py',
        'tree_view.py',
        'dir_stats.py'
    ],
    'Configuration Management': [
        'common_config.py'
    ],
    'Error Monitoring': [
        'analyze_errors.py',
        'error_dashboard.py',
        'error_logger.py'
    ],
    'Specialized Tools': [
        'comprehensive_indicator_analysis.py',
        'extract_indicators.py',
        'analyze_diff_time_severity.py',
        'analyze_nonzero_difftime.py',
        'multiline_reader.py'
    ]
}

def run_tool_help(tool_name):
    """Get help output from a tool."""
    try:
        result = subprocess.run(
            ['./run_any_python_tool.sh', tool_name, '--help'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception as e:
        return -1, "", str(e)

def analyze_interface_pattern(help_output):
    """Analyze if tool follows standardized interface patterns."""
    analysis = {
        'has_positional_args': False,
        'has_file_flag': False,
        'has_scope_flag': False,
        'has_common_flags': [],
        'argument_pattern': 'unknown',
        'standardized': False
    }
    
    # Check for positional arguments
    if 'positional arguments:' in help_output:
        analysis['has_positional_args'] = True
    
    # Check for standard flags
    if '--file' in help_output or '--path' in help_output:
        analysis['has_file_flag'] = True
    if '--scope' in help_output:
        analysis['has_scope_flag'] = True
    
    # Check for common standardized flags
    common_flags = ['--verbose', '--quiet', '--json', '--recursive', '--type']
    for flag in common_flags:
        if flag in help_output:
            analysis['has_common_flags'].append(flag)
    
    # Determine argument pattern
    if 'target' in help_output.lower() and (analysis['has_file_flag'] or analysis['has_scope_flag']):
        analysis['argument_pattern'] = 'standardized_analyze'
        analysis['standardized'] = True
    elif 'pattern' in help_output.lower() and (analysis['has_file_flag'] or analysis['has_scope_flag']):
        analysis['argument_pattern'] = 'standardized_search'
        analysis['standardized'] = True
    elif analysis['has_positional_args'] and len(analysis['has_common_flags']) >= 2:
        analysis['argument_pattern'] = 'partially_standardized'
    elif '--in-files' in help_output:  # Old find_text pattern
        analysis['argument_pattern'] = 'legacy_find_text'
    else:
        analysis['argument_pattern'] = 'custom'
    
    return analysis

def check_tool_existence(tool_name):
    """Check if tool file exists."""
    return Path(tool_name).exists()

def audit_all_tools():
    """Audit all tools for interface consistency."""
    results = {}
    total_tools = 0
    standardized_count = 0
    
    print("COMPREHENSIVE TOOL INTERFACE AUDIT")
    print("=" * 80)
    
    for category, tools in TOOLS.items():
        print(f"\n📁 {category}")
        print("-" * len(category))
        
        for tool in tools:
            total_tools += 1
            
            # Check if tool exists
            if not check_tool_existence(tool):
                print(f"  ❌ {tool:<30} - FILE NOT FOUND")
                results[tool] = {'status': 'missing'}
                continue
            
            # Get help output
            exit_code, stdout, stderr = run_tool_help(tool)
            
            if exit_code != 0:
                print(f"  ⚠️  {tool:<30} - HELP FAILED: {stderr[:50]}")
                results[tool] = {'status': 'help_failed', 'error': stderr}
                continue
            
            # Analyze interface
            analysis = analyze_interface_pattern(stdout)
            results[tool] = analysis
            
            # Display results
            status_icon = "✅" if analysis['standardized'] else "🔄" if analysis['argument_pattern'] == 'partially_standardized' else "❌"
            pattern = analysis['argument_pattern']
            
            print(f"  {status_icon} {tool:<30} - {pattern}")
            
            if analysis['standardized']:
                standardized_count += 1
            
            # Show details for non-standardized tools
            if not analysis['standardized'] and analysis['argument_pattern'] not in ['partially_standardized']:
                flags = analysis['has_common_flags']
                print(f"     Flags: file={analysis['has_file_flag']}, scope={analysis['has_scope_flag']}, common={len(flags)}")
    
    # Summary
    print(f"\n" + "=" * 80)
    print(f"AUDIT SUMMARY")
    print(f"=" * 80)
    print(f"Total tools audited: {total_tools}")
    print(f"Fully standardized: {standardized_count}")
    print(f"Standardization rate: {(standardized_count/total_tools)*100:.1f}%")
    
    # Categorize results
    missing = [t for t, r in results.items() if r.get('status') == 'missing']
    help_failed = [t for t, r in results.items() if r.get('status') == 'help_failed']
    standardized = [t for t, r in results.items() if r.get('standardized', False)]
    partially_std = [t for t, r in results.items() if r.get('argument_pattern') == 'partially_standardized']
    needs_work = [t for t, r in results.items() if r.get('argument_pattern') in ['custom', 'legacy_find_text', 'unknown']]
    
    if missing:
        print(f"\n❌ MISSING TOOLS ({len(missing)}):")
        for tool in missing:
            print(f"   - {tool}")
    
    if help_failed:
        print(f"\n⚠️  HELP FAILED ({len(help_failed)}):")
        for tool in help_failed:
            print(f"   - {tool}")
    
    if needs_work:
        print(f"\n🔧 NEEDS STANDARDIZATION ({len(needs_work)}):")
        for tool in needs_work:
            pattern = results[tool].get('argument_pattern', 'unknown')
            print(f"   - {tool:<30} ({pattern})")
    
    if partially_std:
        print(f"\n🔄 PARTIALLY STANDARDIZED ({len(partially_std)}):")
        for tool in partially_std:
            print(f"   - {tool}")
    
    print(f"\n✅ FULLY STANDARDIZED ({len(standardized)}):")
    for tool in standardized:
        print(f"   - {tool}")
    
    return results

def suggest_improvements(results):
    """Suggest specific improvements for non-standardized tools."""
    print(f"\n" + "=" * 80)
    print("IMPROVEMENT RECOMMENDATIONS")
    print("=" * 80)
    
    needs_work = [t for t, r in results.items() if r.get('argument_pattern') in ['custom', 'legacy_find_text', 'unknown']]
    
    if not needs_work:
        print("🎉 All tools are standardized!")
        return
    
    print("\nPriority tools to standardize (based on usage patterns):")
    
    # High priority - commonly used tools
    high_priority = [
        'smart_find_references.py',
        'analyze_usage.py', 
        'pattern_analysis.py',
        'smart_refactor.py',
        'semantic_diff.py'
    ]
    
    for tool in high_priority:
        if tool in needs_work:
            pattern = results[tool].get('argument_pattern', 'unknown')
            print(f"\n🔥 HIGH PRIORITY: {tool}")
            print(f"   Current pattern: {pattern}")
            
            if 'smart_find_references' in tool:
                print("   Suggested: <target> --scope <path> --type <type>")
            elif 'analyze_usage' in tool:
                print("   Suggested: <symbol> --scope <path> --show-frequency")
            elif 'smart_refactor' in tool:
                print("   Suggested: rename <old> <new> --scope <path> --dry-run")
            elif 'semantic_diff' in tool:
                print("   Suggested: <file1> <file2> --logic-only --show-diff")
    
    # Medium priority
    medium_priority = [t for t in needs_work if t not in high_priority]
    if medium_priority:
        print(f"\n📋 MEDIUM PRIORITY ({len(medium_priority)} tools):")
        for tool in medium_priority[:5]:  # Show first 5
            print(f"   - {tool}")

if __name__ == "__main__":
    if not Path('./run_any_python_tool.sh').exists():
        print("Error: run_any_python_tool.sh not found. Run from project root.")
        sys.exit(1)
    
    results = audit_all_tools()
    suggest_improvements(results)