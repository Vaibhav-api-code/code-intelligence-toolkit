# Data Flow Tracker Guide

**Related Code Files:**
- `code-intelligence-toolkit/data_flow_tracker.py` - Original implementation of the data flow analysis tool
- `code-intelligence-toolkit/data_flow_tracker_v2.py` - Enhanced version with impact analysis, calculation paths, and type tracking
- `code-intelligence-toolkit/doc_generator.py` - Automated documentation generator leveraging data flow analysis
- `code-intelligence-toolkit/run_any_python_tool.sh` - Wrapper script for execution
- `test_data_flow.py` - Simple test examples
- `test_complex_data_flow.py` - Complex test scenarios

---

## Overview

The Data Flow Tracker is a comprehensive static analysis tool that tracks how data flows through your Python and Java code. It builds a complete dependency graph showing how variables affect each other through assignments, function calls, and complex expressions.

## Key Concepts

### Data Flow Analysis
Data flow analysis tracks how values propagate through a program:
- **Forward Analysis**: Given variable X, find all variables that depend on X
- **Backward Analysis**: Given variable Y, find all variables that Y depends on

### Inter-procedural Analysis
The tool tracks data flow across function boundaries:
```python
def process(x):      # x is parameter
    y = x * 2        # y depends on x
    return y         # return value depends on y

result = process(input_val)  # result depends on input_val through process()
```

## Installation

The tool is already integrated into the code-intelligence-toolkit:
```bash
# Direct usage
python3 code-intelligence-toolkit/data_flow_tracker.py --help

# Through wrapper (recommended)
./run_any_python_tool.sh data_flow_tracker.py --help
```

## Basic Usage

### Forward Tracking (What does X affect?)
```bash
# Track what variable 'x' affects
./run_any_python_tool.sh data_flow_tracker.py --var x --file calc.py

# Example output:
# Variable 'x' affects:
# - y = 2 * x (line 10)
# - z = y + 5 (line 11) 
# - result = z * factor (line 15)
```

### Backward Tracking (What affects Y?)
```bash
# Track what affects variable 'result'
./run_any_python_tool.sh data_flow_tracker.py --var result --direction backward --file calc.py

# Example output:
# Variable 'result' depends on:
# - z (line 15: result = z * factor)
# - factor (line 15: result = z * factor)
# - y (line 11: z = y + 5)
# - x (line 10: y = 2 * x)
```

### Both Directions
```bash
# Track both forward and backward dependencies
./run_any_python_tool.sh data_flow_tracker.py --var total --direction both --file calc.py
```

## Advanced Features

### Inter-procedural Analysis
Track data flow across function calls:
```bash
# Enable inter-procedural tracking
./run_any_python_tool.sh data_flow_tracker.py --var user_input --file app.py --inter-procedural

# Tracks flows like:
# user_input → process_data(input_value) → scaled → transform(scaled) → result
```

### Multiple Files
Analyze entire directories or multiple files:
```bash
# Analyze all Python files in a directory
./run_any_python_tool.sh data_flow_tracker.py --var config --scope src/ --recursive

# Analyze specific files
./run_any_python_tool.sh data_flow_tracker.py --var price --file model.py utils.py calc.py
```

### Output Formats

#### JSON Format
Get structured output for programmatic processing:
```bash
./run_any_python_tool.sh data_flow_tracker.py --var x --file calc.py --format json

# Output:
{
  "forward": {
    "variable": "x",
    "affects": [
      {
        "name": "y",
        "location": "calc.py:10",
        "code": "y = 2 * x",
        "expression": "(2 * x)"
      }
    ],
    "flow_paths": ["x → y", "x → y → z"],
    "total_affected": 3
  }
}
```

#### GraphViz Format
Generate visual dependency graphs:
```bash
# Generate DOT file
./run_any_python_tool.sh data_flow_tracker.py --var x --file calc.py --format graph > flow.dot

# Convert to image
dot -Tpng flow.dot -o flow.png
dot -Tsvg flow.dot -o flow.svg
```

### Show All Variables
Analyze all variables in a file:
```bash
./run_any_python_tool.sh data_flow_tracker.py --show-all --file module.py

# Shows dependency information for every variable found
```

### Limit Analysis Depth
Control how deep to trace dependencies:
```bash
# Only trace 2 levels deep
./run_any_python_tool.sh data_flow_tracker.py --var x --max-depth 2 --file calc.py
```

### Filter by File Pattern
Analyze specific file types:
```bash
# Only analyze Python files
./run_any_python_tool.sh data_flow_tracker.py --var data --scope src/ -g "*.py"

# Exclude test files
./run_any_python_tool.sh data_flow_tracker.py --var config --scope . --exclude "*test*"
```

## Supported Python Constructs

### Basic Operations
- Variable assignments: `x = 5`, `y = x + 2`
- Multiple assignments: `a = b = c = 10`
- Augmented assignments: `x += 1`, `y *= 2`

### Complex Expressions
- Binary operations: `result = (a + b) * (c - d)`
- Ternary operators: `val = x if x > 0 else -x`
- Comparisons: `is_valid = x > 0 and y < 100`
- Boolean logic: `flag = condition1 or condition2`

### Data Structures
- Lists: `data = [x, y, z]`, `first = data[0]`
- Tuples: `point = (x, y)`, `a, b = point`
- Dictionaries: `config = {'a': x, 'b': y}`, `val = config['a']`
- Sets: `unique = {x, y, z}`

### Advanced Features
- Tuple unpacking: `first, second, *rest = values`
- List comprehensions: `squares = [x*x for x in data]`
- Dict comprehensions: `mapped = {k: v*2 for k, v in items.items()}`
- Generator expressions: `gen = (x*2 for x in range(10))`

### Object-Oriented
- Instance variables: `self.value = x`
- Method calls: `result = self.process(data)`
- Property access: `val = obj.property`
- Method chaining: `result = obj.method1().method2().value`

### Control Flow
- Function calls: `result = process(x, y)`
- Return values: `return x * 2`
- Global variables: `global config; config = x`
- Lambda functions: `fn = lambda x: x * 2`

## Supported Java Constructs

### Basic Operations
- Variable declarations: `int x = 5;`
- Assignments: `y = x + 2;`
- Field access: `this.value = x;`

### Expressions
- Binary operations: `result = (a + b) * (c - d);`
- Ternary operators: `val = x > 0 ? x : -x;`
- Method calls: `result = process(x, y);`
- Object creation: `obj = new MyClass(x);`

### Data Structures
- Arrays: `int[] data = {x, y, z};`
- Array access: `first = data[0];`
- Method chaining: `result = obj.method1().method2();`

## Real-World Examples

### Example 1: Configuration Parameter Flow
```python
# config_manager.py
def calculate_timeout(base_timeout, retry_count, backoff_factor):
    adjusted_timeout = base_timeout * (1 + backoff_factor)
    max_wait = adjusted_timeout * retry_count
    final_timeout = min(max_wait, 300)  # Cap at 5 minutes
    return final_timeout

# Track what affects final_timeout
$ ./run_any_python_tool.sh data_flow_tracker.py --var final_timeout --direction backward --file config_manager.py

# Output shows:
# final_timeout depends on:
# - max_wait (from adjusted_timeout and retry_count)
# - adjusted_timeout (from base_timeout and backoff_factor)
```

### Example 2: Data Processing Pipeline
```python
# data_processor.py
input_size = 1000
compression_ratio = 0.75
buffer_multiplier = 2

compressed_size = input_size * compression_ratio
buffer_size = compressed_size * buffer_multiplier
final_allocation = buffer_size + (input_size * 0.1)  # 10% overhead

# Track forward flow from compression_ratio
$ ./run_any_python_tool.sh data_flow_tracker.py --var compression_ratio --file data_processor.py

# Shows how changing compression_ratio affects:
# - compressed_size
# - buffer_size  
# - final_allocation
```

### Example 3: Complex Class Analysis
```python
# analyzer.py
class DataAnalyzer:
    def __init__(self):
        self.scale_factor = 1.5
        self.threshold = 0.02
    
    def analyze_data(self, raw_value, weight, confidence):
        weighted_value = raw_value * weight
        score = (weighted_value * confidence) / self.scale_factor
        
        if score > self.threshold:
            result = score * 100
            return self.normalize_result(result)
        return 0
    
    def normalize_result(self, value):
        return value * 0.95  # 5% adjustment

# Analyze the entire module
$ ./run_any_python_tool.sh data_flow_tracker.py --show-all --file analyzer.py --inter-procedural
```

## Output Interpretation

### Flow Paths
The tool shows complete paths of data flow:
```
x → y → z → result
```
This means: x affects y, which affects z, which affects result

### Location Information
Each dependency includes:
- File and line number: `calc.py:15`
- Actual code: `result = x * factor`
- Parsed expression: `(x * factor)`

### Dependency Counts
- `Total affected variables: N` - How many variables are affected (forward)
- `Total dependencies: N` - How many variables contribute (backward)

## Best Practices

1. **Start with key variables**: Focus on critical values like configuration parameters, user inputs, or calculation results

2. **Use inter-procedural for complex code**: Enable `--inter-procedural` when analyzing code with many function calls

3. **Combine with refactoring**: Use before refactoring to understand impact:
   ```bash
   # See what depends on old_method before renaming
   ./run_any_python_tool.sh data_flow_tracker.py --var old_method --file module.py
   ```

4. **Generate graphs for documentation**: Visual graphs help explain complex calculations

5. **Use JSON for automation**: Parse JSON output for automated dependency checking

## Limitations

1. **Static Analysis**: Only tracks explicit data flow, not runtime behavior
2. **No Alias Analysis**: Doesn't track pointer/reference aliases
3. **Limited Dynamic Features**: Can't track `eval()`, `exec()`, or reflection
4. **No Cross-Language**: Can't track Python calling Java or vice versa

## Troubleshooting

### "Variable not found"
- Check variable name spelling
- Ensure the variable is actually assigned in the code
- Try `--show-all` to see all available variables

### "No files found"
- Check file paths are correct
- Use `--scope` for directories
- Ensure file extensions match (`*.py` for Python)

### Large Output
- Use `--max-depth` to limit traversal depth
- Filter specific variables instead of `--show-all`
- Use `--format json` and process programmatically

## Integration with Other Tools

Combine with other code-intelligence-toolkit tools:

```bash
# Find where a method is defined
./run_any_python_tool.sh navigate_ast.py MyClass.py --to process_data

# Track data flow from that method
./run_any_python_tool.sh data_flow_tracker.py --var result --file MyClass.py

# Then refactor safely
./run_any_python_tool.sh replace_text_ast.py --file MyClass.py result new_result
```

## Version 2 Enhanced Features

Data Flow Tracker V2 adds three powerful capabilities for deeper code intelligence:

### 1. Impact Analysis - Know What Will Break

Shows where data "escapes" its local scope and causes observable effects:

```bash
# See all the places where changing db_config would have effects
./run_any_python_tool.sh data_flow_tracker_v2.py --var db_config --show-impact --file app.py
```

Output shows:
- **Returns**: Functions that return values dependent on the variable
- **Side Effects**: File writes, network calls, console output
- **State Changes**: Modifications to global variables or class members
- **Risk Assessment**: Overall risk level of making changes

Example output:
```
============================================================
Impact Analysis
============================================================

🔄 RETURNS:
  - get_connection at db.py:45
    Returns value dependent on db_config

⚠️  SIDE EFFECTS:
  🟡 file_write at logger.py:89
     External call to write

📝 STATE CHANGES:
  - global_write at config.py:23
    External call to cache_config

────────────────────────────────────────────────────────────
SUMMARY:
  Total exit points: 4
  Functions affected: 3
  High risk count: 1

  ⚡ MEDIUM RISK: External side effects detected - ensure testing covers these
```

### 2. Calculation Path Analysis - Understand Complex Logic

Extracts the minimal "critical path" showing exactly how a value is calculated:

```bash
# Understand how final_price is calculated
./run_any_python_tool.sh data_flow_tracker_v2.py --var final_price --show-calculation-path --file pricing.py
```

Shows only the essential steps, filtering out noise:
```
============================================================
Calculation Path
============================================================

1. base_price = get_product_price()
   Location: pricing.py:10
   ↓

2. tax_rate = lookup_tax_rate(location)
   Inputs: location
   Location: pricing.py:15
   ↓

3. discount = apply_coupon(coupon_code)
   Inputs: coupon_code
   Location: pricing.py:20
   ↓

4. final_price = (base_price * (1 + tax_rate)) - discount
   Inputs: base_price, tax_rate, discount
   Location: pricing.py:25
```

### 3. Type and State Tracking - Catch Bugs Early

Monitors how variable types and states evolve through the code:

```bash
# Track type changes and potential issues
./run_any_python_tool.sh data_flow_tracker_v2.py --var user_data --track-state --file process.py
```

Reveals type changes and warnings:
```
============================================================
Type & State Evolution for 'user_data'
============================================================

📈 TYPE EVOLUTION:
  process.py:10: dict ✓
  process.py:15: dict (nullable) ✓
    Possible values: [None]
  process.py:20: UserModel ✓

🔄 STATE CHANGES:
  process.py:10: assignment
  process.py:15: assignment (in conditional)
  process.py:20: assignment

⚠️  WARNINGS:
  - Variable may be None - add null checks
  - Type changes detected: dict → UserModel
```

### V2 Use Cases

**Before Refactoring**:
```bash
# Check impact before renaming a configuration variable
./run_any_python_tool.sh data_flow_tracker_v2.py --var old_config_name --show-impact --file settings.py
```

**Debugging Complex Calculations**:
```bash
# Understand why a value is wrong
./run_any_python_tool.sh data_flow_tracker_v2.py --var wrong_result --show-calculation-path --file calc.py
```

**Type Safety Validation**:
```bash
# Verify type consistency before deployment
./run_any_python_tool.sh data_flow_tracker_v2.py --var api_response --track-state --file handler.py
```

### Combining V2 Features

You can use V2 alongside V1 features:
```bash
# First, see what affects the variable (V1)
./run_any_python_tool.sh data_flow_tracker.py --var total --direction backward --file calc.py

# Then, understand the calculation path (V2)
./run_any_python_tool.sh data_flow_tracker_v2.py --var total --show-calculation-path --file calc.py

# Finally, check impact of changes (V2)
./run_any_python_tool.sh data_flow_tracker_v2.py --var total --show-impact --file calc.py
```

## Intelligence Layer - Transform Analysis into Insights

The Intelligence Layer represents a breakthrough enhancement that transforms complex technical analysis into intuitive, actionable insights through natural language explanations and interactive visualizations.

### 🧠 Natural Language Explanations (`--explain`)

Convert technical analysis into plain English explanations that anyone can understand:

#### Impact Analysis Explanations
```bash
./run_any_python_tool.sh data_flow_tracker_v2.py --var database_config --show-impact --explain --file app.py
```

Example output:
```
📊 **Impact Analysis for 'database_config'**:

🚨 **High Risk Change**: Modifying 'database_config' affects 8 different places across 4 functions. 
It affects 3 return values, causes 2 external side effects (like file writes or console output), 
and modifies 3 global or class variables.

💡 **Recommendation**: Break this change into smaller steps and test each affected function thoroughly.
```

#### Calculation Path Explanations
```bash
./run_any_python_tool.sh data_flow_tracker_v2.py --var final_price --show-calculation-path --explain --file pricing.py
```

Example output:
```
🔍 **How 'final_price' is Calculated**:

This value is calculated through 6 steps, showing the complete algorithm flow.

**The Critical Path**:
1. **Variable Created**: 'base_price' is first declared (depends on: product_id)
2. **Calculation Step**: 'tax_rate' is computed from location (depends on: location)
3. **Calculation Step**: 'discount' is computed from coupon_code (depends on: coupon_code)
4. **Calculation Step**: 'final_price' is computed from base_price, tax_rate, discount

💡 **Understanding**: To debug issues with 'final_price', trace through these 6 steps. 
Each step shows exactly where the value comes from and what influences it.
```

#### State Tracking Explanations
```bash
./run_any_python_tool.sh data_flow_tracker_v2.py --var user_data --track-state --explain --file process.py
```

Example output:
```
🔄 **State Evolution Analysis for 'user_data'**:

**Type Changes Detected**: 'user_data' changes types: dict → UserModel. 
This could indicate potential bugs or intentional polymorphic behavior.

**State Modifications**: 'user_data' is modified 4 times, including 2 changes inside loops.

⚠️ **Potential Issues Detected**:
• Variable may be None - add null checks
• Type changes detected: dict → UserModel

💡 **Analysis Summary**: Consider type annotations or validation to handle type changes safely. 
Track the 4 state modifications to understand variable behavior.
```

### 🌐 Interactive HTML Visualization (`--output-html`)

Generate professional, self-contained HTML reports with interactive network visualizations:

#### Basic HTML Generation
```bash
./run_any_python_tool.sh data_flow_tracker_v2.py --var config --show-impact --output-html --file app.py
```

Output: `data_flow_impact_config_app_py.html`

#### Combined Intelligence
```bash
./run_any_python_tool.sh data_flow_tracker_v2.py --var total --show-calculation-path --explain --output-html --file calc.py
```

This generates both:
- Interactive HTML visualization file
- Console explanation of the analysis

#### HTML Report Features

**🎨 Professional Styling:**
- Risk-based color coding (Red for high risk, Yellow for medium, Green for low)
- Modern, responsive design that works on all devices
- Professional typography and layout

**🔍 Interactive Exploration:**
- **Click nodes** to see detailed information about variables and operations
- **Drag and zoom** to explore complex dependency networks
- **Toggle physics** to freeze or animate the network layout
- **Center view** to reset the visualization focus

**📊 Rich Visualizations:**
- **Impact Analysis**: Shows source variable connected to all affected areas
- **Calculation Path**: Step-by-step flow with input dependencies clearly marked
- **State Tracking**: Timeline of type evolution and state changes
- **Standard Analysis**: Forward/backward dependency networks

**💾 Export Capabilities:**
- **PNG Export**: Save visualizations as high-quality images
- **Self-Contained**: No external dependencies - works offline
- **Shareable**: Email or share HTML files with team members

#### Visualization Types

**Impact Analysis Visualization:**
```bash
./run_any_python_tool.sh data_flow_tracker_v2.py --var sensitive_data --show-impact --output-html --file security.py
```
- Central node: The variable being analyzed
- Connected nodes: Return values (green), side effects (red), state changes (orange)
- Risk-based header colors and indicators

**Calculation Path Visualization:**
```bash
./run_any_python_tool.sh data_flow_tracker_v2.py --var algorithm_result --show-calculation-path --output-html --file compute.py
```
- Linear flow showing calculation steps
- Input variables feeding into each step
- Clear progression from inputs to final result

**State Tracking Visualization:**
```bash
./run_any_python_tool.sh data_flow_tracker_v2.py --var dynamic_var --track-state --output-html --file evolving.py
```
- Timeline of type evolution
- State change annotations with context (loop/conditional)
- Warning indicators for potential issues

### Intelligence Layer Use Cases

#### 🎯 **Code Review Intelligence**
```bash
# Before approving a PR, understand the full impact
./run_any_python_tool.sh data_flow_tracker_v2.py --var modified_variable --show-impact --explain --output-html --file changed_file.py
```

**Benefit**: Reviewers get both intuitive explanations and visual exploration tools

#### 🐛 **Debugging with Intelligence**
```bash
# When a bug is reported, trace the calculation path with explanations
./run_any_python_tool.sh data_flow_tracker_v2.py --var incorrect_result --show-calculation-path --explain --file buggy_module.py
```

**Benefit**: Clear English explanation of how the value is computed + visual trace

#### 🔄 **Refactoring Safety**
```bash
# Before refactoring, get risk assessment and visual impact map
./run_any_python_tool.sh data_flow_tracker_v2.py --var legacy_function --show-impact --explain --output-html --file old_code.py
```

**Benefit**: Risk level assessment + actionable testing recommendations + shareable impact visualization

#### 📚 **Code Documentation**
```bash
# Generate visual documentation of complex algorithms
./run_any_python_tool.sh data_flow_tracker_v2.py --var complex_calculation --show-calculation-path --output-html --file algorithm.py
```

**Benefit**: Self-documenting code with interactive exploration for new team members

#### 🎓 **Learning and Onboarding**
```bash
# Help new developers understand codebase dependencies
./run_any_python_tool.sh data_flow_tracker_v2.py --var core_component --show-impact --explain --output-html --file main.py
```

**Benefit**: Intuitive explanations make complex codebases approachable

## Advanced Use Cases

### Debugging Incorrect Calculations
```bash
# If final_result is wrong, trace back to find the issue
./run_any_python_tool.sh data_flow_tracker.py --var final_result --direction backward --file calc.py
```

### Security Analysis
```bash
# Track where user input flows
./run_any_python_tool.sh data_flow_tracker.py --var user_input --file app.py --inter-procedural
```

### Performance Optimization
```bash
# Find all variables affected by expensive calculation
./run_any_python_tool.sh data_flow_tracker.py --var expensive_calc --file module.py
```

### Code Review
```bash
# Verify no unintended dependencies
./run_any_python_tool.sh data_flow_tracker.py --var sensitive_data --file security.py
```

## Automated Documentation Generation

The intelligence layer now powers automated documentation generation through `doc_generator.py`, which leverages data flow analysis to create intelligent documentation.

### Documentation Generation Features

```bash
# Generate API documentation for functions
./run_any_python_tool.sh doc_generator.py --function calculatePrice --file pricing.py --style api-docs

# Create user-friendly guides for classes
./run_any_python_tool.sh doc_generator.py --class UserManager --file auth.py --style user-guide --depth deep

# Generate technical analysis documentation
./run_any_python_tool.sh doc_generator.py --module --file database.py --style technical --output html

# Quick reference cards
./run_any_python_tool.sh doc_generator.py --function process_data --file data.py --style quick-ref --format docstring

# Tutorial-style documentation
./run_any_python_tool.sh doc_generator.py --class APIClient --file client.py --style tutorial --depth medium
```

### Documentation Styles

1. **API Documentation** (`--style api-docs`): Technical reference with parameters, return values, and usage examples
2. **User Guides** (`--style user-guide`): Friendly explanations accessible to all skill levels
3. **Technical Analysis** (`--style technical`): Deep analysis with data flow, complexity metrics, and architectural insights
4. **Quick Reference** (`--style quick-ref`): Concise format for immediate lookup
5. **Tutorials** (`--style tutorial`): Educational approach with step-by-step guidance

### Output Formats

- **Markdown** (`--format markdown`): For documentation systems and README files
- **HTML** (`--format html`): For web documentation and reports
- **Docstring** (`--format docstring`): For inline Python documentation
- **reStructuredText** (`--format rst`): For Sphinx and other documentation generators

### Intelligence Integration

The documentation generator leverages the same data flow analysis used by the intelligence layer:

- **Dependency Analysis**: Shows what functions depend on and affect
- **Complexity Assessment**: Provides complexity warnings and refactoring suggestions
- **Auto-Generated Examples**: Creates contextually appropriate code samples
- **Risk Assessment**: Identifies high-complexity areas that need careful documentation

### Combined Workflow Example

```bash
# 1. Analyze the data flow first
./run_any_python_tool.sh data_flow_tracker_v2.py --var config --show-impact --explain --file app.py

# 2. Generate comprehensive documentation
./run_any_python_tool.sh doc_generator.py --function setup_config --file app.py --style technical --depth deep

# 3. Create user-friendly guide
./run_any_python_tool.sh doc_generator.py --function setup_config --file app.py --style user-guide --format html
```

This creates a complete documentation suite: technical analysis for developers, visual impact analysis for code review, and user-friendly guides for broader audiences.