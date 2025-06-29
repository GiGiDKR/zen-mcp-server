"""
Path Mode Detector - Automatic detection of Docker vs Local execution mode

This module provides automatic detection of the execution environment to enable
dynamic path format conversion for the MCP zen server. It solves the issue
where different path formats are needed depending on whether the server runs
in Docker or in a local Python environment.

Key Features:
- Multi-level detection with priority order
- Environment variable override support
- Performance caching to avoid repeated detection
- Transparent path conversion between Windows and Docker formats
- Comprehensive logging for debugging

Detection Methods (Priority Order):
1. Environment variable MCP_FILE_PATH_MODE (manual override)
2. Docker environment indicators (/.dockerenv, /proc/1/cgroup)
3. Server configuration analysis (fallback)

Path Conversion:
- Docker mode: Windows paths → /app/project/... format
- Local mode: Paths remain unchanged
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PathModeDetector:
    """
    Detects execution mode (Docker vs local) and provides path conversion.

    This singleton class determines whether the MCP zen server is running in a
    Docker container or local Python environment, then provides automatic path
    conversion to ensure file access works correctly in both contexts.
    """

    _instance: Optional["PathModeDetector"] = None
    _cached_mode: Optional[str] = None

    def __new__(cls) -> "PathModeDetector":
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize detector with detection methods in priority order"""
        if hasattr(self, "_initialized"):
            return

        self._detection_methods = [
            self._detect_from_env_var,
            self._detect_from_docker_indicators,
            self._detect_from_server_config,
        ]
        self._initialized = True

        # Log initialization
        debug_enabled = os.getenv("MCP_DEBUG_PATH_DETECTION", "false").lower()
        if debug_enabled == "true":
            logger.info("PathModeDetector initialized with debug logging")

    def get_path_mode(self) -> str:
        """
        Get the detected path mode.

        Returns:
            'docker' if running in Docker container
            'local' if running in local environment
        """
        if self._cached_mode is not None:
            return self._cached_mode

        # Try each detection method in priority order
        for method in self._detection_methods:
            try:
                result = method()
                if result:
                    self._cached_mode = result
                    method_name = getattr(method, "__name__", str(method))
                    self._log_detection_result(method_name, result)
                    return result
            except Exception as e:
                method_name = getattr(method, "__name__", str(method))
                msg = f"Detection method {method_name} failed: {e}"
                logger.warning(msg)

        # Default fallback to local mode
        self._cached_mode = "local"
        logger.info("All detection methods failed, defaulting to 'local' mode")
        return self._cached_mode

    def convert_path(self, path: str, target_mode: Optional[str] = None) -> str:
        """
        Convert a path to the appropriate format for the current/target mode.

        Args:
            path: Input path (typically Windows format)
            target_mode: Optional target mode override ('docker' or 'local')

        Returns:
            Converted path appropriate for the execution environment
        """
        if not path:
            return path

        mode = target_mode or self.get_path_mode()

        if mode == "local":
            # Local mode: return path unchanged
            return path

        elif mode == "docker":
            # Docker mode: convert Windows paths to Docker container paths
            return self._convert_to_docker_path(path)

        else:
            msg = f"Unknown path mode '{mode}', returning original path"
            logger.warning(msg)
            return path

    def is_docker_mode(self) -> bool:
        """
        Check if running in Docker mode.

        Returns:
            True if Docker mode detected, False otherwise
        """
        return self.get_path_mode() == "docker"

    def _detect_from_env_var(self) -> Optional[str]:
        """
        Priority 1: Check MCP_FILE_PATH_MODE environment variable.

        Supports values: 'docker', 'local', 'auto'
        'auto' is treated as no override (continues to next method)

        Returns:
            'docker' or 'local' if explicitly set, None if 'auto' or unset
        """
        env_mode = os.getenv("MCP_FILE_PATH_MODE", "").lower().strip()

        if env_mode in ("docker", "local"):
            override_msg = "Environment variable override: "
            override_msg += f"MCP_FILE_PATH_MODE={env_mode}"
            self._debug_log(override_msg)
            return env_mode

        if env_mode and env_mode != "auto":
            logger.warning(f"Invalid MCP_FILE_PATH_MODE value '{env_mode}', ignoring")

        return None

    def _detect_from_docker_indicators(self) -> Optional[str]:
        """
        Priority 2: Check for Docker environment indicators.

        Looks for multiple Docker indicators:
        - /.dockerenv file (created by Docker)
        - /proc/1/cgroup contains docker paths
        - Docker-specific environment variables

        Returns:
            'docker' if Docker indicators found, 'local' otherwise
        """
        # Check for /.dockerenv file (most reliable indicator)
        if Path("/.dockerenv").exists():
            self._debug_log("Docker indicator found: /.dockerenv file exists")
            return "docker"

        # Check /proc/1/cgroup for docker paths
        try:
            cgroup_path = Path("/proc/1/cgroup")
            if cgroup_path.exists():
                content = cgroup_path.read_text()
                if "docker" in content.lower() or "/docker/" in content:
                    self._debug_log("Docker indicator found: /proc/1/cgroup contains docker")
                    return "docker"
        except (OSError, PermissionError):
            # /proc filesystem might not be available or accessible
            pass

        # Check for Docker environment variables
        docker_env_vars = [
            "DOCKER_CONTAINER",
            "DOCKER_IMAGE",
            "HOSTNAME",  # Often set to container ID in Docker
        ]

        for var in docker_env_vars:
            if os.getenv(var):
                # Additional validation for HOSTNAME (should look like container ID)
                if var == "HOSTNAME":
                    hostname = os.getenv(var, "")
                    # Container hostnames are typically 12 hex characters
                    if len(hostname) == 12 and all(c in "0123456789abcdef" for c in hostname.lower()):
                        self._debug_log(f"Docker indicator found: {var}={hostname} (container-like)")
                        return "docker"
                else:
                    self._debug_log(f"Docker indicator found: environment variable {var}")
                    return "docker"

        # No Docker indicators found
        self._debug_log("No Docker indicators detected")
        return "local"

    def _detect_from_server_config(self) -> Optional[str]:
        """
        Priority 3: Analyze runtime environment as fallback.

        This method examines runtime indicators that are universal across
        different Docker deployments and container environments.

        Returns:
            'docker' or 'local' based on runtime environment analysis
        """
        try:
            # Check current working directory
            cwd = Path.cwd()
            if str(cwd).startswith("/app"):
                self._debug_log(f"Runtime indicates Docker: working directory {cwd} is in /app")
                return "docker"

            # Check Python executable path
            python_path = sys.executable
            if "/usr/local/bin/python" in python_path or "/usr/bin/python" in python_path:
                self._debug_log(f"Runtime indicates Docker: Python path {python_path}")
                return "docker"

            # Check for container-specific filesystem patterns
            if Path("/usr/bin").exists() and Path("/bin").exists():
                # Unix-like system, check if it looks like a container
                if not Path("/home").exists() or not Path("/var/log").exists():
                    self._debug_log("Runtime indicates Docker: minimal filesystem structure")
                    return "docker"

        except Exception as e:
            logger.warning(f"Error analyzing runtime environment: {e}")

        # Default to local if no Docker indicators in runtime
        self._debug_log("Runtime analysis indicates local environment")
        return "local"

    def _convert_to_docker_path(self, windows_path: str) -> str:
        r"""
        Convert a Windows path to Docker container path format.

        Conversion rules:
        - Windows absolute paths (C:\...) → /app/project/...
        - Relative paths → kept relative but may need adjustment
        - Already Docker paths → unchanged

        Args:
            windows_path: Windows-style path

        Returns:
            Docker container path
        """
        if not windows_path:
            return windows_path

        # Already a Docker path, return unchanged
        if windows_path.startswith("/app/project/") or windows_path.startswith("/workspace/"):
            return windows_path

        # Convert Windows absolute paths
        if len(windows_path) >= 3 and windows_path[1:3] == ":\\":
            # Windows absolute path like C:\Users\...
            path_obj = Path(windows_path)

            # Try to find the project root in the path
            parts = path_obj.parts

            # Look for common project indicators
            for i, part in enumerate(parts):
                if "zen-mcp-server" in part:
                    # Found project root, convert remaining path
                    remaining_parts = parts[i + 1 :] if i + 1 < len(parts) else []
                    docker_path = "/app/project"
                    if remaining_parts:
                        docker_path += "/" + "/".join(remaining_parts)

                    msg = f"Converted Windows path '{windows_path}' → '{docker_path}'"
                    self._debug_log(msg)
                    return docker_path

            # Fallback: assume it's a project file and map to /app/project
            filename = path_obj.name
            docker_path = f"/app/project/{filename}"
            self._debug_log(f"Fallback conversion: '{windows_path}' → '{docker_path}'")
            return docker_path

        # Relative paths or other formats - assume they're within project
        if not windows_path.startswith("/"):
            docker_path = f"/app/project/{windows_path}"
            self._debug_log(f"Relative path conversion: '{windows_path}' → '{docker_path}'")
            return docker_path

        # Unix-style absolute paths - return unchanged
        return windows_path

    def _log_detection_result(self, method_name: str, result: str) -> None:
        """Log detection result for debugging"""
        logger.info(f"Path mode detected: '{result}' (method: {method_name})")

        debug_enabled = os.getenv("MCP_DEBUG_PATH_DETECTION", "false").lower() == "true"
        if debug_enabled:
            logger.info(f"PathModeDetector: Detection complete - mode='{result}', method='{method_name}'")

    def _debug_log(self, message: str) -> None:
        """Log debug message if debug mode enabled"""
        debug_enabled = os.getenv("MCP_DEBUG_PATH_DETECTION", "false").lower() == "true"
        if debug_enabled:
            logger.debug(f"PathModeDetector: {message}")


# Global instance for easy access
_detector_instance: Optional[PathModeDetector] = None


def get_path_detector() -> PathModeDetector:
    """
    Get the global PathModeDetector instance.

    Returns:
        Singleton PathModeDetector instance
    """
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = PathModeDetector()
    return _detector_instance


def convert_path_for_current_mode(path: str) -> str:
    """
    Convenience function for path conversion.

    Args:
        path: Input path to convert

    Returns:
        Path converted for current execution mode
    """
    return get_path_detector().convert_path(path)


def is_running_in_docker() -> bool:
    """
    Convenience function to check if running in Docker.

    Returns:
        True if Docker mode detected, False otherwise
    """
    return get_path_detector().is_docker_mode()
