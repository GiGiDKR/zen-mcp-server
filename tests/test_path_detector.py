"""
Unit tests for PathModeDetector - Simplified multi-platform version

Comprehensive test suite to validate mode detection and
path conversion between Windows, Linux, macOS, WSL, and Docker.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from utils.path_detector import (
    PathModeDetector,
    convert_path_for_current_mode,
    get_path_detector,
    is_running_in_docker,
)

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestPathModeDetectorBasics(unittest.TestCase):
    """Basic tests for PathModeDetector"""

    def setUp(self):
        """Setup before each test"""
        PathModeDetector._instance = None
        if hasattr(PathModeDetector, "_cached_mode"):
            PathModeDetector._cached_mode = None

        # Also clear the global detector instance
        import utils.path_detector

        utils.path_detector._detector_instance = None

    def test_singleton_pattern(self):
        """Test that PathModeDetector follows the Singleton pattern"""
        detector1 = PathModeDetector()
        detector2 = PathModeDetector()
        detector3 = get_path_detector()

        self.assertIs(detector1, detector2)
        self.assertIs(detector1, detector3)

    @patch.dict(os.environ, {"MCP_FILE_PATH_MODE": "docker"})
    def test_env_var_docker_mode(self):
        """Test Docker mode detection via environment variable"""
        detector = PathModeDetector()
        mode = detector.get_path_mode()
        self.assertEqual(mode, "docker")
        self.assertTrue(detector.is_docker_mode())

    @patch.dict(os.environ, {"MCP_FILE_PATH_MODE": "local"})
    def test_env_var_local_mode(self):
        """Test local mode detection via environment variable"""
        detector = PathModeDetector()
        mode = detector.get_path_mode()
        self.assertEqual(mode, "local")
        self.assertFalse(detector.is_docker_mode())

    @patch.dict(os.environ, {}, clear=True)
    def test_default_mode(self):
        """Test default mode without environment variable"""
        detector = PathModeDetector()
        mode = detector.get_path_mode()
        self.assertEqual(mode, "local")  # Default is local

    @patch.dict(os.environ, {"MCP_FILE_PATH_MODE": "invalid"})
    def test_invalid_mode_fallback(self):
        """Test fallback for invalid mode"""
        detector = PathModeDetector()
        mode = detector.get_path_mode()
        self.assertEqual(mode, "local")  # Should fallback to local

    def test_mode_caching(self):
        """Test caching of detected mode"""
        detector = PathModeDetector()
        mode1 = detector.get_path_mode()
        mode2 = detector.get_path_mode()
        self.assertEqual(mode1, mode2)
        self.assertIsNotNone(detector._cached_mode)


class TestWindowsPathConversion(unittest.TestCase):
    """Tests for Windows path conversion"""

    def setUp(self):
        """Setup before each test"""
        PathModeDetector._instance = None
        if hasattr(PathModeDetector, "_cached_mode"):
            PathModeDetector._cached_mode = None

    def test_windows_backslash_paths(self):
        """Test Windows paths with backslash"""
        detector = PathModeDetector()

        test_cases = [
            (r"C:\Users\dev\zen-mcp-server\main.py", "/app/project/zen-mcp-server/main.py"),
            (r"D:\Projects\zen-mcp-server\src\utils.py", "/app/project/src/utils.py"),
            (r"C:\zen-mcp-server\config.json", "/app/project/config.json"),
        ]

        for windows_path, expected_docker in test_cases:
            with self.subTest(path=windows_path):
                result = detector.convert_path(windows_path, target_mode="docker")
                self.assertEqual(result, expected_docker)

                # Local mode should preserve original
                local_result = detector.convert_path(windows_path, target_mode="local")
                self.assertEqual(local_result, windows_path)

    def test_windows_forward_slash_paths(self):
        """Test Windows paths with forward slash"""
        detector = PathModeDetector()

        test_cases = [
            ("C:/Users/dev/zen-mcp-server/main.py", "/app/project/zen-mcp-server/main.py"),
            ("D:/Projects/zen-mcp-server/src/utils.py", "/app/project/src/utils.py"),
        ]

        for windows_path, expected_docker in test_cases:
            with self.subTest(path=windows_path):
                result = detector.convert_path(windows_path, target_mode="docker")
                self.assertEqual(result, expected_docker)

    def test_windows_path_detection(self):
        """Test Windows format detection"""
        detector = PathModeDetector()

        windows_paths = [
            "C:/path/to/file",
            "C:\\path\\to\\file",
            "D:/another/path",
            "Z:\\network\\drive\\file",
        ]

        for path in windows_paths:
            with self.subTest(path=path):
                self.assertTrue(detector._is_windows_path(path))
                self.assertFalse(detector._is_wsl_path(path))
                self.assertFalse(detector._is_unix_path(path))


class TestUnixPathConversion(unittest.TestCase):
    """Tests for Unix/Linux/macOS path conversion"""

    def setUp(self):
        """Setup before each test"""
        PathModeDetector._instance = None
        if hasattr(PathModeDetector, "_cached_mode"):
            PathModeDetector._cached_mode = None

    def test_unix_linux_macos_paths(self):
        """Test Unix/Linux/macOS paths"""
        detector = PathModeDetector()

        test_cases = [
            ("/home/dev/zen-mcp-server/main.py", "/app/project/zen-mcp-server/main.py"),
            ("/Users/dev/projects/zen-mcp-server/src/utils.py", "/app/project/src/utils.py"),
            ("/opt/zen-mcp-server/config.json", "/app/project/config.json"),
        ]

        for unix_path, expected_docker in test_cases:
            with self.subTest(path=unix_path):
                result = detector.convert_path(unix_path, target_mode="docker")
                self.assertEqual(result, expected_docker)

    def test_unix_path_detection(self):
        """Test Unix format detection"""
        detector = PathModeDetector()

        unix_paths = [
            "/home/user/file",
            "/Users/user/file",
            "/opt/project/file",
            "/var/www/file",
            "/usr/local/bin/file",
        ]

        for path in unix_paths:
            with self.subTest(path=path):
                self.assertTrue(detector._is_unix_path(path))
                self.assertFalse(detector._is_windows_path(path))
                self.assertFalse(detector._is_wsl_path(path))


class TestWSLPathConversion(unittest.TestCase):
    """Tests for WSL path conversion"""

    def setUp(self):
        """Setup before each test"""
        PathModeDetector._instance = None
        if hasattr(PathModeDetector, "_cached_mode"):
            PathModeDetector._cached_mode = None

    def test_wsl_paths(self):
        """Test WSL paths (/mnt/...)"""
        detector = PathModeDetector()

        test_cases = [
            ("/mnt/c/Users/dev/zen-mcp-server/main.py", "/app/project/zen-mcp-server/main.py"),
            ("/mnt/d/Projects/zen-mcp-server/src/utils.py", "/app/project/src/utils.py"),
            ("/mnt/c/zen-mcp-server/config.json", "/app/project/config.json"),
        ]

        for wsl_path, expected_docker in test_cases:
            with self.subTest(path=wsl_path):
                result = detector.convert_path(wsl_path, target_mode="docker")
                self.assertEqual(result, expected_docker)

    def test_wsl_path_detection(self):
        """Test WSL format detection"""
        detector = PathModeDetector()

        wsl_paths = [
            "/mnt/c/path/to/file",
            "/mnt/d/another/path",
            "/mnt/z/network/file",
        ]

        for path in wsl_paths:
            with self.subTest(path=path):
                self.assertTrue(detector._is_wsl_path(path))
                self.assertFalse(detector._is_windows_path(path))
                self.assertFalse(detector._is_unix_path(path))


class TestRelativeAndSpecialPaths(unittest.TestCase):
    """Tests for relative and special paths"""

    def setUp(self):
        """Setup before each test"""
        PathModeDetector._instance = None
        if hasattr(PathModeDetector, "_cached_mode"):
            PathModeDetector._cached_mode = None

    def test_relative_paths(self):
        """Test relative paths"""
        detector = PathModeDetector()

        test_cases = [
            ("src/main.py", "/app/project/src/main.py"),
            ("config.json", "/app/project/config.json"),
            ("utils/helper.py", "/app/project/utils/helper.py"),
            ("../parent/file.py", "/app/project/../parent/file.py"),
            ("./current/file.py", "/app/project/./current/file.py"),
        ]

        for rel_path, expected_docker in test_cases:
            with self.subTest(path=rel_path):
                result = detector.convert_path(rel_path, target_mode="docker")
                self.assertEqual(result, expected_docker)

    def test_already_docker_paths(self):
        """Test already Docker-formatted paths"""
        detector = PathModeDetector()

        docker_paths = [
            "/app/project/file.py",
            "/app/project/src/main.py",
            "/workspace/project/config.json",
            "/workspace/file.py",
        ]

        for docker_path in docker_paths:
            with self.subTest(path=docker_path):
                result = detector.convert_path(docker_path, target_mode="docker")
                self.assertEqual(result, docker_path)

    def test_empty_and_edge_cases(self):
        """Test edge cases"""
        detector = PathModeDetector()

        # Empty path
        self.assertEqual(detector.convert_path("", target_mode="docker"), "")
        self.assertEqual(detector.convert_path("", target_mode="local"), "")

        # Just a filename
        result = detector.convert_path("file.py", target_mode="docker")
        self.assertEqual(result, "/app/project/file.py")

    def test_fallback_conversion(self):
        """Test fallback conversion without project indicator"""
        detector = PathModeDetector()

        test_cases = [
            # No project indicator
            ("C:/random/file.py", "/app/project/file.py"),
            ("/home/user/other/file.py", "/app/project/file.py"),
            ("/mnt/c/some/file.py", "/app/project/file.py"),
        ]

        for input_path, expected_docker in test_cases:
            with self.subTest(path=input_path):
                result = detector.convert_path(input_path, target_mode="docker")
                self.assertEqual(result, expected_docker)


class TestConvenienceFunctions(unittest.TestCase):
    """Tests for convenience functions"""

    def setUp(self):
        """Setup before each test"""
        PathModeDetector._instance = None
        if hasattr(PathModeDetector, "_cached_mode"):
            PathModeDetector._cached_mode = None

    def test_get_path_detector_singleton(self):
        """Test that get_path_detector returns the singleton"""
        detector1 = get_path_detector()
        detector2 = get_path_detector()
        self.assertIs(detector1, detector2)
        self.assertIsInstance(detector1, PathModeDetector)

    @patch.dict(os.environ, {"MCP_FILE_PATH_MODE": "docker"})
    def test_convert_path_for_current_mode(self):
        """Test convert_path_for_current_mode"""
        test_path = r"C:\Projects\zen-mcp-server\file.py"
        result = convert_path_for_current_mode(test_path)
        # Should convert to Docker format because mode is docker
        self.assertEqual(result, "/app/project/zen-mcp-server/file.py")

    @patch.dict(os.environ, {"MCP_FILE_PATH_MODE": "local"})
    def test_convert_path_for_current_mode_local(self):
        """Test convert_path_for_current_mode in local mode"""
        test_path = r"C:\Projects\zen-mcp-server\file.py"
        result = convert_path_for_current_mode(test_path)
        # Should preserve original because mode is local
        self.assertEqual(result, test_path)

    @patch.dict(os.environ, {"MCP_FILE_PATH_MODE": "docker"})
    def test_is_running_in_docker(self):
        """Test is_running_in_docker"""
        self.assertTrue(is_running_in_docker())

    @patch.dict(os.environ, {"MCP_FILE_PATH_MODE": "local"})
    def test_is_running_in_docker_local(self):
        """Test is_running_in_docker in local mode"""
        PathModeDetector._instance = None
        PathModeDetector._cached_mode = None
        self.assertFalse(is_running_in_docker())


class TestCrossPlatformCompatibility(unittest.TestCase):
    """Cross-platform compatibility tests"""

    def setUp(self):
        """Setup before each test"""
        PathModeDetector._instance = None
        if hasattr(PathModeDetector, "_cached_mode"):
            PathModeDetector._cached_mode = None

    def test_path_format_exclusivity(self):
        """Test that a path is detected as exactly one format"""
        detector = PathModeDetector()

        test_cases = [
            ("C:/path/file", 1),  # Windows
            (r"C:\path\file", 1),  # Windows
            ("/mnt/c/path/file", 1),  # WSL
            ("/home/user/file", 1),  # Unix
            ("relative/path", 0),  # None
        ]

        for path, expected_count in test_cases:
            with self.subTest(path=path):
                is_windows = detector._is_windows_path(path)
                is_wsl = detector._is_wsl_path(path)
                is_unix = detector._is_unix_path(path)

                detected_count = sum([is_windows, is_wsl, is_unix])
                self.assertEqual(detected_count, expected_count)

    @patch.dict(os.environ, {"MCP_FILE_PATH_MODE": "docker"})
    def test_mixed_platform_paths_conversion(self):
        """Test conversion of paths from different platforms"""
        detector = PathModeDetector()

        mixed_paths = [
            # Windows
            r"C:\Users\dev\zen-mcp-server\file.py",
            "D:/Projects/zen-mcp-server/src/main.py",
            # Unix
            "/home/dev/zen-mcp-server/file.py",
            "/Users/dev/zen-mcp-server/src/main.py",
            # WSL
            "/mnt/c/Users/dev/zen-mcp-server/file.py",
            # Relative
            "src/utils.py",
        ]

        for path in mixed_paths:
            with self.subTest(path=path):
                result = detector.convert_path(path)
                self.assertTrue(result.startswith("/app/project"))
                # Local mode should preserve original
                local_result = detector.convert_path(path, target_mode="local")
                self.assertEqual(local_result, path)


if __name__ == "__main__":
    # Disable logs during tests
    import logging

    logging.disable(logging.CRITICAL)

    # Run tests
    unittest.main(verbosity=2)
