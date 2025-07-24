#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Reliable build script for the Spoon-powered refactor engine.
#
# Author: Vaibhav-api-code
# Co-Author: Claude Code (https://claude.ai/code)
# Created: 2025-07-08
# Updated: 2025-07-23
# License: Mozilla Public License 2.0 (MPL-2.0)


set -Eeuo pipefail
trap 'echo "🔥  Build failed at line $LINENO" >&2' ERR

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "${SCRIPT_DIR}"

LOG() { printf '• %s\n' "$*"; }
GRADLE_CMD=${GRADLE_CMD:-gradle}

LOG "Building Java refactoring engine with ${GRADLE_CMD} …"

if ! command -v "${GRADLE_CMD}" &>/dev/null; then
  echo "Error: ${GRADLE_CMD} not found.  Install Gradle or point GRADLE_CMD to ./gradlew" >&2
  exit 1
fi

mkdir -p src/main/java
cp JavaRefactorWithSpoonV2.java src/main/java/
cp SpoonVariableRenamer.java src/main/java/ 2>/dev/null || true

"${GRADLE_CMD}" --quiet clean spoonJar


# Locate the freshly built JAR (Gradle may append version/hash)
JAR_PATH="$(find build/libs -maxdepth 1 -type f -name 'spoon-refactor-engine-*.jar' | head -n1 || true)"
if [[ -z "${JAR_PATH}" ]]; then
  echo "Error: JAR not produced!" >&2
  exit 1
fi
cp -f "${JAR_PATH}" spoon-refactor-engine.jar
LOG "✓  Built and staged ⇒ spoon-refactor-engine.jar"