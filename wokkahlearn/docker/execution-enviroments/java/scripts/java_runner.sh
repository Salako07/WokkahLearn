#!/bin/bash

# Secure Java code runner with timeout and resource limits

set -e

MAX_EXECUTION_TIME=${MAX_EXECUTION_TIME:-30}
MAX_MEMORY_MB=${MAX_MEMORY_MB:-128}

# Security validation
validate_code() {
    local code_file="$1"
    
    # Check for dangerous patterns
    if grep -q "Runtime\|ProcessBuilder\|System\.exit\|System\.setProperty\|Class\.forName" "$code_file"; then
        echo "Security Error: Dangerous Java operations detected" >&2
        exit 1
    fi
    
    if grep -q "java\.io\.File\|java\.nio\.file\|FileInputStream\|FileOutputStream" "$code_file"; then
        echo "Security Error: File operations not allowed" >&2
        exit 1
    fi
    
    if grep -q "java\.net\|Socket\|ServerSocket\|URL\|HttpURLConnection" "$code_file"; then
        echo "Security Error: Network operations not allowed" >&2
        exit 1
    fi
    
    return 0
}

# Execute Java code
execute_java() {
    local start_time=$(date +%s.%N)
    
    # Find main class
    local main_class="Main"
    if [ -f "/workspace/Main.java" ]; then
        main_class="Main"
    elif [ -f "/workspace/main.java" ]; then
        mv "/workspace/main.java" "/workspace/Main.java"
        main_class="Main"
    else
        echo "Error: No Main.java file found" >&2
        exit 1
    fi
    
    # Validate code
    validate_code "/workspace/Main.java"
    
    # Compile
    if ! timeout ${MAX_EXECUTION_TIME} javac -cp /workspace Main.java 2>&1; then
        echo "Compilation failed" >&2
        exit 1
    fi
    
    # Run with timeout and memory limits
    timeout ${MAX_EXECUTION_TIME} java \
        -Xmx${MAX_MEMORY_MB}m \
        -Xms64m \
        -XX:MaxMetaspaceSize=64m \
        -Djava.security.manager \
        -Djava.security.policy=/dev/null \
        -Dfile.encoding=UTF-8 \
        -cp /workspace \
        Main
    
    local exit_code=$?
    local end_time=$(date +%s.%N)
    local execution_time=$(echo "$end_time - $start_time" | bc -l)
    
    if [ $exit_code -eq 124 ]; then
        echo "Execution timed out after ${MAX_EXECUTION_TIME} seconds" >&2
        exit 124
    fi
    
    exit $exit_code
}

# Main execution
if [ $# -gt 0 ]; then
    # Code provided as argument - write to file
    echo "$1" > /workspace/Main.java
fi

execute_java

---

# docker/execution-environments/cpp/Dockerfile.gcc

FROM gcc:12-alpine

# Install system dependencies
RUN apk add --no-cache \
    bash \
    coreutils \
    make \
    cmake \
    gdb

# Create non-root user
RUN addgroup -g 1000 coderunner && \
    adduser -D -s /bin/sh -u 1000 -G coderunner coderunner

# Set up workspace
WORKDIR /workspace
RUN chown coderunner:coderunner /workspace

# Security settings
ENV MAX_EXECUTION_TIME=30
ENV MAX_MEMORY_MB=128

# Copy execution script
COPY --chown=coderunner:coderunner scripts/cpp_runner.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/cpp_runner.sh

USER coderunner

# Default command
CMD ["g++"]

---

# docker/execution-environments/scripts/build_all.sh

#!/bin/bash

# Build all execution environment Docker images

set -e

echo "🐳 Building WokkahLearn Code Execution Environments..."

# Create network if it doesn't exist
docker network create wokkahlearn_execution 2>/dev/null || true

# Build Python environments
echo "📦 Building Python environments..."
cd python
docker build -f Dockerfile.python311 -t wokkahlearn/python:3.11-alpine .
docker build -f Dockerfile.python39 -t wokkahlearn/python:3.9-alpine .
cd ..

# Build Node.js environment
echo "📦 Building Node.js environment..."
cd nodejs
docker build -f Dockerfile.node18 -t wokkahlearn/nodejs:18-alpine .
cd ..

# Build Java environment
echo "📦 Building Java environment..."
cd java
docker build -f Dockerfile.java17 -t wokkahlearn/java:17-alpine .
cd ..

# Build C++ environment
echo "📦 Building C++ environment..."
cd cpp
docker build -f Dockerfile.gcc -t wokkahlearn/cpp:gcc-alpine .
cd ..

# Build Go environment
echo "📦 Building Go environment..."
cd go
docker build -f Dockerfile.go120 -t wokkahlearn/go:1.20-alpine .
cd ..

# Build Rust environment
echo "📦 Building Rust environment..."
cd rust
docker build -f Dockerfile.rust -t wokkahlearn/rust:stable-alpine .
cd ..

echo "✅ All execution environments built successfully!"
echo ""
echo "Available images:"
docker images | grep wokkahlearn/
echo ""
echo "🚀 Ready for code execution!"