<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

Dependency Analyzer Tool Guide

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-21
Updated: 2025-07-21
License: Mozilla Public License 2.0 (MPL-2.0)
-->

# Dependency Analyzer Tool Guide

**Related Code Files:**
- `code-intelligence-toolkit/dependency_analyzer.py` - Comprehensive Java dependency analysis tool
- `code-intelligence-toolkit/find_text_v5.py` - Integration for pattern searching
- `code-intelligence-toolkit/cross_file_analysis_ast.py` - AST-based dependency analysis

---

## Overview

The `dependency_analyzer.py` is a comprehensive "tool to rule them all" for analyzing Java class dependencies, line counts, and complexity. It provides automated dependency extraction, visualization, and detailed reporting capabilities.

## Features

### 🔍 **Automated Analysis**
- **Dependency Extraction**: Automatically finds and analyzes all dependencies
- **Line Count Analysis**: Counts lines of code for all classes and dependencies
- **Complexity Scoring**: Calculates complexity based on size, dependencies, and category
- **Category Classification**: Automatically categorizes classes (UI, Trading, Analysis, etc.)

### 📊 **Visualization & Reporting**
- **Dependency Graphs**: Interactive network graphs showing relationships
- **Category Breakdowns**: Visual analysis by functional category
- **HTML Reports**: Comprehensive interactive reports
- **Export Formats**: JSON, CSV, Markdown, and HTML exports

### 🎯 **Smart Classification**
Classes are automatically categorized using pattern matching:
- **UI**: GUI components, frames, dialogs, monitors
- **Trading**: Order management, positions, portfolio logic
- **Analysis**: Analyzers, calculators, detectors, trackers
- **Indicator**: VWAP, moving averages, technical indicators
- **Data**: Data structures, caches, buffers, stores
- **Utility**: Helpers, managers, services, utilities
- **Test**: Test classes and test utilities

## Usage Examples

### Basic Analysis
```bash
# Analyze NubiaV7_1_5 with default settings
./run_any_python_tool.sh dependency_analyzer.py ComplexAnalyzerV7_1_5

# Quick summary only
./run_any_python_tool.sh dependency_analyzer.py ComplexAnalyzerV7_1_5 --summary-only

# Show category breakdown
./run_any_python_tool.sh dependency_analyzer.py ComplexAnalyzerV7_1_5 --categories --complexity
```

### Full Analysis with Visualization
```bash
# Generate all outputs (graphs, reports, exports)
./run_any_python_tool.sh dependency_analyzer.py ComplexAnalyzerV7_1_5 --export-all

# Custom depth and specific outputs
./run_any_python_tool.sh dependency_analyzer.py DataProcessorControllerV2 \
    --depth 3 --html-report --graph --json --csv
```

### Visualization Options
```bash
# Generate matplotlib graph only
./run_any_python_tool.sh dependency_analyzer.py MyClass \
    --matplotlib-graph dependency_graph.png

# Generate interactive Plotly graph
./run_any_python_tool.sh dependency_analyzer.py MyClass \
    --plotly-graph interactive_analysis.html

# Both graphs plus HTML report
./run_any_python_tool.sh dependency_analyzer.py MyClass --graph --html-report
```

## Output Formats

### 1. **Console Summary**
Real-time analysis results with:
- Total classes and line counts
- Category breakdowns
- Top complexity classes
- Largest classes by lines

### 2. **HTML Reports**
Interactive web reports featuring:
- Summary statistics dashboard
- Category-based class listings
- Detailed class information table
- Complexity scoring and color coding

### 3. **Dependency Graphs**
Visual network representations showing:
- **Node size** = Lines of code
- **Node color** = Category type
- **Edges** = Dependencies between classes
- **Interactive features** (with Plotly)

### 4. **Data Exports**
- **JSON**: Complete analysis data for programmatic use
- **CSV**: Tabular class information for spreadsheet analysis
- **Markdown**: Documentation-friendly reports

## Example Output Analysis

For **ComplexAnalyzerV7_1_5**, the tool provides:

### Summary Statistics
```
Total Classes: 45+ analyzed dependencies
Total Lines: ~55,000+ lines of code
Average Lines per Class: ~1,200 lines
Categories: 8 different functional areas
```

### Category Breakdown
- **Trading Systems**: DataProcessorControllerV2, StateManagerControllerV3
- **Market Analysis**: DataProfileAnalyzerV4, ClusterAnalyzerV1_7
- **UI Components**: Multiple monitoring and debug interfaces
- **Indicators**: VWAP calculations, proximity tracking
- **Data Management**: Health tracking, sweep detection

### Complexity Insights
- Identifies most complex classes requiring maintenance attention
- Highlights classes with high dependency counts
- Shows architectural bottlenecks and coupling issues

## Advanced Features

### Configuration Options
```bash
# Custom search paths
--project-root /path/to/project

# Analysis depth control
--depth 4  # Analyze up to 4 levels deep

# Category filtering
--list-categories  # Show available categories

# Output customization
--prefix MyAnalysis  # Custom file prefixes
--output-dir custom_output/  # Custom output directory
```

### Integration with Other Tools
The dependency analyzer integrates with existing toolkit tools:
- Uses `find_text_v5.py` for pattern searching
- Leverages `cross_file_analysis_ast.py` for AST analysis
- Compatible with `wc -l` for line counting validation

### Performance Considerations
- **Depth Control**: Use `--depth 2-3` for large codebases
- **Pattern Filtering**: Tool filters out standard Java classes automatically
- **Caching**: Results are cached to improve subsequent analysis speed

## Installation Requirements

### Required Dependencies
```bash
# Core functionality (always available)
python3  # Built into tool

# Optional visualization (recommended)
pip install matplotlib networkx  # For static graphs
pip install plotly  # For interactive graphs
```

### Fallback Modes
- Without matplotlib: Text-based analysis only
- Without plotly: Static graphs only
- Without visualization libs: Full analysis with data exports

## Use Cases

### 1. **Code Architecture Review**
- Understand dependency relationships
- Identify architectural bottlenecks  
- Assess code coupling and cohesion

### 2. **Maintenance Planning**
- Find largest/most complex classes needing attention
- Identify heavily coupled components
- Plan refactoring priorities

### 3. **Documentation Generation**
- Automatically generate dependency documentation
- Create visual architecture diagrams
- Export data for external analysis tools

### 4. **Code Quality Assessment**
- Complexity scoring for quality metrics
- Category distribution analysis
- Dependency depth analysis

## Tips and Best Practices

### 1. **Start Small**
```bash
# Begin with summary to understand scope
dependency_analyzer.py MyClass --summary-only

# Then expand to full analysis
dependency_analyzer.py MyClass --export-all
```

### 2. **Use Appropriate Depth**
- **Depth 1-2**: Quick analysis, immediate dependencies
- **Depth 3-4**: Comprehensive analysis, full picture
- **Depth 5+**: Very detailed (may include framework classes)

### 3. **Combine with Other Tools**
```bash
# Find specific patterns first
./run_any_python_tool.sh find_text_v5.py "OrderSender" --auto-find

# Then analyze the found class
dependency_analyzer.py DataProcessorControllerV2 --html-report
```

### 4. **Regular Analysis**
- Run analysis after major changes
- Track complexity trends over time
- Use for architecture reviews

## Troubleshooting

### Common Issues
1. **Classes not found**: Ensure correct project root with `--project-root`
2. **Too many warnings**: Redirect stderr with `2>/dev/null`
3. **Large output**: Use `--summary-only` for quick checks
4. **Missing visualizations**: Install optional dependencies

### Performance Tips
- Use `--depth 2` for large enterprise codebases
- Filter by specific categories if focusing on particular areas
- Use `--summary-only` for quick health checks

## Summary

The `dependency_analyzer.py` tool provides comprehensive automated analysis of Java class dependencies with:

✅ **Automated dependency discovery and analysis**  
✅ **Visual dependency graphs and reports**  
✅ **Multiple export formats for different needs**  
✅ **Smart classification and complexity scoring**  
✅ **Integration with existing toolkit tools**  

This makes it the definitive "tool to rule them all" for understanding code architecture, planning maintenance, and generating dependency documentation.