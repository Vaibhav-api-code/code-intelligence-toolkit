#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Enhanced Java refactoring with full scope awareness using Eclipse JDT or Spoon.

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-07
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

import argparse
import subprocess
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import tempfile
import shutil
import os


class SpoonRefactorer:
    """
    Spoon-based refactoring - modern and easy to integrate.
    Spoon provides full semantic analysis and scope awareness.
    """
    
    def __init__(self):
        self.spoon_jar = self._find_spoon_jar()
    
    def _find_spoon_jar(self) -> Optional[str]:
        """Find or download Spoon JAR."""
        # Check common locations
        jar_locations = [
            "./lib/spoon-core-10.4.0-jar-with-dependencies.jar",
            "./spoon-core.jar",
            "~/spoon/spoon-core.jar"
        ]
        
        for loc in jar_locations:
            path = Path(loc).expanduser()
            if path.exists():
                return str(path)
        
        # Could download automatically here
        return None
    
    def _create_spoon_processor(self, refactoring_type: str) -> str:
        """Create a Spoon processor for the refactoring."""
        if refactoring_type == "rename_variable":
            return '''
import spoon.processing.AbstractProcessor;
import spoon.reflect.code.CtLocalVariable;
import spoon.reflect.code.CtVariableRead;
import spoon.reflect.code.CtVariableWrite;
import spoon.reflect.code.CtFieldRead;
import spoon.reflect.code.CtFieldWrite;
import spoon.reflect.declaration.*;
import spoon.reflect.reference.CtVariableReference;
import spoon.reflect.visitor.filter.TypeFilter;

public class RenameVariableProcessor extends AbstractProcessor<CtVariable<?>> {
    private String targetClass;
    private String targetMethod;
    private String oldName;
    private String newName;
    private String variableType;
    
    public RenameVariableProcessor(String targetClass, String targetMethod, 
                                  String oldName, String newName, String variableType) {
        this.targetClass = targetClass;
        this.targetMethod = targetMethod;
        this.oldName = oldName;
        this.newName = newName;
        this.variableType = variableType;
    }
    
    @Override
    public void process(CtVariable<?> variable) {
        // Check if we're in the right scope
        if (!variable.getSimpleName().equals(oldName)) {
            return;
        }
        
        // Check class scope if specified
        if (targetClass != null) {
            CtClass<?> containingClass = variable.getParent(CtClass.class);
            if (containingClass == null || !containingClass.getSimpleName().equals(targetClass)) {
                return;
            }
        }
        
        // Check method scope if specified
        if (targetMethod != null && variable instanceof CtLocalVariable) {
            CtMethod<?> containingMethod = variable.getParent(CtMethod.class);
            if (containingMethod == null || !containingMethod.getSimpleName().equals(targetMethod)) {
                return;
            }
        }
        
        // Check variable type
        if ("local".equals(variableType) && !(variable instanceof CtLocalVariable)) {
            return;
        }
        if ("field".equals(variableType) && !(variable instanceof CtField)) {
            return;
        }
        if ("parameter".equals(variableType) && !(variable instanceof CtParameter)) {
            return;
        }
        
        // Rename the variable
        variable.setSimpleName(newName);
        
        // Also update all references
        if (variable instanceof CtField) {
            CtField<?> field = (CtField<?>) variable;
            // Update field references throughout the class
            CtClass<?> clazz = field.getParent(CtClass.class);
            if (clazz != null) {
                clazz.getElements(new TypeFilter<CtVariableReference<?>>(CtVariableReference.class))
                    .stream()
                    .filter(ref -> ref.getSimpleName().equals(oldName))
                    .filter(ref -> ref.getDeclaration() == field)
                    .forEach(ref -> ref.setSimpleName(newName));
            }
        }
    }
}
'''
    
    def rename_variable(self, file_path: Path, old_name: str, new_name: str,
                       scope_class: Optional[str] = None, 
                       scope_method: Optional[str] = None,
                       variable_type: str = "all") -> Dict:
        """Rename variable with full scope awareness using Spoon."""
        
        if not self.spoon_jar:
            return {
                'success': False,
                'error': 'Spoon JAR not found. Install with: ./install_java_refactoring_libs.sh'
            }
        
        # Create temporary directory for processor
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write processor
            processor_file = Path(temp_dir) / "RenameVariableProcessor.java"
            processor_file.write_text(self._create_spoon_processor("rename_variable"))
            
            # Create Spoon launcher script
            launcher_script = f'''
import spoon.Launcher;
import spoon.reflect.CtModel;
import spoon.reflect.declaration.CtClass;
import java.io.File;

public class SpoonRefactor {{
    public static void main(String[] args) {{
        Launcher launcher = new Launcher();
        launcher.addInputResource("{file_path}");
        launcher.setSourceOutputDirectory("{temp_dir}/output");
        
        // Build model
        CtModel model = launcher.buildModel();
        
        // Create and add processor
        RenameVariableProcessor processor = new RenameVariableProcessor(
            {f'"{scope_class}"' if scope_class else 'null'},
            {f'"{scope_method}"' if scope_method else 'null'},
            "{old_name}",
            "{new_name}",
            "{variable_type}"
        );
        
        launcher.addProcessor(processor);
        
        // Process
        launcher.process();
        
        // Pretty print
        launcher.prettyprint();
    }}
}}
'''
            
            launcher_file = Path(temp_dir) / "SpoonRefactor.java"
            launcher_file.write_text(launcher_script)
            
            # Compile and run
            try:
                # Compile processor
                subprocess.run([
                    "javac", "-cp", self.spoon_jar,
                    str(processor_file)
                ], check=True, cwd=temp_dir)
                
                # Compile launcher
                subprocess.run([
                    "javac", "-cp", f"{self.spoon_jar}:.",
                    str(launcher_file)
                ], check=True, cwd=temp_dir)
                
                # Run refactoring
                subprocess.run([
                    "java", "-cp", f"{self.spoon_jar}:.",
                    "SpoonRefactor"
                ], check=True, cwd=temp_dir)
                
                # Read result
                output_file = Path(temp_dir) / "output" / file_path.name
                if output_file.exists():
                    new_content = output_file.read_text()
                    
                    return {
                        'success': True,
                        'new_content': new_content,
                        'changes': self._count_changes(file_path.read_text(), new_content, old_name, new_name)
                    }
                
            except subprocess.CalledProcessError as e:
                return {
                    'success': False,
                    'error': f'Spoon processing failed: {e}'
                }
        
        return {
            'success': False,
            'error': 'Unknown error'
        }
    
    def _count_changes(self, old_content: str, new_content: str, old_name: str, new_name: str) -> int:
        """Count the number of changes made."""
        old_count = old_content.count(old_name)
        new_count = new_content.count(new_name)
        return new_count


class JavaParserSymbolSolverRefactorer:
    """
    JavaParser with Symbol Solver - lightweight but powerful.
    Provides type resolution and scope analysis.
    """
    
    def __init__(self):
        self.gradle_available = shutil.which('gradle') is not None
    
    def _create_refactoring_project(self, file_path: Path, old_name: str, new_name: str,
                                   scope_info: Dict) -> str:
        """Create a temporary Gradle project for refactoring."""
        
        build_gradle = '''
plugins {
    id 'java'
    id 'application'
}

repositories {
    mavenCentral()
}

dependencies {
    implementation 'com.github.javaparser:javaparser-symbol-solver-core:3.25.5'
}

application {
    mainClass = 'RefactorMain'
}
'''
        
        refactor_main = f'''
import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.VariableDeclarator;
import com.github.javaparser.ast.expr.NameExpr;
import com.github.javaparser.ast.expr.FieldAccessExpr;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.resolution.declarations.ResolvedValueDeclaration;
import com.github.javaparser.symbolsolver.JavaSymbolSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.CombinedTypeSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.ReflectionTypeSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.JavaParserTypeSolver;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Paths;

public class RefactorMain {{
    public static void main(String[] args) throws Exception {{
        // Set up symbol solver
        CombinedTypeSolver combinedSolver = new CombinedTypeSolver();
        combinedSolver.add(new ReflectionTypeSolver());
        combinedSolver.add(new JavaParserTypeSolver(new File(".")));
        
        JavaSymbolSolver symbolSolver = new JavaSymbolSolver(combinedSolver);
        StaticJavaParser.getConfiguration().setSymbolResolver(symbolSolver);
        
        // Parse file
        CompilationUnit cu = StaticJavaParser.parse(new File("{file_path}"));
        
        // Find target scope
        String targetClass = {f'"{scope_info.get("class")}"' if scope_info.get("class") else 'null'};
        String targetMethod = {f'"{scope_info.get("method")}"' if scope_info.get("method") else 'null'};
        
        // Rename variables with scope awareness
        cu.findAll(NameExpr.class).forEach(name -> {{
            if (name.getNameAsString().equals("{old_name}")) {{
                try {{
                    // Check if this is the variable we want to rename
                    ResolvedValueDeclaration resolved = name.resolve();
                    
                    // Check scope
                    if (targetClass != null) {{
                        ClassOrInterfaceDeclaration containingClass = 
                            name.findAncestor(ClassOrInterfaceDeclaration.class).orElse(null);
                        if (containingClass == null || 
                            !containingClass.getNameAsString().equals(targetClass)) {{
                            return;
                        }}
                    }}
                    
                    if (targetMethod != null) {{
                        MethodDeclaration containingMethod = 
                            name.findAncestor(MethodDeclaration.class).orElse(null);
                        if (containingMethod == null || 
                            !containingMethod.getNameAsString().equals(targetMethod)) {{
                            return;
                        }}
                    }}
                    
                    // Rename
                    name.setName("{new_name}");
                }} catch (Exception e) {{
                    // Not resolvable, skip
                }}
            }}
        }});
        
        // Also handle variable declarations
        cu.findAll(VariableDeclarator.class).forEach(var -> {{
            if (var.getNameAsString().equals("{old_name}")) {{
                // Apply same scope checks
                if (targetClass != null) {{
                    ClassOrInterfaceDeclaration containingClass = 
                        var.findAncestor(ClassOrInterfaceDeclaration.class).orElse(null);
                    if (containingClass == null || 
                        !containingClass.getNameAsString().equals(targetClass)) {{
                        return;
                    }}
                }}
                
                if (targetMethod != null) {{
                    MethodDeclaration containingMethod = 
                        var.findAncestor(MethodDeclaration.class).orElse(null);
                    if (containingMethod == null || 
                        !containingMethod.getNameAsString().equals(targetMethod)) {{
                        return;
                    }}
                }}
                
                var.setName("{new_name}");
            }}
        }});
        
        // Write result
        Files.write(Paths.get("output.java"), cu.toString().getBytes());
    }}
}}
'''
        
        return build_gradle, refactor_main
    
    def rename_variable(self, file_path: Path, old_name: str, new_name: str,
                       scope_info: Dict) -> Dict:
        """Rename variable using JavaParser with Symbol Solver."""
        
        if not self.gradle_available:
            return {
                'success': False,
                'error': 'Gradle not found. Install gradle to use JavaParser refactoring.'
            }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create build.gradle
            build_gradle, refactor_main = self._create_refactoring_project(
                file_path, old_name, new_name, scope_info
            )
            
            (temp_path / "build.gradle").write_text(build_gradle)
            
            # Create source directory
            src_dir = temp_path / "src" / "main" / "java"
            src_dir.mkdir(parents=True)
            (src_dir / "RefactorMain.java").write_text(refactor_main)
            
            # Copy target file
            shutil.copy(file_path, temp_path / file_path.name)
            
            try:
                # Run gradle
                subprocess.run([
                    "gradle", "run", "-q"
                ], check=True, cwd=temp_path, capture_output=True)
                
                # Read result
                output_file = temp_path / "output.java"
                if output_file.exists():
                    new_content = output_file.read_text()
                    
                    return {
                        'success': True,
                        'new_content': new_content,
                        'changes': new_content.count(new_name) - file_path.read_text().count(new_name)
                    }
                    
            except subprocess.CalledProcessError as e:
                return {
                    'success': False,
                    'error': f'JavaParser processing failed: {e.stderr.decode()}'
                }
        
        return {
            'success': False,
            'error': 'Unknown error'
        }


class EclipseJDTRefactorer:
    """
    Eclipse JDT - the gold standard for Java refactoring.
    Used by Eclipse IDE, provides the most comprehensive refactoring support.
    """
    
    def __init__(self):
        self.eclipse_home = self._find_eclipse()
    
    def _find_eclipse(self) -> Optional[str]:
        """Find Eclipse installation or JDT standalone."""
        # Common Eclipse locations
        locations = [
            "/Applications/Eclipse.app/Contents/Eclipse",
            "~/eclipse",
            "/opt/eclipse",
            "C:\\Program Files\\Eclipse",
            "./eclipse-jdt"
        ]
        
        for loc in locations:
            path = Path(loc).expanduser()
            if path.exists():
                return str(path)
        
        return None
    
    def _create_jdt_refactoring_script(self) -> str:
        """Create Eclipse JDT refactoring script."""
        return '''
import org.eclipse.jdt.core.*;
import org.eclipse.jdt.core.dom.*;
import org.eclipse.jdt.core.dom.rewrite.ASTRewrite;
import org.eclipse.jdt.core.refactoring.CompilationUnitChange;
import org.eclipse.ltk.core.refactoring.*;
import org.eclipse.ltk.core.refactoring.participants.*;
import org.eclipse.jdt.internal.corext.refactoring.rename.*;
import java.util.Map;
import java.util.HashMap;

public class JDTRefactor {
    public static void main(String[] args) throws Exception {
        String filePath = args[0];
        String oldName = args[1];
        String newName = args[2];
        String scopeClass = args.length > 3 ? args[3] : null;
        String scopeMethod = args.length > 4 ? args[4] : null;
        
        // Create AST
        ASTParser parser = ASTParser.newParser(AST.JLS19);
        parser.setSource(Files.readString(Paths.get(filePath)).toCharArray());
        parser.setKind(ASTParser.K_COMPILATION_UNIT);
        parser.setResolveBindings(true);
        
        CompilationUnit cu = (CompilationUnit) parser.createAST(null);
        
        // Create rewrite
        ASTRewrite rewrite = ASTRewrite.create(cu.getAST());
        
        // Visit and rename with full scope awareness
        cu.accept(new ASTVisitor() {
            @Override
            public boolean visit(SimpleName node) {
                if (node.getIdentifier().equals(oldName)) {
                    IBinding binding = node.resolveBinding();
                    if (binding instanceof IVariableBinding) {
                        IVariableBinding varBinding = (IVariableBinding) binding;
                        
                        // Check scope constraints
                        if (scopeClass != null || scopeMethod != null) {
                            ASTNode parent = node.getParent();
                            while (parent != null) {
                                if (scopeClass != null && parent instanceof TypeDeclaration) {
                                    TypeDeclaration type = (TypeDeclaration) parent;
                                    if (!type.getName().getIdentifier().equals(scopeClass)) {
                                        return true; // Skip this occurrence
                                    }
                                }
                                if (scopeMethod != null && parent instanceof MethodDeclaration) {
                                    MethodDeclaration method = (MethodDeclaration) parent;
                                    if (!method.getName().getIdentifier().equals(scopeMethod)) {
                                        return true; // Skip this occurrence
                                    }
                                }
                                parent = parent.getParent();
                            }
                        }
                        
                        // Rename this occurrence
                        rewrite.replace(node, cu.getAST().newSimpleName(newName), null);
                    }
                }
                return true;
            }
        });
        
        // Apply changes
        Document document = new Document(Files.readString(Paths.get(filePath)));
        TextEdit edits = rewrite.rewriteAST(document, null);
        edits.apply(document);
        
        // Write result
        Files.writeString(Paths.get("output.java"), document.get());
    }
}
'''
    
    def rename_variable(self, file_path: Path, old_name: str, new_name: str,
                       scope_info: Dict) -> Dict:
        """Rename variable using Eclipse JDT."""
        
        if not self.eclipse_home:
            return {
                'success': False,
                'error': 'Eclipse JDT not found. Install Eclipse or standalone JDT.'
            }
        
        # This is a simplified version - full JDT integration would require
        # more setup but provides unmatched refactoring capabilities
        
        return {
            'success': False,
            'error': 'Eclipse JDT integration requires additional setup. Use Spoon or JavaParser instead.'
        }


class EnhancedJavaRefactorer:
    """Main class that tries different backends in order of preference."""
    
    def __init__(self):
        self.backends = {
            'spoon': SpoonRefactorer(),
            'javaparser': JavaParserSymbolSolverRefactorer(),
            'jdt': EclipseJDTRefactorer(),
        }
        self.available_backends = self._check_backends()
    
    def _check_backends(self) -> List[str]:
        """Check which backends are available."""
        available = []
        
        # Check Spoon
        if self.backends['spoon'].spoon_jar:
            available.append('spoon')
        
        # Check JavaParser (needs gradle)
        if self.backends['javaparser'].gradle_available:
            available.append('javaparser')
        
        # Check JDT
        if self.backends['jdt'].eclipse_home:
            available.append('jdt')
        
        return available
    
    def rename_variable(self, file_path: Path, old_name: str, new_name: str,
                       scope_class: Optional[str] = None,
                       scope_method: Optional[str] = None,
                       variable_type: str = "all",
                       preferred_backend: Optional[str] = None) -> Dict:
        """Rename variable with full scope awareness."""
        
        if not self.available_backends:
            return {
                'success': False,
                'error': 'No Java refactoring backends available. Run: ./install_java_refactoring_libs.sh',
                'available_backends': []
            }
        
        # Prepare scope info
        scope_info = {
            'class': scope_class,
            'method': scope_method,
            'type': variable_type
        }
        
        # Try preferred backend first
        if preferred_backend and preferred_backend in self.available_backends:
            backend = self.backends[preferred_backend]
            result = backend.rename_variable(file_path, old_name, new_name, 
                                           scope_class, scope_method, variable_type)
            if result['success']:
                result['backend_used'] = preferred_backend
                return result
        
        # Try other backends in order
        for backend_name in self.available_backends:
            if backend_name == preferred_backend:
                continue  # Already tried
            
            backend = self.backends[backend_name]
            
            if backend_name == 'spoon':
                result = backend.rename_variable(file_path, old_name, new_name,
                                               scope_class, scope_method, variable_type)
            else:
                result = backend.rename_variable(file_path, old_name, new_name, scope_info)
            
            if result['success']:
                result['backend_used'] = backend_name
                return result
        
        return {
            'success': False,
            'error': 'All backends failed',
            'available_backends': self.available_backends
        }


def create_installation_script():
    """Create a script to install Java refactoring libraries."""
    
    script_content = '''#!/bin/bash
# Install Java refactoring libraries for enhanced scope-aware refactoring

echo "Installing Java refactoring libraries..."
echo "======================================="

# Create lib directory
mkdir -p lib

# Install Spoon (recommended - easiest to use)
echo "1. Installing Spoon..."
SPOON_VERSION="10.4.0"
SPOON_URL="https://repo1.maven.org/maven2/fr/inria/gforge/spoon/spoon-core/$SPOON_VERSION/spoon-core-$SPOON_VERSION-jar-with-dependencies.jar"
wget -O lib/spoon-core-$SPOON_VERSION-jar-with-dependencies.jar $SPOON_URL
echo "✓ Spoon installed"

# Check for Gradle (needed for JavaParser)
echo ""
echo "2. Checking for Gradle..."
if command -v gradle &> /dev/null; then
    echo "✓ Gradle found"
else
    echo "⚠ Gradle not found. Install with:"
    echo "  macOS: brew install gradle"
    echo "  Linux: sudo apt install gradle"
fi

# Eclipse JDT info
echo ""
echo "3. Eclipse JDT (optional - most powerful):"
echo "For full Eclipse JDT support, you need one of:"
echo "  - Eclipse IDE: https://www.eclipse.org/downloads/"
echo "  - Standalone JDT: https://download.eclipse.org/eclipse/downloads/"

echo ""
echo "Installation complete!"
echo ""
echo "Available refactoring backends:"
echo "- Spoon: ✓ Ready to use (easiest, recommended)"
echo "- JavaParser: Requires Gradle"
echo "- Eclipse JDT: Requires Eclipse or standalone JDT"
'''
    
    script_path = Path("install_java_refactoring_libs.sh")
    script_path.write_text(script_content)
    script_path.chmod(0o755)
    print(f"Created installation script: {script_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced Java refactoring with full scope awareness',
        epilog='''
EXAMPLES:
  # Rename local variable in specific method
  %(prog)s rename File.java --old counter --new index --scope-method processData
  
  # Rename field across entire class
  %(prog)s rename File.java --old userName --new username --type field
  
  # Rename variable in specific class and method
  %(prog)s rename File.java --old temp --new temporary --scope-class MyClass --scope-method calculate
  
  # Check available backends
  %(prog)s --check-backends
  
  # Install required libraries
  %(prog)s --install

BACKENDS:
  • Spoon: Modern, easy to use, good IDE integration (RECOMMENDED)
  • JavaParser + Symbol Solver: Lightweight, good for simple refactoring
  • Eclipse JDT: Most powerful, used by Eclipse IDE

VARIABLE TYPES:
  • all: Rename all variables with the name (default)
  • local: Only local variables
  • field: Only class fields
  • parameter: Only method parameters
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Add commands
    parser.add_argument('--check-backends', action='store_true',
                       help='Check which refactoring backends are available')
    parser.add_argument('--install', action='store_true',
                       help='Create installation script for Java libraries')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Rename command
    rename = subparsers.add_parser('rename', help='Rename a variable')
    rename.add_argument('file', help='Java file to refactor')
    rename.add_argument('--old', required=True, help='Current variable name')
    rename.add_argument('--new', required=True, help='New variable name')
    rename.add_argument('--type', choices=['all', 'local', 'field', 'parameter'],
                       default='all', help='Variable type to rename')
    rename.add_argument('--scope-class', help='Limit to specific class')
    rename.add_argument('--scope-method', help='Limit to specific method')
    rename.add_argument('--backend', choices=['spoon', 'javaparser', 'jdt'],
                       help='Preferred backend to use')
    rename.add_argument('--dry-run', action='store_true',
                       help='Show what would be changed')
    
    args = parser.parse_args()
    
    if args.install:
        create_installation_script()
        return
    
    refactorer = EnhancedJavaRefactorer()
    
    if args.check_backends:
        print("JAVA REFACTORING BACKENDS STATUS")
        print("=" * 50)
        print()
        
        # Check each backend
        spoon = refactorer.backends['spoon']
        javaparser = refactorer.backends['javaparser'] 
        jdt = refactorer.backends['jdt']
        
        print(f"Spoon: {'✓ Available' if spoon.spoon_jar else '✗ Not installed'}")
        if spoon.spoon_jar:
            print(f"  JAR: {spoon.spoon_jar}")
        
        print(f"\nJavaParser: {'✓ Available' if javaparser.gradle_available else '✗ Gradle not found'}")
        
        print(f"\nEclipse JDT: {'✓ Available' if jdt.eclipse_home else '✗ Not found'}")
        if jdt.eclipse_home:
            print(f"  Path: {jdt.eclipse_home}")
        
        print(f"\nAvailable backends: {', '.join(refactorer.available_backends) or 'None'}")
        
        if not refactorer.available_backends:
            print("\nTo install backends, run: ./java_scope_refactor_enhanced.py --install")
        
        return
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'rename':
        file_path = Path(args.file)
        
        if not file_path.exists():
            print(f"Error: File '{args.file}' not found")
            sys.exit(1)
        
        # Store original content
        original_content = file_path.read_text()
        
        # Perform refactoring
        result = refactorer.rename_variable(
            file_path, args.old, args.new,
            args.scope_class, args.scope_method, args.type,
            args.backend
        )
        
        if result['success']:
            print(f"✓ Successfully renamed '{args.old}' to '{args.new}'")
            print(f"  Backend used: {result.get('backend_used', 'unknown')}")
            print(f"  Changes made: {result.get('changes', 'unknown')}")
            
            if args.dry_run:
                print("\nPreview of changes:")
                print("-" * 50)
                # Show diff
                import difflib
                diff = difflib.unified_diff(
                    original_content.splitlines(keepends=True),
                    result['new_content'].splitlines(keepends=True),
                    fromfile=f"{args.file} (original)",
                    tofile=f"{args.file} (modified)"
                )
                print(''.join(diff))
            else:
                # Apply changes
                file_path.write_text(result['new_content'])
                print(f"\n✓ File updated: {args.file}")
        else:
            print(f"✗ Refactoring failed: {result.get('error', 'Unknown error')}")
            if result.get('available_backends'):
                print(f"  Available backends: {', '.join(result['available_backends'])}")


if __name__ == '__main__':
    main()