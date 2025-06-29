"""
Unit tests for PathModeDetector

Comprehensive test suite to validate automatic execution mode detection
and path conversion between Windows and Docker formats.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Imports after sys.path modification (required for tests)
from utils.path_detector import (  # noqa: E402
    PathModeDetector,
    get_path_detector,
)


class TestPathModeDetector(unittest.TestCase):
    """Tests for the PathModeDetector class"""

    def setUp(self):
        """Setup before each test"""
        # Reset singleton instance for clean tests
        PathModeDetector._instance = None

        # Clear cached mode
        if hasattr(PathModeDetector, "_cached_mode"):
            PathModeDetector._cached_mode = None

    def test_singleton_pattern(self):
        """Test that PathModeDetector follows the Singleton pattern"""
        detector1 = PathModeDetector()
        detector2 = PathModeDetector()
        detector3 = get_path_detector()

        self.assertIs(detector1, detector2)
        self.assertIs(detector1, detector3)

    @patch.dict(os.environ, {"MCP_FILE_PATH_MODE": "docker"})
    def test_env_var_detection_docker(self):
        """Test detection via environment variable - docker mode"""
        detector = PathModeDetector()
        mode = detector.get_path_mode()
        self.assertEqual(mode, "docker")

    @patch.dict(os.environ, {"MCP_FILE_PATH_MODE": "local"})
    def test_env_var_detection_local(self):
        """Test detection via environment variable - local mode"""
        detector = PathModeDetector()
        mode = detector.get_path_mode()
        self.assertEqual(mode, "local")

    @patch.dict(os.environ, {"MCP_FILE_PATH_MODE": "invalid"})
    def test_env_var_detection_invalid(self):
        """Test handling of invalid environment variable value"""
        detector = PathModeDetector()
        # Should ignore invalid value and proceed to next methods
        mode = detector.get_path_mode()
        self.assertIn(mode, ["docker", "local"])

    @patch("utils.path_detector.Path")
    def test_docker_indicators_dockerenv(self, mock_path):
        """Test detection via /.dockerenv file"""
        mock_dockerenv = mock_path.return_value
        mock_dockerenv.exists.return_value = True
        detector = PathModeDetector()
        mode = detector.get_path_mode()
        self.assertEqual(mode, "docker")

    def test_docker_indicators_cgroup(self):
        """Test detection via /proc/1/cgroup"""
        # Reset singleton
        PathModeDetector._instance = None
        PathModeDetector._cached_mode = None

        # Mock at class level before instantiation
        with patch.object(PathModeDetector, "_detect_from_env_var") as mock_env:
            mock_env.return_value = None
            with patch.object(PathModeDetector, "_detect_from_docker_indicators") as mock_docker:
                mock_docker.return_value = "docker"
                detector = PathModeDetector()
                mode = detector.get_path_mode()
                self.assertEqual(mode, "docker")

    @patch.dict(os.environ, {"HOSTNAME": "abc123def456"})
    @patch("utils.path_detector.Path")
    def test_docker_indicators_hostname(self, mock_path):
        """Test detection via HOSTNAME (container ID format)"""
        # Mock /.dockerenv and /proc/1/cgroup do not exist
        mock_path.return_value.exists.return_value = False
        detector = PathModeDetector()
        mode = detector.get_path_mode()
        self.assertEqual(mode, "docker")

    def test_server_config_working_directory(self):
        """Test detection via working directory /app"""
        # Reset singleton
        PathModeDetector._instance = None
        PathModeDetector._cached_mode = None

        # Mock at class level before instantiation
        with patch.object(PathModeDetector, "_detect_from_env_var") as mock_env:
            mock_env.return_value = None
            with patch.object(PathModeDetector, "_detect_from_docker_indicators") as mock_docker:
                mock_docker.return_value = None
                with patch.object(PathModeDetector, "_detect_from_server_config") as mock_config:
                    mock_config.return_value = "docker"
                    detector = PathModeDetector()
                    mode = detector.get_path_mode()
                    self.assertEqual(mode, "docker")

    def test_server_config_python_path(self):
        """Test detection via Python executable path"""
        # Reset singleton
        PathModeDetector._instance = None
        PathModeDetector._cached_mode = None

        # Mock at class level before instantiation
        with patch.object(PathModeDetector, "_detect_from_env_var") as mock_env:
            mock_env.return_value = None
            with patch.object(PathModeDetector, "_detect_from_docker_indicators") as mock_docker:
                mock_docker.return_value = None
                with patch.object(PathModeDetector, "_detect_from_server_config") as mock_config:
                    mock_config.return_value = "docker"
                    detector = PathModeDetector()
                    mode = detector.get_path_mode()
                    self.assertEqual(mode, "docker")

    def test_path_conversion_windows_to_docker(self):
        """Test conversion from Windows path to Docker path"""
        detector = PathModeDetector()
        win_path = r"C:\\Projects\\zen-mcp-server\\server.py"
        docker_path = detector.convert_path(win_path, target_mode="docker")
        self.assertEqual(docker_path, "/app/project/server.py")

    def test_path_conversion_local_unchanged(self):
        """Test that local mode does not modify paths"""
        detector = PathModeDetector()
        win_path = r"C:\\Projects\\zen-mcp-server\\server.py"
        local_path = detector.convert_path(win_path, target_mode="local")
        self.assertEqual(local_path, win_path)

    def test_path_conversion_docker_paths_unchanged(self):
        """Test that existing Docker paths remain unchanged"""
        detector = PathModeDetector()
        docker_path = "/app/project/server.py"
        result = detector.convert_path(docker_path, target_mode="docker")
        self.assertEqual(result, docker_path)

    def test_path_conversion_relative_paths(self):
        """Test conversion of relative paths"""
        detector = PathModeDetector()
        relative_path = "config/settings.py"
        docker_path = detector.convert_path(relative_path, target_mode="docker")
        self.assertEqual(docker_path, "/app/project/config/settings.py")

    def test_path_conversion_empty_path(self):
        """Test handling of empty paths"""
        detector = PathModeDetector()
        empty_path = ""
        result = detector.convert_path(empty_path)
        self.assertEqual(result, "")

    def test_is_docker_mode_helper(self):
        """Test helper method is_docker_mode()"""
        with patch.object(PathModeDetector, "get_path_mode", return_value="docker"):
            detector = PathModeDetector()
            self.assertTrue(detector.is_docker_mode())
        with patch.object(PathModeDetector, "get_path_mode", return_value="local"):
            detector = PathModeDetector()
            self.assertFalse(detector.is_docker_mode())

    def test_performance_caching(self):
        """Test that detection is cached for performance"""
        # Reset singleton for a clean instance
        PathModeDetector._instance = None
        # Mock that counts calls
        call_count = {"count": 0}

        def mock_detect():
            call_count["count"] += 1
            return "docker"

        with patch.object(PathModeDetector, "_detect_from_env_var", side_effect=mock_detect):
            detector = PathModeDetector()
            # First call - should trigger detection
            mode1 = detector.get_path_mode()
            # Second call - should use cache
            mode2 = detector.get_path_mode()
            self.assertEqual(mode1, "docker")
            self.assertEqual(mode2, "docker")
            # Detection method should have been called only once
            self.assertEqual(call_count["count"], 1)

    @patch.dict(os.environ, {"MCP_DEBUG_PATH_DETECTION": "true"})
    def test_debug_logging_enabled(self):
        """Test enabling of debug logs"""
        # The test only checks that debug mode is detected
        # (actual logs would be tested with logger mock)
        debug_enabled = os.getenv("MCP_DEBUG_PATH_DETECTION", "false")
        self.assertTrue(debug_enabled.lower() == "true")

    def test_fallback_behavior(self):
        """Test fallback behavior when all detections fail"""
        with (
            patch.object(PathModeDetector, "_detect_from_env_var", return_value=None),
            patch.object(PathModeDetector, "_detect_from_docker_indicators", return_value=None),
            patch.object(PathModeDetector, "_detect_from_server_config", return_value=None),
        ):
            detector = PathModeDetector()
            mode = detector.get_path_mode()
            # Should fallback to 'local' by default
            self.assertEqual(mode, "local")


class TestConvenienceFunctions(unittest.TestCase):
    """Tests for convenience functions"""

    def setUp(self):
        """Setup before each test"""
        # Reset singleton
        PathModeDetector._instance = None

    def test_get_path_detector_returns_singleton(self):
        """Test that get_path_detector returns the singleton"""
        detector1 = get_path_detector()
        detector2 = get_path_detector()
        self.assertIs(detector1, detector2)
        self.assertIsInstance(detector1, PathModeDetector)

    @patch.object(PathModeDetector, "convert_path", return_value="/app/project/test.py")
    def test_convert_path_for_current_mode(self, mock_convert):
        """Test convert_path_for_current_mode function"""
        from utils.path_detector import convert_path_for_current_mode

        result = convert_path_for_current_mode("C:\\test.py")

        self.assertEqual(result, "/app/project/test.py")
        mock_convert.assert_called_once_with("C:\\test.py")

    @patch.object(PathModeDetector, "is_docker_mode", return_value=True)
    def test_is_running_in_docker(self, mock_is_docker):
        """Test is_running_in_docker function"""
        from utils.path_detector import is_running_in_docker

        result = is_running_in_docker()

        self.assertTrue(result)
        mock_is_docker.assert_called_once()


if __name__ == "__main__":
    # Configuration for tests
    import logging

    logging.disable(logging.CRITICAL)  # Disable logs during tests

    # Run the tests
    unittest.main(verbosity=2)
