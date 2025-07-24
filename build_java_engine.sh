#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Build script for Java refactoring engine
#
# Author: Vaibhav-api-code
# Co-Author: Claude Code (https://claude.ai/code)
# Created: 2025-07-08
# Updated: 2025-07-23
# License: Mozilla Public License 2.0 (MPL-2.0)


echo "Building Java refactoring engine..."

# Check if Maven is installed
if ! command -v mvn &> /dev/null; then
    echo "Error: Maven is not installed. Please install Maven first."
    echo "On macOS: brew install maven"
    echo "On Ubuntu: sudo apt-get install maven"
    exit 1
fi

# Clean and build
mvn clean package

if [ $? -eq 0 ]; then
    echo "Build successful! JAR file created at: target/java-refactor-engine.jar"
    # Copy to the expected location
    cp target/java-refactor-engine.jar java-refactor-engine.jar
    echo "JAR file copied to: java-refactor-engine.jar"
else
    echo "Build failed!"
    exit 1
fi