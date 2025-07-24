#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Simple build script for Java refactoring engine without Maven
#
# Author: Vaibhav-api-code
# Co-Author: Claude Code (https://claude.ai/code)
# Created: 2025-07-08
# Updated: 2025-07-23
# License: Mozilla Public License 2.0 (MPL-2.0)


echo "Building Java refactoring engine (simple version)..."

# Check if Java is installed
if ! command -v javac &> /dev/null; then
    echo "Error: Java compiler (javac) is not installed."
    exit 1
fi

# Create lib directory for dependencies
mkdir -p lib

# Check if JavaParser JARs exist
if [ ! -f "lib/javaparser-core-3.25.8.jar" ] || [ ! -f "lib/javaparser-symbol-solver-core-3.25.8.jar" ]; then
    echo "JavaParser libraries not found in lib/ directory."
    echo ""
    echo "Please download the following JARs and place them in the lib/ directory:"
    echo "1. javaparser-core-3.25.8.jar"
    echo "   Download from: https://repo1.maven.org/maven2/com/github/javaparser/javaparser-core/3.25.8/javaparser-core-3.25.8.jar"
    echo ""
    echo "2. javaparser-symbol-solver-core-3.25.8.jar"
    echo "   Download from: https://repo1.maven.org/maven2/com/github/javaparser/javaparser-symbol-solver-core/3.25.8/javaparser-symbol-solver-core-3.25.8.jar"
    echo ""
    echo "3. javassist-3.29.2-GA.jar (dependency)"
    echo "   Download from: https://repo1.maven.org/maven2/org/javassist/javassist/3.29.2-GA/javassist-3.29.2-GA.jar"
    echo ""
    echo "4. guava-31.1-jre.jar (dependency)"
    echo "   Download from: https://repo1.maven.org/maven2/com/google/guava/guava/31.1-jre/guava-31.1-jre.jar"
    echo ""
    echo "You can download them using curl:"
    echo "curl -L -o lib/javaparser-core-3.25.8.jar https://repo1.maven.org/maven2/com/github/javaparser/javaparser-core/3.25.8/javaparser-core-3.25.8.jar"
    echo "curl -L -o lib/javaparser-symbol-solver-core-3.25.8.jar https://repo1.maven.org/maven2/com/github/javaparser/javaparser-symbol-solver-core/3.25.8/javaparser-symbol-solver-core-3.25.8.jar"
    echo "curl -L -o lib/javassist-3.29.2-GA.jar https://repo1.maven.org/maven2/org/javassist/javassist/3.29.2-GA/javassist-3.29.2-GA.jar"
    echo "curl -L -o lib/guava-31.1-jre.jar https://repo1.maven.org/maven2/com/google/guava/guava/31.1-jre/guava-31.1-jre.jar"
    exit 1
fi

# Create build directory
mkdir -p build

# Compile
echo "Compiling JavaRefactor.java..."
javac -cp "lib/*" -d build JavaRefactor.java

if [ $? -ne 0 ]; then
    echo "Compilation failed!"
    exit 1
fi

# Create manifest
echo "Main-Class: JavaRefactor" > build/MANIFEST.MF
echo "Class-Path: lib/javaparser-core-3.25.8.jar lib/javaparser-symbol-solver-core-3.25.8.jar lib/javassist-3.29.2-GA.jar lib/guava-31.1-jre.jar" >> build/MANIFEST.MF

# Create JAR
echo "Creating JAR file..."
cd build
jar cfm ../java-refactor-engine.jar MANIFEST.MF *.class
cd ..

if [ $? -eq 0 ]; then
    echo "Build successful! JAR file created at: java-refactor-engine.jar"
    echo ""
    echo "Note: To run the JAR, you need the lib/ directory with JavaParser JARs in the same location."
else
    echo "JAR creation failed!"
    exit 1
fi