# Docker File Access & Path Detection

This document provides comprehensive information about the **enhanced Docker functionality** in the Zen MCP Server, including automatic path detection, universal file access, and simplified multi-OS configuration.

## Summary

- [Overview](#overview)
- [PathModeDetector](#pathmodedetector)
- [Universal Path Detection](#universal-path-detection)
- [File Access Configuration](#file-access-configuration)
- [Environment Variables](#environment-variables)
- [Setup Scripts](#setup-scripts)
- [Docker Configuration](#docker-configuration)
- [Path Conversion](#path-conversion)
- [Multi-OS Support](#multi-os-support)
- [Debugging](#debugging)
- [Migration Guide](#migration-guide)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The Zen MCP Server includes advanced Docker functionality that automatically detects the execution environment and provides seamless file access across different operating systems. The system eliminates path-related issues when running in Docker containers while maintaining compatibility with local Python environments.

### Key Features

- **Automatic Environment Detection**: Detects Docker vs local execution automatically
- **Universal Path Conversion**: Converts Windows paths to Docker container paths seamlessly
- **Multi-OS Support**: Works on Windows, Linux, macOS, and WSL2
- **Simplified Configuration**: Automated setup scripts for all platforms
- **Environment Variable Override**: Manual control when needed
- **Comprehensive Logging**: Debug modes for troubleshooting

## PathModeDetector

The `PathModeDetector` is the core component that handles automatic environment detection and path conversion. It uses a three-tier detection system with fallback mechanisms.

### Detection Priority Order

1. **Environment Variable Override** (Priority 1)
2. **Docker Native Indicators** (Priority 2)  
3. **Runtime Analysis** (Priority 3 - Fallback)

### Implementation

```python
from utils.path_detector import get_path_detector, convert_path_for_current_mode

# Get current execution mode
detector = get_path_detector()
mode = detector.get_path_mode()  # Returns 'docker' or 'local'

# Convert a path for current environment
converted_path = convert_path_for_current_mode("C:/Users/Gildas/Documents/file.txt")
# In Docker: "/app/project/file.txt"
# In Local:  "C:/Users/Gildas/Documents/file.txt"

# Check if running in Docker
if detector.is_docker_mode():
    print("Running in Docker container")
```

### Singleton Pattern

The `PathModeDetector` uses a singleton pattern to ensure consistent detection results across the application and avoid repeated detection overhead.

## Universal Path Detection

### Method 1: Environment Variable Override

**Highest Priority** - Manual control for specific scenarios.

```bash
# .env file configuration (recommended)
MCP_FILE_PATH_MODE=auto              # Automatic detection (default)
# MCP_FILE_PATH_MODE=docker          # Force Docker mode
# MCP_FILE_PATH_MODE=local           # Force local mode

# Manual export for temporary override
export MCP_FILE_PATH_MODE=docker
```

**Advantages:**
- Explicit manual control
- Portable across all systems
- Easy debugging override
- Configuration file support

### Method 2: Docker Native Indicators

**Universal Docker Detection** - Works with all Docker deployments.

```python
# Detected automatically:
# 1. /.dockerenv file (created by Docker)
# 2. /proc/1/cgroup contains docker paths
# 3. Docker environment variables (DOCKER_CONTAINER, DOCKER_IMAGE)
# 4. HOSTNAME matching container ID pattern (12 hex characters)
```

**Advantages:**
- Native Docker detection
- Works with all orchestrators
- Independent of MCP configuration
- Industry standard approach

### Method 3: Runtime Analysis

**Fallback Detection** - Analyzes runtime environment characteristics.

```python
# Detected indicators:
# 1. Working directory starts with /app
# 2. Python executable in /usr/local/bin or /usr/bin
# 3. Minimal filesystem structure (missing /home or /var/log)
```

**Advantages:**
- Robust fallback mechanism
- Runtime-based detection
- Compatible with custom containers
- Environment-agnostic

## File Access Configuration

### Simplified Docker Configuration

The Docker configuration has been streamlined to use a single `WORKSPACE_FOLDER` variable that works across all operating systems.

#### Environment Variables (`.env`)

```bash
# Primary workspace configuration
WORKSPACE_FOLDER=                    # Optional: workspace to mount
                                     # If empty, uses current directory

# Platform-specific examples:
# Windows: WORKSPACE_FOLDER=c:/Users/Username/Documents/Project
# Linux:   WORKSPACE_FOLDER=/home/username/projects/project
# macOS:   WORKSPACE_FOLDER=/Users/username/Documents/Project
```

#### Docker Compose Volumes

```yaml
services:
  zen-mcp:
    volumes:
      # Workspace: uses WORKSPACE_FOLDER if defined, otherwise current directory
      - ${WORKSPACE_FOLDER:-.}:/workspace:ro
      # Project files: always mounts current directory
      - .:/app/project:ro
      # Logs: always writable
      - ./logs:/app/logs
      # Configuration: named volume for persistence
      - config:/app/conf
```

### Default Behavior

- **`WORKSPACE_FOLDER` defined**: Mounts specified directory to `/workspace:ro`
- **`WORKSPACE_FOLDER` empty/undefined**: Mounts current directory (`.`) to `/workspace:ro`
- **Always mounted**: Current directory to `/app/project:ro` for project files
- **Always mounted**: `./logs` directory for log output

## Environment Variables

### Core Configuration

```bash
# Path detection configuration
MCP_FILE_PATH_MODE=auto              # auto|docker|local
MCP_DEBUG_PATH_DETECTION=false       # true|false

# Workspace configuration  
WORKSPACE_FOLDER=                    # Path to workspace directory

# Docker host OS (auto-detected by setup scripts)
DOCKER_HOST_OS=                      # windows|linux|darwin
```

### Debug Configuration

```bash
# Enable detailed path detection logging
MCP_DEBUG_PATH_DETECTION=true

# This will output:
# - Detection method used
# - Result of each test
# - Path conversions performed
# - Error details if detection fails
```

### API Keys and Other Settings

All existing environment variables remain unchanged:

```bash
# AI Provider API Keys
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
# ... other API keys

# Logging configuration
LOG_LEVEL=INFO
LOG_MAX_SIZE=10MB

# Model configuration
DEFAULT_MODEL=auto
DEFAULT_THINKING_MODE_THINKDEEP=high
```

## Setup Scripts

### Automated Configuration

Both Windows and Unix systems include automated setup scripts that configure the entire Docker environment.

#### Windows (PowerShell)

```powershell
# Basic setup
.\setup.ps1

# With options
.\setup.ps1 -Force                                    # Force reconfiguration
.\setup.ps1 -DocumentsPath "D:\MyProjects"           # Custom documents path
.\setup.ps1 -WorkspacePath "C:\Code\zen-mcp"         # Custom workspace path

# Help
.\setup.ps1 -Help
```

#### Linux/macOS/WSL2 (Bash)

```bash
# Make executable and run
chmod +x setup.sh
./setup.sh

# With options  
./setup.sh --force                                   # Force reconfiguration
./setup.sh --docs "/home/user/Projects"              # Custom documents path
./setup.sh --workspace "/home/user/Code/zen-mcp"     # Custom workspace path

# Help
./setup.sh --help
```

### What Setup Scripts Configure

1. **Environment Variables**: Creates/updates `.env` file with appropriate paths
2. **Docker Configuration**: Ensures docker-compose.yml has correct volume mounts
3. **MCP Client Integration**: Updates `.vscode/mcp.json` for VS Code integration
4. **Dependency Checking**: Verifies Docker and Docker Compose installation
5. **Permission Setup**: Configures file permissions where needed

## Docker Configuration

### Multi-Stage Dockerfile

The Docker image uses a multi-stage build for optimization:

```dockerfile
# Development stage with all tools
FROM python:3.12-slim as development
# ... development dependencies

# Runtime stage optimized for production
FROM python:3.12-slim as runtime  
# ... only runtime dependencies
```

### Container Specifications

```yaml
services:
  zen-mcp:
    image: mcp/zen:latest
    container_name: zen-mcp
    
    # Resource limits
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
    
    # Security
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
      - /app/tmp:noexec,nosuid,size=50m
    
    # Health check
    healthcheck:
      test: ["CMD", "python", "/usr/local/bin/healthcheck.py"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Network Configuration

```yaml
networks:
  zen-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## Path Conversion

### Conversion Rules

The path conversion system handles various path formats and converts them appropriately for the current execution environment.

#### Docker Mode Conversion

```python
# Windows absolute paths
"C:\\Users\\Gildas\\Documents\\zen-mcp-server\\server.py"
# → "/app/project/server.py"

# Relative paths  
"docs/configuration.md"
# → "/app/project/docs/configuration.md"

# Already Docker paths (unchanged)
"/app/project/server.py"
# → "/app/project/server.py"

"/workspace/external_file.txt"
# → "/workspace/external_file.txt"
```

#### Local Mode Conversion

```python
# All paths remain unchanged in local mode
"C:\\Users\\Gildas\\Documents\\file.txt"
# → "C:\\Users\\Gildas\\Documents\\file.txt"

"./relative/path.py"
# → "./relative/path.py"
```

### Intelligent Path Detection

The system automatically detects the project root by looking for the `zen-mcp-server` directory name in the path:

```python
# Input path
"C:\\Users\\Gildas\\Documents\\Fork\\zen-mcp-server\\utils\\path_detector.py"

# Detection process:
# 1. Split path into parts
# 2. Find "zen-mcp-server" part  
# 3. Convert remaining parts to Docker path
# 4. Result: "/app/project/utils/path_detector.py"
```

### Fallback Mechanisms

If project root detection fails, the system provides intelligent fallbacks:

```python
# If no project indicator found, assume it's a project file
"C:\\Users\\Gildas\\Documents\\somefile.txt"
# → "/app/project/somefile.txt"

# Relative paths get project prefix
"script.py"
# → "/app/project/script.py"
```

## Multi-OS Support

### Windows Support

#### Native Windows
```bash
# Setup command
.\setup.ps1

# Paths configured automatically:
# WORKSPACE_FOLDER=C:/Users/Username/Documents/Fork/zen-mcp-server
# DOCUMENTS_DIR=C:/Users/Username/Documents
```

#### Windows with WSL2
```bash
# Use Linux setup script in WSL
./setup.sh

# Paths configured for WSL:
# WORKSPACE_FOLDER=/mnt/c/Users/Username/Documents/Fork/zen-mcp-server
# Special WSL path handling
```

### Linux Support

```bash
# Setup command
./setup.sh

# Paths configured automatically:
# WORKSPACE_FOLDER=/home/username/Documents/Fork/zen-mcp-server
# DOCUMENTS_DIR=/home/username/Documents
```

### macOS Support

```bash
# Setup command
./setup.sh

# Paths configured automatically:
# WORKSPACE_FOLDER=/Users/username/Documents/Fork/zen-mcp-server
# DOCUMENTS_DIR=/Users/username/Documents
```

### Cross-Platform Volume Mounts

The Docker configuration automatically adapts to the host OS:

```yaml
# Windows
volumes:
  - "C:/Users/Username/Workspace:/workspace:ro"

# Linux
volumes:
  - "/home/username/workspace:/workspace:ro"

# macOS
volumes:
  - "/Users/username/Workspace:/workspace:ro"
```

## Debugging

### Enable Debug Logging

```bash
# In .env file
MCP_DEBUG_PATH_DETECTION=true

# Or export temporarily
export MCP_DEBUG_PATH_DETECTION=true
```

### Debug Output Examples

```
PathModeDetector: Environment variable override: MCP_FILE_PATH_MODE=docker
PathModeDetector: Detection complete - mode='docker', method='_detect_from_env_var'
PathModeDetector: Converted Windows path 'C:\...\server.py' → '/app/project/server.py'
```

### Testing Detection

```python
from utils.path_detector import get_path_detector

# Test detection
detector = get_path_detector()
print(f"Detected mode: {detector.get_path_mode()}")

# Test path conversion
test_path = "C:\\Users\\Test\\zen-mcp-server\\file.py"
converted = detector.convert_path(test_path)
print(f"Converted: {test_path} → {converted}")
```

### Common Debug Scenarios

```bash
# Force Docker mode for testing
export MCP_FILE_PATH_MODE=docker

# Force local mode for testing  
export MCP_FILE_PATH_MODE=local

# Enable verbose logging
export MCP_DEBUG_PATH_DETECTION=true

# Reset to automatic detection
export MCP_FILE_PATH_MODE=auto
```

## Migration Guide

### From Previous Versions

If you're upgrading from a previous version of zen-mcp-server:

1. **Run Setup Script**: The automated setup will handle migration
   ```bash
   # Windows
   .\setup.ps1 -Force
   
   # Linux/macOS/WSL2
   ./setup.sh --force
   ```

2. **Update Environment Variables**: Remove old Docker-specific variables
   ```bash
   # Old variables (remove these):
   # DOCKER_WORKSPACE_PATH
   # DOCKER_MOUNT_PATH
   # DOCKER_HOST_PATH
   
   # New simplified variable:
   WORKSPACE_FOLDER=/path/to/your/workspace
   ```

3. **Update Docker Compose**: If you have a custom docker-compose.yml, update volume mounts:
   ```yaml
   # Old format:
   volumes:
     - "${DOCKER_WORKSPACE_PATH}:/workspace"
   
   # New format:
   volumes:
     - "${WORKSPACE_FOLDER:-.}:/workspace:ro"
     - ".:/app/project:ro"
   ```

### MCP Client Configuration

Update your MCP client configuration to use the new Docker setup:

```json
{
  "servers": {
    "zen-docker": {
      "command": "docker-compose",
      "args": ["run", "--rm", "zen-mcp"]
    }
  }
}
```

## Best Practices

### Environment Configuration

1. **Use Setup Scripts**: Always use the automated setup scripts for initial configuration
2. **Version Control**: Add `.env` to `.gitignore` but include `.env.example`
3. **API Key Security**: Use Docker secrets in production environments
4. **Resource Limits**: Configure appropriate memory and CPU limits

### Path Management

1. **Use Relative Paths**: When possible, use relative paths in your code
2. **Environment Detection**: Let the system auto-detect the environment
3. **Debug Mode**: Use debug mode when troubleshooting path issues
4. **Path Validation**: Validate file existence after path conversion

### Docker Deployment

1. **Health Checks**: Always enable health checks in production
2. **Log Management**: Configure log rotation and retention
3. **Security**: Use read-only containers with tmpfs for writable areas
4. **Networks**: Use custom networks for isolation

### Development Workflow

1. **Local Development**: Use local Python environment for development
2. **Testing**: Use Docker for integration testing
3. **CI/CD**: Use Docker for consistent CI/CD environments
4. **Production**: Use Docker Compose or orchestration platforms

## Troubleshooting

### Common Issues

#### Path Detection Issues

**Problem**: Wrong execution mode detected
```bash
# Check current detection
export MCP_DEBUG_PATH_DETECTION=true
python -c "from utils.path_detector import get_path_detector; print(get_path_detector().get_path_mode())"

# Force correct mode temporarily
export MCP_FILE_PATH_MODE=docker  # or 'local'
```

**Problem**: File not found errors in Docker
```bash
# Check volume mounts
docker-compose config

# Verify file exists in container
docker-compose exec zen-mcp ls -la /app/project/
docker-compose exec zen-mcp ls -la /workspace/
```

#### Configuration Issues

**Problem**: Setup script fails
```bash
# Check dependencies
docker --version
docker-compose --version

# Run with verbose output
.\setup.ps1 -Verbose  # Windows
./setup.sh --debug   # Linux/macOS
```

**Problem**: Environment variables not loaded
```bash
# Check .env file exists and has correct format
cat .env

# Verify Docker Compose reads it
docker-compose config
```

#### Docker Issues

**Problem**: Container fails to start
```bash
# Check logs
docker-compose logs zen-mcp

# Check resource usage
docker stats

# Verify health check
docker-compose ps
```

**Problem**: Permission errors
```bash
# Fix log directory permissions
chmod 755 logs/

# Check Docker volume permissions
docker-compose exec zen-mcp ls -la /app/logs/
```

### Debug Commands

```bash
# Test path detection
python -c "
from utils.path_detector import get_path_detector
detector = get_path_detector()
print(f'Mode: {detector.get_path_mode()}')
print(f'Docker: {detector.is_docker_mode()}')
"

# Test path conversion
python -c "
from utils.path_detector import convert_path_for_current_mode
path = 'C:/Users/Test/zen-mcp-server/file.py'
print(f'Original: {path}')
print(f'Converted: {convert_path_for_current_mode(path)}')
"

# Check Docker environment
docker-compose exec zen-mcp env | grep MCP
docker-compose exec zen-mcp python -c "
import os
print('Docker indicators:')
print(f'/.dockerenv exists: {os.path.exists(\"/.dockerenv\")}')
print(f'Working directory: {os.getcwd()}')
print(f'Python executable: {sys.executable}')
"
```

### Getting Help

1. **Enable Debug Mode**: Set `MCP_DEBUG_PATH_DETECTION=true`
2. **Check Logs**: Review both application and Docker logs
3. **Test Manually**: Use the debug commands above
4. **Re-run Setup**: Use setup scripts with force option
5. **GitHub Issues**: Report issues with debug output

---

For additional support, see the [main troubleshooting guide](troubleshooting.md) or open an issue on GitHub with debug output and your configuration details.
