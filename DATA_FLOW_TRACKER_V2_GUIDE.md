# Data Flow Tracker V2 - Comprehensive Guide

**Related Code Files:**
- `code-intelligence-toolkit/data_flow_tracker_v2.py` - Advanced data flow analysis with intelligence layer
- `code-intelligence-toolkit/run_any_python_tool.sh` - Wrapper script for execution
- `code-intelligence-toolkit/templates/` - HTML visualization templates (optional)

---

## Overview

Data Flow Tracker V2 is an advanced code intelligence and algorithm analysis tool that provides deep insights into how data flows through your code. Built on the foundation of the original data flow tracker, V2 adds five major capabilities that transform it from a simple dependency tracker into a comprehensive code intelligence platform.

### Key Enhancements in V2

1. **Impact Analysis** - Shows where data escapes scope and causes effects
2. **Calculation Path Analysis** - Extracts minimal critical path for values
3. **Type and State Tracking** - Monitors type evolution and state changes
4. **Natural Language Explanations** - Intuitive explanations of complex analysis
5. **Interactive HTML Visualization** - Self-contained reports with vis.js network graphs

### When to Use V2

- **Safety Analysis**: Understand what changing a variable affects before refactoring
- **Algorithm Understanding**: Trace how complex calculations derive their values
- **Debugging**: Find the root cause of incorrect values or unexpected behavior
- **Code Review**: Generate comprehensive reports for technical documentation
- **Refactoring**: Assess risk levels before making changes to critical code

## Installation & Requirements

### Core Requirements
```bash
# Already included in code-intelligence-toolkit
./run_any_python_tool.sh data_flow_tracker_v2.py --help
```

### Language Support
- **Python**: Full support with complete AST analysis
- **Java**: Requires `javalang>=0.13.0` (included in requirements-core.txt)

### Optional Dependencies
- **Enhanced HTML**: `jinja2>=3.0.0` for templated reports (requirements-optional.txt)
- **Graph Export**: GraphViz for DOT format visualization exports

## Quick Start

### Basic Usage Patterns

```bash
# Impact analysis - see what changing a variable affects
./run_any_python_tool.sh data_flow_tracker_v2.py --var config --show-impact --file app.py

# Calculation path - understand how a value is computed
./run_any_python_tool.sh data_flow_tracker_v2.py --var final_price --show-calculation-path --file pricing.py

# Type and state tracking - monitor variable evolution
./run_any_python_tool.sh data_flow_tracker_v2.py --var user_data --track-state --file process.py

# Interactive HTML report
./run_any_python_tool.sh data_flow_tracker_v2.py --var database_config --show-impact --output-html --file app.py
```

## Command-Line Reference

### Required Arguments
- `--file FILE` - Source file to analyze (Python or Java)

### Variable Selection
- `--var VAR` - Specific variable to track
- `--var-all` - Generate reports for all variables (batch mode)

### Analysis Modes
- `--show-impact` - Impact analysis (where data escapes scope)
- `--show-calculation-path` - Minimal calculation path extraction
- `--track-state` - Type and state evolution tracking
- `--direction {forward,backward}` - Standard tracking direction (V1 compatibility)

### Output Controls
- `--format {text,json,graph}` - Output format
- `--output-html` - Generate interactive HTML visualization
- `--html-out PATH` - Write HTML to specific path/directory
- `--explain` - Add natural language explanations

### Advanced Options
- `--max-depth N` - Maximum tracking depth (-1 for unlimited)
- `--inter-procedural` - Enable inter-procedural analysis
- `--show-all` - Show all variables and dependencies

## The Five V2 Analysis Modes

### 1. Impact Analysis (`--show-impact`)

**Purpose**: Understand what changing a variable will affect in your codebase.

**What it analyzes**:
- Return value dependencies
- Side effects (file writes, network calls, console output)
- State changes (global variables, class attributes)
- External function calls
- Risk assessment with severity levels

**Example Output**:
```json
{
  "returns": [
    {"type": "return", "function": "calculate_total", "severity": "high"}
  ],
  "side_effects": [
    {"type": "file_write", "location": "save_results:45", "severity": "medium"}
  ],
  "summary": {
    "total_exit_points": 3,
    "functions_affected": 2,
    "high_risk_count": 1,
    "recommendation": "⚠️ HIGH RISK: Review all high-severity exit points"
  }
}
```

**When to use**:
- Before refactoring critical variables
- Assessing the scope of a change
- Code review and safety analysis

### 2. Calculation Path Analysis (`--show-calculation-path`)

**Purpose**: Extract the minimal critical path showing how a value is calculated.

**What it analyzes**:
- Essential calculation steps only (non-essential steps pruned)
- Input variable dependencies
- Function call chains with parameter mapping
- Mathematical operations and transformations

**Example Output**:
```json
[
  {
    "variable": "base_price",
    "operation": "assignment",
    "inputs": ["product.price"],
    "location": "pricing.py:23",
    "essential": true
  },
  {
    "variable": "tax_amount",
    "operation": "calculation",
    "inputs": ["base_price", "tax_rate"],
    "location": "pricing.py:25",
    "essential": true
  },
  {
    "variable": "final_price",
    "operation": "calculation",
    "inputs": ["base_price", "tax_amount"],
    "location": "pricing.py:27",
    "essential": true
  }
]
```

**When to use**:
- Understanding complex algorithms
- Debugging calculation errors
- Optimizing performance bottlenecks
- Creating algorithm documentation

### 3. Type and State Tracking (`--track-state`)

**Purpose**: Monitor how variable types and states evolve through the code.

**What it analyzes**:
- Type changes and confidence levels
- State modifications (assignments, mutations)
- Loop and conditional context
- Null safety warnings

**Example Output**:
```json
{
  "type_evolution": [
    {
      "location": "process.py:15",
      "type": "str",
      "confidence": 0.9,
      "nullable": false,
      "operation": "assignment"
    },
    {
      "location": "process.py:22",
      "type": "dict",
      "confidence": 0.8,
      "nullable": true,
      "operation": "transformation"
    }
  ],
  "warnings": [
    "Variable may be None - add null checks",
    "Type changes detected: str → dict"
  ]
}
```

**When to use**:
- Type safety analysis
- Finding potential null pointer exceptions
- Understanding data transformations
- Optimizing variable usage patterns

### 4. Natural Language Explanations (`--explain`)

**Purpose**: Generate human-readable explanations of analysis results.

**Example Output**:
```
📊 Impact Analysis for 'database_config':

⚠️ Medium Risk Change: Modifying 'database_config' affects 7 places in your code. 
It affects 2 return values, causes 1 external side effects (like file writes), 
and modifies 2 global variables.

💡 Recommendation: Focus testing on the affected areas and verify all return 
values and side effects.

🔍 Detailed Breakdown:
- The variable flows into 3 different functions
- It's used in 2 conditional statements that control program flow
- Changes will affect database connection logic in ConnectionManager
```

**When to use**:
- Code reviews and documentation
- Teaching and knowledge transfer
- Non-technical stakeholder reports

### 5. Interactive HTML Visualization (`--output-html`)

**Purpose**: Generate self-contained HTML reports with interactive network graphs.

**Features**:
- Network visualization using vis.js (no external dependencies)
- Expandable/collapsible sections
- Copy-to-clipboard code examples
- Responsive design for different screen sizes
- Dark/light theme support

**Generated report includes**:
- Executive summary with risk assessment
- Interactive dependency network graph
- Detailed analysis tables
- Code snippets with syntax highlighting
- Downloadable data in JSON format

**When to use**:
- Formal documentation and reports
- Sharing analysis with team members
- Interactive exploration of complex dependencies

## Language-Specific Features

### Python Analysis

**Strengths**:
- Complete AST parsing with full Python syntax support
- Advanced type inference using context and assignments
- Comprehensive function call analysis with parameter mapping
- Exception handling and control flow analysis

**Supported constructs**:
- Functions, classes, methods
- Lambda expressions and comprehensions
- Decorators and context managers
- Async/await patterns
- Import analysis and module dependencies

### Java Analysis

**Strengths**:
- Robust class and method structure analysis
- Package and import dependency tracking
- Method overloading and inheritance handling

**Limitations**:
- Basic type inference (inherits from underlying analyzer)
- Limited state tracking compared to Python
- No generic type parameter analysis

**Supported constructs**:
- Classes, methods, constructors
- Field and local variable tracking
- Static and instance method calls
- Basic inheritance patterns

## Advanced Usage Patterns

### Batch Analysis for Code Review

```bash
# Generate reports for all variables in a module
./run_any_python_tool.sh data_flow_tracker_v2.py --var-all --show-impact --output-html --html-out reports/ --file critical_module.py

# This creates individual HTML reports for each variable
```

### Multi-Mode Analysis

```bash
# Combine multiple analysis modes for comprehensive coverage
./run_any_python_tool.sh data_flow_tracker_v2.py \
  --var user_input \
  --show-impact \
  --show-calculation-path \
  --track-state \
  --explain \
  --output-html \
  --file security_module.py
```

### Integration with CI/CD

```bash
# Risk assessment for continuous integration
./run_any_python_tool.sh data_flow_tracker_v2.py \
  --var critical_config \
  --show-impact \
  --format json \
  --file config.py > impact_report.json

# Parse the JSON to fail builds on high-risk changes
```

### GraphViz Export for Documentation

```bash
# Generate DOT format for inclusion in documentation
./run_any_python_tool.sh data_flow_tracker_v2.py \
  --var data_processor \
  --format graph \
  --file processor.py > data_flow.dot

# Convert to various image formats
dot -Tpng data_flow.dot -o data_flow.png
dot -Tsvg data_flow.dot -o data_flow.svg
```

## Performance and Scalability

### Optimization Features
- **Depth limiting**: Use `--max-depth` to prevent runaway analysis
- **Essential path pruning**: Calculation paths automatically filter non-critical steps
- **Memoization**: Results cached during single analysis run
- **Memory management**: Large codebases handled efficiently

### Performance Guidelines
- **Small files (< 1000 lines)**: All analysis modes, unlimited depth
- **Medium files (1000-5000 lines)**: Use `--max-depth 20` for complex analysis
- **Large files (> 5000 lines)**: Focus on specific variables, use `--max-depth 10`
- **Batch mode**: Process files individually rather than analyzing entire projects

### Memory Usage
- **Basic tracking**: ~10MB per 1000 lines of code
- **Full analysis**: ~50MB per 1000 lines with all modes enabled
- **HTML reports**: Additional ~5MB per report with visualization

## Troubleshooting

### Common Issues

**1. "Function not found" errors**
- Ensure the function exists in the specified file
- Check for typos in function names
- Verify file path is correct

**2. Java analysis fails**
- Install javalang: `pip install javalang>=0.13.0`
- Check Java syntax is valid
- Ensure file is UTF-8 encoded

**3. Large analysis times**
- Use `--max-depth` to limit recursion
- Focus on specific variables instead of `--var-all`
- Check for circular dependencies causing infinite loops

**4. HTML reports not generating**
- Check write permissions to output directory
- Ensure sufficient disk space
- Use `--verbose` for detailed error messages

### Debug Mode

```bash
# Enable verbose logging for troubleshooting
./run_any_python_tool.sh data_flow_tracker_v2.py --var debug_var --show-impact --verbose --file problem.py
```

## Integration with Other Tools

### With Documentation Generator

```bash
# Generate documentation using data flow insights
./run_any_python_tool.sh doc_generator.py --function process_data --style technical --depth deep --file data.py
```

### With Text Analysis Tools

```bash
# Find all variables before analyzing
./run_any_python_tool.sh find_text_v7.py "^[a-zA-Z_][a-zA-Z0-9_]*\s*=" --type regex --file code.py

# Analyze each found variable
for var in $(previous_command_output); do
    ./run_any_python_tool.sh data_flow_tracker_v2.py --var "$var" --show-impact --file code.py
done
```

### With Refactoring Tools

```bash
# Check impact before renaming
./run_any_python_tool.sh data_flow_tracker_v2.py --var old_name --show-impact --file module.py

# If safe, proceed with rename
./run_any_python_tool.sh replace_text_v8.py "old_name" "new_name" module.py
```

## Best Practices

### Analysis Strategy

1. **Start with Impact Analysis**: Always check `--show-impact` before making changes
2. **Use Calculation Paths for Debugging**: When values are wrong, trace with `--show-calculation-path`
3. **Monitor State Changes**: Use `--track-state` for variables that change frequently
4. **Generate Reports for Reviews**: Use `--output-html` for formal documentation

### Risk Assessment

- **HIGH Risk**: Changes affect return values or external systems
- **MEDIUM Risk**: Changes affect internal state or have side effects
- **LOW Risk**: Changes are local scope only

### Code Quality Guidelines

- Variables with >10 exit points may indicate tight coupling
- Calculation paths >20 steps suggest complex algorithms needing decomposition
- Frequent type changes indicate potential design issues

### Documentation Workflow

1. Run impact analysis for critical functions
2. Generate HTML reports for stakeholder review
3. Include calculation paths in algorithm documentation
4. Use state tracking for API boundary analysis

## Real-World Examples

### Example 1: E-commerce Price Calculation

```bash
# Understand how final price is calculated
./run_any_python_tool.sh data_flow_tracker_v2.py \
  --var final_price \
  --show-calculation-path \
  --explain \
  --file pricing_engine.py
```

**Result**: Shows tax calculations, discount applications, and shipping costs flow into final price.

### Example 2: Configuration Change Impact

```bash
# Assess impact of changing database configuration
./run_any_python_tool.sh data_flow_tracker_v2.py \
  --var db_config \
  --show-impact \
  --output-html \
  --file application.py
```

**Result**: Reveals which services, cache systems, and logging components are affected.

### Example 3: Security Variable Tracking

```bash
# Track how user input flows through security checks
./run_any_python_tool.sh data_flow_tracker_v2.py \
  --var user_input \
  --track-state \
  --show-impact \
  --explain \
  --file security_handler.py
```

**Result**: Shows validation steps, sanitization processes, and where the data exits the system.

## API and Programmatic Usage

While primarily designed as a command-line tool, the V2 analyzer can be imported and used programmatically:

```python
from data_flow_tracker_v2 import DataFlowAnalyzerV2

# Create analyzer instance
analyzer = DataFlowAnalyzerV2(source_code, filename, language="python")
analyzer.analyze()

# Get impact analysis
impact = analyzer.track_forward("variable_name")
print(f"Affects {len(impact['affects'])} components")

# Get calculation path
path = analyzer.show_calculation_path("result_var")
print(f"Calculation involves {len(path)} steps")

# Generate explanations
explanation = analyzer.generate_explanation(impact, "impact", "variable_name")
print(explanation)
```

## Conclusion

Data Flow Tracker V2 transforms code analysis from simple dependency tracking into comprehensive code intelligence. Its five analysis modes provide different lenses for understanding code behavior:

- Use **Impact Analysis** for safety and refactoring decisions
- Use **Calculation Paths** for algorithm understanding and debugging
- Use **State Tracking** for type safety and data transformation analysis
- Use **Natural Language Explanations** for documentation and teaching
- Use **HTML Visualization** for interactive exploration and formal reports

The tool scales from quick single-variable checks to comprehensive codebase analysis, making it valuable for developers, code reviewers, and technical writers working with complex codebases.

