# Multi-Platform Path Detector Configuration

The Zen MCP server now supports automatic multi-platform path conversion for full compatibility between Windows, Linux, macOS, and WSL2.

## Supported Platforms

### Windows
- **Format**: `C:\Users\...` or `C:/Users/...`
- **Docker Conversion**: `C:\Users\Gildas\zen-mcp-server\file.py` → `/app/project/file.py`
- **Local Mode**: Paths unchanged

### Linux
- **Format**: `/home/user/...`
- **Docker Conversion**: `/home/user/zen-mcp-server/file.py` → `/app/project/file.py`
- **Local Mode**: Paths unchanged

### macOS
- **Format**: `/Users/username/...`
- **Docker Conversion**: `/Users/john/zen-mcp-server/file.py` → `/app/project/file.py`
- **Local Mode**: Paths unchanged

### WSL2 (Windows Subsystem for Linux)
- **WSL Format**: `/mnt/c/Users/...` (Windows mounts)
- **Linux Format**: `/home/user/...` (native WSL)
- **Docker Conversion**: Both formats → `/app/project/...`
- **Local Mode**: Paths unchanged

## Configuration

### Environment Variable

Set the mode via the `MCP_FILE_PATH_MODE` variable in your `.env` file:

```properties
# Path conversion mode
MCP_FILE_PATH_MODE=docker  # or 'local'

# Optional debug
MCP_DEBUG_PATH_DETECTION=false
```

### Available Modes

#### `docker` Mode
- **Usage**: Running inside a Docker container
- **Behavior**: Automatically converts all host paths to container paths (`/app/project/...`)
- **Advantages**: 
  - Compatible with all MCP clients
  - Automatic cross-platform conversion
  - Works with zen-docker-compose

#### `local` Mode (Default)
- **Usage**: Native Python execution on the host
- **Behavior**: Keeps paths unchanged
- **Advantages**: 
  - Optimal performance
  - Native platform paths

## Automatic Cross-Platform Detection

The system automatically detects the path format **regardless** of the host platform:

### Format Recognition

```python
# Windows (even if running on Linux)
"C:/Users/test/zen-mcp-server/file.py" → "/app/project/file.py"

# Linux/macOS (even if running on Windows)  
"/home/user/zen-mcp-server/file.py" → "/app/project/file.py"

# WSL2 (even if running on Windows)
"/mnt/c/Users/test/zen-mcp-server/file.py" → "/app/project/file.py"

# Relative paths (all platforms)
"src/main.py" → "/app/project/src/main.py"
```

### Project Detection

The system automatically looks for project indicators:
- `zen-mcp-server`
- `mcp-server` 
- `project`

## Conversion Examples

### Windows → Docker
```
Input:   C:\Users\Gildas\Documents\Fork\zen-mcp-server\README.md
Output:  /app/project/README.md

Input:   D:\dev\zen-mcp-server\src\main.py  
Output:  /app/project/src/main.py
```

### Linux → Docker
```
Input:   /home/user/dev/zen-mcp-server/config.yaml
Output:  /app/project/config.yaml

Input:   /opt/zen-mcp-server/tools/analyzer.py
Output:  /app/project/tools/analyzer.py
```

### WSL2 → Docker
```
Input:   /mnt/c/Users/Gildas/zen-mcp-server/file.py
Output:  /app/project/file.py

Input:   /mnt/d/projects/zen-mcp-server/docs/readme.md
Output:  /app/project/docs/readme.md
```

### Relative Paths → Docker
```
Input:   src/main.py
Output:  /app/project/src/main.py

Input:   config\\settings.json  (Windows)
Output:  /app/project/config/settings.json
```

## Platform-Specific Configuration

### Windows PowerShell
```powershell
# .env file
$env:MCP_FILE_PATH_MODE="docker"

# Test
python -c "from utils.path_detector import get_path_detector; print(get_path_detector().get_path_mode())"
```

### Linux/macOS Bash
```bash
# .env file
export MCP_FILE_PATH_MODE="docker"

# Test
python3 -c "from utils.path_detector import get_path_detector; print(get_path_detector().get_path_mode())"
```

### WSL2
```bash
# Works with both Windows and Linux paths
export MCP_FILE_PATH_MODE="docker"

# Test Windows path in WSL
python3 -c "from utils.path_detector import convert_path_for_current_mode; print(convert_path_for_current_mode('/mnt/c/Users/test/zen-mcp-server/file.py'))"
```

## Debug and Troubleshooting

### Enable Debug
```properties
MCP_DEBUG_PATH_DETECTION=true
```

### Typical Debug Messages
```
PathModeDetector: Platform detected: windows
PathModeDetector: Path mode set to 'docker' from environment  
PathModeDetector: Converted path 'C:\Users\test\zen-mcp-server\file.py' -> '/app/project/file.py'
```

### Manual Test
```python
from utils.path_detector import get_path_detector, get_platform_info

# Platform info
detector = get_path_detector()
print(f"Platform: {get_platform_info()}")
print(f"Mode: {detector.get_path_mode()}")

# Test conversion
test_path = "your_path_here"
converted = detector.convert_path(test_path)
print(f"{test_path} → {converted}")
```

## Compatibility and Performance

### Guaranteed Compatibility
- **Windows 10/11**: Native and WSL2
- **Linux**: Ubuntu, Debian, CentOS, etc.
- **macOS**: Intel and Apple Silicon
- **Docker**: All environments
- **MCP Clients**: Claude Desktop, VS Code, etc.

### Performance
- **Smart cache**: Mode and conversions are cached
- **Fast detection**: Efficient format analysis  
- **Zero overhead**: Local mode without conversion
- **Singleton pattern**: Single instance per process
