#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
dependency_analyzer.py - Comprehensive Java class dependency analysis tool with visualization

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-21
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import os
import sys
import argparse
import json
import csv
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
import logging

# Set up logging
LOG = logging.getLogger(__name__)

try:
    import matplotlib.pyplot as plt
    import networkx as nx
    from matplotlib.patches import Rectangle
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# Import our existing tools
try:
    from find_text_v5 import search_with_context
    from cross_file_analysis_ast import analyze_dependencies
    from ast_context_finder import ASTContextFinder
    HAS_ANALYSIS_TOOLS = True
except ImportError:
    HAS_ANALYSIS_TOOLS = False

@dataclass
class ClassInfo:
    """Information about a Java class."""
    name: str
    file_path: str
    line_count: int
    package: str
    imports: List[str]
    dependencies: List[str]
    category: str = "Unknown"
    is_ui: bool = False
    is_test: bool = False
    complexity_score: float = 0.0
    
@dataclass  
class DependencyGraph:
    """Complete dependency analysis result."""
    root_class: ClassInfo
    dependencies: Dict[str, ClassInfo]
    total_lines: int
    categories: Dict[str, List[str]]
    graph_data: Dict[str, Any]
    analysis_summary: Dict[str, Any]

class JavaDependencyAnalyzer:
    """Comprehensive Java class dependency analyzer."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.class_cache: Dict[str, ClassInfo] = {}
        self.search_paths = [
            "src/main/java",
            "src/test/java",
            "java-intelligence-analysis-toolkit"
        ]
        
        # Category patterns for classification
        self.category_patterns = {
            "UI": [r"UI\w*", r"\w*Frame\w*", r"\w*Dialog\w*", r"\w*Panel\w*", r"\w*Monitor\w*"],
            "Processing": [r"\w*Data\w*", r"\w*Process\w*", r"\w*Position\w*", r"\w*Portfolio\w*"],
            "Analysis": [r"\w*Analyzer\w*", r"\w*Calculator\w*", r"\w*Detector\w*", r"\w*Tracker\w*"],
            "Data": [r"\w*Data\w*", r"\w*Store\w*", r"\w*Cache\w*", r"\w*Buffer\w*"],
            "Analyzer": [r"\w*Indicator\w*", r"\w*Analysis\w*", r"\w*Moving\w*", r"\w*Average\w*"],
            "Utility": [r"\w*Util\w*", r"\w*Helper\w*", r"\w*Manager\w*", r"\w*Service\w*"],
            "Test": [r"\w*Test\w*", r"Test\w*"]
        }
    
    def find_java_file(self, class_name: str) -> Optional[Path]:
        """Find the Java file for a given class name."""
        for search_path in self.search_paths:
            full_path = self.project_root / search_path
            if full_path.exists():
                # Walk through directory structure
                for root, dirs, files in os.walk(full_path):
                    for file in files:
                        if file == f"{class_name}.java":
                            return Path(root) / file
        return None
    
    def extract_imports_and_dependencies(self, file_path: Path) -> Tuple[List[str], List[str]]:
        """Extract imports and dependency class names from Java file."""
        imports = []
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract import statements
            import_pattern = r'import\s+(?:static\s+)?([^;]+);'
            imports = re.findall(import_pattern, content)
            
            # Extract class references (simplified heuristic)
            # Look for class instantiations, method calls on classes, etc.
            class_patterns = [
                r'new\s+(\w+)\s*\(',
                r'(\w+)\.(?:getInstance|create|valueOf)\s*\(',
                r'@(\w+)',
                r'extends\s+(\w+)',
                r'implements\s+(\w+)'
            ]
            
            for pattern in class_patterns:
                dependencies.extend(re.findall(pattern, content))
            
            # Remove duplicates and filter out common Java types
            common_types = {'String', 'Integer', 'Double', 'Boolean', 'Object', 'List', 'Map', 'Set'}
            dependencies = [dep for dep in set(dependencies) if dep not in common_types and len(dep) > 2]
            
        except Exception as e:
            LOG.warning(f"Error reading {file_path}: {e}")
        
        return imports, dependencies
    
    def categorize_class(self, class_name: str, file_path: Path) -> str:
        """Categorize a class based on its name and location."""
        # Check for test classes
        if "test" in str(file_path).lower() or "Test" in class_name:
            return "Test"
        
        # Check other patterns
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, class_name, re.IGNORECASE):
                    return category
        
        # Check by file location
        path_str = str(file_path).lower()
        if "ui" in path_str:
            return "UI"
        elif "utils" in path_str:
            return "Utility"
        elif "indicators" in path_str:
            return "Analyzer"
        elif "data" in path_str:
            return "Data"
        
        return "Core"
    
    def calculate_complexity_score(self, class_info: ClassInfo) -> float:
        """Calculate complexity score based on various factors."""
        score = 0.0
        
        # Base score from line count (normalized)
        score += min(class_info.line_count / 1000, 10.0)
        
        # Dependency count factor
        score += len(class_info.dependencies) * 0.1
        
        # Import count factor
        score += len(class_info.imports) * 0.05
        
        # Category multipliers
        category_multipliers = {
            "UI": 1.5,      # UI classes tend to be complex
            "Processing": 2.0,  # Trading logic is inherently complex
            "Analysis": 1.8, # Analysis algorithms are complex
            "Analyzer": 1.3,
            "Core": 1.2,
            "Utility": 0.8,
            "Test": 0.5
        }
        
        multiplier = category_multipliers.get(class_info.category, 1.0)
        score *= multiplier
        
        return round(score, 2)
    
    def analyze_class(self, class_name: str, file_path: Optional[Path] = None) -> Optional[ClassInfo]:
        """Analyze a single Java class."""
        if class_name in self.class_cache:
            return self.class_cache[class_name]
        
        if file_path is None:
            file_path = self.find_java_file(class_name)
        
        if not file_path or not file_path.exists():
            LOG.warning(f"Could not find file for class: {class_name}")
            return None
        
        # Count lines
        try:
            line_count = sum(1 for _ in open(file_path, 'r', encoding='utf-8'))
        except Exception:
            line_count = 0
        
        # Extract package
        package = ""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_lines = f.read(1000)  # Read first 1000 chars
                package_match = re.search(r'package\s+([^;]+);', first_lines)
                if package_match:
                    package = package_match.group(1)
        except Exception:
            pass
        
        # Extract dependencies
        imports, dependencies = self.extract_imports_and_dependencies(file_path)
        
        # Create class info
        class_info = ClassInfo(
            name=class_name,
            file_path=str(file_path),
            line_count=line_count,
            package=package,
            imports=imports,
            dependencies=dependencies,
            category=self.categorize_class(class_name, file_path),
            is_ui="UI" in class_name or "ui" in str(file_path).lower(),
            is_test="Test" in class_name or "test" in str(file_path).lower()
        )
        
        class_info.complexity_score = self.calculate_complexity_score(class_info)
        
        self.class_cache[class_name] = class_info
        return class_info
    
    def analyze_dependencies_recursive(self, root_class: str, max_depth: int = 3, 
                                     current_depth: int = 0) -> DependencyGraph:
        """Recursively analyze dependencies of a class."""
        if current_depth > max_depth:
            return DependencyGraph(None, {}, 0, {}, {}, {})
        
        # Analyze root class
        root_info = self.analyze_class(root_class)
        if not root_info:
            raise ValueError(f"Could not analyze root class: {root_class}")
        
        dependencies = {root_class: root_info}
        categories = defaultdict(list)
        categories[root_info.category].append(root_class)
        
        # Recursively analyze dependencies
        to_analyze = list(root_info.dependencies)
        analyzed = {root_class}
        
        while to_analyze and current_depth < max_depth:
            current = to_analyze.pop(0)
            if current in analyzed:
                continue
            
            dep_info = self.analyze_class(current)
            if dep_info:
                dependencies[current] = dep_info
                categories[dep_info.category].append(current)
                analyzed.add(current)
                
                # Add this class's dependencies to analyze
                for subdep in dep_info.dependencies:
                    if subdep not in analyzed:
                        to_analyze.append(subdep)
        
        # Calculate totals
        total_lines = sum(info.line_count for info in dependencies.values())
        
        # Create graph data for visualization
        graph_data = self._create_graph_data(dependencies)
        
        # Analysis summary
        analysis_summary = {
            "total_classes": len(dependencies),
            "total_lines": total_lines,
            "average_lines_per_class": total_lines / len(dependencies) if dependencies else 0,
            "categories_count": len(categories),
            "complexity_distribution": self._calculate_complexity_distribution(dependencies),
            "largest_classes": sorted(dependencies.values(), key=lambda x: x.line_count, reverse=True)[:10]
        }
        
        return DependencyGraph(
            root_class=root_info,
            dependencies=dependencies,
            total_lines=total_lines,
            categories=dict(categories),
            graph_data=graph_data,
            analysis_summary=analysis_summary
        )
    
    def _create_graph_data(self, dependencies: Dict[str, ClassInfo]) -> Dict[str, Any]:
        """Create graph data for visualization."""
        nodes = []
        edges = []
        
        for class_name, class_info in dependencies.items():
            nodes.append({
                "id": class_name,
                "label": class_name,
                "size": class_info.line_count,
                "category": class_info.category,
                "complexity": class_info.complexity_score,
                "color": self._get_category_color(class_info.category)
            })
            
            # Add edges for dependencies
            for dep in class_info.dependencies:
                if dep in dependencies:  # Only add edges for analyzed dependencies
                    edges.append({
                        "source": class_name,
                        "target": dep,
                        "weight": 1
                    })
        
        return {"nodes": nodes, "edges": edges}
    
    def _get_category_color(self, category: str) -> str:
        """Get color for category visualization."""
        colors = {
            "UI": "#FF6B6B",
            "Processing": "#4ECDC4", 
            "Analysis": "#45B7D1",
            "Data": "#96CEB4",
            "Analyzer": "#FFEAA7",
            "Utility": "#DDA0DD",
            "Core": "#98D8C8",
            "Test": "#F7DC6F"
        }
        return colors.get(category, "#BDC3C7")
    
    def _calculate_complexity_distribution(self, dependencies: Dict[str, ClassInfo]) -> Dict[str, int]:
        """Calculate complexity score distribution."""
        distribution = {"Low": 0, "Medium": 0, "High": 0, "Very High": 0}
        
        for class_info in dependencies.values():
            score = class_info.complexity_score
            if score < 2.0:
                distribution["Low"] += 1
            elif score < 5.0:
                distribution["Medium"] += 1
            elif score < 10.0:
                distribution["High"] += 1
            else:
                distribution["Very High"] += 1
        
        return distribution
    
    def generate_matplotlib_graph(self, result: DependencyGraph, output_path: str):
        """Generate dependency graph using matplotlib."""
        if not HAS_MATPLOTLIB:
            LOG.error("Matplotlib not available. Install with: pip install matplotlib")
            return
        
        plt.style.use('default')
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
        fig.suptitle(f"Dependency Analysis: {result.root_class.name}", fontsize=16, fontweight='bold')
        
        # 1. Dependency Network Graph
        G = nx.DiGraph()
        pos_data = {}
        
        for node in result.graph_data["nodes"]:
            G.add_node(node["id"], **node)
        
        for edge in result.graph_data["edges"]:
            G.add_edge(edge["source"], edge["target"])
        
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Draw network
        node_colors = [result.graph_data["nodes"][i]["color"] for i in range(len(G.nodes()))]
        node_sizes = [max(info.line_count / 10, 100) for info in result.dependencies.values()]
        
        nx.draw(G, pos, ax=ax1, node_color=node_colors, node_size=node_sizes, 
               with_labels=True, font_size=8, font_weight='bold', 
               edge_color='gray', arrows=True, arrowsize=20, alpha=0.8)
        ax1.set_title("Dependency Network Graph\n(Node size = Lines of Code)", fontweight='bold')
        ax1.set_aspect('equal')
        
        # 2. Lines of Code by Category
        category_lines = defaultdict(int)
        for class_name, class_info in result.dependencies.items():
            category_lines[class_info.category] += class_info.line_count
        
        categories = list(category_lines.keys())
        lines = list(category_lines.values())
        colors = [self._get_category_color(cat) for cat in categories]
        
        bars = ax2.bar(categories, lines, color=colors, alpha=0.8, edgecolor='black')
        ax2.set_title("Lines of Code by Category", fontweight='bold')
        ax2.set_ylabel("Lines of Code")
        ax2.set_xlabel("Category")
        plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{int(height):,}', ha='center', va='bottom', fontweight='bold')
        
        # 3. Complexity Score Distribution
        complexity_dist = result.analysis_summary["complexity_distribution"]
        complexity_labels = list(complexity_dist.keys())
        complexity_values = list(complexity_dist.values())
        complexity_colors = ['#2ECC71', '#F39C12', '#E74C3C', '#8E44AD']
        
        wedges, texts, autotexts = ax3.pie(complexity_values, labels=complexity_labels, 
                                          colors=complexity_colors, autopct='%1.1f%%', 
                                          startangle=90, explode=(0.05, 0.05, 0.05, 0.05))
        ax3.set_title("Complexity Distribution", fontweight='bold')
        
        # 4. Top 10 Largest Classes
        largest = result.analysis_summary["largest_classes"][:10]
        class_names = [info.name for info in largest]
        class_lines = [info.line_count for info in largest]
        class_colors = [self._get_category_color(info.category) for info in largest]
        
        bars = ax4.barh(class_names, class_lines, color=class_colors, alpha=0.8, edgecolor='black')
        ax4.set_title("Top 10 Largest Classes", fontweight='bold')
        ax4.set_xlabel("Lines of Code")
        
        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax4.text(width + width*0.01, bar.get_y() + bar.get_height()/2.,
                    f'{int(width):,}', ha='left', va='center', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        LOG.info(f"Matplotlib graph saved to: {output_path}")
    
    def generate_plotly_graph(self, result: DependencyGraph, output_path: str):
        """Generate interactive dependency graph using Plotly."""
        if not HAS_PLOTLY:
            LOG.error("Plotly not available. Install with: pip install plotly")
            return
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Dependency Network", "Lines of Code by Category", 
                          "Complexity Distribution", "Top 10 Largest Classes"),
            specs=[[{"type": "scatter"}, {"type": "bar"}],
                   [{"type": "pie"}, {"type": "bar"}]]
        )
        
        # 1. Network graph (simplified as scatter plot)
        nodes = result.graph_data["nodes"]
        
        # Create hover text
        hover_text = []
        for node in nodes:
            class_info = result.dependencies[node["id"]]
            text = f"<b>{node['id']}</b><br>"
            text += f"Category: {class_info.category}<br>"
            text += f"Lines: {class_info.line_count:,}<br>"
            text += f"Complexity: {class_info.complexity_score}<br>"
            text += f"Dependencies: {len(class_info.dependencies)}"
            hover_text.append(text)
        
        fig.add_trace(
            go.Scatter(
                x=[i for i in range(len(nodes))],
                y=[node["complexity"] for node in nodes],
                mode='markers',
                marker=dict(
                    size=[max(node["size"]/100, 10) for node in nodes],
                    color=[node["color"] for node in nodes],
                    opacity=0.8,
                    line=dict(width=1, color='black')
                ),
                text=[node["label"] for node in nodes],
                hovertext=hover_text,
                hoverinfo='text',
                name="Classes"
            ),
            row=1, col=1
        )
        
        # 2. Category bar chart
        category_lines = defaultdict(int)
        for class_info in result.dependencies.values():
            category_lines[class_info.category] += class_info.line_count
        
        fig.add_trace(
            go.Bar(
                x=list(category_lines.keys()),
                y=list(category_lines.values()),
                marker_color=[self._get_category_color(cat) for cat in category_lines.keys()],
                name="Lines by Category"
            ),
            row=1, col=2
        )
        
        # 3. Complexity pie chart
        complexity_dist = result.analysis_summary["complexity_distribution"]
        fig.add_trace(
            go.Pie(
                labels=list(complexity_dist.keys()),
                values=list(complexity_dist.values()),
                name="Complexity"
            ),
            row=2, col=1
        )
        
        # 4. Top classes horizontal bar
        largest = result.analysis_summary["largest_classes"][:10]
        fig.add_trace(
            go.Bar(
                x=[info.line_count for info in largest],
                y=[info.name for info in largest],
                orientation='h',
                marker_color=[self._get_category_color(info.category) for info in largest],
                name="Largest Classes"
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title_text=f"Dependency Analysis Dashboard: {result.root_class.name}",
            title_x=0.5,
            height=800,
            showlegend=False
        )
        
        # Save as HTML
        pyo.plot(fig, filename=output_path, auto_open=False)
        LOG.info(f"Interactive Plotly graph saved to: {output_path}")
    
    def generate_html_report(self, result: DependencyGraph, output_path: str):
        """Generate comprehensive HTML report."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Dependency Analysis: {result.root_class.name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #3498db; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .category {{ margin: 20px 0; }}
        .class-list {{ display: flex; flex-wrap: wrap; gap: 10px; }}
        .class-item {{ background: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; 
                      border-radius: 5px; min-width: 200px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .complexity-high {{ color: #e74c3c; font-weight: bold; }}
        .complexity-medium {{ color: #f39c12; }}
        .complexity-low {{ color: #27ae60; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Dependency Analysis Report</h1>
        <h2>{result.root_class.name}</h2>
    </div>
    
    <div class="summary">
        <h3>Summary Statistics</h3>
        <p><strong>Total Classes Analyzed:</strong> {result.analysis_summary['total_classes']}</p>
        <p><strong>Total Lines of Code:</strong> {result.total_lines:,}</p>
        <p><strong>Average Lines per Class:</strong> {result.analysis_summary['average_lines_per_class']:.1f}</p>
        <p><strong>Categories:</strong> {result.analysis_summary['categories_count']}</p>
    </div>
    
    <h3>Analysis by Category</h3>
"""
        
        for category, classes in result.categories.items():
            total_lines = sum(result.dependencies[cls].line_count for cls in classes)
            html_content += f"""
    <div class="category">
        <h4>{category} ({len(classes)} classes, {total_lines:,} lines)</h4>
        <div class="class-list">
"""
            for class_name in classes:
                class_info = result.dependencies[class_name]
                complexity_class = "complexity-high" if class_info.complexity_score > 5 else \
                                 "complexity-medium" if class_info.complexity_score > 2 else "complexity-low"
                
                html_content += f"""
            <div class="class-item">
                <strong>{class_name}</strong><br>
                Lines: {class_info.line_count:,}<br>
                Complexity: <span class="{complexity_class}">{class_info.complexity_score}</span><br>
                Dependencies: {len(class_info.dependencies)}
            </div>
"""
            html_content += """
        </div>
    </div>
"""
        
        # Detailed table
        html_content += """
    <h3>Detailed Class Information</h3>
    <table>
        <tr>
            <th>Class Name</th>
            <th>Category</th>
            <th>Lines</th>
            <th>Complexity</th>
            <th>Dependencies</th>
            <th>File Path</th>
        </tr>
"""
        
        for class_name, class_info in sorted(result.dependencies.items(), 
                                           key=lambda x: x[1].line_count, reverse=True):
            complexity_class = "complexity-high" if class_info.complexity_score > 5 else \
                             "complexity-medium" if class_info.complexity_score > 2 else "complexity-low"
            
            html_content += f"""
        <tr>
            <td><strong>{class_name}</strong></td>
            <td>{class_info.category}</td>
            <td>{class_info.line_count:,}</td>
            <td><span class="{complexity_class}">{class_info.complexity_score}</span></td>
            <td>{len(class_info.dependencies)}</td>
            <td><small>{class_info.file_path}</small></td>
        </tr>
"""
        
        html_content += """
    </table>
    
    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666;">
        <p>Generated by dependency_analyzer.py</p>
    </footer>
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        LOG.info(f"HTML report saved to: {output_path}")
    
    def export_json(self, result: DependencyGraph, output_path: str):
        """Export analysis results to JSON."""
        # Convert dataclasses to dicts for JSON serialization
        json_data = {
            "root_class": asdict(result.root_class),
            "dependencies": {name: asdict(info) for name, info in result.dependencies.items()},
            "total_lines": result.total_lines,
            "categories": result.categories,
            "analysis_summary": result.analysis_summary,
            "graph_data": result.graph_data
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        LOG.info(f"JSON export saved to: {output_path}")
    
    def export_csv(self, result: DependencyGraph, output_path: str):
        """Export class information to CSV."""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Class Name', 'Category', 'Lines', 'Complexity Score', 
                           'Dependencies Count', 'Package', 'File Path'])
            
            for class_name, class_info in result.dependencies.items():
                writer.writerow([
                    class_name,
                    class_info.category, 
                    class_info.line_count,
                    class_info.complexity_score,
                    len(class_info.dependencies),
                    class_info.package,
                    class_info.file_path
                ])
        
        LOG.info(f"CSV export saved to: {output_path}")
    
    def export_markdown(self, result: DependencyGraph, output_path: str):
        """Export analysis results to Markdown."""
        md_content = f"""# Dependency Analysis Report: {result.root_class.name}

## Summary Statistics

- **Total Classes Analyzed:** {result.analysis_summary['total_classes']}
- **Total Lines of Code:** {result.total_lines:,}
- **Average Lines per Class:** {result.analysis_summary['average_lines_per_class']:.1f}
- **Categories:** {result.analysis_summary['categories_count']}

## Analysis by Category

"""
        
        for category, classes in result.categories.items():
            total_lines = sum(result.dependencies[cls].line_count for cls in classes)
            md_content += f"### {category} ({len(classes)} classes, {total_lines:,} lines)\n\n"
            
            for class_name in sorted(classes):
                class_info = result.dependencies[class_name]
                md_content += f"- **{class_name}**: {class_info.line_count:,} lines, "
                md_content += f"complexity: {class_info.complexity_score}, "
                md_content += f"dependencies: {len(class_info.dependencies)}\n"
            md_content += "\n"
        
        md_content += """## Detailed Class Information

| Class Name | Category | Lines | Complexity | Dependencies | File Path |
|------------|----------|-------|------------|--------------|-----------|
"""
        
        for class_name, class_info in sorted(result.dependencies.items(), 
                                           key=lambda x: x[1].line_count, reverse=True):
            md_content += f"| {class_name} | {class_info.category} | {class_info.line_count:,} | "
            md_content += f"{class_info.complexity_score} | {len(class_info.dependencies)} | "
            md_content += f"{class_info.file_path} |\n"
        
        md_content += f"\n---\n*Generated by dependency_analyzer.py*\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        LOG.info(f"Markdown report saved to: {output_path}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Java class dependency analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  # Basic analysis
  dependency_analyzer.py ComplexAnalyzerV7_1_5

  # Full analysis with all outputs
  dependency_analyzer.py ComplexAnalyzerV7_1_5 --graph --html-report --export-all

  # Quick analysis with specific depth
  dependency_analyzer.py DataProcessorControllerV2 --depth 2 --csv

  # Generate only visualization
  dependency_analyzer.py MyClass --matplotlib-graph output.png
"""
    )
    
    parser.add_argument('class_name', help='Java class name to analyze')
    parser.add_argument('--project-root', default='.', 
                       help='Project root directory (default: current directory)')
    parser.add_argument('--depth', type=int, default=3, 
                       help='Maximum dependency analysis depth (default: 3)')
    
    # Output options
    parser.add_argument('--output-dir', default='dependency_analysis_output',
                       help='Output directory for generated files')
    parser.add_argument('--prefix', help='Prefix for output files')
    
    # Visualization options
    parser.add_argument('--graph', action='store_true', help='Generate dependency graph')
    parser.add_argument('--matplotlib-graph', help='Generate matplotlib graph (specify filename)')
    parser.add_argument('--plotly-graph', help='Generate interactive Plotly graph (specify filename)')
    
    # Report options
    parser.add_argument('--html-report', action='store_true', help='Generate HTML report')
    parser.add_argument('--markdown', action='store_true', help='Generate Markdown report')
    
    # Export options
    parser.add_argument('--json', action='store_true', help='Export to JSON')
    parser.add_argument('--csv', action='store_true', help='Export to CSV')
    parser.add_argument('--export-all', action='store_true', 
                       help='Export in all formats (JSON, CSV, HTML, Markdown)')
    
    # Analysis options
    parser.add_argument('--categories', action='store_true', 
                       help='Show detailed category breakdown')
    parser.add_argument('--complexity', action='store_true',
                       help='Show complexity analysis')
    parser.add_argument('--summary-only', action='store_true',
                       help='Show only summary statistics')
    
    # Utility options
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--list-categories', action='store_true',
                       help='List available categories and exit')
    
    args = parser.parse_args()
    
    # Set up logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')
    
    if args.list_categories:
        analyzer = JavaDependencyAnalyzer()
        print("Available Categories:")
        for category, patterns in analyzer.category_patterns.items():
            print(f"  {category}: {', '.join(patterns)}")
        return
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Set up file prefix
    prefix = args.prefix or args.class_name
    
    try:
        # Initialize analyzer
        analyzer = JavaDependencyAnalyzer(args.project_root)
        
        print(f"Analyzing dependencies for: {args.class_name}")
        print(f"Maximum depth: {args.depth}")
        print(f"Project root: {args.project_root}")
        print()
        
        # Perform analysis
        result = analyzer.analyze_dependencies_recursive(args.class_name, args.depth)
        
        # Display summary
        if not args.summary_only:
            print("=" * 80)
            print(f"DEPENDENCY ANALYSIS RESULTS: {result.root_class.name}")
            print("=" * 80)
            
            summary = result.analysis_summary
            print(f"Total Classes: {summary['total_classes']}")
            print(f"Total Lines: {summary['total_lines']:,}")
            print(f"Average Lines per Class: {summary['average_lines_per_class']:.1f}")
            print(f"Categories: {summary['categories_count']}")
            print()
            
            if args.categories:
                print("BREAKDOWN BY CATEGORY:")
                print("-" * 40)
                for category, classes in result.categories.items():
                    total_lines = sum(result.dependencies[cls].line_count for cls in classes)
                    print(f"{category}: {len(classes)} classes, {total_lines:,} lines")
                    if args.verbose:
                        for cls in sorted(classes)[:5]:  # Show top 5
                            info = result.dependencies[cls]
                            print(f"  - {cls}: {info.line_count:,} lines")
                        if len(classes) > 5:
                            print(f"  ... and {len(classes) - 5} more")
                    print()
            
            if args.complexity:
                print("COMPLEXITY DISTRIBUTION:")
                print("-" * 40)
                complexity_dist = summary['complexity_distribution']
                for level, count in complexity_dist.items():
                    print(f"{level}: {count} classes")
                print()
                
                print("TOP 5 MOST COMPLEX CLASSES:")
                complex_classes = sorted(result.dependencies.values(), 
                                       key=lambda x: x.complexity_score, reverse=True)[:5]
                for cls in complex_classes:
                    print(f"  {cls.name}: {cls.complexity_score} (category: {cls.category})")
                print()
        
        # Generate outputs
        if args.export_all:
            args.json = args.csv = args.html_report = args.markdown = True
            args.graph = True
        
        if args.json:
            analyzer.export_json(result, output_dir / f"{prefix}_analysis.json")
        
        if args.csv:
            analyzer.export_csv(result, output_dir / f"{prefix}_classes.csv")
        
        if args.html_report:
            analyzer.generate_html_report(result, output_dir / f"{prefix}_report.html")
        
        if args.markdown:
            analyzer.export_markdown(result, output_dir / f"{prefix}_analysis.md")
        
        if args.matplotlib_graph:
            analyzer.generate_matplotlib_graph(result, args.matplotlib_graph)
        elif args.graph and HAS_MATPLOTLIB:
            analyzer.generate_matplotlib_graph(result, output_dir / f"{prefix}_graph.png")
        
        if args.plotly_graph:
            analyzer.generate_plotly_graph(result, args.plotly_graph)
        elif args.graph and HAS_PLOTLY and not args.matplotlib_graph:
            analyzer.generate_plotly_graph(result, output_dir / f"{prefix}_interactive.html")
        
        print(f"\nAnalysis complete! Output saved to: {output_dir}")
        
    except Exception as e:
        LOG.error(f"Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()