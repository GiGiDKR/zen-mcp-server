"""
Multi-Platform Path Mode Detector - Docker vs Local path conversion

This module provides cross-platform path format conversion for Zen.
It supports Windows, Linux, macOS, and WSL2 environments with intelligent path
detection and conversion.

Key Features:
- Multi-platform support (Windows, Linux, macOS, WSL2)
- Intelligent path detection and conversion
- Simple explicit mode configuration (docker/local)
- Performance caching to avoid repeated processing
- Comprehensive logging for debugging

Modes:
- docker: Convert host paths to /app/project/... format
- local: Paths remain unchanged (default)

Platform Support:
- Windows: C:/Users/... to /app/project/...
- Linux/macOS: /home/user/... to /app/project/...
- WSL2: /mnt/c/Users/... to /app/project/...

Configuration:
Set MCP_FILE_PATH_MODE environment variable to 'docker' or 'local'
If not set, defaults to 'local'
"""

import logging
import os
import platform
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PathModeDetector:
    """
    Multi-platform path mode detector with explicit configuration.

    This singleton class uses explicit configuration to determine whether
    to convert paths for Docker container or keep them unchanged for local use.
    Supports Windows, Linux, macOS, and WSL2.
    """

    _instance: Optional["PathModeDetector"] = None
    _cached_mode: Optional[str] = None
    _platform_info: Optional[dict] = None

    def __new__(cls) -> "PathModeDetector":
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize detector"""
        if getattr(self, "_initialized", False):
            return

        PathModeDetector._platform_info = None
        self._initialized = True
        self._detect_platform()

        # Log initialization
        debug_enabled = os.getenv("MCP_DEBUG_PATH_DETECTION", "false").lower()
        if debug_enabled == "true":
            logger.info("PathModeDetector initialized (multi-platform)")
            logger.info(f"Platform info: {PathModeDetector._platform_info}")

    def _detect_platform(self):
        """Detect current platform and set platform-specific info"""
        system = platform.system().lower()

        PathModeDetector._platform_info = {
            "system": system,
            "is_windows": system == "windows",
            "is_linux": system == "linux",
            "is_macos": system == "darwin",
            "is_wsl": False,
            "path_separator": os.sep,
            "common_project_indicators": [
                "zen-mcp-server",
                "mcp-server",
                "project",
            ],
        }

        # Detect WSL2
        if system == "linux":
            try:
                # Check for WSL in /proc/version
                with open("/proc/version") as f:
                    version_info = f.read().lower()
                    if "microsoft" in version_info or "wsl" in version_info:
                        PathModeDetector._platform_info["is_wsl"] = True
                        self._debug_log("WSL2 environment detected")
            except (OSError, FileNotFoundError):
                pass

        self._debug_log(f"Platform detected: {PathModeDetector._platform_info['system']}")
        if PathModeDetector._platform_info["is_wsl"]:
            self._debug_log("WSL2 mode enabled")

    def get_path_mode(self) -> str:
        """
        Get the configured path mode.

        Returns:
            'docker' if MCP_FILE_PATH_MODE=docker
            'local' otherwise (default)
        """
        if PathModeDetector._cached_mode is not None:
            return PathModeDetector._cached_mode

        # Get mode from environment variable
        env_mode = os.getenv("MCP_FILE_PATH_MODE", "").lower().strip()

        if env_mode == "docker":
            PathModeDetector._cached_mode = "docker"
            self._debug_log("Path mode set to 'docker' from environment")
        else:
            PathModeDetector._cached_mode = "local"
            if env_mode and env_mode != "local":
                msg = f"Invalid MCP_FILE_PATH_MODE '{env_mode}', using 'local'"
                logger.warning(msg)
            self._debug_log("Path mode set to 'local' (default)")

        return PathModeDetector._cached_mode

    def convert_path(self, path: str, target_mode: Optional[str] = None) -> str:
        """
        Convert a path to the appropriate format for the current/target mode.

        Args:
            path: Input path (any platform format)
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
            # Docker mode: convert host paths to Docker container paths
            return self._convert_to_docker_path(path)

        else:
            msg = f"Unknown path mode '{mode}', returning original path"
            logger.warning(msg)
            return path

    def is_docker_mode(self) -> bool:
        """
        Check if running in Docker mode.

        Returns:
            True if Docker mode configured, False otherwise
        """
        return self.get_path_mode() == "docker"

    def _convert_to_docker_path(self, host_path: str) -> str:
        """
        Convert a host system path to Docker container path format.
        Detects path format automatically for cross-platform support.

        Args:
            host_path: Host system path (any platform format)

        Returns:
            Docker container path
        """
        if not host_path:
            return host_path

        # Already a Docker path, return unchanged
        if host_path.startswith("/app/project/") or host_path.startswith("/workspace/"):
            return host_path

        # Detect path format and convert accordingly
        return self._convert_by_path_format(host_path)

    def _convert_by_path_format(self, path: str) -> str:
        """
        Convert path based on its format, regardless of current platform.
        This enables cross-platform path processing.
        """
        # Detect path format by analyzing the string
        if self._is_windows_path(path):
            return self._convert_windows_format(path)
        elif self._is_wsl_path(path):
            return self._convert_wsl_format(path)
        elif self._is_unix_path(path):
            return self._convert_unix_format(path)
        else:
            # Relative or unrecognized format
            return self._handle_relative_path(path)

    def _is_windows_path(self, path: str) -> bool:
        """Check if path is Windows format (C:/... or C:\\...)"""
        return len(path) >= 3 and path[1] == ":" and path[2] in ("/", "\\")

    def _is_wsl_path(self, path: str) -> bool:
        """Check if path is WSL format (/mnt/...)"""
        return path.startswith("/mnt/")

    def _is_unix_path(self, path: str) -> bool:
        """Check if path is Unix format (absolute starting with /)"""
        return path.startswith("/") and not self._is_wsl_path(path)

    def _convert_windows_format(self, original_path: str) -> str:
        """Convert Windows-format path"""
        try:
            # Normalize to use forward slashes
            normalized = original_path.replace("\\", "/")
            parts = normalized.split("/")
            return self._find_project_in_parts(parts, original_path)
        except Exception:
            return self._handle_fallback_conversion(original_path)

    def _convert_wsl_format(self, original_path: str) -> str:
        """Convert WSL-format path (/mnt/c/...)"""
        parts = original_path.split("/")
        if len(parts) >= 4:  # /mnt/c/...
            # Remove /mnt/drive_letter and treat rest as Windows-like path
            remaining_parts = parts[3:]  # Skip /mnt/c
            return self._find_project_in_parts(remaining_parts, original_path)
        return self._handle_fallback_conversion(original_path)

    def _convert_unix_format(self, original_path: str) -> str:
        """Convert Unix-format path"""
        parts = original_path.split("/")
        return self._find_project_in_parts(parts, original_path)

    def _find_project_in_parts(self, parts: list, original_path: str) -> str:
        """Find project root and create relative Docker path from path parts"""
        # Ensure platform info is initialized
        if PathModeDetector._platform_info is None:
            self._detect_platform()
        if PathModeDetector._platform_info is None:
            # Still None after detection, fallback immediately
            return self._handle_fallback_conversion(original_path)

        # Strategy 1: Look for generic project containers first
        # (like "Projects"). These typically contain multiple projects,
        # so we skip the container
        for i, part in enumerate(parts):
            if "project" in part.lower() and part.lower() != "project":
                # Found generic project container like "Projects"
                next_index = i + 1
                if next_index < len(parts):
                    # Check if the next part is a specific project name to skip
                    if parts[next_index].lower() in ["zen-mcp-server", "mcp-server"]:
                        # Check what comes after the project name
                        after_project_index = next_index + 1
                        if after_project_index < len(parts):
                            remaining_after_project = parts[after_project_index:]
                            # If there's only one item (a file), include
                            # project name. If there's more than one item
                            # (subdirs), exclude project name.
                            if len(remaining_after_project) == 1:
                                # Direct file in project, include project name
                                remaining_parts = parts[next_index:]
                                docker_path = "/app/project"
                                if remaining_parts:
                                    docker_path += "/" + "/".join(remaining_parts)

                                msg = f"Converted '{original_path}' -> '{docker_path}' (included project name for direct file)"
                                self._debug_log(msg)
                                return docker_path
                            else:
                                # Subdirectories in project,
                                # skip project name
                                remaining_parts = remaining_after_project
                                docker_path = "/app/project"
                                if remaining_parts:
                                    docker_path += "/" + "/".join(remaining_parts)

                                msg = (
                                    f"Converted '{original_path}' -> '{docker_path}' (skipped project name for subdirs)"
                                )
                                self._debug_log(msg)
                                return docker_path
                        else:
                            # Only project name, no file
                            docker_path = "/app/project"
                            msg = f"Converted '{original_path}' -> '{docker_path}' (project root only)"
                            self._debug_log(msg)
                            return docker_path
                    else:
                        # Take everything after the container
                        remaining_parts = parts[next_index:]
                        docker_path = "/app/project"
                        if remaining_parts:
                            docker_path += "/" + "/".join(remaining_parts)

                        msg = f"Converted '{original_path}' -> '{docker_path}' (skipped project container)"
                        self._debug_log(msg)
                        return docker_path

        # Strategy 2: Look for specific project names (zen-mcp-server, mcp-server)
        project_names = ["zen-mcp-server", "mcp-server"]
        for project_name in project_names:
            for i, part in enumerate(parts):
                if project_name == part.lower():
                    # Found exact project name
                    # Include it if there are meaningful parent directories
                    # For Unix: skip system dirs like /opt, /usr, /var
                    # For Windows: skip drive letters
                    system_dirs = ["opt", "usr", "var", "etc", "bin", "sbin", "lib"]
                    drive_letters = ["C:", "D:", "E:", "Z:"]

                    meaningful_parents = [p for p in parts[:i] if p not in drive_letters + system_dirs and p != ""]

                    if len(meaningful_parents) > 0:
                        # Has parent directories, include project name
                        remaining_parts = parts[i:] if i < len(parts) else []
                        docker_path = "/app/project"
                        if remaining_parts:
                            docker_path += "/" + "/".join(remaining_parts)

                        msg = f"Converted '{original_path}' -> '{docker_path}' (included project name with parents)"
                        self._debug_log(msg)
                        return docker_path
                    else:
                        # No meaningful parents, skip project name
                        remaining_parts = parts[i + 1 :] if i + 1 < len(parts) else []
                        docker_path = "/app/project"
                        if remaining_parts:
                            docker_path += "/" + "/".join(remaining_parts)

                        msg = f"Converted '{original_path}' -> '{docker_path}' (skipped root project name)"
                        self._debug_log(msg)
                        return docker_path

        # Strategy 3: Fallback to generic "project" indicator
        for i, part in enumerate(parts):
            if "project" == part.lower():
                remaining_parts = parts[i + 1 :] if i + 1 < len(parts) else []
                docker_path = "/app/project"
                if remaining_parts:
                    docker_path += "/" + "/".join(remaining_parts)

                msg = f"Converted '{original_path}' -> '{docker_path}' (found generic project)"
                self._debug_log(msg)
                return docker_path

        # No project indicator found - fallback
        return self._handle_fallback_conversion(original_path)

    def _handle_fallback_conversion(self, original_path: str) -> str:
        """Handle fallback conversion when no project indicator found"""
        try:
            filename = Path(original_path).name
            docker_path = f"/app/project/{filename}"
            fallback_msg = f"Fallback: '{original_path}' -> '{docker_path}'"
            self._debug_log(fallback_msg)
            return docker_path
        except Exception:
            # Last resort - return as relative path
            return self._handle_relative_path(original_path)

    def _handle_relative_path(self, path: str) -> str:
        """Handle relative paths by mapping to /app/project"""
        # Normalize path separators to forward slashes for Docker
        normalized_path = path.replace("\\", "/")

        if not normalized_path.startswith("/"):
            docker_path = f"/app/project/{normalized_path}"
            rel_msg = f"Relative path: '{path}' -> '{docker_path}'"
            self._debug_log(rel_msg)
            return docker_path

        # Unix-style absolute paths - return unchanged
        return path

    def get_platform_info(self) -> dict:
        """Get current platform information"""
        return PathModeDetector._platform_info.copy() if PathModeDetector._platform_info else {}

    def _debug_log(self, message: str) -> None:
        """Log debug message if debug mode enabled"""
        debug_enabled = os.getenv("MCP_DEBUG_PATH_DETECTION", "false").lower()
        if debug_enabled == "true":
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
    Convert a path using the current path mode configuration.

    Args:
        path: Input path to convert (any platform format)

    Returns:
        Converted path appropriate for current mode
    """
    detector = get_path_detector()
    return detector.convert_path(path)


def is_running_in_docker() -> bool:
    """
    Check if the current configuration is set to Docker mode.

    Returns:
        True if Docker mode is configured, False otherwise
    """
    detector = get_path_detector()
    return detector.is_docker_mode()


def get_platform_info() -> dict:
    """
    Get information about the current platform.

    Returns:
        Dictionary with platform information
    """
    detector = get_path_detector()
    return detector.get_platform_info()


# Backward compatibility
MultiPlatformPathDetector = PathModeDetector
