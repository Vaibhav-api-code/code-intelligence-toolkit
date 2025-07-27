# Data Flow Tracker - Advanced Examples

**Related Code Files:**
- `code-intelligence-toolkit/data_flow_tracker.py` - The data flow analysis tool
- Example code files in your project

---

## Overview

This document provides real-world examples of using the Data Flow Tracker to analyze complex algorithms, debug calculations, and ensure data integrity in various types of applications.

## Example 1: Weighted Average Calculation Analysis

### Scenario
You need to understand how input values flow through a weighted average calculation.

```java
// WeightedCalculator.java
public class WeightedCalculator {
    private double cumulativeWeight = 0;
    private double cumulativeWeightedValue = 0;
    
    public double updateAverage(double value, double weight) {
        cumulativeWeightedValue += value * weight;
        cumulativeWeight += weight;
        double average = cumulativeWeightedValue / cumulativeWeight;
        return average;
    }
}
```

### Analysis Command
```bash
# Track how value affects the final average
./run_any_python_tool.sh data_flow_tracker.py --var value --file WeightedCalculator.java

# Output:
# value affects:
# → cumulativeWeightedValue (line 7: cumulativeWeightedValue += value * weight)
# → average (line 9: average = cumulativeWeightedValue / cumulativeWeight)
```

### Insights
- Value directly impacts cumulativeWeightedValue
- Changes to value calculation will affect average accuracy
- Weight is equally important in the calculation

## Example 2: Resource Allocation Dependencies

### Scenario
Analyze how resource allocation depends on various parameters.

```python
# resource_manager.py
class ResourceManager:
    def __init__(self):
        self.total_resources = 100000
        self.allocation_ratio = 0.02  # 2%
        self.scale_factor = 10
    
    def calculate_allocation(self, priority_score, demand_factor):
        base_demand = abs(priority_score - demand_factor)
        allocated_amount = self.total_resources * self.allocation_ratio
        
        # Base allocation
        base_allocation = allocated_amount / base_demand
        
        # Apply scaling
        scaled_allocation = base_allocation * self.scale_factor
        
        # Apply maximum limit
        max_allocation = self.total_resources * 0.3
        final_allocation = min(scaled_allocation, max_allocation)
        
        return final_allocation
```

### Analysis Commands
```bash
# Track what affects final allocation (backward analysis)
./run_any_python_tool.sh data_flow_tracker.py --var final_allocation --direction backward --file resource_manager.py

# Track impact of changing allocation_ratio (forward analysis)
./run_any_python_tool.sh data_flow_tracker.py --var allocation_ratio --file resource_manager.py --inter-procedural

# Generate visual dependency graph
./run_any_python_tool.sh data_flow_tracker.py --var base_allocation --format graph --file resource_manager.py > flow.dot
dot -Tpng flow.dot -o dependencies.png
```

### Results
```
final_allocation depends on:
← scaled_allocation (line 18: final_allocation = min(scaled_allocation, max_allocation))
← max_allocation (line 18)
← base_allocation (line 15: scaled_allocation = base_allocation * self.scale_factor)
← self.scale_factor (line 15)
← allocated_amount (line 12: base_allocation = allocated_amount / base_demand)
← base_demand (line 12)
← self.total_resources (line 10: allocated_amount = self.total_resources * self.allocation_ratio)
← self.allocation_ratio (line 10)
← priority_score (line 9: base_demand = abs(priority_score - demand_factor))
← demand_factor (line 9)
```

## Example 3: Data Processing Pipeline

### Scenario
Debug complex data processing calculations to find bottlenecks.

```java
// DataProcessor.java
public class DataProcessor {
    private double processingThreshold = 0.65;
    
    public double processData(Map<String, Integer> inputData, 
                             Map<String, Integer> referenceData,
                             int batchSize) {
        int inputSum = 0;
        int referenceSum = 0;
        
        // Sum input values
        int count = 0;
        for (Integer value : inputData.values()) {
            inputSum += value;
            if (++count >= batchSize) break;
        }
        
        // Sum reference values
        count = 0;
        for (Integer value : referenceData.values()) {
            referenceSum += value;
            if (++count >= batchSize) break;
        }
        
        // Calculate ratio
        double totalValue = inputSum + referenceSum;
        double processingRatio = inputSum / totalValue;
        
        // Generate result
        if (processingRatio > processingThreshold) {
            return 1.0; // High priority
        } else if (processingRatio < (1 - processingThreshold)) {
            return -1.0; // Low priority
        }
        return 0.0; // Normal
    }
}
```

### Debugging Process
```bash
# 1. Track what affects the processing ratio
./run_any_python_tool.sh data_flow_tracker.py --var processingRatio --direction backward --file DataProcessor.java

# 2. See full dependency chain
./run_any_python_tool.sh data_flow_tracker.py --show-all --file DataProcessor.java

# 3. Track specific parameter impact
./run_any_python_tool.sh data_flow_tracker.py --var batchSize --file DataProcessor.java
```

### Discovered Issue
The analysis reveals that `batchSize` parameter affects both `inputSum` and `referenceSum`, but the counting logic might terminate early if data has fewer entries than requested.

## Example 4: Multi-Component System Dependencies

### Scenario
Understand dependencies in a system that combines multiple components.

```python
# multi_component_system.py
class MultiComponentSystem:
    def __init__(self):
        self.filter_window = 20
        self.smoothing_factor = 14
        self.amplification = 1.5
        
    def process_signal(self, raw_data, timestamps):
        # Calculate components
        filtered = self.apply_filter(raw_data, self.filter_window)
        smoothed = self.apply_smoothing(filtered, self.smoothing_factor)
        baseline = sum(raw_data[-20:]) / 20
        
        # Check conditions
        above_baseline = raw_data[-1] > baseline
        
        # Signal quality  
        quality_good = smoothed > 30 and smoothed < 70
        
        # Amplitude check
        current_amplitude = raw_data[-1]
        amplitude_high = current_amplitude > baseline * self.amplification
        
        # Combined result
        if above_baseline and quality_good and amplitude_high:
            signal_strength = (smoothed - 50) / 50 * self.calculate_confidence()
            return ('PROCESS', signal_strength)
        
        return ('SKIP', 0.0)
```

### Comprehensive Analysis
```bash
# Analyze entire module with inter-procedural tracking
./run_any_python_tool.sh data_flow_tracker.py --show-all --file multi_component_system.py --inter-procedural

# Track specific component dependencies
./run_any_python_tool.sh data_flow_tracker.py --var filter_window --file multi_component_system.py

# See what affects the final signal
./run_any_python_tool.sh data_flow_tracker.py --var signal_strength --direction backward --file multi_component_system.py
```

### Key Findings
- `signal_strength` depends on smoothing calculation and confidence method
- Changing `filter_window` affects filtering but not signal strength directly
- `amplification` is critical for signal generation

## Example 5: Performance-Critical Calculations

### Scenario
Identify calculation bottlenecks by tracing expensive operations.

```java
// PerformanceCritical.java
public class PerformanceCritical {
    private double previousValue = 0;
    private double smoothingFactor = 0.1;
    private double threshold = 0.001;
    
    public boolean shouldProcess(double currentValue, long timestamp) {
        // Expensive calculation 1
        double valueChange = (currentValue - previousValue) / previousValue;
        
        // Expensive calculation 2
        double smoothedChange = smoothingFactor * valueChange + 
                               (1 - smoothingFactor) * previousSmoothed;
        
        // Expensive calculation 3
        double complexity = calculateComplexity(dataHistory);
        
        // Decision logic
        boolean valueSignal = Math.abs(smoothedChange) > threshold;
        boolean complexityOk = complexity < maxComplexity;
        boolean timeValid = isWithinWindow(timestamp);
        
        return valueSignal && complexityOk && timeValid;
    }
}
```

### Performance Analysis
```bash
# Find what depends on expensive complexity calculation
./run_any_python_tool.sh data_flow_tracker.py --var complexity --file PerformanceCritical.java

# Check if any calculations are unused
./run_any_python_tool.sh data_flow_tracker.py --show-all --file PerformanceCritical.java | grep "Affects 0 variables"
```

## Example 6: Parameter Sensitivity Analysis

### Scenario
Before optimizing parameters, understand their impact radius.

```python
# parameter_sensitive_algorithm.py
class Algorithm:
    def __init__(self):
        # Key parameters
        self.window_size = 50
        self.activation_threshold = 0.02
        self.deactivation_threshold = 0.01
        self.scale_factor = 1.0
        
    def calculate_activation(self, data):
        # Historical metrics
        history = self.extract_window(data, self.window_size)
        mean_value = sum(history) / len(history)
        std_dev = self.calculate_std(history)
        
        # Score calculation
        current_value = (data[-1] - data[-2]) / data[-2]
        score = (current_value - mean_value) / std_dev
        
        # Activation logic
        if score > self.activation_threshold:
            output = self.scale_factor * (score - self.activation_threshold)
            return min(output, 1.0)  # Cap at 100%
        
        return 0.0
```

### Parameter Impact Analysis
```bash
# See everything affected by window_size
./run_any_python_tool.sh data_flow_tracker.py --var window_size --file parameter_sensitive_algorithm.py

# Output shows:
# window_size affects:
# → history (via extract_window)
# → mean_value
# → std_dev  
# → score
# → output
# This reveals window_size has wide impact!

# Compare with activation_threshold impact
./run_any_python_tool.sh data_flow_tracker.py --var activation_threshold --file parameter_sensitive_algorithm.py

# Output shows:
# activation_threshold affects:
# → output (only when score > activation_threshold)
# This shows activation_threshold has limited, conditional impact
```

## Best Practices for Analysis

### 1. Pre-Deployment Checks
Always analyze data flow before deploying changes:
```bash
# Check what a modified calculation affects
./run_any_python_tool.sh data_flow_tracker.py --var modified_calc --file module.py
```

### 2. Critical Parameter Verification
Ensure critical parameters flow correctly to outputs:
```bash
# Verify parameter flows to final output
./run_any_python_tool.sh data_flow_tracker.py --var critical_param --file module.py --inter-procedural
```

### 3. Debugging Incorrect Values
When output is wrong, trace backwards:
```bash
# Start from wrong output and trace back
./run_any_python_tool.sh data_flow_tracker.py --var wrong_output --direction backward --file module.py
```

### 4. Performance Optimization
Identify unused calculations:
```bash
# Find calculations that don't affect anything
./run_any_python_tool.sh data_flow_tracker.py --show-all --file module.py | grep "Affects 0"
```

### 5. Documentation Generation
Create visual docs for complex algorithms:
```bash
# Generate complete dependency graph
./run_any_python_tool.sh data_flow_tracker.py --show-all --format graph --file complex_algorithm.py > algorithm.dot
dot -Tsvg algorithm.dot -o algorithm_flow.svg
```

## Common Patterns in Complex Code

### 1. Cumulative Calculations
Variables like `cumulativeSum` have wide impact:
- Track with forward analysis
- Changes affect all downstream calculations

### 2. Threshold Parameters
Variables like `threshold` have conditional impact:
- May not show in basic analysis
- Use `--show-all` to see conditional dependencies

### 3. Window-Based Dependencies
Window sizes affect many calculations:
- Critical to analyze before changing
- Often have cascading effects

### 4. Scale Factors
Multipliers and scale factors amplify everything:
- Always verify their flow to final output
- Check for proper bounds/limits

## Integration with Other Tools

### Complete Analysis Workflow
```bash
# 1. View module structure
./run_any_python_tool.sh show_structure_ast.py Module.java

# 2. Find key calculations
./run_any_python_tool.sh find_text.py "calculate.*" --type regex --file Module.java

# 3. Analyze data flow
./run_any_python_tool.sh data_flow_tracker.py --var output --file Module.java

# 4. Check for issues
./run_any_python_tool.sh suggest_refactoring.py Module.java

# 5. Safe refactoring
./run_any_python_tool.sh replace_text_ast.py --file Module.java oldVar newVar
```

## Troubleshooting Tips

1. **Large Modules**: Use `--max-depth` to limit analysis depth
2. **Multiple Files**: Analyze core calculation files first
3. **Java Code**: Ensure javalang is installed
4. **Complex Expressions**: Check JSON output for full expression details
5. **Performance**: For large codebases, analyze specific variables rather than `--show-all`