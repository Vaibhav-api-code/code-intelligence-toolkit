#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
dependency_analyzer_fixed.py - Fixed version with better Java class filtering

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

# Standard Java packages to exclude
STANDARD_PACKAGES = {
    'java.', 'javax.', 'sun.', 'com.sun.', 'jdk.', 'org.w3c.', 'org.xml.',
    'org.omg.', 'org.ietf.', 'org.jcp.', 'netscape.', 'org.apache.commons.',
    'org.slf4j.', 'org.apache.log4j.', 'org.junit.', 'org.mockito.',
    'org.hamcrest.', 'org.jfree.', 'org.json.', 'com.google.common.',
    'com.fasterxml.', 'org.springframework.', 'android.', 'androidx.'
}

# Standard Java types to exclude (expanded list)
STANDARD_TYPES = {
    # Primitives and wrappers
    'String', 'Integer', 'Double', 'Boolean', 'Long', 'Float', 'Short', 'Byte', 
    'Character', 'Object', 'Number', 'Void',
    
    # Collections
    'List', 'ArrayList', 'LinkedList', 'Set', 'HashSet', 'TreeSet', 'Map', 
    'HashMap', 'TreeMap', 'LinkedHashMap', 'Queue', 'Deque', 'Stack', 'Vector',
    'Collection', 'Iterator', 'Iterable', 'Collections', 'Arrays',
    
    # Common interfaces
    'Runnable', 'Callable', 'Comparable', 'Comparator', 'Serializable', 
    'Cloneable', 'AutoCloseable', 'Closeable',
    
    # Common exceptions
    'Exception', 'RuntimeException', 'IllegalArgumentException', 
    'IllegalStateException', 'NullPointerException', 'IOException',
    'IndexOutOfBoundsException', 'UnsupportedOperationException',
    
    # Threading
    'Thread', 'ThreadLocal', 'ThreadPoolExecutor', 'Executor', 'ExecutorService',
    'Future', 'CompletableFuture', 'Lock', 'ReentrantLock', 'Semaphore',
    'CountDownLatch', 'CyclicBarrier', 'AtomicInteger', 'AtomicLong', 
    'AtomicBoolean', 'AtomicReference',
    
    # IO
    'File', 'Path', 'Files', 'InputStream', 'OutputStream', 'Reader', 'Writer',
    'BufferedReader', 'BufferedWriter', 'PrintWriter', 'PrintStream',
    'FileInputStream', 'FileOutputStream', 'FileReader', 'FileWriter',
    
    # Time
    'Date', 'Calendar', 'LocalDate', 'LocalTime', 'LocalDateTime', 'Instant',
    'Duration', 'Period', 'ZonedDateTime', 'TimeZone', 'SimpleDateFormat',
    'DateFormat', 'Timer', 'TimerTask',
    
    # Reflection & Annotations
    'Class', 'Method', 'Field', 'Constructor', 'Annotation', 'Override',
    'Deprecated', 'SuppressWarnings', 'FunctionalInterface', 'SafeVarargs',
    
    # Swing/AWT
    'JFrame', 'JPanel', 'JButton', 'JLabel', 'JTextField', 'JTextArea',
    'JScrollPane', 'JTable', 'JList', 'JComboBox', 'JCheckBox', 'JRadioButton',
    'JSpinner', 'JSlider', 'JProgressBar', 'JFileChooser', 'JDialog',
    'JTabbedPane', 'JMenuBar', 'JMenu', 'JMenuItem', 'JSeparator',
    'Component', 'Container', 'Window', 'Frame', 'Dialog', 'Panel',
    'Color', 'Font', 'Graphics', 'Graphics2D', 'Image', 'Icon',
    'BorderLayout', 'FlowLayout', 'GridLayout', 'BoxLayout', 'GridBagLayout',
    'GridBagConstraints', 'Insets', 'Dimension', 'Point', 'Rectangle',
    
    # Logging
    'Logger', 'LogManager', 'Level', 'Handler', 'Formatter',
    
    # Math
    'Math', 'BigDecimal', 'BigInteger', 'Random',
    
    # Text
    'StringBuilder', 'StringBuffer', 'Pattern', 'Matcher', 'Formatter',
    'DecimalFormat', 'NumberFormat',
    
    # Network
    'URL', 'URI', 'URLConnection', 'HttpURLConnection', 'Socket', 'ServerSocket',
    
    # Misc
    'System', 'Runtime', 'Process', 'ProcessBuilder', 'Properties', 'Preferences',
    'Scanner', 'UUID', 'Optional', 'Base64', 'Objects', 'Enum',
    
    # JFreeChart (common in the project)
    'JFreeChart', 'ChartPanel', 'XYPlot', 'TimeSeries', 'TimeSeriesCollection',
    'XYSeries', 'XYSeriesCollection', 'NumberAxis', 'DateAxis', 'ValueMarker',
    'XYLineAndShapeRenderer', 'XYBarRenderer', 'BasicStroke', 'Millisecond',
    'DefaultTableModel', 'SpinnerNumberModel',
    
    # Common generic words that aren't classes
    'return', 'param', 'link', 'code', 'deprecated', 'author', 'version',
    'since', 'throws', 'see', 'value', 'serial', 'serialData',
    'implSpec', 'implNote', 'apiNote', 'literal', 'index', 'summary',
    'hidden', 'provides', 'uses', 'category', 'todo', 'factory', 'title',
    'start', 'end', 'this', 'super', 'true', 'false', 'null', 'void',
    'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default',
    'break', 'continue', 'try', 'catch', 'finally', 'throw', 'throws',
    'new', 'class', 'interface', 'enum', 'extends', 'implements',
    'package', 'import', 'static', 'final', 'abstract', 'public',
    'private', 'protected', 'synchronized', 'volatile', 'transient',
    'native', 'strictfp', 'const', 'goto', 'instanceof', 'assert',
    'boolean', 'byte', 'char', 'short', 'int', 'long', 'float', 'double',
    'the', 'a', 'an', 'and', 'or', 'not', 'is', 'are', 'was', 'were',
    'has', 'have', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'can', 'settings', 'time', 'data',
    'info', 'error', 'warning', 'debug', 'trace', 'config', 'options',
    'result', 'results', 'item', 'items', 'element', 'elements', 'node',
    'nodes', 'key', 'keys', 'value', 'values', 'entry', 'entries',
    'source', 'target', 'destination', 'origin', 'input', 'output'
}

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
    """Comprehensive Java class dependency analyzer with fixed filtering."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.class_cache: Dict[str, ClassInfo] = {}
        self.search_paths = [
            "src/main/java",
            "src/test/java",
            "java-intelligence-analysis-toolkit",
            "src",  # Add generic src
            "."     # Add root
        ]
        
        # Project packages (discovered dynamically)
        self.project_packages = self._discover_project_packages()
        
        # Category patterns for classification
        self.category_patterns = {
            "UI": [r"UI\w*", r"\w*Frame\w*", r"\w*Dialog\w*", r"\w*Panel\w*", r"\w*Monitor\w*", r"\w*Chart\w*"],
            "Processing": [r"\w*Data\w*", r"\w*Process\w*", r"\w*Position\w*", r"\w*Portfolio\w*", r"\w*Sender\w*"],
            "Analysis": [r"\w*Analyzer\w*", r"\w*Calculator\w*", r"\w*Detector\w*", r"\w*Tracker\w*"],
            "Data": [r"\w*Data\w*", r"\w*Store\w*", r"\w*Cache\w*", r"\w*Buffer\w*", r"\w*Distributor\w*"],
            "Analyzer": [r"\w*Indicator\w*", r"\w*Analysis\w*", r"\w*Moving\w*", r"\w*Average\w*", r"\w*Complex\w*"],
            "Utility": [r"\w*Util\w*", r"\w*Helper\w*", r"\w*Manager\w*", r"\w*Service\w*", r"\w*Controller\w*"],
            "Test": [r"\w*Test\w*", r"Test\w*"]
        }
    
    def _discover_project_packages(self) -> Set[str]:
        """Discover project-specific packages by scanning the codebase."""
        packages = set()
        
        # Common project prefixes
        common_prefixes = ['com.example', 'external.api', 'com.example', 'org.project']
        packages.update(common_prefixes)
        
        # Scan for actual packages
        for search_path in self.search_paths:
            full_path = self.project_root / search_path
            if full_path.exists():
                for root, dirs, files in os.walk(full_path):
                    for file in files:
                        if file.endswith('.java'):
                            # Extract package from file
                            try:
                                java_file = Path(root) / file
                                with open(java_file, 'r', encoding='utf-8') as f:
                                    for line in f:
                                        if line.strip().startswith('package '):
                                            pkg = line.strip()[8:].rstrip(';').strip()
                                            if pkg and not any(pkg.startswith(std) for std in STANDARD_PACKAGES):
                                                packages.add(pkg)
                                            break
                            except:
                                pass
        
        return packages
    
    def _is_standard_import(self, import_str: str) -> bool:
        """Check if an import is from standard Java libraries."""
        return any(import_str.startswith(pkg) for pkg in STANDARD_PACKAGES)
    
    def _is_project_import(self, import_str: str) -> bool:
        """Check if an import belongs to the project."""
        return any(import_str.startswith(pkg) for pkg in self.project_packages)
    
    def find_java_file(self, class_name: str) -> Optional[Path]:
        """Find the Java file for a given class name."""
        # First try direct path
        for search_path in self.search_paths:
            full_path = self.project_root / search_path
            if full_path.exists():
                # Try to find by walking through directory structure
                for root, dirs, files in os.walk(full_path):
                    for file in files:
                        if file == f"{class_name}.java":
                            return Path(root) / file
        
        # Try common patterns for demo classes
        if class_name.startswith("Demo") or class_name.startswith("Example"):
            indicators_path = self.project_root / "src/main/java/com/example/package/indicators"
            if indicators_path.exists():
                test_file = indicators_path / f"{class_name}.java"
                if test_file.exists():
                    return test_file
        
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
            all_imports = re.findall(import_pattern, content)
            
            # Filter imports - only keep project imports
            imports = [imp for imp in all_imports 
                      if self._is_project_import(imp) and not self._is_standard_import(imp)]
            
            # Extract class references (enhanced patterns)
            class_patterns = [
                r'new\s+(\w+)(?:<[^>]+>)?\s*\(',  # Constructor with generics
                r'(\w+)\.(?:getInstance|create|valueOf|getOrCreateInstance)\s*\(',  # Factory methods
                r'@(\w+)\s*(?:\([^)]*\))?',  # Annotations with optional params
                r'extends\s+(\w+)(?:<[^>]+>)?',  # Extends with generics
                r'implements\s+(\w+)(?:<[^>]+>)?',  # Implements with generics
                r'<(\w+)(?:<[^>]+>)?[,>]',  # Generic type parameters
                r'(\w+)(?:<[^>]+>)?\s+\w+\s*[=;]',  # Variable declarations
                r'catch\s*\(\s*(\w+)',  # Exception catches
                r'throws\s+(\w+)',  # Thrown exceptions
                r'instanceof\s+(\w+)',  # Instance checks
                r'(\w+)\.class\b',  # Class literals
            ]
            
            potential_deps = set()
            for pattern in class_patterns:
                potential_deps.update(re.findall(pattern, content))
            
            # Extract class names from imports too
            for imp in imports:
                parts = imp.split('.')
                if parts:
                    class_name = parts[-1]
                    if class_name and class_name not in STANDARD_TYPES:
                        potential_deps.add(class_name)
            
            # Verify dependencies - only keep those we can find Java files for
            for dep in potential_deps:
                if (dep not in STANDARD_TYPES and 
                    len(dep) > 2 and 
                    dep[0].isupper() and  # Likely a class name
                    not dep.isupper()):   # Not a constant
                    # Try to find the Java file for this dependency
                    if self.find_java_file(dep):
                        dependencies.append(dep)
            
            # Remove duplicates
            dependencies = list(set(dependencies))
            
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
            "Processing": 2.0,  # Processing logic is inherently complex
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
            LOG.info(f"Could not find file for class: {class_name}")
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
                for line in f:
                    if line.strip().startswith('package '):
                        package = line.strip()[8:].rstrip(';').strip()
                        break
        except Exception:
            pass
        
        # Extract dependencies
        imports, dependencies = self.extract_imports_and_dependencies(file_path)
        
        # Create class info
        class_info = ClassInfo(
            name=class_name,
            file_path=str(file_path.relative_to(self.project_root)),
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
        
        # Limit total classes to prevent runaway analysis
        max_classes = 100
        
        while to_analyze and current_depth < max_depth and len(dependencies) < max_classes:
            current = to_analyze.pop(0)
            if current in analyzed or current in STANDARD_TYPES:
                continue
            
            dep_info = self.analyze_class(current)
            if dep_info:
                dependencies[current] = dep_info
                categories[dep_info.category].append(current)
                analyzed.add(current)
                
                # Add this class's dependencies to analyze
                for subdep in dep_info.dependencies:
                    if subdep not in analyzed and subdep not in STANDARD_TYPES:
                        to_analyze.append(subdep)
            
            # Prevent infinite expansion
            if len(to_analyze) > 50:
                LOG.info(f"Limiting dependency expansion, {len(to_analyze)} items in queue")
                to_analyze = to_analyze[:20]
        
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
        node_colors = [self._get_category_color(result.dependencies[node].category) for node in G.nodes()]
        node_sizes = [max(result.dependencies[node].line_count / 10, 100) for node in G.nodes()]
        
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
        <p>Generated by dependency_analyzer_fixed.py</p>
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
        
        md_content += f"\n---\n*Generated by dependency_analyzer_fixed.py*\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        LOG.info(f"Markdown report saved to: {output_path}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fixed Java class dependency analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  # Basic analysis
  dependency_analyzer_fixed.py ComplexAnalyzerV7_1_5

  # Full analysis with all outputs
  dependency_analyzer_fixed.py ComplexAnalyzerV7_1_5 --graph --html-report --export-all

  # Quick analysis with specific depth
  dependency_analyzer_fixed.py DataProcessorControllerV2 --depth 2 --csv

  # Generate only visualization
  dependency_analyzer_fixed.py MyClass --matplotlib-graph output.png
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